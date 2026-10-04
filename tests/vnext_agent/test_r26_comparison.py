import copy
import importlib.util
import itertools
import json
import random
import re
import subprocess
import sys
import zipfile
import pytest
from scripts.vnext_agent import build_r26 as build

ORIGINS=['zegama_center_stops','segura_herriko_plaza_stops','idiazabal_center_stops']
TIMES=['09:30','09:45','10:00','10:15']
def args(times,origin=ORIGINS[0]):
    return dict(origin_id=origin,destination_id='beasain_official_centre_anchor',date='2026-09-29',appointment_times=times,duration_minutes=20)

@pytest.fixture(scope='module')
def observed(tmp_path_factory):
    build.build();root=tmp_path_factory.mktemp('r26')
    with zipfile.ZipFile(build.ZIP) as z:z.extractall(root)
    cases=[dict(id='caps',tool='consultar_capacidades',arguments={})]
    for origin in ORIGINS:
        for times in [[t] for t in TIMES]+list(map(list,itertools.permutations(TIMES,2))):
            cases.append(dict(id=origin+str(times),tool='plan_visit',arguments=args(times,origin),keep_raw=True))
    for i,times in enumerate([[],None,'09:30',['09:30']*2,['09:30','09:45','10:00'],['24:00'],['9:30'],['09:30:00'],[True],[{}],[float('nan')]]):
        cases.append(dict(id='invalid'+str(i),tool='plan_visit',arguments=args(times)))
    result=subprocess.run([sys.executable,'-X','utf8','-m','scripts.vnext_agent.worker_r20',str(root)],cwd=build.ROOT,input=json.dumps({'cases':cases}),capture_output=True,text=True,encoding='utf-8',timeout=180)
    assert result.returncode==0,result.stderr
    data=json.loads(result.stdout)
    spec=importlib.util.spec_from_file_location('r26_tools_test',root/'tools.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    return data,m

def seconds(human):
    h,m,s=map(int,re.fullmatch(r'(\d+) h (\d+) min (\d+) s',human).groups());assert m<60 and s<60
    return h*3600+m*60+s

def test_schema_and_catalog(observed):
    data,_=observed
    assert len(data['signatures'])==10
    assert data['signatures']['plan_visit']['fields']==list(args([]))
    catalog=data['records']['caps']['view']
    cap=next(c for c in catalog['capabilities'] if c['id']=='plan_visit')
    assert [f['name'] for f in cap['input_fields']]==list(args([]))
    field=next(f for f in cap['input_fields'] if f['name']=='appointment_times')
    assert field['minItems']==1 and field['maxItems']==2 and field['uniqueItems']
    assert 'individual_calls' not in json.dumps(catalog)

@pytest.mark.parametrize('index',range(11))
def test_invalid(observed,index):
    row=observed[0]['records']['invalid'+str(index)]
    assert row['status']=='error' and not row['claims'] and row['execute_calls']==0

@pytest.mark.parametrize('origin',ORIGINS)
@pytest.mark.parametrize('pair',list(itertools.permutations(TIMES,2)))
def test_provider_comparison(observed,origin,pair):
    data,_=observed;row=data['records'][origin+str(list(pair))]
    assert row['status']=='valid',row
    assert row['execute_calls']==1
    v=row['view'];ledger=v['comparison_ledger'];left,right=v['mobility']['scenarios']
    assert ledger['comparison_verified']
    assert ledger['total_delta_seconds']==right['time_summary']['total_s']-left['time_summary']['total_s']
    assert ledger['total_delta_seconds']==row['raw']['comparisons'][0]['total_difference_s']
    for key,rawkey in [('total','total_s'),('start','scope_start_s'),('end','scope_end_s')]:
        d=right['time_summary'][rawkey]-left['time_summary'][rawkey]
        assert ledger[key+'_delta_seconds']==d and seconds(ledger[key+'_delta_human'])==abs(d)
    reverse=data['records'][origin+str(list(reversed(pair)))]['view']['comparison_ledger']
    assert reverse['total_delta_seconds']==-ledger['total_delta_seconds']
    assert reverse['total_delta_human']==ledger['total_delta_human']
    assert all(len(s['duration_ledger']['components'])==8 for s in (left,right))

def test_known_oracle(observed):
    ledger=observed[0]['records'][ORIGINS[0]+str(['09:30','09:45'])]['view']['comparison_ledger']
    assert ledger['left']['total_seconds']==10691 and ledger['right']['total_seconds']==8591
    assert ledger['total_delta_seconds']==-2100 and ledger['start_delta_seconds']==2100 and ledger['end_delta_seconds']==0
    assert ledger['total_delta_human']=='0 h 35 min 0 s'
    assert '0 h 35 min 0 s menos' in ledger['comparison_sentence']
    assert '0 h 35 min 0 s más tarde' in ledger['comparison_sentence']

@pytest.mark.parametrize('origin',ORIGINS)
@pytest.mark.parametrize('time',TIMES)
def test_single_preserves_provider(observed,origin,time):
    row=observed[0]['records'][origin+str([time])];assert row['status']=='valid'
    assert 'comparison_ledger' not in row['view']
    s=row['view']['mobility']['scenarios'][0]
    assert s['duration_ledger']['total_seconds']==row['raw']['itinerary']['total_s']
    assert s['components_s']==row['raw']['components_s']

@pytest.mark.parametrize('fault',['status','origin','destination','date','duration','time','defaults','total','start','end','human','provider_delta','comparable','index','missing','partition','component'])
def test_fail_closed_projection(observed,fault):
    data,m=observed;v=copy.deepcopy(data['records'][ORIGINS[0]+str(['09:30','09:45'])]['view']);s=v['mobility']['scenarios'][1];c=v['mobility']['comparisons'][0]
    if fault=='status':s['status']='error'
    elif fault in ('origin','destination','date','duration','time','defaults'):
        field={'origin':'origin_id','destination':'destination_id','duration':'duration_minutes','time':'appointment_time','defaults':'boarding_margin_minutes'}.get(fault,fault);s['effective_parameters'][field]='tampered'
    elif fault=='total':s['duration_ledger']['total_seconds']+=1
    elif fault in ('start','end'):s['journey_scope'][fault]['seconds']+=1
    elif fault=='human':s['duration_ledger']['total_human']='0 h 0 min 0 s'
    elif fault=='provider_delta':c['total_difference_s']+=1
    elif fault=='comparable':c['comparability']='not_comparable'
    elif fault=='index':c['right_index']=0
    elif fault=='missing':v['mobility']['scenarios'].pop()
    elif fault=='partition':s['duration_ledger']['partition_verified']=False
    elif fault=='component':s['duration_ledger']['components'][0]['seconds']+=1
    with pytest.raises(m.ContractViolation):m._r26_comparison(v,args(['09:30','09:45']))

def test_formatter_fuzz(observed):
    _,m=observed;rng=random.Random(26)
    for _ in range(5000):
        a,b=rng.randrange(86400),rng.randrange(86400)
        assert seconds(m._duration_hms(abs(b-a)))==abs(b-a)
        assert m._duration_hms(abs(b-a))==m._duration_hms(abs(a-b))


def test_determinism_directions_and_synthetic_equal(observed):
    data,m=observed
    directions=set()
    for origin in ORIGINS:
        for pair in itertools.permutations(TIMES,2):
            view=data['records'][origin+str(list(pair))]['view']
            first=m._r26_comparison(copy.deepcopy(view),args(list(pair),origin))
            assert first==m._r26_comparison(copy.deepcopy(view),args(list(pair),origin))
            directions.add(first['direction'])
            reversed_ledger=data['records'][origin+str(list(reversed(pair)))]['view']['comparison_ledger']
            assert reversed_ledger['direction']=={'less':'more','more':'less','equal':'equal'}[first['direction']]
    assert {'less','more'} <= directions
    view=copy.deepcopy(data['records'][ORIGINS[0]+str(['09:30','09:45'])]['view'])
    view['mobility']['scenarios'][1]=copy.deepcopy(view['mobility']['scenarios'][0])
    view['mobility']['scenarios'][1]['effective_parameters']['appointment_time']='09:45:00'
    view['mobility']['comparisons'][0]['total_difference_s']=0
    equal=m._r26_comparison(view,args(['09:30','09:45']))
    assert equal['direction']=='equal' and equal['total_delta_seconds']==0
    assert equal['total_delta_human']=='0 h 0 min 0 s'
    assert equal['comparison_sentence'].startswith('Ambos escenarios tienen la misma duración calculada.')

def test_public_failure_has_no_partial_claims(observed,monkeypatch):
    data,m=observed;v=copy.deepcopy(data['records'][ORIGINS[0]+str(['09:30','09:45'])]['view'])
    v['mobility']['comparisons'][0]['total_difference_s']+=1
    monkeypatch.setattr(m,'_r26_prior_public_call',lambda *a,**k:json.dumps(v))
    result=json.loads(m.public_call('plan_visit',args(['09:30','09:45']),'fault'))
    assert result['status']=='error' and result['claims']==[] and 'mobility' not in result and 'comparison_ledger' not in result
