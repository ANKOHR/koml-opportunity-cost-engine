import json
from koml_opportunity_cost_engine.fixtures import generate


def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    for path in tmp_path.rglob('*.json'):
        data=json.loads(path.read_text(encoding='utf-8'))
        assert data['synthetic'] is True
        assert all(r['synthetic'] for r in data.get('records',[]) if isinstance(r,dict)) if isinstance(data.get('records'),list) else True
    assert (tmp_path/'SYNTHETIC.md').read_text().startswith('<!-- SYNTHETIC')
    assert len(json.loads((tmp_path/'tasks.json').read_text())['records'])==200
    assert len(json.loads((tmp_path/'tiny/tasks.json').read_text())['records'])==5


def test_fixture_files_deterministic(tmp_path):
    generate(tmp_path/'a'); generate(tmp_path/'b')
    for path in (tmp_path/'a').rglob('*'):
        if path.is_file(): assert path.read_bytes()==(tmp_path/'b'/path.relative_to(tmp_path/'a')).read_bytes()
