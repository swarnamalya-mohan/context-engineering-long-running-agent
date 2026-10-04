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
