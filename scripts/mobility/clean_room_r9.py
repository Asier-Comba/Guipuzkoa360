"""Reproduce the frozen W1 candidate in a temporary, offline staged tree."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/vnext/w1"
R4_ID = "official-goierrialdea-go01-r4-20260929"
R5_ID = "official-goierrialdea-go01-health-r5-20260929"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_sha(path: Path) -> str:
    raw = path.read_bytes()
    if path.suffix.lower() == ".osm":
        raw = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(raw).hexdigest()


def copy_file(source: Path, root: Path) -> dict:
    relative = source.relative_to(ROOT)
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    normalized = source.suffix.lower() == ".osm"
    size = len(source.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")) if normalized else source.stat().st_size
    return {"path": relative.as_posix(), "sha256": evidence_sha(source), "bytes": size,
            "hash_basis": "canonical_lf" if normalized else "exact_bytes"}


def run(command: list[str], cwd: Path) -> dict:
    env = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
           "WINDIR": os.environ.get("WINDIR", ""), "PYTHONIOENCODING": "utf-8", "PYTHONHASHSEED": "0"}
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, encoding="utf-8",
                               capture_output=True, check=False, timeout=60)
    if completed.returncode:
        raise RuntimeError(f"command failed: {command!r}\n{completed.stderr}")
    recorded = ["python", *command[1:]] if command and Path(command[0]).resolve() == Path(sys.executable).resolve() else command
    return {"argv": recorded, "returncode": completed.returncode, "stdout": completed.stdout.strip(),
            "network": "DISABLED_BY_PROCEDURE_NO_NETWORK_CALLS"}


def drill(output: Path) -> dict:
    canonical_r4 = ROOT / f"prototypes/ir_y_volver/snapshots/{R4_ID}.json"
    canonical_r5 = ROOT / f"prototypes/ir_y_volver/snapshots/{R5_ID}.json"
    canonical_r8 = json.loads((DOC / "DELIVERY_EVIDENCE_R8.json").read_text(encoding="utf-8"))
    staged = []
    commands = []
    with tempfile.TemporaryDirectory(prefix="g360-r9-clean-") as temporary:
        room = Path(temporary)
        shutil.copytree(ROOT / "prototypes", room / "prototypes")
        for source in (
            ROOT / "scripts/mobility/build_goierrialdea_snapshot.py",
            ROOT / "scripts/mobility/build_health_r5.py",
            ROOT / "datos_originales/movilidad/goierrialdea-3276fcae.zip",
            ROOT / "datos_originales/movilidad/beasain-network-r4-public.osm",
            ROOT / "datos_originales/centros-salud.xlsx",
            ROOT / "datos_originales/movilidad/r5/beasain-official.html",
            ROOT / "datos_originales/movilidad/r5/padi-2026.pdf",
            DOC / "HEALTH_DESTINATION_R4.json",
        ):
            staged.append(copy_file(source, room))
        (room / "scripts/mobility").mkdir(parents=True, exist_ok=True)
        metadata = {"snapshot_id": R4_ID, "retrieved_date": "2026-09-29",
                    "url": "https://opendata.euskadi.eus/transport/moveuskadi/lurraldebus/goierrialdea/gtfs_goierrialdea.zip",
                    "validated_dates": ["2026-09-29"], "source_sha256": "3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4",
                    "index_last_update": "2026-09-29 07:01:13"}
        metadata_path = room / "work/metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        generated_r4 = room / f"prototypes/ir_y_volver/snapshots/{R4_ID}.json"
        generated_r4.unlink()
        commands.append(run([sys.executable, "-I", "scripts/mobility/build_goierrialdea_snapshot.py",
                             "datos_originales/movilidad/goierrialdea-3276fcae.zip", generated_r4.relative_to(room).as_posix(),
                             "--metadata", metadata_path.relative_to(room).as_posix()], room))
        generated_health = room / "work/generated-health.json"
        code = ("import sys;from pathlib import Path;sys.path.insert(0,'.');"
                "from scripts.mobility.build_health_r5 import build;build(Path('work/generated-health.json'))")
        commands.append(run([sys.executable, "-I", "-c", code], room))
        shutil.copyfile(generated_health, room / f"prototypes/ir_y_volver/snapshots/{R5_ID}.json")
        allowlist = {"schema_version": "0.3.0", "snapshot_id": R5_ID, "file": f"{R5_ID}.json", "sha256": sha(generated_health)}
        (room / "prototypes/ir_y_volver/snapshots/allowlist_r5.json").write_text(
            json.dumps(allowlist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        requests = {case: canonical_r8["cases"][case]["request"] for case in ("MAIN", "VARIATION_TIME", "VARIATION_DURATION", "LIMIT_DATE", "LIMIT_SCOPE")}
        request_path = room / "work/requests.json"
        request_path.write_text(json.dumps(requests, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        runner = ("import json,sys;sys.path.insert(0,'.');from prototypes.ir_y_volver.provider_r6 import plan_visit;"
                  "q=json.load(open('work/requests.json',encoding='utf-8'));"
                  "out={k:plan_visit(v) for k,v in q.items()};"
                  "open('work/results.json','w',encoding='utf-8',newline='\\n').write(json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\\n')")
        commands.append(run([sys.executable, "-I", "-c", runner], room))
        results_path = room / "work/results.json"
        results = json.loads(results_path.read_text(encoding="utf-8"))
        observed = {case: {"status": result["status"], "total_s": result["itinerary"]["total_s"] if result["itinerary"] else None}
                    for case, result in results.items()}
        expected = {case: {"status": canonical_r8["cases"][case]["provider_result"]["status"],
                           "total_s": canonical_r8["cases"][case]["provider_result"]["itinerary"]["total_s"] if canonical_r8["cases"][case]["provider_result"]["itinerary"] else None}
                    for case in requests}
        delta = observed["VARIATION_TIME"]["total_s"] - observed["MAIN"]["total_s"]
        comparisons = {
            "r4_snapshot": {"generated_sha256": sha(generated_r4), "canonical_sha256": sha(canonical_r4), "identical": sha(generated_r4) == sha(canonical_r4)},
            "health_snapshot": {"generated_sha256": sha(generated_health), "canonical_sha256": sha(canonical_r5), "identical": sha(generated_health) == sha(canonical_r5)},
            "canonical_claims": {"observed": observed, "expected": expected, "identical": observed == expected,
                                 "delta_s": delta, "expected_delta_s": -2100, "identical_delta": delta == -2100},
        }
        output_hashes = {"r4_snapshot": sha(generated_r4), "health_snapshot": sha(generated_health), "provider_results": sha(results_path)}
    report = {
        "drill_version": "r9.0", "network_used": False, "workspace_parent_on_pythonpath": False,
        "temporary_layout": ["datos_originales/", "docs/vnext/w1/HEALTH_DESTINATION_R4.json", "prototypes/", "scripts/mobility/", "work/"],
        "inputs": staged, "commands": commands, "output_hashes": output_hashes, "comparisons": comparisons,
        "stages": [
            {"stage": "GTFS raw → R4 snapshot", "classification": "REPRODUCED_FROM_PINNED_RAW"},
            {"stage": "Pinned OSM current-model extract → walking links", "classification": "REPRODUCED_FROM_PINNED_RAW"},
            {"stage": "Health reconciliation → R5 snapshot", "classification": "REPRODUCED_FROM_PINNED_DERIVED",
             "reason": "Builder consumes HEALTH_DESTINATION_R4 plus pinned external bytes; it does not re-extract every semantic field from XLSX/HTML/PDF."},
            {"stage": "R6 provider → canonical claims", "classification": "REPRODUCED_FROM_PINNED_DERIVED"},
            {"stage": "Historical PoC OSM identity", "classification": "SOURCE_BYTES_NOT_AVAILABLE",
             "reason": "The current-model OSM acquisition is pinned; this is not an exact reproduction of the earlier PoC historical network."},
        ],
        "missing_links": ["Historical PoC OSM bytes are unavailable and are not claimed as R6 input.",
                          "Health semantic extraction is preserved as a pinned derived input rather than reimplemented clean-room."],
        "source_to_claim_fully_raw_reproducible": False,
        "candidate_reproducible_from_pinned_raw_and_pinned_derived": all(item["identical"] for item in comparisons.values() if "identical" in item),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = drill(args.output)
    print(json.dumps({"reproducible": report["candidate_reproducible_from_pinned_raw_and_pinned_derived"],
                      "fully_raw": report["source_to_claim_fully_raw_reproducible"], "comparisons": report["comparisons"]}))


if __name__ == "__main__":
    main()
