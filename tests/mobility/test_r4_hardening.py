"""Adversarial contract/data/temporal checks; fixtures enter only by injection."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from prototypes.ir_y_volver import provider as p
from prototypes.ir_y_volver.snapshot_validation import strict_loads, SnapshotError
from tests.mobility.test_provider import load_fixture, request


@pytest.fixture
def snapshot(monkeypatch):
    value = load_fixture()
    monkeypatch.setattr(p, '_load_snapshot', lambda _:value)
    return value


@pytest.mark.parametrize('field,index', [('pickup_type',0),('drop_off_type',1)])
@pytest.mark.parametrize('value,expected', [(0,'ok'),(1,'no_feasible_journey'),(2,'no_feasible_journey'),
    (3,'no_feasible_journey'),('', 'ok'),(None,'unknown'),(9,'unknown'),(False,'unknown'),('0','unknown'),([], 'unknown')])
def test_permission_matrix(snapshot, field, index, value, expected):
    snapshot['trips'][0]['stops'][index][field] = value
    assert p.plan_visit(request())['status'] == expected


@pytest.mark.parametrize('value,expected', [(0,0),(1,1),('',1),(None,None),('missing',1),(2,None),(False,None),('1',None)])
def test_timepoint_matrix(snapshot,value,expected):
    row=snapshot['trips'][0]['stops'][0]
    if value == 'missing':
        row.pop('timepoint')
    else:
        row['timepoint']=value
    result=p.plan_visit(request())
    if expected is None:
        assert result['status']=='unknown'
    else:
        assert result['itinerary']['outbound']['from_timepoint']==expected


@pytest.mark.parametrize('kind', ['root_null','root_list','defaults','bool_margin','walking','trips_empty','trip_null',
    'orphan_service','orphan_stop','sequence_bool','reverse_time','source_empty','source_null','coverage_null',
    'calendar_null','calendar_bool','exception_unknown','nan_coordinate','origin_null','entity_orphan',
    'profile_extra','incomplete_coverage'])
def test_corrupt_snapshot_never_yields_itinerary(monkeypatch,kind):
    s=load_fixture()
    if kind=='root_null': s=None
    elif kind=='root_list': s=[]
    elif kind=='defaults': s['defaults']={}
    elif kind=='bool_margin': s['defaults']['arrival_margin_minutes']=True
    elif kind=='walking': s['walking_profiles']=[]
    elif kind=='trips_empty': s['trips']=[]
    elif kind=='trip_null': s['trips'][0]=None
    elif kind=='orphan_service': s['trips'][0]['service_id']='missing'
    elif kind=='orphan_stop': s['trips'][0]['stops'][0]['stop_id']='missing'
    elif kind=='sequence_bool': s['trips'][0]['stops'][0]['sequence']=True
    elif kind=='reverse_time': s['trips'][0]['stops'][1]['arrival']='08:00:00'
    elif kind=='source_empty': s['sources']=[]
    elif kind=='source_null': s['sources']=[None]
    elif kind=='coverage_null': s['coverage']=None
    elif kind=='calendar_null': s['calendar']=[None]
    elif kind=='calendar_bool': s['calendar'][0]['monday']=True
    elif kind=='exception_unknown': s['calendar_dates']=[{'service_id':'X','date':'20260929','exception_type':1}]
    elif kind=='nan_coordinate': s['stops']['A']['lat']=float('nan')
    elif kind=='origin_null': s['origins']['origin_a']=None
    elif kind=='entity_orphan': s['origins']['origin_a']['stop_ids']=['X']
    elif kind=='profile_extra': s['walking_profiles']['slow']={'description':'ignored','source':'unknown'}
    elif kind=='incomplete_coverage': s['coverage']['direct_search_complete']=False
    monkeypatch.setattr(p,'_load_snapshot',lambda _:s)
    result=p.plan_visit(request())
    assert result['status']=='unknown'
    assert result['itinerary'] is result['components_s'] is result['components'] is None


@pytest.mark.parametrize('raw',['{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}','{"x":-Infinity}'])
def test_strict_json(raw):
    with pytest.raises((ValueError,SnapshotError)):
        strict_loads(raw)


@pytest.mark.parametrize('snapshot_id',['synthetic-contract-v1','TEST_X','../../tests/mobility/fixtures/synthetic_snapshot.json'])
def test_production_cannot_run_fixtures(snapshot_id):
    assert p.plan_visit(request(snapshot_id=snapshot_id))['status']=='unknown'


def test_only_requested_allowlisted_file_read(monkeypatch,tmp_path):
    manifest=json.loads(p.MANIFEST_PATH.read_text(encoding='utf-8'))
    entry=manifest['snapshots'][p.DEFAULT_SNAPSHOT_ID]
    (tmp_path/entry['file']).write_bytes((p.MANIFEST_PATH.parent/entry['file']).read_bytes())
    (tmp_path/'foreign-corrupt.json').write_text('{')
    m=tmp_path/'allowlist.json';m.write_text(json.dumps(manifest))
    monkeypatch.setattr(p,'MANIFEST_PATH',m)
    r=p.plan_visit(real_request())
    assert r['status']=='ok'
    (tmp_path/entry['file']).write_text('{}')
    r=p.plan_visit(real_request())
    assert r['status']=='unknown' and 'hash mismatch' in r['error']['message']


def real_request(**changes):
    return dict(origin_id='zegama_center_stops',destination_id='beasain_center_stop_pair',
                date='2026-09-29',appointment_time='10:00',duration_minutes=30,**changes)


@pytest.mark.parametrize('margin',[0,1,3,8,120])
def test_initial_presence_buffer_once(snapshot,margin):
    # Return shifted late enough to isolate initial-buffer arithmetic.
    snapshot['trips'][1]['stops'][0].update(arrival='13:00:00',departure='13:00:00')
    snapshot['trips'][1]['stops'][1].update(arrival='13:40:00',departure='13:40:00')
    r=p.plan_visit(request(boarding_margin_minutes=margin))
    it=r['itinerary']; cs=r['components']
    assert r['status']=='ok'
    assert it['start_s']==32400-margin*60
    assert it['total_s']==it['end_s']-it['start_s']==sum(x['seconds'] for x in cs)
    assert it['total_s']==it['vehicle_span_s']+margin*60
    assert all(x['end_s']-x['start_s']==x['seconds']>=0 for x in cs)
    assert all(a['end_s']==b['start_s'] for a,b in zip(cs,cs[1:]))


@pytest.mark.parametrize('appointment,status,slack',[('10:00:00','ok',0),('10:00:01','no_feasible_journey',None),('09:59:59','ok',1)])
def test_return_boundary_one_second(snapshot,appointment,status,slack):
    r=p.plan_visit(request(appointment_time=appointment,duration_minutes=37))
    assert r['status']==status
    if slack is not None: assert r['itinerary']['return_slack_s']==slack


@pytest.mark.parametrize('appointment,status',[('09:50:00','ok'),('09:49:59','no_feasible_journey'),('09:50:01','ok')])
def test_arrival_boundary_one_second(snapshot,appointment,status):
    assert p.plan_visit(request(appointment_time=appointment))['status']==status


@pytest.mark.parametrize('deadline,status',[('11:20:00','ok'),('11:19:59','no_feasible_journey'),('11:20:01','ok')])
def test_return_deadline(snapshot,deadline,status):
    assert p.plan_visit(request(return_deadline=deadline))['status']==status


def test_cross_day_appointment(snapshot):
    assert p.plan_visit(request(appointment_time='23:50',duration_minutes=30))['status']=='unsupported'


def test_comparison_changes_all_parameters_and_preserves_outcomes(snapshot):
    result=p.compare_visits([request(),request(appointment_time='09:55',duration_minutes=32),request(duration_minutes=500),request(date='2027-01-01')])
    assert [r['status'] for r in result['results']]==['ok','ok','no_feasible_journey','unknown']
    pair=result['comparisons'][0]
    assert set(pair['requested_changes'])=={'appointment_time','duration_minutes'}
    assert pair['held_constant']['origin_id']=='origin_a'
    assert len(result['differences_s'])==1
    assert len(result['comparisons'])==6


def test_determinism_and_finite_output():
    a=p.plan_visit(real_request()); b=p.plan_visit(real_request())
    assert json.dumps(a,allow_nan=False,sort_keys=True)==json.dumps(b,allow_nan=False,sort_keys=True)


def test_snapshot_malformed_manifest(monkeypatch,tmp_path):
    m=tmp_path/'allowlist.json';m.write_text('null');monkeypatch.setattr(p,'MANIFEST_PATH',m)
    assert p.plan_visit(real_request())['status']=='unknown'
    assert p.get_capabilities()['snapshots']==[]


def test_missed_return_selects_later_departure(snapshot):
    later=copy.deepcopy(snapshot['trips'][1]);later['trip_id']='BACK_WD_2'
    later['stops'][0].update(arrival='11:40:00',departure='11:40:00')
    later['stops'][1].update(arrival='12:20:00',departure='12:20:00')
    snapshot['trips'].append(later)
    exact=p.plan_visit(request(duration_minutes=37))
    missed=p.plan_visit(request(duration_minutes=37,appointment_time='10:00:01'))
    assert exact['itinerary']['return_slack_s']==0
    assert exact['itinerary']['return']['trip_id']=='BACK_WD_1'
    assert missed['itinerary']['return']['trip_id']=='BACK_WD_2'
    assert missed['itinerary']['total_s']-exact['itinerary']['total_s']==3600


def test_dst_is_explicitly_unsupported(snapshot):
    snapshot['coverage'].update(end_date='2026-10-25',validated_dates=['2026-10-25'])
    for row in snapshot['calendar']:row['end_date']='2026-10-25'
    r=p.plan_visit(request(date='2026-10-25'))
    assert r['status']=='unsupported' and r['error']['code']=='dst_transition'


def test_raw_gtfs_oracle_real_cases():
    from scripts.mobility.raw_oracle_r4 import read_raw,calculate,ORIGINS
    raw=read_raw(Path(__file__).resolve().parents[2]/'datos_originales/movilidad/goierrialdea-3276fcae.zip')
    for origin in ORIGINS:
        for hour in ('09:30','13:00','17:00','23:00'):
            req=real_request();req.update(origin_id=origin,appointment_time=hour)
            expected=calculate(raw,req);result=p.plan_visit(req)
            assert result['status']==expected['status']
            if result['itinerary']:
                assert result['itinerary']['total_s']==expected['total_s']
                assert result['itinerary']['outbound']['trip_id']==expected['outbound_trip_id']
                assert result['itinerary']['return']['trip_id']==expected['return_trip_id']


@pytest.mark.parametrize('raw', ['null','[]','{"snapshot_id":"x","snapshot_id":"y"}','{"bad":NaN}'])
def test_hash_valid_but_corrupt_snapshot(monkeypatch,tmp_path,raw):
    manifest=json.loads(p.MANIFEST_PATH.read_text(encoding='utf-8'))
    entry=manifest['snapshots'][p.DEFAULT_SNAPSHOT_ID]
    file=tmp_path/entry['file'];file.write_text(raw,encoding='utf-8')
    entry['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
    m=tmp_path/'allowlist.json';m.write_text(json.dumps(manifest),encoding='utf-8')
    monkeypatch.setattr(p,'MANIFEST_PATH',m)
    result=p.plan_visit(real_request())
    assert result['status']=='unknown' and result['itinerary'] is None
