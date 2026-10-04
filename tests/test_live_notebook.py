"""Execute all notebook logic with a stub transport; no claims about API quality."""
import json
from pathlib import Path
from types import SimpleNamespace
import matplotlib
matplotlib.use('Agg')

ROOT = Path(__file__).resolve().parents[1]


def test_standalone_notebook_all_demo_cells(tmp_path, monkeypatch):
    notebook = json.loads((ROOT / 'notebooks/live_context_methods_demo.ipynb').read_text())
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('OPENAI_API_KEY', 'transport-stub')
    calls = []
    def parse(**kwargs):
        schema = kwargs['text_format']
        prompt = kwargs['input']
        calls.append(kwargs)
        if schema.__name__ == 'CompactMemory':
            value = {'objective': 'Find API clients. MIT and Apache-2.0 allowed; AGPL-3.0 excluded.',
                     'decisions': ['Gamma/license: Gamma is ineligible; AGPL-3.0 not permitted.'],
                     'next_steps': ['Await possible policy update.']}
        elif schema.__name__ == 'ExtractedFacts':
            value = {'facts': ['REST client supports sending HTTP requests.'], 'evidence_ids': ['Alpha/readme']}
        else:
            task = prompt.split('CONTEXT:', 1)[0]
            blocked = 'CURRENT policy' in task or ('Gamma' in task and 'AGPL-3.0' not in task)
            value = {'status': 'ineligible' if blocked else 'eligible', 'reason': 'Controlled evidence',
                     'evidence_ids': ['Gamma/license' if 'Gamma' in task else 'Alpha/license']}
        return SimpleNamespace(output_parsed=schema.model_validate(value),
            usage=SimpleNamespace(input_tokens=len(prompt)//4 + 50, output_tokens=30,
                                  input_tokens_details=SimpleNamespace(cached_tokens=0)),
            id=f'transport-stub-{len(calls)}', status='completed')
    class ClientStub:
        def __init__(self, **kwargs):
            self.responses = SimpleNamespace(parse=parse)
    import openai
    monkeypatch.setattr(openai, 'OpenAI', ClientStub)
    import IPython.display
    monkeypatch.setattr(IPython.display, 'display', lambda *args, **kwargs: None)
    namespace = {}
    for cell in notebook['cells']:
        if cell['cell_type'] != 'code':
            continue
        code = ''.join(cell['source'])
        if code.startswith('%pip'):
            continue
        exec(compile(code, 'live_context_methods_demo.ipynb', 'exec'), namespace)
    assert len(calls) == 25
    assert set(namespace['summary_table'].index) == {
        '1 Tool filtering', '2 Skills', '3 Memory', '4 Artifacts',
        '5 Compaction', '6 Isolation', '7 Invalidation', '8 JIT documents'}
    assert all(row['status_agreement'] for row in namespace['pair_rows'])
    assert namespace['impacted'] == ['Gamma']
    assert len(namespace['selected_memory']) == 1
    assert namespace['artifact_path'].read_text() == namespace['raw_readme']
    assert namespace['summary_table'].loc['5 Compaction', 'setup_input'] > 0
    assert (namespace['RUN_DIR'] / 'comparison.csv').exists()
