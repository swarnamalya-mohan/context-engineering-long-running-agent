from __future__ import annotations

from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from repo_agent.config import Settings
from repo_agent.hooks import validate_candidate
from repo_agent.models import AgentState
from repo_agent.runtime import AgentRuntime
from repo_agent.state_store import event


def build_graph(*, settings: Settings | None = None, repo_root: str | Path = ".", checkpointer=None):
    settings = settings or Settings.from_env()
    runtime = AgentRuntime(settings, repo_root)

    def initialize(state: AgentState) -> dict[str, Any]:
        policy = runtime.initial_policy()
        return {"phase": "base", "active_change": None, "policy": policy, "previous_policy": {}, "candidates": {}, "rejected": {}, "evidence": [], "events": [event("initialized", policy=policy)], "working_history": ["Loaded base OpenSpec policy."], "running_summary": "", "review_queue": [], "reviewed_names": [], "final_recommendation": "", "metrics": {"subagent_runs": 0, "input_tokens": 0, "output_tokens": 0, "compactions": 0, "raw_chars_seen": 0, "filtered_chars_sent": 0}}

    def discover(state: AgentState) -> dict[str, Any]:
        mutable = dict(state)
        items = runtime.github.search_alternatives(mutable["policy"].get("product", "Postman"), settings.target_repos)
        candidates = dict(mutable.get("candidates", {})); rejected = dict(mutable.get("rejected", {}))
        for item in items:
            record = runtime.repo_record(item)
            if record["archived"]:
                record["status"] = "rejected"; record["rejection_reasons"] = ["repository archived"]; rejected[record["full_name"]] = record; continue
            reasons = validate_candidate(record, mutable["policy"])
            if reasons:
                record["status"] = "rejected"; record["rejection_reasons"] = reasons; rejected[record["full_name"]] = record
            else:
                record["status"] = "screened"; candidates[record["full_name"]] = record
        ranked = sorted(candidates.values(), key=lambda x: (x.get("stars", 0), x.get("forks", 0)), reverse=True)
        review_queue = [record["full_name"] for record in ranked[: settings.deep_review]]
        return {"phase": "base-review", "candidates": candidates, "rejected": rejected, "review_queue": review_queue, "events": list(mutable.get("events", [])) + [event("discovery_complete", discovered=len(items), screened=len(candidates), rejected=len(rejected), queued=len(review_queue))], "working_history": list(mutable.get("working_history", [])) + [f"Discovered {len(items)} repos; queued {len(review_queue)} for deep review."]}

    def review_base(state: AgentState) -> dict[str, Any]:
        mutable = dict(state); runtime.review_names(mutable, list(mutable.get("review_queue", [])), mutable["policy"]); mutable["reviewed_names"] = sorted(name for name, record in {**mutable.get("candidates", {}), **mutable.get("rejected", {})}.items() if record.get("analysis")); mutable["phase"] = "base-reviewed"; runtime.store.save_json("base_review_state.json", mutable); return mutable

    def apply_sso_change(state: AgentState) -> dict[str, Any]:
        mutable = dict(state); _, impacted = runtime.apply_openspec_change(mutable, "require-enterprise-sso"); mutable["review_queue"] = impacted; mutable["phase"] = "sso-change"; return mutable

    def review_sso(state: AgentState) -> dict[str, Any]:
        mutable = dict(state); runtime.review_names(mutable, list(mutable.get("review_queue", [])), mutable["policy"]); mutable["phase"] = "sso-reviewed"; runtime.store.save_json("sso_review_state.json", mutable); return mutable

    def apply_agpl_change(state: AgentState) -> dict[str, Any]:
        mutable = dict(state); _, impacted = runtime.apply_openspec_change(mutable, "allow-agpl"); mutable["review_queue"] = impacted; mutable["phase"] = "agpl-change"; return mutable

    def review_agpl(state: AgentState) -> dict[str, Any]:
        mutable = dict(state); queue = [name for name in mutable.get("review_queue", []) if (mutable.get("candidates", {}).get(name) or {}).get("status") == "reopened"]
        if queue: runtime.review_names(mutable, queue, mutable["policy"])
        mutable["phase"] = "agpl-reviewed"; return mutable

    def compact(state: AgentState) -> dict[str, Any]:
        mutable = dict(state); runtime.compact_if_needed(mutable, force=True); mutable["phase"] = "compacted"; return mutable

    def finalize(state: AgentState) -> dict[str, Any]:
        mutable = dict(state); mutable["final_recommendation"] = runtime.synthesize(mutable); mutable["phase"] = "complete"; mutable.setdefault("events", []).append(event("finalized")); runtime.store.save_json("final_state.json", mutable); return mutable

    builder = StateGraph(AgentState)
    for name, fn in [("initialize", initialize), ("discover", discover), ("review_base", review_base), ("apply_sso_change", apply_sso_change), ("review_sso", review_sso), ("apply_agpl_change", apply_agpl_change), ("review_agpl", review_agpl), ("compact", compact), ("finalize", finalize)]: builder.add_node(name, fn)
    builder.add_edge(START, "initialize"); builder.add_edge("initialize", "discover"); builder.add_edge("discover", "review_base"); builder.add_edge("review_base", "apply_sso_change"); builder.add_edge("apply_sso_change", "review_sso"); builder.add_edge("review_sso", "apply_agpl_change"); builder.add_edge("apply_agpl_change", "review_agpl"); builder.add_edge("review_agpl", "compact"); builder.add_edge("compact", "finalize"); builder.add_edge("finalize", END)
    return builder.compile(checkpointer=checkpointer or InMemorySaver())
