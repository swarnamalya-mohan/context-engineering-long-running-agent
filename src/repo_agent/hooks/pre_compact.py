from __future__ import annotations

from pathlib import Path
from typing import Any

from repo_agent.state_store import ArtifactStore


def checkpoint_before_compaction(state: dict[str, Any], store: ArtifactStore, compaction_index: int) -> Path:
    durable = {"policy": state.get("policy"), "candidates": state.get("candidates", {}), "rejected": state.get("rejected", {}), "evidence": state.get("evidence", [])}
    return store.save_json(f"precompact_{compaction_index}.json", durable)
