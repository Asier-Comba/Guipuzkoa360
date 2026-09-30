import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

from scripts.mobility.build_goierrialdea_snapshot import build

ROOT=Path(__file__).resolve().parents[2]


def test_snapshot_rebuild_is_byte_identical(tmp_path):
    metadata=json.loads((ROOT/'docs/vnext/w1/R4_SOURCE_METADATA.json').read_text(encoding='utf-8'))
    target=tmp_path/'rebuilt.json'
    build(ROOT/'datos_originales/movilidad/goierrialdea-3276fcae.zip',target,metadata)
    assert target.read_bytes()==(ROOT/'prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-r4-20260929.json').read_bytes()


def test_manifest_and_clean_offline_assembly(tmp_path):
    manifest=json.loads((ROOT/'docs/vnext/w1/RUNTIME_MANIFEST_R4.json').read_text(encoding='utf-8'))
    assert manifest['total_bytes']==sum(x['bytes'] for x in manifest['files'])
    for entry in manifest['files']:
        raw=(ROOT/entry['path']).read_bytes()
        assert len(raw)==entry['bytes']
        assert hashlib.sha256(raw).hexdigest()==entry['sha256']
        target=tmp_path/entry['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    command='''import json,socket
def forbidden(*a,**kw): raise RuntimeError("network forbidden")
socket.socket=forbidden
from prototypes.ir_y_volver import get_capabilities,plan_visit,compare_visits
q=dict(origin_id="zegama_center_stops",destination_id="beasain_center_stop_pair",date="2026-09-29",appointment_time="10:00",duration_minutes=30)
assert get_capabilities()["schema_version"]=="0.2.0"
assert plan_visit(q)["status"]=="ok"
assert compare_visits([q,{**q,"date":"2027-01-01"}])["results"][1]["status"]=="unknown"
print("ISOLATED_OFFLINE_PASS")
'''
    env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')}
    output=subprocess.check_output([sys.executable,'-c',command],cwd=tmp_path,env=env,text=True)
    assert 'ISOLATED_OFFLINE_PASS' in output
