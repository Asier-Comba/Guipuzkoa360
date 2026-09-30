"""Reproducible local consumer cost profile; not an SLA or portal benchmark."""
import json
import math
import platform
import statistics
import sys
import time
import tracemalloc

from prototypes.ir_y_volver import provider_r6 as p
from scripts.mobility.build_health_r5 import DOC, dump

SAMPLES=7


def percentile(values,fraction):return sorted(values)[math.ceil(len(values)*fraction)-1]


def call(size,base):
    return p.plan_visit(base) if size==1 else p.compare_visits([{**base,'duration_minutes':20+i%2} for i in range(size)])


def run():
    base=dict(origin_id='zegama_center_stops',destination_id=p.ID,date='2026-09-29',appointment_time='09:45',duration_minutes=20)
    base['destination_id']='beasain_official_centre_anchor'
    measurements={}
    for size in (1,2,4,8,16,32):
        timings=[];result=None
        for _ in range(SAMPLES):
            start=time.perf_counter();result=call(size,base);timings.append((time.perf_counter()-start)*1000)
        tracemalloc.start();call(size,base);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        measurements[str(size)]={'operation':'plan_visit' if size==1 else 'compare_visits','samples':SAMPLES,
          'median_ms':statistics.median(timings),'p95_ms':percentile(timings,.95),'minimum_ms':min(timings),
          'maximum_ms':max(timings),'payload_bytes':len(json.dumps(result,ensure_ascii=False,allow_nan=False).encode()),
          'python_peak_allocation_bytes':peak,'not_rss':True}
    repeated=[]
    for _ in range(50):
        start=time.perf_counter();p.plan_visit(base);repeated.append((time.perf_counter()-start)*1000)
    artifact={'status':'PASS','not_sla':True,'not_portal':True,'not_network_throughput':True,
      'environment':{'python':sys.version.split()[0],'platform':platform.platform(),'implementation':platform.python_implementation()},
      'measurements':measurements,'single_repeated_50':{'median_ms':statistics.median(repeated),'p95_ms':percentile(repeated,.95)}}
    dump(DOC/'PERFORMANCE_R7.json',artifact);print(json.dumps(artifact));return artifact


if __name__=='__main__':run()
