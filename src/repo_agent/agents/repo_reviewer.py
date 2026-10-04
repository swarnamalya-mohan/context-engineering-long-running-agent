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


def review_repository(*, repo: dict[str, Any], policy: dict[str, Any], github: GitHubTool, llm: OpenAIResponsesLLM, pruned_readme_chars: int) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        raw_readme = github.read_readme(repo["full_name"])
    except Exception as exc:
        raw_readme = f"README unavailable: {exc}"
    filtered, firewall_metrics = filter_tool_output(raw_readme, pruned_readme_chars)
    try:
        releases = github.releases(repo["full_name"], 3)
    except Exception:
        releases = []
    rules = select_rules(repo, filtered, policy)
    skill_names = choose_skills(repo, filtered, policy)
    payload = f"""
CURRENT EFFECTIVE OPENSPEC POLICY:
{json.dumps(policy, indent=2, default=str)}

REPOSITORY METADATA:
{json.dumps(repo, indent=2, default=str)}

RECENT RELEASES:
{json.dumps(releases, indent=2)}

FILTERED README EVIDENCE:
{filtered}

RELEVANCE-GATED RULES:
{''.join(rules)}

ON-DEMAND SKILLS:
{''.join(SKILLS[name] for name in skill_names)}
"""
    result = llm.text(BASE_INSTRUCTIONS, payload)
    parsed = parse_json_loose(result.text)
    telemetry = {**firewall_metrics, "loaded_skills": skill_names, "rule_count": len(rules), "input_tokens": result.input_tokens, "output_tokens": result.output_tokens}
    return parsed, telemetry
