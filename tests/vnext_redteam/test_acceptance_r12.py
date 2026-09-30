"""Exact-package projection mutations, genuine positives and bounded smoke."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import pytest
from scripts.vnext_product.intake_candidate_r12 import projection_findings, PACKAGE_SHA, W1_RUNTIME

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'resultados/vnext/r12'
def read(name):return json.loads((BASE/name).read_bytes())
def health():return deepcopy(next(r for r in read('candidate_evidence.json')['results'] if r['id']=='W3-main'))
def labels():return read('health_evidence.json')['labels']

def test_review_binds_exact_evidence_and_preserves_territorial_positives():
    r=read('candidate_review.json')
    assert r['package_sha256']==PACKAGE_SHA and r['w1_runtime_git_real']==W1_RUNTIME
    assert hashlib.sha256((BASE/'candidate_evidence.json').read_bytes()).hexdigest()==r['evidence_sha256']
    assert len(r['calls'])==34 and all(c['status']!='FAIL' for c in r['calls'])
    assert all(r['territorial_retest'].values()) and r['verified_conditional_delta_s']==-2100
    assert {f['id'] for f in r['findings']}=={'LABEL_NOT_IN_CONSUMER_CATALOG'}
    assert {f['stop_id'] for f in r['findings']}=={'7214'}
    assert read('candidate_evidence.json')['model_executed']==0

@pytest.mark.parametrize('mutate',[
    lambda v:v['mobility']['scenarios'][0]['itinerary']['outbound'].__setitem__('to_stop_label','Wrong stop'),
    lambda v:v['mobility']['scenarios'][0]['itinerary'].__setitem__('total_s',1),
    lambda v:v['mobility']['scenarios'][0]['walking']['outbound'].__setitem__('entrance_verified',True),
    lambda v:v['mobility']['scenarios'][0]['sources'][0].__setitem__('transformation','invented'),
])
def test_projection_gate_detects_wrong_names_totals_walk_and_source(mutate):
    r=health();assert not projection_findings(r,labels())
    mutate(r['public_result'])
    assert any(f['severity']=='HIGH' for f in projection_findings(r,labels()))

def test_foreign_root_failure_is_recorded_separately_from_supported_candidate():
    rows={r['id']:r for r in read('foreign_cwd_diagnostic.json')['results']}
    assert rows['legacy_r4_explicit']['envelope']['status']=='error'
    assert rows['legacy_r4_explicit']['envelope']['raw_result_json'] is None
    assert rows['health_defaults_omitted']['public_result']['mobility']['scenarios'][0]['itinerary']['outbound']['from_stop_label']=='8305'
    assert not read('foreign_cwd_diagnostic.json')['cwd_is_package']
    assert read('candidate_evidence.json')['cwd_is_package']

def test_smoke_budget_is_twelve_messages_not_twelve_conversations():
    p=json.loads((ROOT/'docs/vnext/w3/SMOKE_PLAN_R12.json').read_bytes())
    assert p['max_user_messages_including_retries']==12
    assert len(p['messages'])==12 and len({m['id'] for m in p['messages']})==12
    assert p['messages'][-1]['session']=='B'
    assert all('plan_visit' not in m['user_text'] and '_stops' not in m['user_text'] for m in p['messages'])

def test_shared_assets_and_saved_editors_are_byte_identical():
    assert all(r['identical'] for r in read('shared_asset_review.json'))
    assert all(r['identical'] for r in read('portal_code_review.json'))

def test_studio_declared_assembly_cannot_be_promoted_from_import_only_preparation():
    r=read('deployment_review.json')
    assert r['status']=='FAIL' and r['severity']=='HIGH'
    assert 'datos_preparados/vnext/w1_r6_runtime.zip' not in r['declared_context_files']
    actual=read('declared_files_diagnostic.json')['direct_tool_outputs']['health']
    assert actual['status']=='error' and not actual['claims']
    assert actual['error']['code']=='contract_violation'
    assert actual['error']['message']=='capability:stale_validation_evidence'
