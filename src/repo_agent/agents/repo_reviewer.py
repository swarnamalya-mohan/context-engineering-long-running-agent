from __future__ import annotations

import json
from typing import Any

from repo_agent.agents.rules import select_rules
from repo_agent.hooks import filter_tool_output
from repo_agent.llm import OpenAIResponsesLLM, parse_json_loose
from repo_agent.skills import SKILLS
from repo_agent.tools.github import GitHubTool

BASE_INSTRUCTIONS = """
You are an evidence-first open-source repository analyst.
Return ONLY valid JSON. Do not use Markdown fences.
Never guess an unsupported capability; use null when evidence is insufficient.
Distinguish open-source functionality from paid/enterprise-only functionality.

JSON shape:
{
  "summary": "short description",
  "self_hosted": true,
  "rest_client": true,
  "graphql": null,
  "team_collaboration": true,
  "openapi": null,
  "enterprise_sso": null,
  "enterprise_sso_paid_only": null,
  "strengths": ["..."],
  "risks": ["..."],
  "evidence": [{"claim": "...", "source": "README/release/metadata", "snippet": "short evidence"}],
  "confidence": 0.0
}
Boolean fields may also be false or null.
"""


def choose_skills(repo: dict[str, Any], filtered_readme: str, policy: dict[str, Any]) -> list[str]:
    names = ["feature_verification"]
    if policy.get("enterprise_sso_required"):
        names.append("enterprise_sso_verification")
    if (repo.get("license") or "UNKNOWN") in {"UNKNOWN", "NOASSERTION", "OTHER"}:
        names.append("license_audit")
    return names


def review_repository(*, repo: dict[str, Any], policy: dict[str, Any], github: GitHubTool, llm: OpenAIResponsesLLM, pruned_readme_chars: int, store=None, memory=None) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        raw_readme = github.read_readme(repo["full_name"])
    except Exception as exc:
        raw_readme = f"README unavailable: {exc}"
    artifact = None
    if store is not None:
        import hashlib
        digest = hashlib.sha256(raw_readme.encode()).hexdigest()
        artifact = str(store.save_json(f"raw/{digest}.json", {
            "repo": repo["full_name"], "source": "README", "text": raw_readme}))
    filtered, firewall_metrics = filter_tool_output(raw_readme, pruned_readme_chars)
    try:
        releases = github.releases(repo["full_name"], 3)
    except Exception:
        releases = []
    rules = select_rules(repo, filtered, policy)
    skill_names = choose_skills(repo, filtered, policy)
    # Prior conclusions and rankings must not masquerade as fresh source facts.
    metadata = {key: repo.get(key) for key in (
        "full_name", "html_url", "description", "stars", "forks", "license",
        "archived", "pushed_at", "language")}
    jit_files = []
    jit_evidence = []
    jit_errors = []
    if policy.get("enterprise_sso_required"):
        try:
            paths = github.file_map(repo["full_name"])
            selected = sorted(path for path in paths if
                any(term in path.lower() for term in ("sso", "saml", "oidc", "authentication"))
                and path.lower().endswith((".md", ".mdx", ".rst", ".txt")))[:3]
            for path in selected:
                text = github.read_file(repo["full_name"], path)
                if store is not None:
                    import hashlib
                    digest = hashlib.sha256(text.encode()).hexdigest()
                    store.save_json(f"raw/{digest}.json", {"repo": repo["full_name"], "source": path, "text": text})
                jit_files.append(path)
                jit_evidence.append({"path": path, "text": text[:2000]})
        except Exception as exc:
            jit_errors.append(str(exc))
    payload = f"""
CURRENT EFFECTIVE OPENSPEC POLICY:
{json.dumps(policy, indent=2, default=str)}

REPOSITORY METADATA:
{json.dumps(metadata, indent=2, default=str)}

RECENT RELEASES:
{json.dumps(releases, indent=2)}

FILTERED README EVIDENCE:
{filtered}

JUST-IN-TIME AUTHENTICATION DOCUMENTS:
{json.dumps(jit_evidence, default=str)}

SELECTED MEMORY (historical evidence, not a current verdict):
{json.dumps(memory or {}, default=str)}

RELEVANCE-GATED RULES:
{''.join(rules)}

ON-DEMAND SKILLS:
{''.join(SKILLS[name] for name in skill_names)}
"""
    result = llm.text(BASE_INSTRUCTIONS, payload)
    parsed = parse_json_loose(result.text)
    from repo_agent.context import count_tokens
    telemetry = {**firewall_metrics, "raw_artifact": artifact, "jit_files": jit_files, "jit_errors": jit_errors,
                 "raw_tokens": count_tokens(raw_readme, llm.model),
                 "filtered_tokens": count_tokens(filtered, llm.model),
                 "prompt_tokens": count_tokens(BASE_INSTRUCTIONS + payload, llm.model),
                 "selected_memory_count": len((memory or {}).get("evidence", [])), "loaded_skills": skill_names, "rule_count": len(rules), "input_tokens": result.input_tokens, "output_tokens": result.output_tokens}
    return parsed, telemetry

