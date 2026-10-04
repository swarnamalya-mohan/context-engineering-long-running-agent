# Design

The runtime applies this OpenSpec delta at a deliberate checkpoint in the long-running workflow. The spec-change hook compares the effective policy before and after the change, identifies previously reviewed candidates, and queues them for re-evaluation. The `enterprise_sso_verification` skill is loaded only after the SSO requirement becomes active.
