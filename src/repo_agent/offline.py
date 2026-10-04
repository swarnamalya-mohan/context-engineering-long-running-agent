"""Synthetic fixture demo using the same graph/runtime; no network or API key."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from repo_agent.config import Settings
from repo_agent.graph import build_graph
from repo_agent.llm import LLMResult
from repo_agent.runtime import AgentRuntime


class FixtureGitHub:
    def search_alternatives(self, product, target):
        return [{"full_name": f"demo/{name}", "license": {"spdx_id": license_id},
                 "stargazers_count": stars, "pushed_at": datetime.now(timezone.utc).isoformat(),
                 "html_url": f"https://example.invalid/{name}"}
                for name, license_id, stars in [
                    ("alpha", "MIT", 300), ("beta", "Apache-2.0", 200),
                    ("gamma", "AGPL-3.0", 100)]]

    def read_readme(self, name):
        return ("Unrelated installation narrative.\n" * 1500 +
                "# Features\nSelf-hosted REST client with team collaboration.\n")

    def releases(self, name, n):
        return []

    def file_map(self, name):
        return ["README.md", "docs/enterprise-sso.md", "docs/tutorial.md"]

    def read_file(self, name, path):
        if name.endswith("alpha"):
            return "Enterprise SSO is not supported."
        return "Self-hosted open-source edition supports enterprise SAML SSO."


class FixtureLLM:
    """Explicitly scripted responses, not evidence of live LLM quality."""
    model = "gpt-4o-mini"

    def text(self, instructions, user_input):
        if instructions.startswith("Compact"):
            return LLMResult("Repository reviews completed. Continue under current policy; consult durable evidence.")
        if instructions.startswith("You are the final"):
            return LLMResult("Verified synthetic finalists: demo/beta and demo/gamma. Alpha lost eligibility after SSO became mandatory.")
        metadata = json.loads(user_input.split("REPOSITORY METADATA:\n", 1)[1].split("\n\nRECENT RELEASES:", 1)[0])
        sso = "SKILL: ENTERPRISE SSO VERIFICATION" in user_input
        supported = not metadata["full_name"].endswith("alpha")
        analysis = {"summary": "Synthetic API client", "self_hosted": True,
                    "rest_client": True, "team_collaboration": True,
                    "enterprise_sso": supported if sso else None,
                    "enterprise_sso_paid_only": False if sso else None,
                    "confidence": 1.0, "strengths": [], "risks": [],
                    "evidence": [{"claim": "enterprise_sso" if sso else "rest_client",
                                  "source": "docs/enterprise-sso.md" if sso else "README",
                                  "snippet": "Supported" if supported else "No enterprise SSO"}]}
        return LLMResult(json.dumps(analysis))


def fixture_runtime(repo_root):
    runtime = AgentRuntime(Settings(openai_api_key="offline-placeholder", max_workers=1), repo_root, github=FixtureGitHub(), llm=FixtureLLM())
    runtime.github = FixtureGitHub()
    runtime.llm = FixtureLLM()
    return runtime


def run_offline(repo_root="."):
    runtime = fixture_runtime(repo_root)
    graph = build_graph(settings=runtime.settings, repo_root=repo_root, runtime=runtime)
    config = {"configurable": {"thread_id": "offline-demo"}}
    for update in graph.stream({}, config, stream_mode="updates"):
        phase = next(iter(update))
        state = next(iter(update.values()))
        print(f"{phase}: {len(state.get('events', []))} events")
    state = graph.get_state(config).values
    runtime.store.save_json("offline_final_state.json", state)
    return state


if __name__ == "__main__":
    state = run_offline()
    print(state["final_recommendation"])
