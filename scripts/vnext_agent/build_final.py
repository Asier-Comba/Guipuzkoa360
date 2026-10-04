"""Reproducible final package: R28 tools/assets with verified threshold rendering."""
import ast
import json
import zipfile
from pathlib import Path

from scripts.vnext_agent import build_r28
from scripts.vnext_agent.build_r21 import ROOT, sha

OUT = ROOT / 'scripts/vnext_agent/dist/final'
ZIP = OUT / 'gipuzkoa360-entrega-final.zip'
MANIFEST = OUT / 'gipuzkoa360-entrega-final-manifest.json'
PORTAL = ROOT / 'agentes/gipuzkoa360_vnext/portal_final'


def build():
    baseline = build_r28.build()
    assert baseline['zip_sha256'] == '3cdeeb990aa9397bad859cd66a4834f41b390bcba2b4d538f7eb775b9c967049'
    main = (PORTAL / 'main.py').read_bytes().replace(b'\r\n', b'\n')
    ast.parse(main)
    OUT.mkdir(parents=True, exist_ok=True)
    members = {}
    with zipfile.ZipFile(build_r28.ZIP) as original, zipfile.ZipFile(ZIP, 'w') as final:
        for info in original.infolist():
            content = main if info.filename == 'main.py' else original.read(info.filename)
            final.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members[info.filename] = {'bytes': len(content), 'sha256': sha(content)}
            if info.filename == 'tools.py':
                assert (PORTAL / 'tools.py').read_bytes().replace(b'\r\n', b'\n') == content
    report = json.loads(build_r28.MANIFEST.read_bytes())
    report.update(package='GIPUZKOA360_final_verified_threshold_presentation',
                  base_r28_runtime='829296f0adbc3cfee1056e0b06991fb08c48b0f3',
                  base_r28_zip_sha256=baseline['zip_sha256'], changed_members=['main.py'],
                  main_changed=True, members=members, sha256=sha(ZIP.read_bytes()),
                  bytes=ZIP.stat().st_size, uncompressed_bytes=sum(x['bytes'] for x in members.values()),
                  runtime_delta='Verified threshold partition is rendered before another model call; R28 analytical tools and all context assets unchanged.')
    assert report['bytes'] < report['limit_bytes']
    MANIFEST.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    return {'zip_sha256':report['sha256'],'manifest_sha256':sha(MANIFEST.read_bytes()),'bytes':report['bytes']}


if __name__ == '__main__':
    print(json.dumps(build(),sort_keys=True))
