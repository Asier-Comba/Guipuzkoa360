"""Pinned R18 bytes; only the public interface and projection may change."""
import ast
import io
import json
import subprocess
import sys
import zipfile
from scripts.vnext_agent.build_r16 import ROOT, sha

BASE='574d3d2dca5f84433f39c425b7ecce1c4cd01944'
BASE_ZIP='scripts/vnext_agent/dist/r18/gipuzkoa360-r18-final-agent.zip'
BASE_MANIFEST='scripts/vnext_agent/dist/r18/gipuzkoa360-r18-final-agent-manifest.json'
BASE_HASH='57fe8ccab8ab3613c0729aa9a4b25702dbaead5d74bfb6216e8bbe117c421256'
BASE_MANIFEST_HASH='d2eee50d906be5056c227102c8c2005b9cb93c3916d8fbf6a3df35571ec4af74'
OUT=ROOT/'scripts/vnext_agent/dist/r19'
ZIP=OUT/'gipuzkoa360-r19-final-agent.zip'
MANIFEST=OUT/'gipuzkoa360-r19-final-agent-manifest.json'
PORTAL=ROOT/'agentes/gipuzkoa360_vnext/portal_r19'
DELTA=ROOT/'scripts/vnext_agent/r19_interface.py'
PROMPT=ROOT/'scripts/vnext_agent/r19_prompt.txt'
BINDINGS=ROOT/'scripts/vnext_agent/r19_bindings.py'

def blob(path):return subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT)

def generated_main(data):
    text=data.decode('utf-8'); lines=text.splitlines(keepends=True)
    replacements={}
    binding_text=BINDINGS.read_text(encoding='utf-8').replace('\r\n','\n')
    for node in ast.parse(binding_text).body:
        if isinstance(node,ast.FunctionDef):
            start=min([node.lineno]+[d.lineno for d in node.decorator_list])
            replacements[node.name]=''.join(binding_text.splitlines(keepends=True)[start-1:node.end_lineno])+'\n'
    changes=[]
    for node in ast.parse(text).body:
        if isinstance(node,ast.FunctionDef) and node.name in replacements:
            start=min([node.lineno]+[d.lineno for d in node.decorator_list])
            changes.append((start-1,node.end_lineno,replacements.pop(node.name)))
        if isinstance(node,ast.Assign) and getattr(node.targets[0],'id',None)=='SYSTEM_PROMPT':
            changes.append((node.lineno-1,node.end_lineno,'SYSTEM_PROMPT = '+repr(PROMPT.read_text(encoding='utf-8').replace('\r\n','\n').strip())+'\n'))
    assert not replacements
    for start,end,replacement in sorted(changes,reverse=True):lines[start:end]=[replacement]
    text=''.join(lines).replace('from typing import Any, Callable','from typing import Any, Callable, Literal')
    ast.parse(text)
    return text.encode('utf-8')

def generated_tools(data):
    text=data.decode('utf-8'); assert text.count('def _public_result(')==1
    text=text.replace('def _public_result(', 'def _r18_public_result(')
    text+='\n\n'+DELTA.read_text(encoding='utf-8').replace('\r\n','\n')
    ast.parse(text)
    return text.encode('utf-8')

def build():
    if sys.version_info[:2]!=(3,12):raise RuntimeError('Canonical bundle requires CPython 3.12')
    baseline,meta=blob(BASE_ZIP),blob(BASE_MANIFEST)
    assert sha(baseline)==BASE_HASH and sha(meta)==BASE_MANIFEST_HASH
    prior=json.loads(meta); OUT.mkdir(parents=True,exist_ok=True);PORTAL.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(baseline)) as old,zipfile.ZipFile(ZIP,'w') as new:
        overrides={'main.py':generated_main(old.read('main.py')),'tools.py':generated_tools(old.read('tools.py'))}
        members={};changed=[]
        for info in old.infolist():
            original=old.read(info.filename);data=overrides.get(info.filename,original)
            new.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
            members[info.filename]={'bytes':len(data),'sha256':sha(data)}
            if data!=original:changed.append(info.filename)
    assert changed==['main.py','tools.py'] and len(members)==25
    for name,data in overrides.items():(PORTAL/name).write_bytes(data)
    report={'package':'GIPUZKOA360_R19_final_agent','base_r18_head':BASE,'base_r18_zip_sha256':BASE_HASH,'base_r18_manifest_sha256':BASE_MANIFEST_HASH,'sha256':sha(ZIP.read_bytes()),'bytes':ZIP.stat().st_size,'members':members,'members_count':len(members),'changed_members':changed,'context_paths':prior['context_paths'],'context_assets_changed':[],'uncompressed_bytes':sum(x['bytes'] for x in members.values()),'limit_bytes':prior['limit_bytes'],'public_tools':9,'w1_runtime_changed':False,'v4_changed':False,'source_delta_sha256':sha(DELTA.read_bytes().replace(b'\r\n',b'\n')),'bindings_sha256':sha(BINDINGS.read_bytes().replace(b'\r\n',b'\n')),'system_prompt_sha256':sha(PROMPT.read_bytes().replace(b'\r\n',b'\n')),'runtime_delta':'Public bindings and evidence projection only; raw engine and all 23 other members unchanged','portal_real_agent':'NOT_RUN'}
    assert report['bytes']<report['limit_bytes']
    MANIFEST.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    return {'zip_sha256':report['sha256'],'manifest_sha256':sha(MANIFEST.read_bytes()),'bytes':report['bytes']}

if __name__=='__main__':print(json.dumps(build(),sort_keys=True))
