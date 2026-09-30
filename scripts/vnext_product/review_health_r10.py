"""Review pinned W1 health package and contrast selected journeys with raw GTFS."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from scripts.vnext_product.package_review import review_zip

W1_SUPPORT = "6ebf41e2f1fe24f1c3678c4be13c6c44cf8cb62b"
W1_RUNTIME = "cb061a97e78d6b5c967104fef6b935132fdc450f"
PACKAGE_SHA = "c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910"
GTFS_SHA = "3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4"
BASE = {"origin_id":"zegama_center_stops","destination_id":"beasain_official_centre_anchor",
        "date":"2026-09-29","appointment_time":"09:30","duration_minutes":20}
REQUESTS = {"main":BASE, "time":{**BASE,"appointment_time":"09:45"},
            "duration":{**BASE,"duration_minutes":90},
            "origin":{**BASE,"origin_id":"segura_herriko_plaza_stops"},
            "no_feasible":{**BASE,"appointment_time":"22:00"},
            "date":{**BASE,"date":"2026-09-30"},
            "destination":{**BASE,"destination_id":"home"},
            "profile":{**BASE,"walking_profile_id":"wheelchair"}}
CHILD = '''import json,sys
from prototypes.ir_y_volver import provider_r6 as p
requests=json.load(sys.stdin)
json.dump({"outputs":{k:{"request":q,"result":p.plan_visit(q)} for k,q in requests.items()},
"comparison":p.compare_visits([requests["main"],requests["time"]]),"capabilities":p.get_capabilities()},sys.stdout,ensure_ascii=False)
'''

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def seconds(clock):
    h,m,s=map(int,clock.split(":"));return h*3600+m*60+s

def distance(a,b):
    lat1,lon1,lat2,lon2=map(math.radians,(*a,*b))
    h=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 6371000*2*math.atan2(math.sqrt(h),math.sqrt(max(0,1-h)))

def contrast(result,rows):
    q=result["normalized_request"];it=result["itinerary"]
    observed=[]
    for part in ("outbound","return"):
        leg=it[part]
        start=rows[(leg["trip_id"],leg["from_stop_id"],str(leg["from_stop_sequence"]))]
        end=rows[(leg["trip_id"],leg["to_stop_id"],str(leg["to_stop_sequence"]))]
        if start["departure_time"]!=leg["departure_time"] or end["arrival_time"]!=leg["arrival_time"]:
            raise ValueError("Provider times differ from raw GTFS rows")
        if start["pickup_type"] not in ("", "0") or end["drop_off_type"] not in ("", "0"):
            raise ValueError("Selected raw permissions are not ordinary")
        observed.extend([start,end])
    walking={}
    for part,link in result["walking"].items():
        geometry=link["geometry"]
        metres=sum(distance(a,b) for a,b in zip(geometry,geometry[1:]))
        duration=math.ceil(metres/50)*60+120
        if abs(metres-link["total_metres"])>0.001 or duration!=link["seconds"]:
            raise ValueError("Independent geometry/formula differs from walking output")
        walking[part]={"metres_reconstructed":metres,"seconds_reconstructed":duration,
                       "basis":"pinned derived geometry + published formula; not measured walk"}
    bm=q["boarding_margin_minutes"]*60
    start=seconds(it["outbound"]["departure_time"])-bm
    end=seconds(it["return"]["arrival_time"])
    total=end-start
    slack=seconds(it["return"]["departure_time"])-seconds(q["appointment_time"])-q["duration_minutes"]*60-walking["return"]["seconds_reconstructed"]-bm
    if total!=it["total_s"] or slack!=it["return_slack_s"]:
        raise ValueError("Raw chronology disagrees with total/slack")
    if sum(result["components_s"].values())!=total:
        raise ValueError("Component sum differs")
    cursor=start
    for component in result["components"]:
        if component["start_s"]!=cursor or component["end_s"]-cursor!=component["seconds"]:
            raise ValueError("Component intervals are not disjoint/contiguous")
        cursor=component["end_s"]
    return {"status":"PASS","raw_rows":observed,"walking":walking,
            "total_s_reconstructed":total,"slack_s_reconstructed":slack,
            "limitation":"Checks selected rows, geometry lengths and arithmetic; not exhaustive optimality or physical entrance."}

def run(root,package,out):
    import jsonschema
    root=root.resolve()
    manifest=json.loads((root/"docs/vnext/w1/RUNTIME_MANIFEST_R6.json").read_bytes())
    if sha(package)!=PACKAGE_SHA:raise ValueError("W1 health package differs from announced pin")
    static=review_zip(package,{x["path"]:x["sha256"] for x in manifest["files"]},[])
    with tempfile.TemporaryDirectory(prefix="g360-w3-health-") as directory:
        with zipfile.ZipFile(package) as archive:archive.extractall(directory)
        proc=subprocess.run([sys.executable,"-X","utf8","-c",CHILD],cwd=directory,input=json.dumps(REQUESTS),text=True,encoding="utf-8",capture_output=True,check=True)
        evidence=json.loads(proc.stdout)
    schemas={name:json.loads((root/f"prototypes/ir_y_volver/contracts/v0.3.1/{name}.schema.json").read_bytes()) for name in ("result","comparison","catalog")}
    for item in evidence["outputs"].values():jsonschema.validate(item["result"],schemas["result"])
    jsonschema.validate(evidence["comparison"],schemas["comparison"])
    catalog=json.loads((root/"datos_preparados/movilidad/operational_catalog_r6.json").read_bytes())
    jsonschema.validate(catalog,schemas["catalog"])
    gtfs=root/"datos_originales/movilidad/goierrialdea-3276fcae.zip"
    if sha(gtfs)!=GTFS_SHA:raise ValueError("GTFS raw pin differs")
    with zipfile.ZipFile(gtfs) as archive:
        rows={}
        for line,row in enumerate(csv.DictReader(io.StringIO(archive.read("stop_times.txt").decode("utf-8-sig"))),2):
            rows[(row["trip_id"],row["stop_id"],row["stop_sequence"])]=dict(row,csv_line=line)
    contrasted={k:contrast(item["result"],rows) for k,item in evidence["outputs"].items() if item["result"]["status"]=="ok"}
    delta=contrasted["time"]["total_s_reconstructed"]-contrasted["main"]["total_s_reconstructed"]
    evidence.update(classification="OFFLINE_PINNED_W1_HEALTH_0.3.1_NOT_AGENT",
                    provider_pin=W1_RUNTIME,support_pin=W1_SUPPORT,package_sha256=PACKAGE_SHA,
                    catalog=catalog,labels=json.loads((root/"datos_preparados/movilidad/consumer_labels_r7.json").read_bytes()),
                    result_schema=schemas["result"],comparison_schema=schemas["comparison"])
    out.mkdir(parents=True,exist_ok=True)
    payload=(json.dumps(evidence,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    (out/"health_evidence.json").write_bytes(payload)
    report={"classification":"INDEPENDENT_OFFLINE_PRODUCER_REVIEW", "w1_runtime_pin":W1_RUNTIME,
            "w1_support_pin":W1_SUPPORT,"package_sha256":PACKAGE_SHA,"static":static,
            "schema_validation":"PASS", "statuses":{k:v["result"]["status"] for k,v in evidence["outputs"].items()},
            "contrast":contrasted,"verified_delta_s":delta,"llm_executed":0,"portal_executed":0,
            "health_evidence_sha256":hashlib.sha256(payload).hexdigest(),
            "acceptance":"PASS_MODELLED_OFFICIAL_POINT_WITH_VISIBLE_LIMITS",
            "not_verified":["physical entrance","door to door","appointment availability","punctuality","exhaustive route optimality"]}
    (out/"health_review.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument("--w1-root",type=Path,required=True);p.add_argument("--package",type=Path,required=True);p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args();r=run(a.w1_root,a.package,a.output_dir);print(json.dumps({"acceptance":r["acceptance"],"delta":r["verified_delta_s"],"statuses":r["statuses"]}))

if __name__=="__main__":main()
