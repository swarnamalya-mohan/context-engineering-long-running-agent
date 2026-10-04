from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    phase: str
    active_change: str | None
    policy: dict[str, Any]
    previous_policy: dict[str, Any]
    candidates: dict[str, dict[str, Any]]
    rejected: dict[str, dict[str, Any]]
    evidence: list[dict[str, Any]]
    events: list[dict[str, Any]]
    working_history: list[str]
    running_summary: str
    review_queue: list[str]
    reviewed_names: list[str]
    final_recommendation: str
    metrics: dict[str, int | float]
