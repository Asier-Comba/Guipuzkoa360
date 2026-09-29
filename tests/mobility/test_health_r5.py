import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest
from prototypes.ir_y_volver import provider as r4
from prototypes.ir_y_volver import provider_r5 as p
from prototypes.ir_y_volver.schema_r5 import validate
from scripts.mobility.build_health_r5 import build, select_centre
from scripts.mobility.package_r5 import build as package

ROOT=Path(__file__).resolve().parents[2]
Q={'origin_id':'zegama_center_stops','destination_id':'beasain_official_centre_anchor','date':'2026-09-29','appointment_time':'09:45','duration_minutes':20}


def schema(name): return json.loads((p.HERE/f'contracts/v0.3.0/{name}.schema.json').read_bytes())


def test_health_plan_and_closed_contract():
    r=p.plan_visit(Q);assert r['status']=='ok';validate(r,schema('result'))
    it=r['itinerary']; assert it['total_s']==it['end_s']-it['start_s']==sum(c['seconds'] for c in r['components'])
    assert r['walking']['outbound']['seconds']>0 and r['walking']['return']['seconds']>0
    assert r['health_destination']['entrance_verified'] is False
    refs={x['source_id'] for x in r['sources']}
    assert all(set(c['source_refs'])<=refs for c in r['components'])
    for field in ('normalized_request','itinerary','health_destination'):
        broken=copy.deepcopy(r);broken[field]['unexpected']=True
        with pytest.raises(ValueError):validate(broken,schema('result'))
    for field in ('sources','components'):
        broken=copy.deepcopy(r);broken[field][0]['unexpected']=True
        with pytest.raises(ValueError):validate(broken,schema('result'))
    broken=copy.deepcopy(r);broken['walking']['outbound']['unexpected']=True
    with pytest.raises(ValueError):validate(broken,schema('result'))


def test_capabilities_and_mixed_comparison():
    c=p.get_capabilities(); validate(c,schema('capabilities'))
    assert len(c['snapshots'])==2 and c['error'] is None
    old={**Q,'snapshot_id':r4.DEFAULT_SNAPSHOT_ID,'destination_id':'beasain_center_stop_pair'}
    assert p.plan_visit(old)==r4.plan_visit(old)
    assert p.compare_visits([old,old])==r4.compare_visits([old,old])
    mix=p.compare_visits([Q,old]);validate(mix,schema('comparison'))
    assert mix['comparisons'][0]['total_difference_s'] is None
    assert mix['comparisons'][0]['comparability']=='not_comparable'
    result=p.compare_visits([Q,{**Q,'duration_minutes':40}]);validate(result,schema('comparison'))
    assert result['comparisons'][0]['requested_changes']==[{'field':'duration_minutes','left':20,'right':40}]


@pytest.mark.parametrize('change,status',[
    ({'date':'2026-10-01'},'unknown'),({'origin_id':'not_here'},'unsupported'),
    ({'duration_minutes':float('nan')},'error'),({'duration_minutes':True},'error'),
    ({'appointment_time':'23:59'},'unsupported'),({'return_deadline':'08:00'},'no_feasible_journey'),
    ({'walking_profile_id':'senior'},'error'),({'extra':0},'error')])
def test_controlled_errors(change,status):
    r=p.plan_visit({**Q,**change});assert r['status']==status;validate(r,schema('result'))


@pytest.mark.parametrize('mutation',[
    lambda h:h['health_destination'].update(entrance_verified=True),
    lambda h:h['health_destination'].update(human_review_required=False),
    lambda h:h['walking_links']['7219']['outbound'].update(seconds=0),
    lambda h:h['walking_links']['7219']['outbound'].update(total_metres=float('inf')),
    lambda h:h['walking_links']['7219']['outbound'].update(network_sha256='0'*64),
    lambda h:h['walking_links']['7219']['outbound'].update(connector_metres=[100.1,0]),
    lambda h:h['walking_links']['7219']['outbound'].update(start_node_id='wrong'),
    lambda h:h['sources'][0].update(source_sha256='0'*64),
    lambda h:h.update(walking_links={}),
    lambda h:h['source_conflict'].update(chosen_source_id='PADI_2026'),
])
def test_corrupt_health_evidence(mutation):
    h,b=p._load();mutation(h)
    with pytest.raises(ValueError):p.validate_health(h,b)


def test_source_conflict_and_snapshot_rebuild(tmp_path):
    h,_=p._load(); records=h['source_conflict']['records']
    assert select_centre(records)==select_centre(records[::-1])
    assert select_centre(records)['human_review_required']
    with pytest.raises(ValueError):select_centre([records[0],records[0]])
    dest=tmp_path/'health.json';build(dest)
    assert dest.read_bytes()==(p.HERE/f'snapshots/{p.ID}.json').read_bytes()


