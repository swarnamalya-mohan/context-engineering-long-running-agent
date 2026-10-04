from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .parser import Requirement, parse_spec

DEFAULT_WEIGHTS = {"feature_fit": 0.45, "project_health": 0.20, "enterprise_fit": 0.20, "community": 0.15}


def base_policy() -> dict[str, Any]:
    return {"product": "Postman", "self_hosted_required": False, "rest_client_required": False, "team_collaboration_required": False, "enterprise_sso_required": False, "active_within_months": None, "allowed_licenses": [], "weights": deepcopy(DEFAULT_WEIGHTS), "requirement_names": [], "applied_changes": []}


def _apply_requirement(policy: dict[str, Any], requirement: Requirement) -> None:
    name = requirement.name.lower()
    body = requirement.body
    if requirement.name not in policy["requirement_names"]:
        policy["requirement_names"].append(requirement.name)
    if name == "self-hosted deployment": policy["self_hosted_required"] = True
    elif name == "rest client capability": policy["rest_client_required"] = True
    elif name == "team collaboration": policy["team_collaboration_required"] = True
    elif name == "enterprise sso": policy["enterprise_sso_required"] = True
    elif name == "active project": policy["active_within_months"] = 12
    elif name == "allowed licenses":
        known = ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "AGPL-3.0"]
        policy["allowed_licenses"] = [license_id for license_id in known if license_id in body]


def load_main_policy(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root)
    document = parse_spec(root / "openspec/specs/repo-evaluation/spec.md")
    policy = base_policy()
    for requirement in document.requirements:
        _apply_requirement(policy, requirement)
    return policy


def apply_change(policy: dict[str, Any], repo_root: str | Path, change_name: str) -> dict[str, Any]:
    root = Path(repo_root)
    document = parse_spec(root / f"openspec/changes/{change_name}/specs/repo-evaluation/spec.md")
    updated = deepcopy(policy)
    for requirement in document.requirements:
        if requirement.operation in {"ADDED", "MODIFIED", None}:
            _apply_requirement(updated, requirement)
    if change_name not in updated["applied_changes"]:
        updated["applied_changes"].append(change_name)
    return updated


def policy_delta(old: dict[str, Any], new: dict[str, Any]) -> dict[str, dict[str, Any]]:
    keys = sorted(set(old) | set(new))
    return {key: {"old": old.get(key), "new": new.get(key)} for key in keys if old.get(key) != new.get(key)}
