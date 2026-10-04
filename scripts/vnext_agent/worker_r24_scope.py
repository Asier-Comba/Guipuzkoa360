"""Cold-process health scope test observer; never a model or portal simulator."""
import copy
import json
import os
from pathlib import Path
import socket
import sys

def run(root):
    def denied(*a,**kw): raise RuntimeError('Scope test network denied')
    socket.socket=denied; socket.create_connection=denied
    root=Path(root).resolve(); os.environ['GIPUZKOA360_VNEXT_ROOT']=str(root); sys.path.insert(0,str(root))
    import tools as m
    records={}
    original=m._r23_mobility_view
    for origin in ('zegama_center_stops','segura_herriko_plaza_stops','idiazabal_center_stops'):
        for clock in ('09:30','09:45'):
            args={'request':dict(origin_id=origin,destination_id='beasain_official_centre_anchor',date='2026-09-29',appointment_time=clock,duration_minutes=20)}
            evidence=m.execute('plan_visit',args,'TEST',root=root)
            assert evidence['status']=='valid',evidence.get('error')
            raw=m.strict_loads(evidence['raw_result_json']); before=copy.deepcopy(raw)
            prior=original(raw,root,args)
            view=m.strict_loads(m.public_call('plan_visit',args,'TEST',root=root))
            assert raw==before
            projected=m._mobility_view(raw,root,args); assert raw==before
            records[origin+':'+clock]={'raw':raw,'view':view,'prior':prior,'projected':projected}
    failures={}
    args={'request':dict(origin_id='zegama_center_stops',destination_id='beasain_official_centre_anchor',date='2026-09-29',appointment_time='09:30',duration_minutes=20)}
    for mutation in ('scope','summary_end','summary_start','destination_id','entrance','origin_stop','return_stop','return_clock','departure_clock'):
        def tampered(*a,**kw):
            view=copy.deepcopy(original(*a,**kw)); s=view['scenarios'][0]
            if mutation=='scope': s['scope']='health_anchor_endpoint'
            if mutation=='summary_end': s['time_summary']['scope_end_clock']='00:00:00'
            if mutation=='summary_start': s['time_summary']['scope_start_s']+=1
            if mutation=='destination_id': s['health_destination']['centre_id']='NOT_OBSERVED'
            if mutation=='entrance': s['health_destination']['entrance_verified']=True
            if mutation=='origin_stop': s['itinerary']['origin_stop_id']='NOT_OBSERVED'
            if mutation=='return_stop': s['itinerary']['return_stop_id']='NOT_OBSERVED'
            if mutation=='return_clock': s['itinerary']['return']['arrival_time']='00:00:00'
            if mutation=='departure_clock': s['itinerary']['outbound']['departure_time']='00:00:00'
            return view
        m._r23_mobility_view=tampered
        failures[mutation]=m.strict_loads(m.public_call('plan_visit',args,'TEST',root=root))
    m._r23_mobility_view=original
    return {'records':records,'faults':failures,'network':'denied','model_calls':0}

if __name__=='__main__': print(json.dumps(run(sys.argv[1]),ensure_ascii=False,allow_nan=False))
