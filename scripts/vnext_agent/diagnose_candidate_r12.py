"""Reproduce candidate roots and legacy projection without altering the ZIP.

Full stacks and local paths are private diagnostics in a temporary directory.
Only a summarized, path-free finding should be published for coordination.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
W1_SUPPORT = "c9cb37f6c65e77149e18cd883eeaff40d1c1bb8e"
SUPPORT_FILES = (
    "scripts/mobility/intake_candidate_r11.py",
    "scripts/mobility/verify_candidate_parity_r10.py",
    "docs/vnext/w1/MODEL_VIEW_REQUIREMENTS_R11.json",
    "docs/vnext/w1/CONSUMER_CONFORMANCE_R7.json",
    "datos_preparados/metadata_sources.json",
)

WORKER = r'''
import hashlib,importlib.util,json,os,socket,sys,traceback
from pathlib import Path

settings=json.loads(sys.stdin.read())
directory=Path(settings['candidate'])
observer=Path(settings['observer'])
socket.socket=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('diagnostic network forbidden'))
sys.path.insert(0,str(directory))
sys.path.append(str(observer))
import tools
exceptions=[]
def trace(frame,event,arg):
    if event=='exception':
        kind,value,_=arg
        filename=frame.f_code.co_filename
        if ('tools.py' in filename or 'adapter' in filename) and not isinstance(value,ImportError):
            exceptions.append({'stage':frame.f_code.co_name,'file':filename,
                               'exception':kind.__name__,'message':str(value),
                               'stack':''.join(traceback.format_stack(frame))})
    return trace
def metadata():
    root=tools._workspace_root()
    files={}
    for relative in ('datos_preparados/vnext/consumer_labels_r7.json','datos_preparados/vnext/operational_catalog_r6.json','contracts/vnext/evidence-v1.1.schema.json'):
        path=root/relative
        files[relative]={'path':str(path),'exists':path.is_file(),
                         'sha256':hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None}
    return {'cwd':str(Path.cwd()),'root_effective':str(root),'tools_file':tools.__file__,
            'adapter_files':{name:getattr(sys.modules.get(name),'__file__',None) for name in ('mobility_adapter','health_adapter')},'assets':files}
fixture=json.loads((directory/'datos_preparados/vnext/w1_conformance_r7.json').read_text(encoding='utf-8'))
requirements=json.loads((observer/'docs/vnext/w1/MODEL_VIEW_REQUIREMENTS_R11.json').read_text(encoding='utf-8'))['requirements']
records=[]
for case in fixture['cases']:
    request=case.get('request',case.get('requests'))
    start=len(exceptions)
    sys.settrace(trace)
    envelope=tools.execute('plan_visit',{'request':request},case['case_id'],root=directory)
    sys.settrace(None)
    raw=json.loads(envelope['raw_result_json']) if envelope['raw_result_json'] else None
    record={'case_id':case['case_id'],'input':request,'evidence':envelope,'metadata':metadata(),
            'execution_exceptions':exceptions[start:]}
    try:
        record['model_view']=json.loads(tools.public_result(envelope))
    except Exception as exc:
        record['projection_exception']={'class':type(exc).__name__,'message':str(exc),'stack':traceback.format_exc()}
    if case['case_id']=='legacy_r4_explicit':
        from prototypes.ir_y_volver import provider_r6
        from scripts.mobility import intake_candidate_r11 as intake
        expected=provider_r6.plan_visit(request)
        try:
            record['evaluator_findings']=intake.validate_model_view(record.get('model_view',{}),raw or expected,requirements)
        except Exception as exc:
            record['evaluator_exception']={'class':type(exc).__name__,'message':str(exc),'stack':traceback.format_exc()}
    records.append(record)
print(json.dumps({'control':settings['control'],'records':records},ensure_ascii=False,sort_keys=True))
'''


def diagnose(package: Path, manifest: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    saved_package = output / "input_candidate.zip"
    saved_manifest = output / "input_manifest.json"
    shutil.copy2(package, saved_package)
    shutil.copy2(manifest, saved_manifest)
    directory = output / "candidate"
    observer = output / "observer"
    directory.mkdir()
    observer.mkdir()
    with zipfile.ZipFile(saved_package) as archive:
        archive.extractall(directory)
    with zipfile.ZipFile(directory / "datos_preparados/vnext/w1_r6_runtime.zip") as archive:
        archive.extractall(observer)
    for relative in SUPPORT_FILES:
        destination = observer / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(subprocess.check_output(["git", "show", f"{W1_SUPPORT}:{relative}"], cwd=ROOT))
    environment = {**os.environ, "PYTHONPATH": "", "PYTHONNOUSERSITE": "1", "PYTHONUTF8": "1"}
    for key in ("GIPUZKOA360_VNEXT_ROOT", "GIPUZKOA360_DATA_DIR"):
        environment.pop(key, None)
    reports = {}
    for control, cwd in (("A_clean_extraction", directory), ("B_foreign_data_cwd", observer)):
        completed = subprocess.run([sys.executable, "-c", WORKER], cwd=cwd, env=environment,
                                   input=json.dumps({"candidate": str(directory), "observer": str(observer), "control": control}),
                                   text=True, encoding="utf-8", capture_output=True, check=True)
        report = json.loads(completed.stdout)
        (output / f"{control}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        reports[control] = [{"case_id": row["case_id"], "status": row["evidence"]["status"],
                            "error": row["evidence"]["error"],
                            "legacy_evaluator_exception": row.get("evaluator_exception", {}).get("message"),
                            "execution_exception_types": sorted({item["exception"] for item in row["execution_exceptions"]})}
                           for row in report["records"]]
    summary = {"package_sha256": hashlib.sha256(saved_package.read_bytes()).hexdigest(),
               "w1_support_pin": W1_SUPPORT, "controls": reports, "private_diagnostics": str(output)}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    output = args.output_dir or Path(tempfile.mkdtemp(prefix="g360-w2-r12-diagnostics-")) / "baseline"
    summary = diagnose(args.package.resolve(), args.manifest.resolve(), output.resolve())
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
