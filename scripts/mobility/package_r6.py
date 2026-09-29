"""Deterministic clean R6 package layered over the frozen R5 manifest."""
import argparse
import json
import zipfile
from pathlib import Path

from scripts.mobility.build_health_r5 import ROOT, BASE, DOC, dump, sha


def build(output=None, write_manifest=True):
    old=json.loads((DOC/'RUNTIME_MANIFEST_R5.json').read_bytes())
    paths=[ROOT/f['path'] for f in old['files']]
    for entry in old['files']:
        p=ROOT/entry['path']
        if p.stat().st_size!=entry['bytes'] or sha(p)!=entry['sha256']: raise ValueError('R5 file changed: '+str(p))
    paths += [BASE/'provider_r6.py', ROOT/'datos_preparados/movilidad/operational_catalog_r6.json']
    paths += sorted((BASE/'contracts/v0.3.1').glob('*.schema.json'))
    paths=sorted(set(paths))
    runtime={p for p in paths}
    manifest={'contract_versions':['0.2.0','0.3.0','0.3.1'],
      'entrypoint':'prototypes.ir_y_volver.provider_r6','runtime_network_required':False,
      'files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),
                'role':'runtime' if p in runtime else 'audit'} for p in paths]}
    manifest['total_bytes']=sum(x['bytes'] for x in manifest['files'])
    if output:
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for p in paths:
                info=zipfile.ZipInfo(p.relative_to(ROOT).as_posix(),(2026,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED;info.create_system=3;info.external_attr=0o644<<16
                z.writestr(info,p.read_bytes())
        manifest['package_sha256']=sha(Path(output));manifest['package_bytes']=Path(output).stat().st_size
    if write_manifest: dump(DOC/'RUNTIME_MANIFEST_R6.json',manifest)
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path)
    result=build(parser.parse_args().output);print(json.dumps({k:v for k,v in result.items() if k!='files'}))
