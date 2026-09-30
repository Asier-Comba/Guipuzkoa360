"""Build runtime allowlist/manifest and reproducible ZIP; no historical overwrites."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def build(output=None):
    base = ROOT / 'prototypes/ir_y_volver'
    snapshot = base / 'snapshots/official-goierrialdea-go01-r4-20260929.json'
    s = json.loads(snapshot.read_text(encoding='utf-8'))
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    dump(base / 'snapshots/allowlist.json', {'schema_version':'0.2.0','snapshots':{s['snapshot_id']:{
        'file':snapshot.name,'sha256':digest(snapshot),'schema_version':'0.2.0',
        'validation_status':'VALIDATED_STOP_ONLY',
        **{key:s[key] for key in ('coverage','sources','walking_profiles')}}}})
    files = [ROOT / 'prototypes/__init__.py', base/'__init__.py',base/'provider.py',base/'snapshot_validation.py',
             base/'snapshots/allowlist.json',snapshot, *sorted((base/'contracts/v0.2.0').glob('*.schema.json'))]
    manifest = {'contract_version':'0.2.0','runtime_network_required':False,
        'files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)} for p in files],
        'total_bytes':sum(p.stat().st_size for p in files)}
    dump(ROOT/'docs/vnext/w1/RUNTIME_MANIFEST_R4.json',manifest)
    if output:
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for p in files:
                info = zipfile.ZipInfo(p.relative_to(ROOT).as_posix(),(2026,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=0o644 << 16
                z.writestr(info,p.read_bytes())
        return {'sha256':digest(Path(output)),'bytes':Path(output).stat().st_size, 'runtime_bytes':manifest['total_bytes']}
    return manifest


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path)
    print(json.dumps(build(parser.parse_args().output)))
