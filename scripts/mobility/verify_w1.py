"""Genera evidencia reproducible del proveedor W1 sin acceder a Internet."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prototypes.ir_y_volver import provider


SNAPSHOT = ROOT / "prototypes" / "ir_y_volver" / "snapshots" / "official-goierrialdea-go01-20260928.json"
CONTRACTS = ROOT / "prototypes" / "ir_y_volver" / "contracts"
CASES_OUTPUT = ROOT / "docs" / "vnext" / "w1" / "REAL_CASES.json"
PERFORMANCE_OUTPUT = ROOT / "docs" / "vnext" / "w1" / "PERFORMANCE.json"

CASE_INPUTS = [
    ("W1-RC-01", "zegama_center_stops", "09:30"),
    ("W1-RC-02", "zegama_center_stops", "10:00"),
    ("W1-RC-03", "zegama_center_stops", "15:00"),
    ("W1-RC-04", "zegama_center_stops", "17:00"),
    ("W1-RC-05", "segura_herriko_plaza_stops", "09:30"),
    ("W1-RC-06", "segura_herriko_plaza_stops", "13:00"),
    ("W1-RC-07", "segura_herriko_plaza_stops", "19:00"),
    ("W1-RC-08", "idiazabal_center_stops", "10:00"),
    ("W1-RC-09", "idiazabal_center_stops", "12:00"),
    ("W1-RC-10", "idiazabal_center_stops", "17:00"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def request(origin_id: str, appointment_time: str) -> dict[str, object]:
    return {
        "origin_id": origin_id,
        "destination_id": "beasain_center_stop_pair",
        "date": "2026-09-29",
        "appointment_time": appointment_time,
        "duration_minutes": 30,
        "snapshot_id": "official-goierrialdea-go01-20260928",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100)
    args = parser.parse_args()
    if args.iterations < 1:
        raise SystemExit("--iterations debe ser positivo")

    rows = []
    requests = []
    for case_id, origin_id, appointment_time in CASE_INPUTS:
        item = request(origin_id, appointment_time)
        result = provider.plan_visit(item)
        if result["status"] != "ok":
            raise SystemExit(f"{case_id} no es viable: {result}")
        requests.append(item)
        rows.append({
            "case_id": case_id,
            "classification": "VERIFIED_LIVE_SOURCE_SNAPSHOT",
            "question": f"¿Puedo ir y volver desde {origin_id} para una cita a las {appointment_time} de 30 minutos?",
            "request": item,
            "expected": {
                "status": "ok",
                "total_s": result["itinerary"]["total_s"],
                "outbound_trip_id": result["itinerary"]["outbound"]["trip_id"],
                "return_trip_id": result["itinerary"]["return"]["trip_id"],
            },
            "source_rows": {
                "outbound": result["itinerary"]["outbound"],
                "return": result["itinerary"]["return"],
            },
            "components_s": result["components_s"],
            "oracle": "Enumeración independiente de parejas sobre stop_times; ver test_ten_official_rows_against_independent_oracle.",
        })

    snapshot_bytes = SNAPSHOT.stat().st_size
    cases = {
        "schema_version": "0.1.0",
        "snapshot_id": "official-goierrialdea-go01-20260928",
        "snapshot_sha256": sha256(SNAPSHOT),
        "source_gtfs_sha256": "3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4",
        "date": "2026-09-29",
        "cases": rows,
    }
    CASES_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    CASES_OUTPUT.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    for item in requests:
        provider.plan_visit(item)
    samples_ms = []
    payload_sizes = []
    for index in range(args.iterations):
        item = requests[index % len(requests)]
        started = time.perf_counter_ns()
        result = provider.plan_visit(item)
        samples_ms.append((time.perf_counter_ns() - started) / 1_000_000)
        payload_sizes.append(len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")))

    ordered = sorted(samples_ms)
    p95_index = max(0, min(len(ordered) - 1, (95 * len(ordered) + 99) // 100 - 1))
    performance = {
        "schema_version": "0.1.0",
        "environment": "local; network disabled by design; warm cache",
        "iterations": args.iterations,
        "latency_ms": {
            "min": round(min(samples_ms), 3),
            "median": round(statistics.median(samples_ms), 3),
            "p95_nearest_rank": round(ordered[p95_index], 3),
            "max": round(max(samples_ms), 3),
        },
        "snapshot": {"bytes": snapshot_bytes, "sha256": sha256(SNAPSHOT)},
        "response_payload_bytes": {"min": min(payload_sizes), "max": max(payload_sizes)},
        "contract_sha256": {path.name: sha256(path) for path in sorted(CONTRACTS.glob("*")) if path.is_file()},
        "note": "Mide ejecución Python local, no latencia del portal ni del transporte real.",
    }
    PERFORMANCE_OUTPUT.write_text(json.dumps(performance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"cases": len(rows), **performance}, ensure_ascii=False))


if __name__ == "__main__":
    main()
