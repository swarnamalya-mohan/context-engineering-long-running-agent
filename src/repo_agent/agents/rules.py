from __future__ import annotations

from typing import Any

RULES = {
    "project_health": "PROJECT HEALTH RULE: Popularity is not maintenance. Prefer recent activity and explicit evidence.",
    "license": "LICENSE RULE: Treat GitHub license metadata as evidence but flag ambiguity or commercial licensing caveats.",
    "enterprise": "ENTERPRISE FEATURE RULE: If SSO, RBAC, audit logs, teams, or enterprise editions are mentioned, distinguish OSS from paid-only availability.",
}


def select_rules(repo: dict[str, Any], readme: str, policy: dict[str, Any]) -> list[str]:
    selected = [RULES["project_health"]]
    low = readme.lower()
    if repo.get("license") or "license" in low:
        selected.append(RULES["license"])
    if policy.get("enterprise_sso_required") or any(term in low for term in ["sso", "saml", "oidc", "rbac", "enterprise"]):
        selected.append(RULES["enterprise"])
    return selected
