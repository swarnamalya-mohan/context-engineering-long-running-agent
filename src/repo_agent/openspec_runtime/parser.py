from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class Requirement:
    name: str
    body: str
    scenarios: list[str] = field(default_factory=list)
    operation: str | None = None


@dataclass
class SpecDocument:
    path: Path
    requirements: list[Requirement]


def _sections(text: str) -> Iterable[tuple[str | None, str]]:
    current_operation: str | None = None
    buffer: list[str] = []

    def flush():
        nonlocal buffer
        if buffer:
            value = "\n".join(buffer).strip()
            buffer = []
            return value
        return None

    for line in text.splitlines():
        m = re.match(r"^## (ADDED|MODIFIED|REMOVED|RENAMED) Requirements\s*$", line)
        if m:
            previous = flush()
            if previous:
                yield current_operation, previous
            current_operation = m.group(1)
            continue
        buffer.append(line)
    previous = flush()
    if previous:
        yield current_operation, previous


def parse_spec(path: str | Path) -> SpecDocument:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    requirements: list[Requirement] = []

    for operation, section in _sections(text):
        matches = list(re.finditer(r"^### Requirement: (.+?)\s*$", section, flags=re.M))
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
            block = section[start:end].strip()
            scenario_matches = list(re.finditer(r"^#### Scenario: (.+?)\s*$", block, flags=re.M))
            if scenario_matches:
                body = block[: scenario_matches[0].start()].strip()
                scenarios = []
                for s_index, s_match in enumerate(scenario_matches):
                    s_start = s_match.start()
                    s_end = scenario_matches[s_index + 1].start() if s_index + 1 < len(scenario_matches) else len(block)
                    scenarios.append(block[s_start:s_end].strip())
            else:
                body = block
                scenarios = []

            requirements.append(
                Requirement(
                    name=match.group(1).strip(),
                    body=body,
                    scenarios=scenarios,
                    operation=operation,
                )
            )

    return SpecDocument(path=path, requirements=requirements)