def test_tampered_snapshot_fails_closed(tmp_path,monkeypatch):
    manifest=json.loads(p.MANIFEST.read_bytes());dest=tmp_path/'allowlist.json'
    dest.write_text(json.dumps(manifest));(tmp_path/manifest['file']).write_text('{}')
    monkeypatch.setattr(p,'MANIFEST',dest)
    assert p.plan_visit(Q)['status']=='unknown'
    assert p.get_capabilities()['error']['code']=='invalid_health_snapshot'


def test_double_package_and_isolated_no_network(tmp_path):
    a=package(tmp_path/'a.zip',False);b=package(tmp_path/'b.zip',False)
    assert a['package_sha256']==b['package_sha256']
    with zipfile.ZipFile(tmp_path/'a.zip') as z:z.extractall(tmp_path/'isolated')
    command='''import socket,json
def forbid(*a,**kw): raise RuntimeError('no network')
socket.socket=forbid
from prototypes.ir_y_volver.provider_r5 import plan_visit,get_capabilities
q=json.loads(%r)
assert plan_visit(q)['status']=='ok'
assert len(get_capabilities()['snapshots'])==2
print('PASS')
''' % json.dumps(Q)
    env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')}
    result=subprocess.check_output([sys.executable,'-c',command],cwd=tmp_path/'isolated',env=env,text=True)
    assert 'PASS' in result


def test_selection_tie_break_is_explicit(monkeypatch):
    real=p.plan_visit(Q);h,b=p._load()
    out=real['itinerary']['outbound'];back=real['itinerary']['return']
    def timed(leg,departure,arrival,**changes):
        fmt=lambda s:f'{s//3600:02d}:{s%3600//60:02d}:{s%60:02d}'
        return {**leg,'departure_s':departure,'arrival_s':arrival,'departure_time':fmt(departure),'arrival_time':fmt(arrival),**changes}
    outs=[timed(out,30600,32400,to_stop_id='7215',trip_id='a'),timed(out,30600,32400,to_stop_id='7219',trip_id='z'),
          timed(out,30600,32400,to_stop_id='7219',trip_id='b')]
    backs=[timed(back,37800,39600,trip_id='z'),timed(back,37800,39600,trip_id='a')]
    monkeypatch.setattr(p,'_load',lambda:(h,b))
    monkeypatch.setattr(r4,'_legs',lambda s,a,f,t:outs if '8305' in f else backs)
    selected=p.plan_visit(Q)['itinerary']
    assert selected['outbound']['trip_id']=='b' and selected['return']['trip_id']=='a'
    outs.reverse();backs.reverse()
    assert p.plan_visit(Q)['itinerary']==selected


def test_return_slack_zero_minus_one_and_next(monkeypatch):
    real=p.plan_visit(Q);h,b=p._load();out=real['itinerary']['outbound'];back=real['itinerary']['return']
    out={**out,'departure_s':r4._clock_seconds(out['departure_time']),'arrival_s':r4._clock_seconds(out['arrival_time'])}
    ready=35100+1200+h['walking_links'][back['from_stop_id']]['return']['seconds']+180
    def leg(delta):
        dep=ready+delta;arrival=dep+2000
        return {**back,'departure_s':dep,'arrival_s':arrival,'trip_id':'trip_'+str(delta),
            'departure_time':f'{dep//3600:02d}:{dep%3600//60:02d}:{dep%60:02d}',
            'arrival_time':f'{arrival//3600:02d}:{arrival%3600//60:02d}:{arrival%60:02d}'}
    backs=[leg(-1),leg(0),leg(1800)]
    monkeypatch.setattr(p,'_load',lambda:(h,b));monkeypatch.setattr(r4,'_legs',lambda s,a,f,t:[out] if '8305' in f else backs)
    it=p.plan_visit(Q)['itinerary'];assert it['return_slack_s']==0 and it['return']['trip_id']=='trip_0'
    backs.remove(backs[1]);it=p.plan_visit(Q)['itinerary'];assert it['return_slack_s']==1800
    backs.pop();assert p.plan_visit(Q)['status']=='no_feasible_journey'


def test_all_health_matrix_rows_match_independent_csv_oracle():
    from scripts.mobility.verify_health_r5 import read_raw,oracle
    h,_=p._load();raw=read_raw()
    for origin in h['origins']:
        for minute in range(510,721,15):
            for duration in (20,30,40):
                q={**Q,'origin_id':origin,'appointment_time':f'{minute//60:02d}:{minute%60:02d}','duration_minutes':duration}
                r=p.plan_visit(q);e=oracle(raw,q,h)
                assert r['status']==e['status']=='ok'
                assert r['itinerary']['total_s']==e['total_s']
                assert r['itinerary']['return_slack_s']==e['return_slack_s']
                validate(r,schema('result'))
