import json
from koml_opportunity_cost_engine.core import evaluate
from koml_opportunity_cost_engine.fixtures import generate, fixture_data
from koml_opportunity_cost_engine.report import render


def test_report_matches_ground_truth_exact(tmp_path):
    generate(tmp_path)
    expected=json.loads((tmp_path/'expectations.json').read_text())
    report=json.loads(render(evaluate(fixture_data()),'json'))
    for key in ('records','decision_count','dominated_count','selected_value_total','foregone_value_total','avoidable_gap_total'): assert report[key]==expected[key]
    md=render(report)
    for key in ('selected_value_total','foregone_value_total','avoidable_gap_total'): assert expected[key] in md


def test_report_zero_false_positives():
    r=evaluate(fixture_data())
    assert [d['decision'] for d in r['decisions'] if d['dominated']]==[f'decision-{g:02}' for g in range(0,40,2)]


def test_report_carries_provenance_banner():
    for fmt in ('md','json'): assert 'SYNTHETIC fixtures' in render(evaluate(fixture_data()),fmt)


def test_hypothetical_figures_labelled():
    for fmt in ('md','json'):
        output=render(evaluate(fixture_data()),fmt)
        assert 'HYPOTHETICAL' in output and 'not measured savings' in output


def test_handles_unicode_and_long_inputs():
    data=fixture_data(); row=data['records'][0]
    row['title']='工作 café '+ 'x'*9000
    row['id']='C:\\Henry\\工作|<task>\n'+ 'x'*9000
    r=evaluate(data)
    assert row['id'] in render(r,'json') or row['id'] in json.loads(render(r,'json'))['decisions'][0]['selected_id']
    assert '&#124;' in render(r) and '&lt;' in render(r)


def test_no_em_dashes_in_outputs():
    for fmt in ('md','json'): assert chr(8212) not in render(evaluate(fixture_data()),fmt)
