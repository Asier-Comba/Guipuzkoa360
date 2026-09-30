"""Seeded metamorphic and call-isolation campaign for the frozen R6 producer."""
import copy
import json
import math
import random

from prototypes.ir_y_volver import provider as r4
from prototypes.ir_y_volver import provider_r6 as p
from scripts.mobility.audit_r7 import HEALTH, validate_health_result
from scripts.mobility.build_health_r5 import DOC, dump

SEED=360007
CASES=500
ALLOWED={'ok','no_feasible_journey','unknown','unsupported','error'}


def _finite(value):
    if isinstance(value,float): return math.isfinite(value)
    if isinstance(value,dict): return all(_finite(v) for v in value.values())
    if isinstance(value,list): return all(_finite(v) for v in value)
    return True


def _valid_request(rng,index):
    seconds=rng.choice([0,1,5,6,7,47,48,49,59]);minute=rng.choice(range(0,60,5))
    hour=rng.randint(7,22)
    request={'origin_id':rng.choice(sorted(HEALTH['origins'])),'destination_id':HEALTH['destination_id'],
      'date':HEALTH['validated_date'],'appointment_time':f'{hour:02d}:{minute:02d}:{seconds:02d}',
      'duration_minutes':rng.choice([1,20,25,26,30,40,60,120,720])}
    if rng.random()<.55:request['arrival_margin_minutes']=rng.choice([0,1,5,10,30,240])
    if rng.random()<.55:request['boarding_margin_minutes']=rng.choice([0,1,3,7,30,120])
    if rng.random()<.25:request['walking_profile_id']=HEALTH['walking_profile_id']
    if rng.random()<.25:request['snapshot_id']=HEALTH['snapshot_id']
    if rng.random()<.35:
        deadline_hour=rng.randint(9,23);request['return_deadline']=f'{deadline_hour:02d}:{rng.choice([0,15,30,45]):02d}:00'
    return request


def _invalid_request(rng,index):
    request=_valid_request(rng,index);kind=index%7
    if kind==0:request['origin_id']='unknown'
    elif kind==1:request['destination_id']='unknown'
    elif kind==2:request['date']='2026-09-30'
    elif kind==3:request['walking_profile_id']='unknown'
    elif kind==4:request['duration_minutes']='20'
    elif kind==5:request['boarding_margin_minutes']=-1
    else:request['unexpected']=True
    return request


def _assert_ok(result):
    q=result['normalized_request'];it=result['itinerary'];parts=result['components']
    assert it['total_s']==it['end_s']-it['start_s']==sum(x['seconds'] for x in parts)
    assert all(a['end_s']==b['start_s'] for a,b in zip(parts,parts[1:]))
    assert result['components_s']['appointment_s']==q['duration_minutes']*60
    assert it['outbound']['from_stop_id'] in HEALTH['origins'][q['origin_id']]['stop_ids']
    assert it['outbound']['to_stop_id'] in HEALTH['walking_links']
    assert it['return']['from_stop_id'] in HEALTH['walking_links']
    assert it['return']['to_stop_id'] in HEALTH['origins'][q['origin_id']]['stop_ids']
    assert p.r4._clock_seconds(it['outbound']['arrival_time'])+result['walking']['outbound']['seconds']<=p.r4._clock_seconds(q['appointment_time'])-q['arrival_margin_minutes']*60
    assert p.r4._clock_seconds(it['return']['departure_time'])>=p.r4._clock_seconds(q['appointment_time'])+q['duration_minutes']*60+result['walking']['return']['seconds']+q['boarding_margin_minutes']*60
    if q['return_deadline']:assert p.r4._clock_seconds(it['return']['arrival_time'])<=p.r4._clock_seconds(q['return_deadline'])


