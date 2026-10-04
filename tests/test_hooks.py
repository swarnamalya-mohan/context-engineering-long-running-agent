from repo_agent.hooks.context_firewall import filter_tool_output
from repo_agent.hooks.validation import validate_candidate


def test_context_firewall_reduces_large_irrelevant_text():
    raw = ("noise line\n" * 5000) + "# Self-hosting\nDocker self-hosting is supported.\n"
    filtered, metrics = filter_tool_output(raw, max_chars=4000)
    assert "Self-hosting" in filtered
    assert metrics["filtered_chars"] < metrics["raw_chars"]


def test_sso_hard_requirement_rejects_false():
    record = {"license": "MIT", "analysis": {"enterprise_sso": False, "enterprise_sso_paid_only": False}}
    policy = {"allowed_licenses": ["MIT"], "enterprise_sso_required": True, "active_within_months": None}
    reasons = validate_candidate(record, policy)
    assert any("enterprise_sso" in reason for reason in reasons)
