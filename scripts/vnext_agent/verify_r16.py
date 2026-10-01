"""Bounded author delta check of immutable R15 against generated R16.

Reuses the existing non-gold-directed cases, not a model, holdout or stress20k.
Preserves full raw byte parity; presentation is checked separately and explicitly.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import tempfile
import time
import zipfile

from scripts.vnext_agent import verify_r15 as previous
from scripts.vnext_agent.build_r16 import BASE, BASE_HASH, BASE_ZIP, MANIFEST, ROOT, ZIP, blob, sha


def run(output):
    started = time.monotonic()
    baseline, candidate = blob(BASE_ZIP), ZIP.read_bytes()
    assert sha(baseline) == BASE_HASH
    oracle_bytes = previous.ORACLE.read_bytes()
    assert sha(oracle_bytes) == previous.ORACLE_HASH
    cases = previous.make_cases(baseline, json.loads(oracle_bytes))
    for case in cases:
        case["keep_view"] = True
    with tempfile.TemporaryDirectory(prefix="g360-r16-author-") as temporary:
        roots = [Path(temporary) / name for name in ("r15", "r16")]
        for root, data in zip(roots, (baseline, candidate)):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                assert all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in archive.namelist())
                archive.extractall(root)
        with ThreadPoolExecutor(max_workers=2) as pool:
            old, new = list(pool.map(lambda root: previous.run_worker(root, cases), roots))
    findings, records = [], []
    summaries = 0
    for case in cases:
        before, after = old["records"][case["id"]], new["records"][case["id"]]
        issues = []
        for key in ("status", "error", "raw_sha256", "raw_status", "outcomes", "totals_s", "execute_calls"):
            if before.get(key) != after.get(key):
                issues.append("unchanged_execution:" + key)
        if after["status"] == "escaped_exception" or after.get("raw_exposed_publicly"):
            issues.append("uncontrolled_execution_or_raw_exposure")
        if case.get("expected") == "valid" and after["status"] != "valid":
            issues.append("expected_valid")
        if case.get("expected") in {"safe_error", "binding_rejected"} and (
            after["status"] not in {"error", "unsupported", "binding_rejected"}
            or after.get("claims") or after.get("raw_contains_ok")
        ):
            issues.append("invalid_not_closed")
        if "oracle" in case and not after.get("oracle", {}).get("pass"):
            issues.append("oracle")
        left, right = before.get("view", {}), after.get("view", {})
        # Numeric claims and source identities must survive the presentation delta.
        columns = ("id", "value", "unit", "source_ids", "evidence_path", "entity_id", "metric_id")
        extract = lambda view: [{k: claim[k] for k in columns} for claim in view.get("claims", [])]
        if extract(left) != extract(right):
            issues.append("numeric_claim_or_source_identity_changed")
        for a, b in zip(left.get("mobility", {}).get("scenarios", []), right.get("mobility", {}).get("scenarios", []), strict=True):
            for key in ("status", "error", "scenario_kind", "scope", "time_basis", "itinerary", "components_s", "walking", "health_destination"):
                if a.get(key) != b.get(key):
                    issues.append("unchanged_scenario:" + key)
            if b["status"] == "ok":
                summaries += 1
                summary, total = b.get("time_summary", {}), b["itinerary"]["total_s"]
                if (summary.get("total_s") != total or summary.get("total_hms") != f"{total//3600} h {(total//60)%60} min {total%60} s"
                    or summary.get("scope_end_s", 0) - summary.get("scope_start_s", 0) != total
                    or sum(b["components_s"].values()) != total
                    or summary.get("initial_wait_s") != b["components_s"]["initial_wait_s"]):
                    issues.append("canonical_summary_invariant")
                for field in ("scope_start", "scope_end"):
                    seconds = summary.get(field + "_s", -1)
                    clock = f"{seconds//3600:02d}:{(seconds//60)%60:02d}:{seconds%60:02d}"
                    if not 0 <= seconds < 86400 or summary.get(field + "_clock") != clock:
                        issues.append("civil_clock")
        if "oracle" in case:
            # Oracle comparison also checks every original raw critical fact.
            if before.get("oracle") != after.get("oracle"):
                issues.append("oracle_facts_changed")
        if issues:
            findings.append({"case": case["id"], "issues": issues})
        records.append({"id": case["id"], "group": case["group"], "status": after["status"],
                        "raw_sha256": after.get("raw_sha256"), "issues": issues})
    signatures = new["signatures"]
    if old["signatures"].keys() != signatures.keys() or any(
        old["signatures"][name][key] != signatures[name][key]
        for name in signatures for key in ("fields", "required", "types", "defaults")
    ):
        findings.append({"case": "signatures", "issues": ["public_contract_changed"]})
    catalog = new["records"]["recovery:consultar_capacidades"]["view"]["mobility_catalog"]
    if {x["municipality_name"] for x in catalog["origin_options"]} != {"Zegama", "Segura", "Idiazabal"}:
        findings.append({"case": "coverage", "issues": ["origins_changed"]})
    if catalog["comparison"]["mode"] != "individual_calls" or catalog["comparison"]["batch_supported"]:
        findings.append({"case": "comparison", "issues": ["public_comparison_changed"]})
    # Audit only model-facing text. Source IDs are retained as trace identifiers.
    views = json.dumps([r.get("view") for r in new["records"].values()], ensure_ascii=False)
    for jargon in ("R5.1", "provider_r6", '"engine_contract"', '"provider_defaults"', '"source_sha256"'):
        if jargon in views:
            findings.append({"case": "public_jargon", "issues": [jargon]})
    report = {
        "classification": "R16_AUTHOR_DELTA_CHECK_NOT_INDEPENDENT_NOT_REAL_AGENT",
        "status": "PASS" if not findings else "FAIL", "base_r15_head": BASE,
        "base_r15_zip_sha256": BASE_HASH, "r16_zip_sha256": sha(candidate),
        "r16_manifest_sha256": sha(MANIFEST.read_bytes()),
        "cases": len(cases), "raw_execution_parity": len(cases) - sum(bool(r["issues"]) for r in records),
        "oracle_cases": sum("oracle" in c for c in cases), "time_summaries_checked": summaries,
        "invalid_cases": sum(c.get("expected") in {"safe_error", "binding_rejected"} for c in cases),
        "network": "socket creation denied in cold workers", "model_calls": 0, "holdout": "SEALED_NOT_EXECUTED",
        "findings": findings, "records": records, "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {k:v for k,v in report.items() if k != "records"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "work/r16-audit.json")
    report = run(parser.parse_args().output)
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(report["status"] != "PASS")