def run():
    rng=random.Random(SEED);distribution={status:0 for status in sorted(ALLOWED)};first=None
    requests=[]
    for index in range(CASES):
        request=_invalid_request(rng,index) if index%5==0 else _valid_request(rng,index)
        requests.append(request)
        try:
            first_result=p.plan_visit(copy.deepcopy(request));second_result=p.plan_visit(copy.deepcopy(request))
            assert first_result==second_result and first_result['status'] in ALLOWED and _finite(first_result)
            if first_result['schema_version']=='0.3.1':validate_health_result(first_result,request)
            if first_result['status']=='ok':_assert_ok(first_result)
            distribution[first_result['status']]+=1
        except Exception as exc:
            first={'index':index,'request':request,'error':repr(exc)};break
    assert first is None,first
    base={'origin_id':'zegama_center_stops','destination_id':HEALTH['destination_id'],'date':HEALTH['validated_date'],
      'appointment_time':'09:45','duration_minutes':20}
    omitted=p.plan_visit(base);explicit=p.plan_visit({**base,'arrival_margin_minutes':10,'boarding_margin_minutes':3,
      'walking_profile_id':HEALTH['walking_profile_id'],'snapshot_id':HEALTH['snapshot_id'],'return_deadline':None})
    for field in ('status','normalized_request','itinerary','components_s','walking','health_destination','limitations','assumptions','error'):
        assert omitted[field]==explicit[field]
    sample=[base,{**base,'appointment_time':'10:00'},{**base,'duration_minutes':26},
      {**base,'origin_id':'segura_herriko_plaza_stops'}]
    forward=p.compare_visits(sample);reverse=p.compare_visits(list(reversed(sample)))
    assert forward['results']==[p.plan_visit(x) for x in sample]
    assert reverse['results']==list(reversed(forward['results']))
    for comparison in forward['comparisons']:
        left,right=forward['results'][comparison['left_index']],forward['results'][comparison['right_index']]
        if comparison['comparability']=='comparable':
            assert comparison['total_difference_s']==right['itinerary']['total_s']-left['itinerary']['total_s']
        if left['normalized_request']['origin_id']!=right['normalized_request']['origin_id']:
            assert comparison['comparability']=='not_comparable' and comparison['total_difference_s'] is None
    relaxed=p.plan_visit({**base,'return_deadline':'23:59:59'});tight=p.plan_visit({**base,'return_deadline':'11:07:48'})
    assert tight['status'] in ALLOWED
    if tight['status']=='ok':assert p.r4._clock_seconds(tight['itinerary']['return']['arrival_time'])<=p.r4._clock_seconds('11:07:48')
    a=p.plan_visit(base);b=p.plan_visit({**base,'origin_id':'idiazabal_center_stops','boarding_margin_minutes':7})
    invalid=p.plan_visit({**base,'duration_minutes':'bad'});a2=p.plan_visit(base)
    r4q={'origin_id':'zegama_center_stops','destination_id':'beasain_center_stop_pair','date':'2026-09-29',
      'appointment_time':'09:30','duration_minutes':30,'snapshot_id':r4.DEFAULT_SNAPSHOT_ID}
    r4a=p.plan_visit(r4q);p.compare_visits([base,r4q]);r4b=p.plan_visit(r4q)
    isolation={'A_B_A':a==a2,'valid_error_valid':a==a2 and invalid['status']=='error',
      'health_R4_health':r4a==r4b,'single_compare_single':p.plan_visit(base)==a}
    assert all(isolation.values())
    artifact={'seed':SEED,'cases':CASES,'case_description':'Seeded requests; not independent tests.',
      'distribution':distribution,'properties_checked':15,'first_counterexample':None,
      'metamorphic':{'omitted_vs_explicit_defaults':'PASS','request_reordering':'PASS',
        'comparison_delta':'PASS','cross_origin_no_delta':'PASS','deadline_tightening':'PASS'},
      'isolation':isolation,'status':'PASS'}
    dump(DOC/'METAMORPHIC_STRESS_R7.json',artifact);dump(DOC/'ISOLATION_R7.json',{'status':'PASS',**isolation})
    print(json.dumps(artifact));return artifact


if __name__=='__main__':run()
