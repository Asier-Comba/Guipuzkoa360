"""Independent boundary evidence, cross-origin table and bounded local cost."""
import json
import copy
import hashlib
import math
import statistics
import time
import tracemalloc
import tempfile
from pathlib import Path

from prototypes.ir_y_volver import provider_r6 as p
from scripts.mobility.build_health_r5 import DOC, dump
from scripts.mobility.verify_health_r5 import oracle, read_raw

BASE = dict(origin_id='zegama_center_stops', destination_id='beasain_official_centre_anchor',
            date='2026-09-29', duration_minutes=20)


def _public(result):
    return {'status': result['status'], 'error': result['error'], 'normalized_request': result['normalized_request'],
            'itinerary': result['itinerary'], 'components_s': result['components_s'],
            'parameter_provenance': result.get('parameter_provenance')}


def run(output=DOC):
    health, _ = p.r5._load(); raw = read_raw(); cases = []
    requests = [
      ('outbound_one_second_before', {**BASE, 'appointment_time':'09:34:05'}),
      ('outbound_exact_margin', {**BASE, 'appointment_time':'09:34:06'}),
      ('outbound_one_second_after', {**BASE, 'appointment_time':'09:34:07'}),
      ('duration_last_departure', {**BASE, 'appointment_time':'09:45', 'duration_minutes':25}),
      ('duration_loses_departure', {**BASE, 'appointment_time':'09:45', 'duration_minutes':26}),
      ('deadline_one_second_before', {**BASE, 'appointment_time':'09:45', 'return_deadline':'11:07:47'}),
      ('deadline_exact', {**BASE, 'appointment_time':'09:45', 'return_deadline':'11:07:48'}),
      ('deadline_one_second_after', {**BASE, 'appointment_time':'09:45', 'return_deadline':'11:07:49'}),
    ]
    for case_id, request in requests:
        result = p.plan_visit(request); expected = oracle(raw, request, health)
        passed = result['status'] == expected['status']
        if result['status'] == 'ok':
            passed &= result['itinerary']['total_s'] == expected['total_s']
            passed &= result['itinerary']['outbound']['trip_id'] == expected['outbound_trip_id']
            passed &= result['itinerary']['return']['trip_id'] == expected['return_trip_id']
        assert passed
        cases.append({'case_id':case_id, 'request':request, 'independent_expected':expected,
                      'provider_result':_public(result), 'pass':True})
    negative = [
      ('outside_day', {**BASE,'appointment_time':'23:50'}, 'unsupported'),
      ('date_not_validated', {**BASE,'appointment_time':'09:45','date':'2026-09-30'}, 'unknown'),
      ('destination_unknown', {**BASE,'appointment_time':'09:45','destination_id':'unknown'}, 'unsupported'),
      ('profile_unknown', {**BASE,'appointment_time':'09:45','walking_profile_id':'unknown'}, 'error'),
      ('snapshot_unknown', {**BASE,'appointment_time':'09:45','snapshot_id':'unknown'}, 'unknown')]
    for case_id, request, status in negative:
        result=p.plan_visit(request); assert result['status']==status
        cases.append({'case_id':case_id,'request':request,'expected_status':status,
                      'provider_result':_public(result),'pass':True})
    original=p.r5.MANIFEST; manifest=json.loads(original.read_bytes())
    snapshot=json.loads((original.parent/manifest['file']).read_bytes())
    snapshot['walking_links']['7219']['outbound']['seconds'] += 1
    raw_corrupt=(json.dumps(snapshot,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    with tempfile.TemporaryDirectory() as folder:
        target=Path(folder);(target/manifest['file']).write_bytes(raw_corrupt)
        base_name=snapshot['base_snapshot_id']+'.json'
        (target/base_name).write_bytes((original.parent/base_name).read_bytes())
        manifest['sha256']=hashlib.sha256(raw_corrupt).hexdigest()
        (target/'allowlist.json').write_text(json.dumps(manifest),encoding='utf-8')
        p.r5.MANIFEST=target/'allowlist.json'
        try: result=p.plan_visit({**BASE,'appointment_time':'09:45'})
        finally: p.r5.MANIFEST=original
    assert result['status']=='unknown' and result['error']['code']=='invalid_health_snapshot'
    cases.append({'case_id':'corrupted_walking_link','request':{**BASE,'appointment_time':'09:45'},
      'corruption':'7219 outbound seconds +1 with valid manifest hash','expected_status':'unknown',
      'provider_result':_public(result),'pass':True})
    dump(output/'BOUNDARY_CASES_R6.json', {'oracle':'raw GTFS CSV selection independent of provider plan_visit',
        'summary':{'cases':len(cases),'pass':len(cases),'fail':0},'cases':cases})
    common=dict(destination_id=BASE['destination_id'],date=BASE['date'],appointment_time='09:45',duration_minutes=20)
    side=[]
    for origin in sorted(health['origins']):
        request={**common,'origin_id':origin}; result=p.plan_visit(request); assert result['status']=='ok'
        side.append({'request':request,'result':_public(result),'comparison_semantics':'side_by_side_only'})
    dump(output/'CROSS_ORIGIN_SCENARIOS_R6.json', {'held_constant':list(common),
        'numeric_cross_origin_delta_supported':False,
        'limitation':'No population inference or individual recommendation.', 'scenarios':side})
    timings={}
    seed={**BASE,'appointment_time':'09:45'}
    for size in (1,2,8,32):
        samples=[]
        for _ in range(3):
            start=time.perf_counter()
            result=p.plan_visit(seed) if size==1 else p.compare_visits([{**seed,'duration_minutes':20+i%2} for i in range(size)])
            samples.append((time.perf_counter()-start)*1000)
        tracemalloc.start()
        result=p.plan_visit(seed) if size==1 else p.compare_visits([{**seed,'duration_minutes':20+i%2} for i in range(size)])
        _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        timings[str(size)]={'operation':'plan_visit' if size==1 else 'compare_visits',
          'p50_ms':statistics.median(samples),'max_ms':max(samples),'python_peak_bytes':peak,
          'payload_bytes':len(json.dumps(result,ensure_ascii=False,allow_nan=False).encode())}
    dump(output/'PERFORMANCE_R6.json', {'local_python_not_portal':True,'samples_per_size':3,'measurements':timings})
    print(json.dumps({'boundary':f"{len(cases)}/{len(cases)}",'performance_sizes':[1,2,8,32]}))
    return cases


if __name__=='__main__': run()
