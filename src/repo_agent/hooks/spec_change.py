from __future__ import annotations

from typing import Any

from repo_agent.openspec_runtime import policy_delta


def impacted_candidates(old_policy: dict[str, Any], new_policy: dict[str, Any], candidates: dict[str, dict[str, Any]], rejected: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    delta = policy_delta(old_policy, new_policy)
    meaningful = set(delta) - {"applied_changes", "requirement_names"}
    if not meaningful:
        return delta, []
    # License-only changes require reassessing repos whose eligibility changed.
    if meaningful == {"allowed_licenses"}:
        old_allowed = set(old_policy.get("allowed_licenses", []))
        new_allowed = set(new_policy.get("allowed_licenses", []))
        return delta, sorted(name for name, record in {**candidates, **rejected}.items()
                             if record.get("license") in old_allowed ^ new_allowed)
    reviewed = [name for name, record in {**candidates, **rejected}.items() if record.get("analysis")]
    return delta, sorted(set(reviewed))


def stale_rejection_can_reopen(record: dict[str, Any], new_policy: dict[str, Any]) -> bool:
    reasons = record.get("rejection_reasons") or []
    if not reasons:
        return False
    if all(reason.startswith("license=") for reason in reasons):
        return record.get("license") in set(new_policy.get("allowed_licenses") or [])
    return False

