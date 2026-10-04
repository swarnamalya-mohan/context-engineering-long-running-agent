# Spec Delta

## ADDED Requirements

### Requirement: Enterprise SSO
The system SHALL require enterprise SSO capability and SHALL distinguish open-source SSO from SSO available only in a paid edition.

#### Scenario: SSO is paid-only
- **WHEN** a candidate offers SSO only in a commercial or enterprise edition
- **THEN** the evaluator rejects the candidate under the open-source enterprise evaluation

#### Scenario: SSO is verified in the open-source edition
- **WHEN** repository evidence verifies SSO in the open-source edition
- **THEN** the evaluator marks the SSO requirement satisfied and stores the supporting evidence
