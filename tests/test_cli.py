import json
import time
from koml_opportunity_cost_engine.cli import main
from koml_opportunity_cost_engine.fixtures import generate


def test_run_completes_on_fixture(tmp_path,capsys):
    generate(tmp_path/'input'); start=time.perf_counter()
    assert main(['run','--input',str(tmp_path/'input'),'--state',str(tmp_path/'state.json')])==0
    assert main(['report','--state',str(tmp_path/'state.json'),'--format','md'])==0
    assert time.perf_counter()-start < 5
    assert 'SYNTHETIC' in capsys.readouterr().out


def test_empty_input_renders_without_traceback(tmp_path,capsys):
    assert main(['compare','--input',str(tmp_path)])==0
    r=json.loads(capsys.readouterr().out)
    assert r['records']==0 and r['foregone_value_total']=='0.00'
    assert r['provenance']=='NO INPUT RECORDS'


def test_malformed_input_named_error(tmp_path,capsys):
    (tmp_path/'tasks.json').write_text('{\n bad')
    assert main(['run','--input',str(tmp_path)])==2
    error=capsys.readouterr().err
    assert 'ParseError' in error and 'tasks.json' in error and 'line 2' in error


def test_determinism_byte_identical(tmp_path):
    generate(tmp_path/'input')
    for name in ('a','b'): assert main(['run','--input',str(tmp_path/'input'),'--state',str(tmp_path/name)])==0
    assert (tmp_path/'a').read_bytes()==(tmp_path/'b').read_bytes()


def test_cli_smoke_all_subcommands(tmp_path,capsys):
    import pytest
    for command in ('fixtures','run','report','compare','audit'):
        with pytest.raises(SystemExit) as exc: main([command,'--help'])
        assert exc.value.code==0
    assert main(['fixtures','--out',str(tmp_path/'input')])==0
    for command in ('compare','audit'): assert main([command,'--input',str(tmp_path/'input')])==0
    capsys.readouterr()
    assert main(['audit','--input',str(tmp_path/'input')])==0
    r=json.loads(capsys.readouterr().out)
    assert len(r['audit_matches'])==20 and len(r['decisions'])==40


def test_missing_input_named_error(tmp_path,capsys):
    assert main(['run','--input',str(tmp_path/'absent')])==2
    assert 'MissingInput' in capsys.readouterr().err


def test_report_write_failure_no_partial_files(tmp_path,capsys):
    generate(tmp_path/'input'); state=tmp_path/'state'
    assert main(['run','--input',str(tmp_path/'input'),'--state',str(state)])==0
    before=set(tmp_path.iterdir())
    assert main(['report','--state',str(state),'--out',str(tmp_path/'absent'/'report')])==2
    assert 'WriteError' in capsys.readouterr().err
    assert set(tmp_path.iterdir())==before


def test_bad_state_named_error(tmp_path,capsys):
    state=tmp_path/'state'; state.write_text('{\n bad')
    assert main(['report','--state',str(state)])==2
    assert 'line 2' in capsys.readouterr().err
    state.write_text('{}')
    assert main(['report','--state',str(state)])==2
    assert 'SchemaError' in capsys.readouterr().err


def test_duplicate_json_keys_named_error(tmp_path,capsys):
    (tmp_path/'tasks.json').write_text('{"synthetic":true,"synthetic":false}')
    assert main(['run','--input',str(tmp_path)])==2
    error=capsys.readouterr().err
    assert 'ParseError' in error and 'duplicate JSON field' in error and 'line 1' in error


def test_atomic_failure_preserves_existing_destination(tmp_path,capsys):
    from koml_opportunity_cost_engine.cli import atomic_write
    from koml_opportunity_cost_engine.core import InputError
    from unittest.mock import patch
    import pytest
    path=tmp_path/'report';path.write_text('existing')
    with patch('koml_opportunity_cost_engine.cli.os.replace',side_effect=OSError('planted failure')):
        with pytest.raises(InputError,match='WriteError'): atomic_write(path,'replacement')
    assert path.read_text()=='existing'
    assert list(tmp_path.iterdir())==[path]


def test_hand_written_tiny_input(capsys):
    assert main(['compare','--input','examples/tiny'])==0
    r=json.loads(capsys.readouterr().out)
    assert (r['records'],r['decision_count'],r['dominated_count'])==(5,1,1)
    assert (r['selected_value_total'],r['foregone_value_total'],r['avoidable_gap_total'])==('120.00','160.00','40.00')
