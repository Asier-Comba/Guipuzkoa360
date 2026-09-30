"""Deterministic isolated multi-snapshot package; frozen R4 manifest is read-only."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from scripts.mobility.build_health_r5 import ROOT, BASE, DOC, ID, dump, sha


def build(output=None,write_manifest=True):
    old=json.loads((DOC/'RUNTIME_MANIFEST_R4.json').read_bytes())
    paths=[ROOT/f['path'] for f in old['files']]
    for entry in old['files']:
        p=ROOT/entry['path']
        if p.stat().st_size!=entry['bytes'] or sha(p)!=entry['sha256']: raise ValueError('R4 file changed: '+str(p))
    paths += [BASE/name for name in ['provider_r5.py','walking_r5.py','schema_r5.py',
        'snapshots/allowlist_r5.json',f'snapshots/{ID}.json']]
    paths += sorted((BASE/'contracts/v0.3.0').glob('*.schema.json'))
    paths=sorted(paths)
    manifest={'contract_versions':['0.2.0','0.3.0'],'entrypoint':'prototypes.ir_y_volver.provider_r5',
        'runtime_network_required':False,'files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths],
        'total_bytes':sum(p.stat().st_size for p in paths)}
    if output:
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for p in paths:
                info=zipfile.ZipInfo(p.relative_to(ROOT).as_posix(),(2026,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED; info.create_system=3;info.external_attr=0o644<<16
                z.writestr(info,p.read_bytes())
        manifest['package_sha256']=sha(Path(output));manifest['package_bytes']=Path(output).stat().st_size
    if write_manifest: dump(DOC/'RUNTIME_MANIFEST_R5.json',manifest)
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path)
    r=build(p.parse_args().output);print(json.dumps({k:v for k,v in r.items() if k!='files'}))
