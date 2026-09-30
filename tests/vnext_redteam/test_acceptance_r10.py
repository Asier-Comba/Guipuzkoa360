"""Known-development independent arithmetic and importer/capture integrity; no LLM runs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
from scripts.vnext_product.local_smoke_r10 import capture_turn, check_config
from scripts.vnext_product.review_health_r10 import contrast
ROOT=Path(__file__).resolve().parents[2]
R10=ROOT/'resultados/vnext/r10'


def load(name):return json.loads((R10/name).read_bytes())


def test_health_report_is_bound_to_exact_evidence_and_reconstructs_selected_gtfs_rows():
    evidence=load('health_evidence.json');review=load('health_review.json')
    assert hashlib.sha256((R10/'health_evidence.json').read_bytes()).hexdigest()==review['health_evidence_sha256']
    for name,data in review['contrast'].items():
        rows={}
        for row in data['raw_rows']:
            rows[(row['trip_id'],row['stop_id'],row['stop_sequence'])]=row
        # Uses W3's independent arithmetic, not W1's oracle.
        rebuilt=contrast(evidence['outputs'][name]['result'],rows)
        assert rebuilt['total_s_reconstructed']==data['total_s_reconstructed']
        bad=deepcopy(evidence['outputs'][name]['result']);bad['itinerary']['total_s']+=1
        with pytest.raises(ValueError,match='Raw chronology'):contrast(bad,rows)
    assert review['verified_delta_s']==review['contrast']['time']['total_s_reconstructed']-review['contrast']['main']['total_s_reconstructed']==-2100


def test_current_w2_public_view_contains_only_rates_with_lineage():
    evidence=load('w2_retest_evidence.json');report=load('w2_retest_report.json')
    assert hashlib.sha256((R10/'w2_retest_evidence.json').read_bytes()).hexdigest()==report['evidence_sha256']
    assert not [c for c in evidence['Aduna']['public_result']['claims'] if 'per_10000' in c['label']]
    rates=[c for c in evidence['Tolosa']['public_result']['claims'] if 'per_10000' in c['label']]
    assert len(rates)==8 and all(c['source_ids'] and c['denominator'] for c in rates)
    assert evidence['substitution']['public_result']['status']=='error'
    assert evidence['substitution']['public_result']['claims']==[]


def test_health_html_rebuild_is_byte_identical_and_embeds_exact_evidence():
    html=ROOT/'resultados/vnext/health.html';before=html.read_bytes()
    subprocess.run([sys.executable,'-m','scripts.vnext_product.build_health_visual'],cwd=ROOT,check=True,capture_output=True)
    assert html.read_bytes()==before
    text=before.decode();embedded=text.split('<script id="evidence" type="application/json">',1)[1].split('</script>',1)[0]
    assert json.loads(embedded)==load('health_evidence.json')
    assert '<script src=' not in text and 'Resultado offline, sin conversación con el agente.' in text


def test_smoke_plan_preserves_frozen_conversation_prompts_without_holdout():
    plan=json.loads((ROOT/'docs/vnext/w3/SMOKE_PLAN_R10.json').read_bytes())
    corpus=ROOT/'tests/vnext_redteam/conversation_scenarios.json'
    scenarios={s['id']:s for s in json.loads(corpus.read_bytes())['scenarios']}
    assert plan['conversation_corpus_sha256']==hashlib.sha256(corpus.read_bytes()).hexdigest()
    assert len(plan['cases'])==12 and plan['scorable_turns_planned']==36
    for case in plan['cases']:assert case['turns']==scenarios[case['conversation_id']]['turns']


def test_failed_model_capture_never_forges_an_assistant_final():
    class Broken:
        def invoke(self,*args,**kwargs):raise RuntimeError('controlled test failure')
    observer=SimpleNamespace(events=[],model_calls=1)
    capture=capture_turn(Broken(),observer,'test prompt',[])
    assert capture['invocation_state']=='failed' and capture['final_response'] is None
    assert capture['observed_messages']==[] and 'controlled test failure' in capture['error_observation']
    observer.model_calls=0
    capture=capture_turn(Broken(),observer,'test prompt',[])
    assert capture['invocation_state']=='not_started' and capture['llm_executed'] is False


def test_local_runner_rejects_missing_resource_authorization_before_loading_model(tmp_path):
    with pytest.raises(ValueError,match='human'):check_config({},tmp_path)
