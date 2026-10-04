from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def validate_candidate(record: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    license_id = record.get("license") or "UNKNOWN"
    allowed = set(policy.get("allowed_licenses") or [])
    if license_id != "UNKNOWN" and allowed and license_id not in allowed:
        reasons.append(f"license={license_id} not allowed")
    months = policy.get("active_within_months")
    pushed_at = record.get("pushed_at")
    if months and pushed_at:
        try:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - pushed).days > months * 31:
                reasons.append(f"project inactive for >{months} months")
        except ValueError:
            pass
    analysis = record.get("analysis") or {}
    if analysis:
        checks = {"self_hosted_required": "self_hosted", "rest_client_required": "rest_client", "team_collaboration_required": "team_collaboration", "enterprise_sso_required": "enterprise_sso"}
        for policy_key, analysis_key in checks.items():
            if policy.get(policy_key) is True and analysis.get(analysis_key) is False:
                reasons.append(f"hard requirement failed: {analysis_key}")
        if policy.get("enterprise_sso_required") and analysis.get("enterprise_sso_paid_only") is True:
            reasons.append("hard requirement failed: enterprise_sso is paid-only")
    return reasons
