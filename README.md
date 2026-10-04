# Context engineering for a long-running repository agent

An OpenAI + LangGraph conference demo showing **WRITE → SELECT → COMPRESS → ISOLATE → INVALIDATE** under changing OpenSpec requirements.

## Run in Colab

[Open the conference notebook](https://colab.research.google.com/github/swarnamalya-mohan/context-engineering-long-running-agent/blob/feature/initial-agent-implementation/notebooks/conference_demo.ipynb)

The implementation currently lives on `feature/initial-agent-implementation` (draft PR #1), so clone that branch:

```bash
git clone --branch feature/initial-agent-implementation https://github.com/swarnamalya-mohan/context-engineering-long-running-agent.git
cd context-engineering-long-running-agent
pip install -e '.[dev]'
python -m repo_agent.offline
python -m pytest -q
```

The offline rehearsal uses **synthetic repositories and scripted LLM responses**, with the same graph, reviews, validation, artifact storage, and compaction hooks as live mode. It proves orchestration behavior, not live model accuracy. First tokenization may download tiktoken encoding data.

For live GitHub discovery and OpenAI Responses API reviews:

```bash
export OPENAI_API_KEY='your-key'
export OPENAI_MODEL='gpt-4o-mini'
# Optional: export GITHUB_TOKEN='your-token'
python -m repo_agent --stream
```

## What the audience sees

| Mechanism | Implementation | Observable proof |
|---|---|---|
| Write | Raw source snapshots, durable candidate records and evidence | `artifacts/raw/`, phase snapshots and compaction checkpoint |
| Select | Exact repository memory retrieval, newest-first deduplication, eight-item limit | `selected_memory_count`; no other repository history in worker context |
| Just-in-time documents | File map followed by up to three authentication-document reads | `jit_files` stays empty until SSO becomes mandatory |
| Progressive skills | Requirement-gated workflow instructions | `loaded_skills` adds SSO verification after the spec change |
| Compress | README relevance filtering; bounded summary replaces transient history | Measured raw/filtered tokens; before/after compaction tokens |
| Isolate | Independent repository review calls with scoped metadata and evidence | Worker prompts exclude global history and previous rankings |
| Invalidate | Changed policy fields mark affected conclusions stale | `conclusion_invalidated`; stale candidates excluded from final synthesis |
| Reopen | AGPL policy change reopens prior license-only rejections | Gamma is reviewed under the updated policy |
| Recover | JSON checkpoint retains policy, decisions, evidence, phase and queue | Notebook reconstructs runtime state after clearing history |

Scenario: Alpha and Beta satisfy the base spec. Enterprise SSO becomes mandatory; Alpha fails, Beta remains eligible. Allowing AGPL reopens Gamma, which passes SSO. These names are fictional fixtures.

## Architecture and limits

`openspec/specs/` defines the base contract. `openspec/changes/` provides SSO and license changes. The runtime parses a **small supported subset** of OpenSpec Markdown requirement names; it is not a general OpenSpec CLI implementation. Effective policy is separate from transient working history.

Each reviewer gets current policy, scoped metadata, filtered README, recent releases, selected memory, and applicable skill text. Authentication documents are fetched only when SSO is required. Raw outputs are stored externally and excluded from later LLM contexts; artifact paths remain in telemetry. Character limits bound README and document excerpts; token metrics cover the assembled reviewer prompt and README filtering separately.

Required capabilities with insufficient evidence fail validation. Authentication path selection is heuristic and can miss documentation; this produces unverified results rather than invented support. Unknown license metadata needs additional audit. Live discovery is bounded and not exhaustive.

The default LangGraph checkpointer is `InMemorySaver`; JSON snapshots support manual runtime recovery, not automatic process-resumable graph execution. Compaction summarizes transient history with the previous summary and keeps a bounded continuation. Durable evidence remains available independently. Prompt caching and semantic/vector retrieval are not implemented in this demo.

## Inspect the evidence

The notebook displays per-call token counts, loaded skills, files read, invalidations, reopen events, candidate decisions, and compaction measurements. Live API usage is recorded separately from locally counted prompt tokens. Artifacts are ignored by Git and can contain fetched repository text; API keys are read from environment variables or Colab Secrets.

## Live-run diagnostics

Discovery queries product names/descriptions and API-client topics across all four searches before ranking, and filters obvious resource directories. This is a heuristic relevance filter, not exhaustive product discovery. Repository reviews use OpenAI Responses structured parsing with a Pydantic schema; refusals or incomplete output produce an explicit `review_failed` status. The notebook shows review errors separately from policy rejections. An empty recommendation can still be a valid result under mandatory SSO when supplied sources do not verify support.

The live notebook prints decision reports after base, SSO, and AGPL review stages. When no final candidates qualify, final output includes candidate counts, the highest-scoring rejected reviews with full reasons, and pending/failed review statuses. These diagnostics are not endorsements of ineligible candidates.
