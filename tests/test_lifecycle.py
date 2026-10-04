import json
from copy import deepcopy
from pathlib import Path

from repo_agent.context import select_memory
from repo_agent.hooks.spec_change import impacted_candidates
from repo_agent.hooks.validation import validate_candidate
from repo_agent.offline import fixture_runtime
from repo_agent.graph import build_graph

ROOT = Path(__file__).resolve().parents[1]


def runtime_at(tmp_path):
    import shutil
    shutil.copytree(ROOT / 'openspec', tmp_path / 'openspec')
    return fixture_runtime(tmp_path)


def test_full_graph_proves_five_mechanisms(tmp_path):
    runtime = runtime_at(tmp_path)
    graph = build_graph(settings=runtime.settings, repo_root=tmp_path, runtime=runtime)
    states = list(graph.stream({}, {'configurable': {'thread_id': 'test'}}, stream_mode='values'))
    final = states[-1]
    assert set(final['candidates']) == {'demo/beta', 'demo/gamma'}
    assert final['rejected']['demo/alpha']['status'] == 'rejected'
    contexts = [e for e in final['events'] if e['type'] == 'context_assembled']
    assert len(contexts) == 5
    assert all(e['filtered_tokens'] < e['raw_tokens'] for e in contexts)
    assert all(Path(e['raw_artifact']).exists() for e in contexts)
    assert all('enterprise_sso_verification' not in e['loaded_skills'] for e in contexts[:2])
    assert all(e['jit_files'] == ['docs/enterprise-sso.md'] for e in contexts[2:])
    stale = next(s for s in states if s.get('phase') == 'sso-change')
    assert all(r['status'] == 'stale' for r in stale['candidates'].values())
    assert 'demo/gamma' in next(e for e in final['events'] if e['type'] == 'openspec_change_applied' and e['change'] == 'allow-agpl')['reopened']
    compaction = next(e for e in final['events'] if e['type'] == 'compaction')
    assert compaction['after_tokens'] < compaction['before_tokens']
    checkpoint = json.loads(Path(compaction['durable_checkpoint']).read_text())
    assert checkpoint['evidence'] == final['evidence']
    assert final['working_history'] == []
    assert checkpoint['policy'] == final['policy']


def test_selective_memory_is_scoped_and_deduplicated():
    evidence = [{'repo': 'a', 'claim': 'x', 'source': 'r', 'snippet': 's'}] * 10
    evidence += [{'repo': 'b', 'claim': 'private'}]
    memory = select_memory({'evidence': evidence}, 'a')
    assert len(memory['evidence']) == 1
    assert all(e['repo'] == 'a' for e in memory['evidence'])


def test_repeated_spec_application_does_not_invalidate(tmp_path):
    runtime = runtime_at(tmp_path)
    policy = runtime.initial_policy()
    delta, impacted = impacted_candidates(policy, deepcopy(policy), {'a': {'analysis': {'rest_client': True}}}, {})
    assert delta == {} and impacted == []


def test_unknown_mandatory_sso_fails_closed():
    reasons = validate_candidate({'license': 'MIT', 'analysis': {'enterprise_sso': None}}, {'enterprise_sso_required': True})
    assert any('unverified' in r for r in reasons)


def test_stale_candidate_never_enters_final_prompt(tmp_path):
    runtime = runtime_at(tmp_path)
    assert runtime.synthesize({'policy': runtime.initial_policy(), 'candidates': {'a': {'status': 'stale', 'analysis': {'rest_client': True}}}}).startswith('No verified')
