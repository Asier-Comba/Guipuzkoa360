"""Opt-in real-model development runner for an already authorized model factory.

This records observations; it does not claim W3 scoring or portal execution.
No credentials are read or created by this module.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from scripts.vnext_agent.build_package import ZIP


ROOT = Path(__file__).resolve().parents[2]
CASES = Path(__file__).with_name("agent_smoke_r10.json")

WORKER = """import importlib,json,sys,time,traceback
from datetime import datetime,timezone
from pathlib import Path

def stamp():
    return datetime.now(timezone.utc).isoformat()

def message(value):
    if isinstance(value,dict):
        return value
    return {'type':getattr(value,'type',None),'content':getattr(value,'content',None),
            'tool_calls':getattr(value,'tool_calls',None),'id':getattr(value,'id',None),
            'name':getattr(value,'name',None)}

settings=json.loads(sys.stdin.read())
module_name,attribute=settings['model_factory'].split(':',1)
factory=getattr(importlib.import_module(module_name),attribute)
model=factory()
import main
agent=main.build_agent(model)
histories={}
for index,case in enumerate(settings['cases'],1):
    session=case['session_id']
    before=histories.get(session,[])
    start=stamp()
    clock=time.perf_counter()
    input_messages=before+[{'role':'user','content':case['user']}]
    state='started'
    error=None
    result=None
    try:
        result=agent.invoke({'messages':input_messages})
        after=[message(item) for item in result['messages']]
        histories[session]=after
        state='completed'
    except Exception as exc:
        after=None
        error={'class':type(exc).__name__,'message':str(exc)}
        state='failed'
    print(json.dumps({'schema_version':'W2_LOCAL_LLM_OBSERVATION_1',
          'execution_mode':'LOCAL_LLM','scoring_eligible':False,
          'case_id':case['case_id'],'session_id':session,'turn_index':index,
          'invocation_state':state,'llm_executed':True,
          'started_at':start,'ended_at':stamp(),'elapsed_ms':round((time.perf_counter()-clock)*1000),
          'model_class':type(model).__module__+'.'+type(model).__qualname__,
          'model_id_observed':getattr(model,'model',None) or getattr(model,'model_name',None),
          'model_config_observed':None,
          'history_before':before,'input_messages':input_messages,'history_after':after,
          'tool_calls_and_outputs':[item for item in (after or []) if item.get('tool_calls') or item.get('type')=='tool'],
          'final_response':after[-1] if state=='completed' and after else None,
          'error':error,'package_sha256':settings['package_sha256']},ensure_ascii=False,sort_keys=True),flush=True)
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the extracted W2 package with an already authorized injected model")
    parser.add_argument("--model-factory", required=True, help="Importable module:function returning the authorized LangChain chat model")
    parser.add_argument("--factory-path", type=Path, help="Explicit directory containing that already-authorized factory module")
    parser.add_argument("--cases", type=Path, default=CASES)
    parser.add_argument("--package", type=Path, default=ZIP)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if ":" not in args.model_factory:
        parser.error("--model-factory must be module:function")
    if args.factory_path is not None and not args.factory_path.is_dir():
        parser.error("--factory-path must name an existing directory")
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if type(cases) is not list or not cases or any(type(item) is not dict or set(item) != {"case_id", "session_id", "user"} for item in cases):
        parser.error("case file must be a nonempty array of {case_id, session_id, user}")
    package = args.package.resolve(strict=True)
    package_hash = hashlib.sha256(package.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="g360-r10-agent-") as temporary:
        checkout = Path(temporary)
        with zipfile.ZipFile(package) as archive:
            archive.extractall(checkout)
        factory_search = [str(checkout)] + ([str(args.factory_path.resolve())] if args.factory_path else [])
        environment = {**os.environ, "PYTHONPATH": os.pathsep.join(factory_search), "GIPUZKOA360_VNEXT_ROOT": str(checkout)}
        child = subprocess.run([sys.executable, "-c", WORKER], input=json.dumps({"model_factory": args.model_factory, "cases": cases, "package_sha256": package_hash}), cwd=checkout, env=environment, text=True, capture_output=True)
    if child.returncode:
        raise SystemExit(f"Runner could not start or complete: {child.stderr.strip()}")
    rows = [json.loads(line) for line in child.stdout.splitlines()]
    if len(rows) != len(cases):
        raise SystemExit("Incomplete observation: not every case produced a record")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")
    print(json.dumps({"records": len(rows), "completed": sum(row["invocation_state"] == "completed" for row in rows), "failed": sum(row["invocation_state"] == "failed" for row in rows), "package_sha256": package_hash, "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
