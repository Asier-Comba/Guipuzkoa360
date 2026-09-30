"""Actual evidence regression gates: no false real-agent acceptance or budget reset."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'resultados/vnext/r14'
def read(name):return json.loads((BASE/name).read_bytes())

def test_exact_accepted_identity_and_downloaded_code_assets():
    acceptance=read('W1_ACCEPTANCE_R14.json')
    assert acceptance['checkpoint']['author']['login']=='oierdu'
    assert acceptance['checkpoint']['body'].startswith('W1_R14_FRONTDOOR_ACCEPTANCE=PASS')
    for key in ['hotfix_sha','zip_sha256','manifest_sha256']:assert acceptance[key] in acceptance['checkpoint']['body']
    code=read('studio_code_hashes.json')
    assert len(code)==2
    for row in code:assert hashlib.sha256((BASE/('studio_'+row['file'])).read_bytes()).hexdigest()==row['sha256']
    assets=read('studio_asset_hashes.json')
    assert len(assets)==15 and all(a['matches'] for a in assets)
    for row in assets:assert hashlib.sha256((BASE/'studio_assets'/row['path']).read_bytes()).hexdigest()==row['sha256']

def test_m05_failure_stops_budget_without_scoring_unsubmitted_turns():
    smoke=read('PORTAL_SMOKE_R14.json')
    assert smoke['status']=='STOPPED_HIGH_M05'
    assert smoke['messages_total_used']==5 and smoke['messages_remaining']==7 and smoke['new_user_messages_sent']==1
    assert len(smoke['turns'])==8
    assert smoke['turns'][0]['status']=='FAIL_HIGH'
    assert all(t['status']=='NOT_RUN_STOPPED_HIGH' and set(t['dimensions'].values())=={'NOT_OBSERVED'} for t in smoke['turns'][1:])
    card=read('TURN_SCORECARD_R14.json')
    assert card['turns'][0]['dimensions']['ARGS']=='FAIL'
    assert card['turns'][0]['dimensions']['BINDING']=='PASS'
    assert card['turns'][0]['dimensions']['ERROR'].startswith('FAIL')

def test_actual_invalid_optional_has_no_authoritative_health_number():
    turn=read('PORTAL_SMOKE_R14.json')['turns'][0]
    assert len(turn['tool_calls'])==len(turn['tool_outputs'])==4
    assert all(c['arguments']['return_deadline']=='' and c['arguments']['duration_minutes']==20 for c in turn['tool_calls'][1:])
    for output in turn['tool_outputs'][1:3]:
        assert output['error']['message']=='mobility:invalid_clock'
        assert not output['claims'] and output['raw_result_sha256'] is None and output['effective_request'] is None
    assert 'Failed to create sandbox' in turn['tool_outputs'][3]['platform_error']
    assert 'No puedo calcular' in turn['assistant_final']

def test_offline_positive_control_cannot_grant_real_agent_go():
    control=read('M05_offline_reproduction.json')
    assert control['model_calls']==0 and 'NOT_AGENT' in control['classification']
    assert 'return_deadline' not in control['control']['arguments']
    assert control['control']['output']['mobility']['scenarios'][0]['itinerary']['total_s']==10691
    readiness=json.loads((ROOT/'docs/vnext/w3/RELEASE_READINESS_R14.json').read_bytes())
    assert readiness['READY_FOR_FEEDBACK']==readiness['RELEASE_GO']=='NO'
    assert readiness['high']==1 and readiness['medium']==2
    assert 'cálculos offline verificados' in (ROOT/'resultados/vnext/health.html').read_text(encoding='utf-8')
