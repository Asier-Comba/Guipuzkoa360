"""R4 independent raw-GTFS evidence, sensitivity and local performance."""
import hashlib
import itertools
import json
import statistics
import subprocess
import sys
import time
import tracemalloc
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from prototypes.ir_y_volver import provider
from scripts.mobility.raw_oracle_r4 import read_raw, calculate, ORIGINS
from scripts.mobility.package_r4 import dump


def run():
    source=ROOT/'datos_originales/movilidad/goierrialdea-3276fcae.zip'
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    assert sha=='3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4'
    raw=read_raw(source)
    matrix=[]
    for origin,hour,duration,margins in itertools.product(ORIGINS, ['09:30','10:00','13:00','17:00','22:00'],[15,30,60],[(0,0),(10,3),(15,8)]):
        req=dict(origin_id=origin,destination_id='beasain_center_stop_pair',date='2026-09-29',
            appointment_time=hour,duration_minutes=duration,arrival_margin_minutes=margins[0],boarding_margin_minutes=margins[1])
        expected=calculate(raw,req)
        actual=provider.plan_visit(req)
        assert actual['status']==expected['status'], (req,actual,expected)
        if actual['status']=='ok':
            it=actual['itinerary']
            assert it['total_s']==expected['total_s']==sum(actual['components_s'].values())==it['end_s']-it['start_s']
            assert it['outbound']['trip_id']==expected['outbound_trip_id']
            assert it['return']['trip_id']==expected['return_trip_id']
            assert it['return_slack_s']==expected['return_slack_s']
        matrix.append({'request':req,'expected':expected,'provider_status':actual['status'],
            'provider_total_s':actual['itinerary']['total_s'] if actual['itinerary'] else None,'difference_s':0 if actual['itinerary'] else None,'conclusion':'PASS'})
    old=json.loads((ROOT/'docs/vnext/w1/REAL_CASES.json').read_text(encoding='utf-8'))
    reconciled=[]
    for case in old['cases']:
        req={**case['request'],'snapshot_id':provider.DEFAULT_SNAPSHOT_ID}
        actual=provider.plan_visit(req);expected=calculate(raw,req)
        assert actual['itinerary']['total_s']==expected['total_s']
        reconciled.append({'case_id':case['case_id'],'historical_0_1_total_s':case['expected']['total_s'],
            'new_0_2_total_s':expected['total_s'],'delta_s':expected['total_s']-case['expected']['total_s'],
            'same_outbound':actual['itinerary']['outbound']['trip_id']==case['expected']['outbound_trip_id'],
            'same_return':actual['itinerary']['return']['trip_id']==case['expected']['return_trip_id'],
            'permission_repair_impact':'none: selected raw permissions are 0',
            'request':req,'independent_raw_expected':expected,'provider_result':actual,'conclusion':'PASS'})
    # Keep nonviable real evidence, not just successful journeys.
    edge=next(x for x in matrix if x['provider_status']=='no_feasible_journey')
    reconciled.append({'case_id':'R4-NO-RETURN','request':edge['request'],'independent_raw_expected':edge['expected'],
        'provider_result':provider.plan_visit(edge['request']),'conclusion':'PASS'})
    route_ids={r['route_id'] for r in raw['routes.txt'] if r['route_short_name'].upper()=='GO01'}
    trip_ids={r['trip_id'] for r in raw['trips.txt'] if r['route_id'] in route_ids}
    selected=[r for r in raw['stop_times.txt'] if r['trip_id'] in trip_ids]
    impact={'raw_rows':len(raw['stop_times.txt']),'go01_rows':len(selected),'go01_trips':len(trip_ids),
        'go01_counts':{f:dict(Counter(r.get(f,'') for r in selected)) for f in ('pickup_type','drop_off_type','timepoint')},
        'feed_counts':{f:dict(Counter(r.get(f,'') for r in raw['stop_times.txt'])) for f in ('pickup_type','drop_off_type','timepoint')},
        'go01_conditioned_trips':len({r['trip_id'] for r in selected if r.get('pickup_type') in ('2','3') or r.get('drop_off_type') in ('2','3')})}
    request=matrix[0]['request']
    samples=[]
    for _ in range(30):
        t=time.perf_counter_ns();res=provider.plan_visit(request);samples.append((time.perf_counter_ns()-t)/1e6)
    tracemalloc.start();provider.plan_visit(request);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    cold=[]
    command='import json,time; from prototypes.ir_y_volver import provider as p; q=json.loads('+repr(json.dumps(request))+'); t=time.perf_counter_ns(); r=p.plan_visit(q); print((time.perf_counter_ns()-t)/1e6)'
    for _ in range(3):
        cold.append(float(subprocess.check_output([sys.executable,'-c',command],cwd=ROOT,text=True)))
    performance={'classification':'LOCAL_PYTHON_NOT_PORTAL','warm_process_calls':len(samples),
        'warm_process_median_ms':statistics.median(samples),'warm_process_p95_ms':sorted(samples)[28],
        'fresh_process_first_call_ms':cold,'peak_python_allocated_bytes':peak,
        'payload_bytes':len(json.dumps(res,ensure_ascii=False,allow_nan=False).encode()),
        'note':'No provider cache. Cold means fresh interpreter, not OS disk-cache flush. Tracemalloc measures Python allocations, not RSS.'}
    dump(ROOT/'docs/vnext/w1/REAL_CASES_R4.json',{'schema_version':'0.2.0','source_sha256':sha,'cases':reconciled})
    dump(ROOT/'docs/vnext/w1/MATRIX_R4.json',{'classification':'NEW_RAW_GTFS_ORACLE_NOT_HISTORICAL_POC','cases':matrix,'pass':len(matrix),'fail':0})
    dump(ROOT/'docs/vnext/w1/IMPACT_R4.json',impact)
    dump(ROOT/'docs/vnext/w1/PERFORMANCE_R4.json',performance)
    print(json.dumps({'matrix_pass':len(matrix),'real_cases':len(reconciled),'impact':impact,'performance':performance}))


if __name__=='__main__':run()
