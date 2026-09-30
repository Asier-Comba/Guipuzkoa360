"""W3 patch3 evidence and mutation checks, without borrowing upstream verdicts."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.vnext_product.intake_candidate_r13 import project,ZIP_SHA
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'resultados/vnext/r13'
def read(n):return json.loads((BASE/n).read_bytes())
def labels():
    l=json.loads((ROOT/'resultados/vnext/r12/health_evidence.json').read_bytes())['labels']
    l['stops'].append({'stop_id':'7214','name':'Beasain - Zaldizurreta 7'})
    return l
def row():return deepcopy(next(r for r in read('flat_declared.json')['records'] if r['id']=='W3-main'))

def test_exact_patch3_all_supported_layouts_and_independent_gtfs_contrast():
    report=read('offline_review.json')
    assert report['package_sha256']==ZIP_SHA and report['acceptance']=='PASS'
    assert len(report['declared_paths'])==15
    assert len(report['modes'])==4 and all(m['status']=='PASS' and m['cases']==36 for m in report['modes'])
    assert report['independent_source']['contrast']['main']['total_s_reconstructed']==10691
    assert report['independent_source']['contrast']['time']['total_s_reconstructed']==8591
    for mode in report['modes']:
        data=read(mode['mode']+'.json');assert data['root_matches'] and data['model_calls']==0
        assert data['invalid_root']['status']=='error' and not data['invalid_root']['claims']
        by={r['id']:r for r in data['records']}
        assert not [c for c in by['Aduna']['public_result']['claims'] if 'per_10000' in c['label']]
        assert len([c for c in by['Tolosa']['public_result']['claims'] if 'per_10000' in c['label']])==8
        assert any(c['label']=='highlighted_count' and c['value']==7 and c['unit']=='municipios' for c in by['coincidence']['public_result']['claims'])
        assert by['legacy_r4_explicit']['public_result']['mobility']['scenarios'][0]['itinerary']['outbound']['to_stop_label']=='Beasain - Zaldizurreta 7'

@pytest.mark.parametrize('mutate',[
    lambda v:v['mobility']['scenarios'][0]['itinerary']['outbound'].__setitem__('from_stop_label','Wrong'),
    lambda v:v['mobility']['scenarios'][0]['itinerary'].__setitem__('total_s',0),
    lambda v:v['mobility']['scenarios'][0]['health_destination'].__setitem__('entrance_verified',True),
    lambda v:v['mobility']['scenarios'][0]['parameter_attribution'][0].__setitem__('w2_attribution','human_explicit'),
])
def test_projection_gate_rejects_material_mutations(mutate):
    r=row();assert not project(r,labels())
    mutate(r['public_result']);assert any(f['severity']=='HIGH' for f in project(r,labels()))

def test_plan_twelve_messages_and_clean_session_no_internal_ids_or_gold():
    plan=json.loads((ROOT/'docs/vnext/w3/SMOKE_PLAN_R13.json').read_bytes())
    assert len(plan['messages'])==plan['max_total_user_messages_including_retries']==12
    assert plan['messages'][-1]['session']=='B' and plan['package_sha256']==ZIP_SHA
    assert all('plan_visit' not in r['text'] and 'origin_id' not in r['text'] and '-2100' not in r['text'] for r in plan['messages'])

def test_actual_smoke_stops_on_high_and_never_promotes_offline_health_to_agent_success():
    smoke=read('PORTAL_SMOKE_R13.json')
    assert smoke['user_messages_used_of_12']==len(smoke['turns'])==4
    assert smoke['status']=='STOPPED_HIGH' and smoke['high']==1
    turn=smoke['turns'][3]
    assert len(turn['tool_calls'])==len(turn['tool_outputs'])==2
    assert all(isinstance(c['arguments']['request'],str) for c in turn['tool_calls'])
    assert all(r['status']=='error' and not r['claims'] and r['raw_result_sha256'] is None for r in turn['tool_outputs'])
    assert 'arguments:request:invalid_value' in turn['assistant_final']
    replay=read('request_binding_reproduction.json')
    assert replay['model_calls']==0 and all(r['raw_result'] is None for r in replay['results'])
    assert smoke['official_delivery']['MAIN']=='FAIL' and smoke['clean_session']=='NOT_RUN_STOPPED_HIGH'

def test_scorecard_does_not_average_away_the_failure_or_score_unsubmitted_turns():
    card=read('TURN_SCORECARD_R13.json')
    assert len(card['turns'])==12
    assert card['turns'][3]['dimensions']['ARGUMENT_BINDING']=='FAIL'
    assert all(set(t['dimensions'])==set(card['dimensions']) for t in card['turns'])
    assert all(set(t['dimensions'].values())=={'NOT_OBSERVED'} for t in card['turns'][4:])
    assert card['turns'][1]['dimensions']['FOLLOWUP_CONTEXT']=='PASS'

def test_actual_agent_demographic_figure_is_independently_contrasted_with_source_row():
    contrast=read('agent_figure_contrast.json')
    assert contrast['source_id']=='EUSTAT_EMH_2025'
    assert contrast['result']==round(int(contrast['row']['population_75_plus'])/int(contrast['row']['population_total'])*100,3)==7.101
    observed=next(json.loads(n['result']) for n in read('M01.json') if n.get('result') and json.loads(n['result'])['capability_id']=='obtener_resumen_territorial')
    claim=next(c for c in observed['claims'] if c['metric_id']=='pct_75_plus')
    assert claim['value']==contrast['result'] and claim['denominator']['value']==507
    assert claim['source_ids']==[contrast['source_id']] and claim['assumptions']
