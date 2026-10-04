from __future__ import annotations

from typing import Any
import pandas as pd


def candidate_frame(state: dict[str, Any]) -> pd.DataFrame:
    rows = list((state.get("candidates") or {}).values()) + list((state.get("rejected") or {}).values())
    if not rows: return pd.DataFrame()
    frame = pd.DataFrame(rows); keep = ["full_name", "score", "license", "stars", "status", "spec_version", "rejection_reasons"]
    return frame[[column for column in keep if column in frame.columns]]


def evidence_frame(state: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(state.get("evidence") or [])


def event_frame(state: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(state.get("events") or [])
