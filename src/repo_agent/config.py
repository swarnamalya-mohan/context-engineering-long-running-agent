from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str = "gpt-5.4-mini"
    github_token: str | None = None
    target_repos: int = 30
    deep_review: int = 10
    max_workers: int = 4
    enable_sso_demo: bool = False
    context_compact_at_tokens: int = 12000
    max_readme_chars: int = 30000
    pruned_readme_chars: int = 8000

    @classmethod
    def from_env(cls) -> "Settings":
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is required")
        return cls(
            openai_api_key=key,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
            github_token=os.getenv("GITHUB_TOKEN"),
            target_repos=int(os.getenv("TARGET_REPOS", "30")),
            deep_review=int(os.getenv("DEEP_REVIEW", "10")),
            max_workers=int(os.getenv("MAX_WORKERS", "4")),
            enable_sso_demo=os.getenv("ENABLE_SSO_DEMO", "false").lower() in {"true", "1", "yes"},
        )

