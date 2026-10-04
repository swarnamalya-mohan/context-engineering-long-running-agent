from __future__ import annotations

from typing import Any

import tiktoken


def _encoder(model: str):
    try:
        return tiktoken.encoding_for_model(model)
    except Exception:
        return tiktoken.get_encoding("o200k_base")


def count_tokens(text: str, model: str) -> int:
    return len(_encoder(model).encode(text or ""))


def working_context_tokens(state: dict[str, Any], model: str) -> int:
    text = (state.get("running_summary") or "") + "\n" + "\n".join(
        state.get("working_history") or []
    )
    return count_tokens(text, model)



def select_memory(state: dict[str, Any], repo_name: str, limit: int = 8) -> dict[str, Any]:
    """Exact entity recall, bounded and deduplicated; never returns other repos."""
    seen = set()
    selected = []
    for item in reversed(state.get("evidence", [])):
        key = (item.get("claim"), item.get("source"), item.get("snippet"))
        if item.get("repo") == repo_name and key not in seen:
            seen.add(key)
            selected.append(item)
        if len(selected) >= limit:
            break
    record = (state.get("candidates", {}).get(repo_name)
              or state.get("rejected", {}).get(repo_name) or {})
    return {"repo": repo_name, "status": record.get("status"),
            "stale_fields": record.get("stale_fields", []), "evidence": selected}
