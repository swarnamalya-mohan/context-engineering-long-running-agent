from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


def _bool_score(value: Any) -> float:
    if value is True:
        return 1.0
    if value is False:
        return 0.0
    return 0.35


def _activity_score(pushed_at: str | None) -> float:
    if not pushed_at:
        return 0.0
    try:
        pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    months = max(0.0, (datetime.now(timezone.utc) - pushed).days / 30.44)
    return max(0.0, min(1.0, 1 - months / 24.0))


def score_candidate(record: dict[str, Any], policy: dict[str, Any]) -> float:
    analysis = record.get("analysis") or {}
    feature_fit = sum([
        _bool_score(analysis.get("self_hosted")),
        _bool_score(analysis.get("rest_client")),
        _bool_score(analysis.get("team_collaboration")),
        _bool_score(analysis.get("graphql")),
        _bool_score(analysis.get("openapi")),
    ]) / 5
    enterprise_fit = _bool_score(analysis.get("enterprise_sso"))
    if analysis.get("enterprise_sso_paid_only") is True:
        enterprise_fit = 0.0
    project_health = _activity_score(record.get("pushed_at"))
    community = min(1.0, math.log10(max(10, record.get("stars", 0))) / 5.0)
    components = {"feature_fit": feature_fit, "project_health": project_health, "enterprise_fit": enterprise_fit, "community": community}
    weights = policy.get("weights") or {}
    total = sum(components[key] * weights.get(key, 0.0) for key in components)
    return round(total * 100, 2)
