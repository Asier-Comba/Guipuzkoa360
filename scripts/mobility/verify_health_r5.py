"""Independent CSV journey oracle and complete R5 matrix (no historical expected totals)."""
import csv
import io
import json
import math
import statistics
import subprocess
import sys
import time
import tracemalloc
import zipfile
from pathlib import Path
from datetime import date

from prototypes.ir_y_volver import provider_r5 as p
from scripts.mobility.build_health_r5 import ROOT,DOC,dump,sha


def clock(text):
    h,m,*s=map(int,text.split(':')); return 3600*h+60*m+(s[0] if s else 0)


def read_raw():
    with zipfile.ZipFile(ROOT/'datos_originales/movilidad/goierrialdea-3276fcae.zip') as z:
        return {name:list(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig'))))
                for name in ('routes.txt','trips.txt','stop_times.txt','calendar.txt')}


def oracle(raw,q,h):
    day=q['date'].replace('-','');weekday=['monday','tuesday','wednesday','thursday','friday','saturday','sunday'][date.fromisoformat(q['date']).weekday()]
    services={r['service_id'] for r in raw['calendar.txt'] if r['start_date']<=day<=r['end_date'] and r[weekday]=='1'}
    routes={r['route_id'] for r in raw['routes.txt'] if r['route_short_name']=='GO01'}
    trips={r['trip_id'] for r in raw['trips.txt'] if r['route_id'] in routes and r['service_id'] in services}
    rows={tid:[] for tid in trips}
    for line,r in enumerate(raw['stop_times.txt'],2):
        if r['trip_id'] in trips: rows[r['trip_id']].append({**r,'csv_line':line})
    origins=set(h['origins'][q['origin_id']]['stop_ids']);targets=set(h['walking_links'])
    out=[];back=[]
    for trip in rows.values():
        trip.sort(key=lambda r:int(r['stop_sequence']))
        for i,a in enumerate(trip):
            if a.get('pickup_type','') not in ('','0'):continue
            for b in trip[i+1:]:
                if b.get('drop_off_type','') not in ('','0'):continue
                if a['stop_id'] in origins and b['stop_id'] in targets:out.append((a,b))
                if a['stop_id'] in targets and b['stop_id'] in origins:back.append((a,b))
    ap=clock(q['appointment_time']);duration=q['duration_minutes']*60
    margin=q.get('arrival_margin_minutes',10)*60;boarding=q.get('boarding_margin_minutes',3)*60
    deadline=clock(q['return_deadline']) if q.get('return_deadline') else 86399
    # Independent selection: latest feasible outward departure + earliest feasible return arrival.
    valid_out=[(a,b) for a,b in out if clock(a['departure_time'])>=boarding and
        clock(b['arrival_time'])+h['walking_links'][b['stop_id']]['outbound']['seconds']<=ap-margin]
    valid_back=[(a,b) for a,b in back if clock(b['arrival_time'])<=deadline and
        clock(a['departure_time'])>=ap+duration+h['walking_links'][a['stop_id']]['return']['seconds']+boarding]
    if not valid_out or not valid_back:return {'status':'no_feasible_journey','total_s':None,'rows':[]}
    latest=max(clock(a['departure_time']) for a,b in valid_out)
    earliest=min(clock(b['arrival_time']) for a,b in valid_back)
    pairs=[]
    for a,b in valid_out:
        if clock(a['departure_time'])!=latest:continue
        for c,d in valid_back:
            if clock(d['arrival_time'])!=earliest:continue
            metres=h['walking_links'][b['stop_id']]['outbound']['total_metres']+h['walking_links'][c['stop_id']]['return']['total_metres']
            pairs.append(((metres,a['trip_id'],c['trip_id'],b['stop_id'],c['stop_id']),[a,b,c,d]))
    _,selected=min(pairs,key=lambda x:x[0])
    a,b,c,d=selected
    return {'status':'ok','total_s':earliest-latest+boarding,'rows':selected,
        'outbound_trip_id':a['trip_id'],'return_trip_id':c['trip_id'],
        'return_slack_s':clock(c['departure_time'])-ap-duration-h['walking_links'][c['stop_id']]['return']['seconds']-boarding}


def run(output=DOC):
    h,_=p._load();raw=read_raw();cases=[]
    for origin in sorted(h['origins']):
        for minute in range(510,721,15):
            for duration in (20,30,40):
                q=dict(origin_id=origin,destination_id=h['destination_id'],date=h['validated_date'],
                       appointment_time=f'{minute//60:02d}:{minute%60:02d}',duration_minutes=duration)
                r=p.plan_visit(q);expected=oracle(raw,q,h)
                assert r['status']==expected['status']
                if r['status']=='ok':
                    it=r['itinerary']; assert it['total_s']==expected['total_s']
                    assert it['outbound']['trip_id']==expected['outbound_trip_id'] and it['return']['trip_id']==expected['return_trip_id']
                    assert it['return_slack_s']==expected['return_slack_s']
                    for leg,rows in [(it['outbound'],expected['rows'][:2]),(it['return'],expected['rows'][2:])]:
                        assert leg['from_stop_id']==rows[0]['stop_id'] and leg['to_stop_id']==rows[1]['stop_id']
                        assert leg['departure_time']==rows[0]['departure_time'] and leg['arrival_time']==rows[1]['arrival_time']
                cases.append({'request':q,'result':r,'oracle':expected,'pass':True})
    transitions=[]
    for i,a in enumerate(cases):
        for j,b in enumerate(cases[i+1:],i+1):
            qa,qb=a['request'],b['request']
            if qa['origin_id']!=qb['origin_id']:continue
            changed=[k for k in qa if qa[k]!=qb[k]]
            if len(changed)!=1:continue
            ra,rb=a['result'],b['result']
            if ra['status']!=rb['status']: transitions.append({'left':i,'right':j,'kind':'feasibility_change'});continue
            if ra['status']!='ok':continue
            ia,ib=ra['itinerary'],rb['itinerary'];delta=ib['total_s']-ia['total_s']
            transitions.append({'left':i,'right':j,'changed':changed[0],'delta_s':delta,
                'outbound_changed':ia['outbound']['trip_id']!=ib['outbound']['trip_id'],
                'return_changed':ia['return']['trip_id']!=ib['return']['trip_id']})
    deltas=[x for x in transitions if 'delta_s' in x]
    summary={'cases':len(cases),'pass':len(cases),'fail':0,'status_counts':{s:sum(c['result']['status']==s for c in cases) for s in ('ok','no_feasible_journey','unknown')},
        'minimum_absolute_delta':min(deltas,key=lambda x:abs(x['delta_s'])),
        'maximum_absolute_delta':max(deltas,key=lambda x:abs(x['delta_s'])),
        'return_changes':sum(x.get('return_changed',False) for x in transitions),
        'outbound_changes':sum(x.get('outbound_changed',False) for x in transitions)}
    dump(output/'HEALTH_MATRIX_R5.json',{'summary':summary,'cases':cases,'transitions':transitions})
    fixtures=[cases[0],next(c for c in cases if c['request']['origin_id']=='zegama_center_stops' and c['request']['appointment_time']=='09:45' and c['request']['duration_minutes']==20)]
    dump(output/'REAL_CASES_R5.json',fixtures)
    q=fixtures[-1]['request'];times=[]
    for _ in range(30):
        start=time.perf_counter();r=p.plan_visit(q);times.append((time.perf_counter()-start)*1000)
    fresh=[]
    for _ in range(3):
        code='from prototypes.ir_y_volver.provider_r5 import plan_visit;import time,json;s=time.perf_counter();r=plan_visit('+repr(q)+');assert r["status"]=="ok";print((time.perf_counter()-s)*1000)'
        fresh.append(float(subprocess.check_output([sys.executable,'-c',code],cwd=ROOT,text=True)))
    tracemalloc.start();p.plan_visit(q);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    dump(output/'PERFORMANCE_R5.json',{'warm_calls':30,'p50_ms':statistics.median(times),'p95_ms':sorted(times)[math.ceil(.95*len(times))-1],
        'first_call_fresh_interpreter_ms':fresh,'python_allocations_peak_bytes':peak,'not_rss':True,'not_portal_latency':True,
        'payload_bytes':len(json.dumps(r,ensure_ascii=False,allow_nan=False).encode()),
        'snapshot_bytes':(p.HERE/f'snapshots/{p.ID}.json').stat().st_size,'walking_links':sum(len(v) for v in h['walking_links'].values())})
    print(json.dumps(summary));return summary


if __name__=='__main__': run()
