"""Record deterministic candidate tool observations; no model is invoked or scored."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from scripts.vnext_agent.build_r15 import MANIFEST, ROOT, ZIP, build as build_package


CASES = [
    ("territory", "obtener_resumen_territorial", {"municipio": "Aduna"}),
    ("followup_75", "analizar_coincidencia", {"categoria_servicio": "primary_care", "grupo_edad": "75", "umbral_km": 3.0, "cuantil": 0.80}),
    ("unsupported_age", "analizar_envejecimiento", {"grupo_edad": "70"}),
    ("unknown_source", "consultar_fuente", {"source_id": "TEST_FALSE_SOURCE"}),
    ("visit", "plan_visit", {"request": {"origin_id": "zegama_center_stops", "destination_id": "beasain_official_centre_anchor", "date": "2026-09-29", "appointment_time": "09:45", "duration_minutes": 20}}),
    ("comparison", "plan_visit", {"request": [
        {"origin_id": "zegama_center_stops", "destination_id": "beasain_official_centre_anchor", "date": "2026-09-29", "appointment_time": "09:30", "duration_minutes": 30},
        {"origin_id": "zegama_center_stops", "destination_id": "beasain_official_centre_anchor", "date": "2026-09-29", "appointment_time": "10:30", "duration_minutes": 30},
    ]}),
    ("no_viable", "plan_visit", {"request": {"origin_id": "zegama_center_stops", "destination_id": "beasain_official_centre_anchor", "date": "2026-09-29", "appointment_time": "00:30", "duration_minutes": 30}}),
    ("unknown_date", "plan_visit", {"request": {"origin_id": "zegama_center_stops", "destination_id": "beasain_official_centre_anchor", "date": "2026-09-30", "appointment_time": "09:30", "duration_minutes": 30}}),
]

CHILD = """import json,sys,socket
socket.socket=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('offline network forbidden'))
import tools
payload=json.loads(sys.stdin.read())
result=tools.execute(payload['name'],payload['arguments'],payload['request_id'])
print(tools.canonical({'evidence':result,'model_view':tools.strict_loads(tools.public_result(result))}))
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def record(output_dir: Path) -> dict:
    build_package()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory(prefix="g360-w2-offline-") as directory:
        checkout = Path(directory)
        with zipfile.ZipFile(ZIP) as archive:
            archive.extractall(checkout)
        assert not (checkout / ".git").exists()
        environment = {**os.environ, "PYTHONPATH": "", "PYTHONNOUSERSITE": "1", "GIPUZKOA360_VNEXT_ROOT": str(checkout)}
        for index, (name, tool_name, arguments) in enumerate(CASES, start=1):
            request_id = f"OFFLINE_W2_R10_{index:02d}"
            started = stamp()
            completed = subprocess.run(
                [sys.executable, "-c", CHILD], input=json.dumps({"name": tool_name, "arguments": arguments, "request_id": request_id}, ensure_ascii=False),
                cwd=checkout, env=environment, text=True, capture_output=True, check=True,
            )
            ended = stamp()
            payload = json.loads(completed.stdout)
            evidence_bytes = (json.dumps(payload["evidence"], ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            relative = f"evidence/{name}.json"
            (output_dir / relative).write_bytes(evidence_bytes)
            rows.append({
                "schema_version": "W2_OFFLINE_TOOL_1", "trace_contract_reference": "W3_TRACE_2.1.0",
                "scoring_eligible": False, "execution_mode": "OFFLINE_TOOL", "invocation_state": "completed",
                "llm_executed": False, "model_id": None, "model_config": None,
                "attempt": 1, "record_id": request_id, "started_at": started, "ended_at": ended,
                "request": {"tool": tool_name, "arguments": arguments, "request_id": request_id},
                "tool_calls": [{"name": tool_name, "arguments": arguments, "arguments_sha256": sha(json.dumps(arguments, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")), "output_or_error": payload["model_view"], "output_sha256": sha(json.dumps(payload["model_view"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))}],
                "history_before": [], "history_after": [], "final_response": None,
                "package_sha256": manifest["sha256"], "package_manifest_sha256": sha(MANIFEST.read_bytes()),
                "evidence": {"path": relative, "sha256": sha(evidence_bytes)},
                "observed_status": payload["evidence"]["status"], "outcomes": payload["evidence"]["outcomes"],
            })
    trace_path = output_dir / "offline_tools.jsonl"
    trace_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")
    return {"records": len(rows), "trace_path": str(trace_path), "package_sha256": manifest["sha256"], "llm_executed": 0, "execution_mode": "OFFLINE_TOOL", "w3_scorer_run": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "scripts/vnext_agent/dist/offline_recording")
    args = parser.parse_args()
    print(json.dumps(record(args.output_dir), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
