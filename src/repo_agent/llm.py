from __future__ import annotations

import json
import re
from dataclasses import dataclass

from openai import OpenAI
from repo_agent.review_schema import ReviewAnalysis


@dataclass
class LLMResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class OpenAIResponsesLLM:
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def text(self, instructions: str, user_input: str) -> LLMResult:
        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=user_input,
        )
        usage = getattr(response, "usage", None)
        return LLMResult(
            text=response.output_text,
            input_tokens=int(getattr(usage, "input_tokens", 0) or 0) if usage else 0,
            output_tokens=int(getattr(usage, "output_tokens", 0) or 0) if usage else 0,
        )

    def review(self, instructions: str, user_input: str) -> LLMResult:
        response = self.client.responses.parse(
            model=self.model,
            instructions=instructions,
            input=user_input,
            text_format=ReviewAnalysis,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ValueError(f"Review did not return structured analysis (status={response.status}).")
        usage = response.usage
        return LLMResult(
            text=parsed.model_dump_json(),
            input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
        )


def parse_json_loose(text: str) -> dict:
    value = text.strip()
    value = re.sub(r"^```(?:json)?\s*", "", value)
    value = re.sub(r"\s*```$", "", value)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", value, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))

