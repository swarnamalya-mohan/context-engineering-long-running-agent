from repo_agent.reporting import decision_report


def test_empty_shortlist_still_shows_full_reasons_and_pending_work():
    state = {'rejected': {'a': {'full_name': 'a/client', 'status': 'rejected',
             'analysis': {'enterprise_sso': None}, 'score': 80,
             'rejection_reasons': ['hard requirement failed or unverified: enterprise_sso']}},
             'candidates': {'b': {'full_name': 'b/client', 'status': 'screened'}}}
    report = decision_report(state)
    assert 'Verified eligible: 0' in report
    assert 'a/client' in report and 'enterprise_sso' in report
    assert 'b/client — screened' in report
    assert 'remain ineligible' in report


def test_stale_analysis_does_not_appear_in_verified_shortlist():
    state = {'candidates': {'a': {'full_name': 'a/client', 'status': 'stale', 'analysis': {'rest_client': True}}}}
    assert 'Verified eligible: 0' in decision_report(state)
    assert 'Verified shortlist' not in decision_report(state)


def test_base_shortlist_has_verified_products():
    state = {'candidates': {'a': {'full_name': 'a/client', 'status': 'evaluated', 'analysis': {'rest_client': True}, 'score': 50, 'license': 'MIT'}}}
    report = decision_report(state)
    assert 'Verified eligible: 1' in report
    assert 'Verified shortlist under this policy' in report
