from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from pathlib import Path
from typing import Any

from repo_agent.agents.repo_reviewer import review_repository
from repo_agent.config import Settings
from repo_agent.context import working_context_tokens
from repo_agent.hooks import checkpoint_before_compaction, impacted_candidates, stale_rejection_can_reopen, validate_candidate
from repo_agent.llm import OpenAIResponsesLLM
from repo_agent.openspec_runtime import apply_change, load_main_policy
from repo_agent.scoring import score_candidate
from repo_agent.skills import SKILLS
from repo_agent.state_store import ArtifactStore, event
from repo_agent.tools.github import GitHubTool


class AgentRuntime:
    def __init__(self, settings: Settings, repo_root: str | Path = "."):
        self.settings = settings
        self.repo_root = Path(repo_root).resolve()
        self.github = GitHubTool(settings.github_token, settings.max_readme_chars)
        self.llm = OpenAIResponsesLLM(settings.openai_api_key, settings.openai_model)
        self.store = ArtifactStore(self.repo_root / "artifacts")

    def initial_policy(self) -> dict[str, Any]:
        return load_main_policy(self.repo_root)

    @staticmethod
    def repo_record(item: dict[str, Any]) -> dict[str, Any]:
        license_obj = item.get("license") or {}
        license_id = (license_obj.get("spdx_id") if isinstance(license_obj, dict) else str(license_obj or "UNKNOWN")) or "UNKNOWN"
        return {"full_name": item["full_name"], "html_url": item.get("html_url"), "description": item.get("description"), "stars": item.get("stargazers_count", 0), "forks": item.get("forks_count", 0), "open_issues": item.get("open_issues_count", 0), "language": item.get("language"), "license": license_id, "archived": item.get("archived", False), "pushed_at": item.get("pushed_at"), "analysis": None, "score": None, "status": "discovered", "rejection_reasons": [], "spec_version": "base"}

    def compact_if_needed(self, state: dict[str, Any], force: bool = False) -> None:
        tokens = working_context_tokens(state, self.settings.openai_model)
        if not force and tokens < self.settings.context_compact_at_tokens:
            return
        history = state.get("working_history") or []
        if not history:
            return
        metrics = state.setdefault("metrics", {})
        index = int(metrics.get("compactions", 0)) + 1
        checkpoint = checkpoint_before_compaction(state, self.store, index)
        result = self.llm.text("Compact only transient execution history. Preserve current phase, unresolved questions, and recent decisions needed for the next action. Do not duplicate durable repo facts, evidence, rejections, or OpenSpec requirements.", "\n\n".join(history)[-60000:])
        state["running_summary"] = result.text
        state["working_history"] = []
        metrics["compactions"] = index
        metrics["input_tokens"] = int(metrics.get("input_tokens", 0)) + result.input_tokens
        metrics["output_tokens"] = int(metrics.get("output_tokens", 0)) + result.output_tokens
        state.setdefault("events", []).append(event("compaction", before_tokens=tokens, after_tokens=working_context_tokens(state, self.settings.openai_model), durable_checkpoint=str(checkpoint)))

    def review_names(self, state: dict[str, Any], names: list[str], policy: dict[str, Any]) -> None:
        candidates = state.setdefault("candidates", {})
        rejected = state.setdefault("rejected", {})
        evidence = state.setdefault("evidence", [])
        metrics = state.setdefault("metrics", {})
        source_records = {**rejected, **candidates}
        results = {}
        with ThreadPoolExecutor(max_workers=self.settings.max_workers) as pool:
            futures = {pool.submit(review_repository, repo=deepcopy(source_records[name]), policy=policy, github=self.github, llm=self.llm, pruned_readme_chars=self.settings.pruned_readme_chars): name for name in names if name in source_records}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results[name] = future.result()
                except Exception as exc:
                    state.setdefault("events", []).append(event("review_error", repo=name, error=str(exc)))
        for name, (analysis, telemetry) in results.items():
            record = candidates.get(name) or rejected.pop(name, None)
            if not record:
                continue
            candidates[name] = record
            record["analysis"] = analysis
            record["spec_version"] = "+".join(policy.get("applied_changes") or []) or "base"
            record["score"] = score_candidate(record, policy)
            reasons = validate_candidate(record, policy)
            record["rejection_reasons"] = reasons
            if reasons:
                record["status"] = "rejected"
                rejected[name] = candidates.pop(name)
            else:
                record["status"] = "evaluated"
            for item in analysis.get("evidence") or []:
                evidence.append({"repo": name, "spec_version": record["spec_version"], "claim": item.get("claim"), "source": item.get("source"), "snippet": str(item.get("snippet", ""))[:240]})
            metrics["subagent_runs"] = int(metrics.get("subagent_runs", 0)) + 1
            metrics["input_tokens"] = int(metrics.get("input_tokens", 0)) + int(telemetry.get("input_tokens", 0))
            metrics["output_tokens"] = int(metrics.get("output_tokens", 0)) + int(telemetry.get("output_tokens", 0))
            metrics["raw_chars_seen"] = int(metrics.get("raw_chars_seen", 0)) + int(telemetry.get("raw_chars", 0))
            metrics["filtered_chars_sent"] = int(metrics.get("filtered_chars_sent", 0)) + int(telemetry.get("filtered_chars", 0))
            state.setdefault("events", []).append(event("repo_reviewed", repo=name, status=record["status"], score=record["score"], loaded_skills=telemetry.get("loaded_skills", []), context_reduction_pct=telemetry.get("reduction_pct")))
            state.setdefault("working_history", []).append(f"Reviewed {name}; status={record['status']}; score={record['score']}; reasons={record['rejection_reasons']}")
        self.compact_if_needed(state)

    def apply_openspec_change(self, state: dict[str, Any], change_name: str) -> tuple[dict[str, Any], list[str]]:
        old = deepcopy(state["policy"])
        new = apply_change(old, self.repo_root, change_name)
        delta, impacted = impacted_candidates(old, new, state.get("candidates", {}), state.get("rejected", {}))
        state["previous_policy"] = old
        state["policy"] = new
        state["active_change"] = change_name
        reopened = []
        for name, record in list((state.get("rejected") or {}).items()):
            if stale_rejection_can_reopen(record, new):
                reopened.append(name)
                record["status"] = "reopened"
                record["rejection_reasons"] = []
                state["candidates"][name] = state["rejected"].pop(name)
        impacted = sorted(set(impacted + reopened))
        state.setdefault("events", []).append(event("openspec_change_applied", change=change_name, delta=delta, impacted_count=len(impacted), reopened=reopened))
        state.setdefault("working_history", []).append(f"Applied OpenSpec change {change_name}; impacted={len(impacted)}; reopened={reopened}")
        return delta, impacted

    def synthesize(self, state: dict[str, Any], top_n: int = 8) -> str:
        active = [record for record in state.get("candidates", {}).values() if record.get("analysis") and record.get("status") != "rejected"]
        active.sort(key=lambda record: record.get("score") or 0, reverse=True)
        finalists = active[:top_n]
        names = {record["full_name"] for record in finalists}
        evidence = [item for item in state.get("evidence", []) if item["repo"] in names]
        compact = [{"repo": r["full_name"], "url": r.get("html_url"), "score": r.get("score"), "license": r.get("license"), "stars": r.get("stars"), "analysis": r.get("analysis")} for r in finalists]
        prompt = f"CURRENT EFFECTIVE OPENSPEC POLICY:\n{json.dumps(state['policy'], indent=2)}\n\nFINALISTS:\n{json.dumps(compact, indent=2)}\n\nDURABLE EVIDENCE:\n{json.dumps(evidence[:100], indent=2)}\n\n{SKILLS['final_comparison']}\nReturn a concise Top 3 with fit, evidence, caveats, and the most important rank change caused by OpenSpec changes."
        result = self.llm.text("You are the final decision agent. Use only the current policy and supplied evidence.", prompt)
        metrics = state.setdefault("metrics", {})
        metrics["input_tokens"] = int(metrics.get("input_tokens", 0)) + result.input_tokens
        metrics["output_tokens"] = int(metrics.get("output_tokens", 0)) + result.output_tokens
        return result.text
