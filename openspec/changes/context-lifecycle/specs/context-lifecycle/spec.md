## ADDED Requirements

### Requirement: Scoped memory
The system SHALL retrieve deduplicated evidence for only the current repository, bounded to eight entries.

#### Scenario: Multiple repositories in durable memory
- **WHEN** Alpha is reviewed
- **THEN** Beta evidence SHALL NOT enter Alpha's prompt

### Requirement: Invalidation
The system SHALL mark impacted conclusions stale before applying new evaluation decisions and SHALL exclude stale conclusions from synthesis.

#### Scenario: Mandatory SSO activated
- **WHEN** enterprise SSO becomes required
- **THEN** reviewed repository conclusions SHALL become stale and be re-evaluated

### Requirement: Source preservation
The system SHALL save fetched source content before filtering and record artifact references and context measurements.

#### Scenario: Large README
- **WHEN** a README is filtered
- **THEN** the source snapshot SHALL remain available after the review

### Requirement: Continuation
The system SHALL checkpoint policy, decisions, evidence and pending work before clearing transient history.

#### Scenario: Compaction
- **WHEN** history is compacted
- **THEN** durable evidence SHALL remain unchanged
