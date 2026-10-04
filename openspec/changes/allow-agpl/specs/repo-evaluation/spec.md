# Spec Delta

## MODIFIED Requirements

### Requirement: Allowed licenses
The system SHALL accept MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, and AGPL-3.0 licenses and SHALL reject other known licenses.

#### Scenario: Previously rejected AGPL candidate
- **WHEN** an AGPL-3.0 candidate was rejected under an earlier specification
- **THEN** the evaluator reopens that candidate for evaluation without losing its historical evidence
