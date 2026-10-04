# Repository Evaluation Specification

## Purpose

Define the durable evaluation policy for an agent that searches and verifies open-source alternatives to Postman.

## Requirements

### Requirement: Evidence-backed feature verification
The system SHALL require evidence for feature claims and SHALL represent insufficient evidence as unknown rather than guessing.

#### Scenario: Feature cannot be verified
- **WHEN** a repository claims a feature but supplied evidence does not establish it
- **THEN** the evaluator records the feature as unknown and preserves the claim as unverified

### Requirement: Self-hosted deployment
The system SHALL require the candidate's open-source edition to support self-hosted operation.

#### Scenario: SaaS-only candidate
- **WHEN** a candidate has no evidence of self-hosted operation
- **THEN** the evaluator rejects the candidate under the active specification

### Requirement: REST client capability
The system SHALL require a usable REST API client capability.

#### Scenario: Missing REST client
- **WHEN** the evaluator verifies that a candidate lacks REST request functionality
- **THEN** the evaluator rejects the candidate

### Requirement: Team collaboration
The system SHALL require collaboration functionality suitable for a multi-user engineering team.

#### Scenario: No collaboration capability
- **WHEN** the evaluator verifies that a candidate has no team collaboration capability
- **THEN** the evaluator rejects the candidate

### Requirement: Active project
The system SHALL require repository activity within the previous 12 months.

#### Scenario: Stale project
- **WHEN** the repository has no qualifying activity within 12 months
- **THEN** the evaluator rejects the candidate as inactive

### Requirement: Allowed licenses
The system SHALL accept MIT, Apache-2.0, BSD-2-Clause, and BSD-3-Clause licenses and SHALL reject other known licenses.

#### Scenario: Disallowed known license
- **WHEN** the repository has a known license outside the allowed set
- **THEN** the evaluator records a deterministic license rejection reason
