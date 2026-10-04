## ADDED Requirements

### Requirement: Optional enterprise SSO scenario
The default graph SHALL skip the enterprise SSO policy change. CLI configuration and notebook controls SHALL permit explicit activation of the original stricter scenario.

#### Scenario: Default execution
- **WHEN** the graph runs with default settings
- **THEN** enterprise SSO SHALL remain optional and the SSO verification skill SHALL NOT be activated

#### Scenario: Explicit SSO demo
- **WHEN** ENABLE_SSO_DEMO is true
- **THEN** the graph SHALL activate SSO, invalidate affected conclusions and re-evaluate them
