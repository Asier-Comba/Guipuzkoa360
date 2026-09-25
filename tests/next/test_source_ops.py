import copy
import csv
import json
import shutil
from pathlib import Path
import pytest
from scripts.ops.compute_source_health import compute, ROOT
from scripts.ops.source_watcher import detect

@pytest.fixture
def metadata():
    return {'source_id':'official', 'official_url':'https://example.org/catalog', 'period':'2025-01-01',
            'sha256':'a'*64, 'schema':{'id':'string','value':'integer'}, 'primary_key':'id',
            'rows':[{'id':'20002','value':1}]}

@pytest.mark.parametrize('change,status', [({},'NO_CHANGE'), ({'sha256':'b'*64},'POTENTIAL_UPDATE'),
    ({'schema':{'id':'integer'}},'SCHEMA_CHANGE'), ({'available':False},'SOURCE_UNAVAILABLE'),
    ({'period':'2024-01-01'},'REVIEW_REQUIRED'), ({'official_url':'https://other.invalid'},'REVIEW_REQUIRED'),
    ({'sha256':'invalid'},'REVIEW_REQUIRED'), ({'period':'not-date'},'REVIEW_REQUIRED'),
    ({'rows':[{'id':'20002','value':2}]},'REVIEW_REQUIRED'),
    ({'rows':[{'id':'20002'}, {'id':'20002'}]},'REVIEW_REQUIRED')])
def test_watcher_statuses_and_read_only(metadata,change,status):
    candidate = {**copy.deepcopy(metadata), **change}
    before = copy.deepcopy((metadata,candidate))
    result = detect(metadata,candidate)
    assert result['status'] == status
    assert result['automatic_promotion'] is False
    assert (metadata,candidate) == before
    assert result['proposal']['validation_status'] == 'NOT_RUN'

def test_watcher_keyed_diff(metadata):
    candidate = {**metadata, 'sha256':'b'*64, 'rows':[{'id':'20003','value':2}]}
    proposal = detect(metadata,candidate)['proposal']
    assert proposal['rows_added'] == proposal['rows_removed'] == 1
    assert proposal['coverage_change'] == 0

def test_incomplete_metadata_not_no_change(metadata):
    assert detect(metadata,{})['status'] == 'REVIEW_REQUIRED'

def test_metadata_must_be_objects():
    with pytest.raises(ValueError): detect([], {})

def test_empty_manifest_is_not_valid(tmp_path):
    shutil.copytree(ROOT/'datos_preparados', tmp_path/'datos_preparados')
    (tmp_path/'datos_preparados/runtime_manifest.json').write_text('{"files":[],"total_bytes":0}',encoding='utf-8')
    assert compute(tmp_path)['manifest_integrity']['status'] == 'FAIL'

def test_actual_source_health():
    r = compute()
    assert r['status'] == 'PASS'
    assert r['municipality_coverage']['present'] == 88
    assert r['service_record_count'] == 148
    assert r['source_count'] == 3
    assert r['traceability_coverage']['numerator'] == 412

@pytest.mark.parametrize('mutation', ['missing','duplicate','coordinate','orphan','source','hash'])
def test_health_rejects_corruption_in_isolated_copy(tmp_path,mutation):
    shutil.copytree(ROOT/'datos_preparados', tmp_path/'datos_preparados')
    path = tmp_path/'datos_preparados/runtime_servicios.csv'
    with path.open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f); fields=reader.fieldnames; rows=list(reader)
    if mutation == 'missing': rows[0]['source_id']=''
    elif mutation == 'duplicate': rows.append(dict(rows[0]))
    elif mutation == 'coordinate': rows[0]['latitude']='NaN'
    elif mutation == 'orphan': rows[0]['municipality_code']='20999'
    elif mutation == 'source': rows[0]['source_id']='FAKE'
    elif mutation == 'hash': rows[0]['service_name'] += ' changed'
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    assert compute(tmp_path)['status'] == 'FAIL'
