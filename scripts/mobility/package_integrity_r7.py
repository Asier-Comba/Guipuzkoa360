"""R7 integrity/portability audit of the frozen deterministic R6 ZIP."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile

from scripts.mobility.build_health_r5 import ROOT, DOC, dump
from scripts.mobility.package_r6 import build

EXPECTED='c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910'
FORBIDDEN=('.git','__pycache__','.pyc','.tmp','.temp','holdout','secret')
SECRET_MARKERS=(b'ghp_',b'github_pat_',b'BEGIN PRIVATE KEY',b'password=',b'api_key=')


def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()


def run():
    manifest=json.loads((DOC/'RUNTIME_MANIFEST_R6.json').read_bytes())
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder);a=root/'a.zip';b=root/'b.zip'
        built_a=build(a,write_manifest=False);built_b=build(b,write_manifest=False)
        raw_a=a.read_bytes();raw_b=b.read_bytes();assert raw_a==raw_b
        assert sha_bytes(raw_a)==EXPECTED==manifest['package_sha256']
        with zipfile.ZipFile(a) as archive:
            infos=archive.infolist();names=[x.filename for x in infos]
            assert len(names)==len(set(names))==len({x.casefold() for x in names})
            declared={x['path']:x for x in manifest['files']};assert set(names)==set(declared)
            checks={'relative_paths':True,'no_parent_segments':True,'no_duplicates':True,
              'no_casefold_collisions':True,'no_symlinks':True,'no_unexpected_executables':True,
              'no_git_cache_temporaries_holdout':True,'no_secret_markers':True,'declared_bytes_hashes':True}
            total=0
            for info in infos:
                path=PurePosixPath(info.filename);assert not path.is_absolute() and '..' not in path.parts
                mode=info.external_attr>>16;assert mode&0o170000!=0o120000 and mode&0o111==0
                assert not any(marker in info.filename.casefold() for marker in FORBIDDEN)
                raw=archive.read(info);assert not any(marker in raw for marker in SECRET_MARKERS)
                entry=declared[info.filename];assert len(raw)==entry['bytes'] and sha_bytes(raw)==entry['sha256'];total+=len(raw)
            assert total==manifest['total_bytes']==built_a['total_bytes']==built_b['total_bytes']
            extracted=root/'clean';archive.extractall(extracted)
        code="""import sys,socket;sys.path.insert(0,'.');socket.socket=lambda *a,**k:(_ for _ in ()).throw(RuntimeError('network disabled'));from prototypes.ir_y_volver.provider_r6 import plan_visit;q=dict(origin_id='zegama_center_stops',destination_id='beasain_official_centre_anchor',date='2026-09-29',appointment_time='09:45',duration_minutes=20);r=plan_visit(q);assert r['status']=='ok' and r['schema_version']=='0.3.1';print('PASS')"""
        env={k:v for k,v in os.environ.items() if k.upper()!='PYTHONPATH'}
        clean=subprocess.check_output([sys.executable,'-I','-c',code],cwd=extracted,env=env,text=True).strip()
        assert clean=='PASS'
    artifact={'status':'PASS','scope':'package integrity and portability; not a complete security audit',
      'package_sha256':EXPECTED,'package_bytes':manifest['package_bytes'],'uncompressed_bytes':manifest['total_bytes'],
      'members':len(manifest['files']),'double_build_byte_identical':True,'clean_offline_import':True,
      'no_repo_parent_or_pythonpath':True,'checks':checks}
    dump(DOC/'PACKAGE_INTEGRITY_R7.json',artifact);print(json.dumps(artifact));return artifact


if __name__=='__main__':run()
