from __future__ import annotations

FEATURE_TERMS = ["self-host", "self hosted", "rest", "graphql", "openapi", "team", "collaboration", "sso", "saml", "oidc", "rbac", "enterprise", "license", "docker", "collection", "workspace"]


def filter_tool_output(raw: str, max_chars: int = 8000) -> tuple[str, dict[str, float | int]]:
    lines = raw.splitlines()
    kept: list[str] = []
    for line in lines:
        stripped = line.strip()
        low = stripped.lower()
        if stripped.startswith("#") or any(term in low for term in FEATURE_TERMS):
            kept.append(stripped)
    result = "\n".join(kept)
    result = (result if result.strip() else raw)[:max_chars]
    return result, {"raw_chars": len(raw), "filtered_chars": len(result), "reduction_pct": round(100 * (1 - len(result) / max(1, len(raw))), 1)}
