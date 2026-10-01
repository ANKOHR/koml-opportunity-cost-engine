import copy
import pytest
from koml_opportunity_cost_engine.core import evaluate, InputError
from koml_opportunity_cost_engine.fixtures import fixture_data


def test_fixture_ground_truth_matches_hand_computed():
    r = evaluate(fixture_data())
    assert (r['records'], r['decision_count'], r['dominated_count']) == (200, 40, 20)
    assert (r['selected_value_total'], r['foregone_value_total'], r['avoidable_gap_total']) == ('4000.00', '4600.00', '1000.00')
    for i, row in enumerate(r['decisions']):
        assert row == dict(decision=f'decision-{i:02}', selected_id=f'task-{i:02}-0', best_alternative_id=f'task-{i:02}-1', selected_value='100.00', foregone_value='150.00' if i % 2 == 0 else '80.00', avoidable_gap='50.00' if i % 2 == 0 else '0.00', dominated=i % 2 == 0)


@pytest.mark.parametrize('field,value', [('value','-1'),('value','NaN'),('value','Infinity'),('value','0.001'),('value','1000000001'),('value',1),('date','2026-10-01'),('id',''),('title','x'*10001),('selected',1),('synthetic',False)])
def test_rejects_adversarial_values(field,value):
    data=fixture_data(); data['records'][0][field]=value
    with pytest.raises(InputError, match='SchemaError'): evaluate(data)


def test_duplicate_ids_and_schema_drift():
    data=fixture_data(); data['records'][1]['id']=data['records'][0]['id']
    with pytest.raises(InputError,match='duplicate id'): evaluate(data)
    data=fixture_data(); data['records'][0]['extra']=1
    with pytest.raises(InputError,match='extra'): evaluate(data)


def test_corrupted_fixture_changes_computed_results():
    data=fixture_data(); data['records'][1]['value']='200.25'
    r=evaluate(data)
    assert r['foregone_value_total']=='4650.25'
    assert r['avoidable_gap_total']=='1050.25'


def test_ties_choose_lexicographic_id_and_not_flagged():
    data=fixture_data(); data['records']=data['records'][:5]
    data['records'][1]['value']='100.00'; data['records'][2]['value']='100.00'
    r=evaluate(data)['decisions'][0]
    assert r['best_alternative_id']=='task-00-1'
    assert not r['dominated']


def test_real_input_provenance():
    data=fixture_data(); data.update(synthetic=False,entered_by='Henry')
    for row in data['records']: row['synthetic']=False
    assert evaluate(data)['provenance']=='REAL inputs entered by Henry'
    data['entered_by']='someone else'
    with pytest.raises(InputError): evaluate(data)


def test_decision_constraints():
    for change in ('selection','date','single'):
        data=fixture_data(); data['records']=data['records'][:5]
        if change=='selection': data['records'][1]['selected']=True
        if change=='date': data['records'][1]['date']='2026-09-29'
        if change=='single': data['records']=data['records'][:1]
        with pytest.raises(InputError): evaluate(data)
