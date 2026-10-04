# Context Engineering for Long-Running Agents

Conference demo project: a LangGraph agent that researches open-source alternatives to Postman while demonstrating context engineering, OpenSpec-driven requirement changes, isolated subagents, deterministic hooks, external evidence, and compaction.

## Architecture

- **OpenSpec** = durable intent and explicit requirement changes
- **LangGraph** = long-running orchestration and checkpoints
- **OpenAI Responses API** = repo-review and synthesis reasoning
- **GitHub API** = repository discovery, README evidence, releases
- **Rules** = relevance-gated instructions
- **Skills** = procedures loaded only when needed
- **Hooks** = deterministic tool filtering, validation, spec-change handling, pre-compaction persistence
- **External evidence/state** = repo facts and rejection history stay outside transient LLM context

> **Graph state is what the system knows. Context is what the model sees right now.**

## Demo storyline

```text
Base OpenSpec
  ↓
Discover GitHub candidates
  ↓
Metadata screening
  ↓
Isolated repo-review subagents
  ↓
Store evidence + rank
  ↓
OpenSpec change: enterprise SSO becomes mandatory
  ↓
Re-evaluate prior candidates
  ↓
Load SSO verification skill only now
  ↓
OpenSpec change: AGPL-3.0 becomes allowed
  ↓
Reopen stale license rejections
  ↓
Force compaction
  ↓
Evidence-backed Top 3
```

There is intentionally **no Kubernetes spec change**. The main SDD change is **enterprise SSO becoming mandatory**, which directly changes the product-selection outcome.

## Repository structure

```text
openspec/
  specs/repo-evaluation/spec.md
  changes/
    require-enterprise-sso/
    allow-agpl/

src/repo_agent/
  graph.py
  runtime.py
  agents/
  hooks/
  skills/
  tools/
  openspec_runtime/

notebooks/
  conference_demo.ipynb

tests/
```

## Run locally

```bash
git clone https://github.com/swarnamalya-mohan/context-engineering-long-running-agent.git
cd context-engineering-long-running-agent

python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Set environment variables:

```bash
export OPENAI_API_KEY="..."
export GITHUB_TOKEN="..."
export OPENAI_MODEL="gpt-5.4-mini"
export TARGET_REPOS=30
export DEEP_REVIEW=10
```

Run with streamed LangGraph updates:

```bash
python -m repo_agent --stream
```

For the full conference experiment:

```bash
export TARGET_REPOS=100
export DEEP_REVIEW=20
python -m repo_agent --stream
```

Artifacts are written to `artifacts/`, including pre-compaction snapshots and final state.

## OpenSpec

The durable source of truth is:

```text
openspec/specs/repo-evaluation/spec.md
```

The first live requirement change is:

```text
openspec/changes/require-enterprise-sso/
```

The agent converts the human-readable OpenSpec artifacts into a compact runtime policy. The Markdown spec remains the auditable source of truth.

## Context engineering mapping

| Concept | Implementation |
|---|---|
| Durable intent | OpenSpec main spec |
| Requirement change | OpenSpec delta |
| Conditional rules | `agents/rules.py` |
| On-demand skills | `skills/catalog.py` |
| Tool-output firewall | `hooks/context_firewall.py` |
| Hard validation | `hooks/validation.py` |
| Spec-change hook | `hooks/spec_change.py` |
| Pre-compaction checkpoint | `hooks/pre_compact.py` |
| Isolated subagents | `agents/repo_reviewer.py` |
| Long-running orchestration | `graph.py` |
| Durable evidence | LangGraph state + `artifacts/` |

## Tests

```bash
pip install -e '.[dev]'
pytest -q
```

The unit tests do not require API keys.

## Conference reliability

Run one full experiment before the talk and keep `artifacts/final_state.json` as a fallback. The live demo should show the behavior, but the conference should not depend on Wi-Fi or API availability.
