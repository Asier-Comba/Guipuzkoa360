"""Read-only, offline health counters for the versioned source snapshot. No quality score."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "municipios.csv": ("municipality_code", ["municipality_code", "population_total", "source_ids", "reference_period"]),
    "demografia.csv": ("municipality_code", ["municipality_code", "population_total", "population_65_plus", "population_75_plus", "source_id", "reference_period"]),
    "runtime_servicios.csv": ("service_id", ["service_id", "municipality_code", "latitude", "longitude", "easting_m", "northing_m", "source_id", "reference_period"]),
    "runtime_municipality_points.csv": ("municipality_code", ["municipality_code", "latitude", "longitude", "easting_m", "northing_m", "source_id", "reference_period"]),
}

def compute(root=ROOT):
    data = root/"datos_preparados"
    catalog = json.loads((data/"metadata_sources.json").read_text(encoding="utf-8"))
    catalog = catalog["sources"] if isinstance(catalog, dict) else catalog
    ids = {s["source_id"] for s in catalog}
    contract = json.loads((data/"data_contract.json").read_text(encoding="utf-8"))
    tables, missing, duplicates, invalid, traced, total = {}, 0, 0, 0, 0, 0
    details, periods = {}, set()
    for filename, (key, minimum) in FILES.items():
        with (data/filename).open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        tables[filename] = rows
        columns = set(minimum) | set(contract["files"].get("datos_preparados/"+filename, {}).get("required_columns", []))
        absent = sum(not r.get(c, "").strip() for r in rows for c in columns)
        counts = Counter(r.get(key) for r in rows)
        repeated = sum(n-1 for n in counts.values() if n > 1)
        missing += absent
        duplicates += repeated
        details[filename] = {"rows": len(rows), "missing_required_cells": absent, "duplicate_keys": repeated}
        for row in rows:
            total += 1
            refs = row.get("source_ids", row.get("source_id", "")).split("|")
            traced += bool(refs) and all(ref in ids for ref in refs)
            try:
                periods.add(date.fromisoformat(row["reference_period"]))
            except (KeyError, ValueError):
                missing += 1
            if filename.startswith("runtime_"):
                try:
                    lat, lon, east, north = (float(row[k]) for k in ("latitude", "longitude", "easting_m", "northing_m"))
                    valid = all(math.isfinite(n) for n in (lat, lon, east, north)) and 42 <= lat <= 44 and -3 <= lon <= -1 and 0 < east < 1_000_000 and 0 < north < 10_000_000
                except (ValueError, TypeError, KeyError):
                    valid = False
                invalid += not valid
    municipalities = {r["municipality_code"] for r in tables["municipios.csv"]}
    demography = {r["municipality_code"] for r in tables["demografia.csv"]}
    points = {r["municipality_code"] for r in tables["runtime_municipality_points.csv"]}
    missing_fk = sum(r["municipality_code"] not in municipalities for r in tables["runtime_servicios.csv"])
    manifest = json.loads((data/"runtime_manifest.json").read_text(encoding="utf-8"))
    checks = []
    for entry in manifest["files"]:
        path = (root/entry["path"]).resolve()
        safe = path.is_relative_to(data.resolve())
        blob = path.read_bytes() if safe and path.is_file() else b""
        checks.append({"path": entry["path"], "matches": safe and len(blob) == entry["bytes"] and hashlib.sha256(blob).hexdigest() == entry["sha256"]})
    expected_paths = {"datos_preparados/"+name for name in FILES} | {
        "datos_preparados/runtime_municipios.geojson", "datos_preparados/metadata_sources.json", "datos_preparados/data_contract.json"}
    manifest_paths = [e['path'] for e in manifest['files']]
    integrity = (set(manifest_paths) == expected_paths and len(manifest_paths) == len(expected_paths)
                 and all(c["matches"] for c in checks)
                 and sum(e["bytes"] for e in manifest["files"]) == manifest["total_bytes"])
    coverage = len(municipalities & demography & points)
    valid_codes = all(len(c) == 5 and c.startswith("20") and c.isdigit() for c in municipalities)
    ok = coverage == 88 and len(municipalities | demography | points) == 88 and valid_codes and not any((missing, duplicates, invalid, missing_fk)) and total == traced and integrity
    return {"status": "PASS" if ok else "FAIL", "offline": True,
            "source_count": sum(s.get("source_type") != "derived" for s in catalog), "catalog_entries": len(catalog),
            "municipality_coverage": {"present": coverage, "expected": 88, "keys_equal": municipalities == demography == points},
            "service_record_count": len(tables["runtime_servicios.csv"]),
            "missing_required_fields": missing, "duplicate_keys": duplicates, "invalid_coordinates": invalid,
            "orphan_service_municipalities": missing_fk,
            "traceability_coverage": {"numerator": traced, "denominator": total, "value": traced/total if total else None,
                                      "definition": "CSV rows whose declared source identifiers resolve in the versioned catalog"},
            "manifest_integrity": {"status": "PASS" if integrity else "FAIL", "files": checks},
            "reference_periods": [p.isoformat() for p in sorted(periods)],
            "cross_source_reference_spread_days": (max(periods)-min(periods)).days if periods else None,
            "tables": details}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT/"analisis/ops/source_health.json")
    args = parser.parse_args()
    report = compute()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "PASS" else 1)

if __name__ == "__main__":
    main()
