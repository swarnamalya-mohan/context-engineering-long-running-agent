from pathlib import Path
from repo_agent.openspec_runtime import apply_change, load_main_policy, parse_spec, policy_delta

ROOT = Path(__file__).resolve().parents[1]


def test_main_spec_parses_requirements():
    doc = parse_spec(ROOT / "openspec/specs/repo-evaluation/spec.md")
    names = {req.name for req in doc.requirements}
    assert "Self-hosted deployment" in names
    assert "Allowed licenses" in names
    assert "Enterprise SSO" not in names


def test_base_policy():
    policy = load_main_policy(ROOT)
    assert policy["self_hosted_required"] is True
    assert policy["rest_client_required"] is True
    assert policy["enterprise_sso_required"] is False
    assert "MIT" in policy["allowed_licenses"]
    assert "AGPL-3.0" not in policy["allowed_licenses"]


def test_enterprise_sso_change():
    base = load_main_policy(ROOT)
    changed = apply_change(base, ROOT, "require-enterprise-sso")
    assert changed["enterprise_sso_required"] is True
    assert "enterprise_sso_required" in policy_delta(base, changed)


def test_allow_agpl_change():
    base = load_main_policy(ROOT)
    changed = apply_change(base, ROOT, "allow-agpl")
    assert "AGPL-3.0" in changed["allowed_licenses"]
