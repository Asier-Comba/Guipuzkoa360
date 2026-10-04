"""Bounded public-schema audit, not independent acceptance or LLM evidence."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import re
import tempfile
import time
import zipfile

from scripts.vnext_agent import verify_r15 as previous
from scripts.vnext_agent.build_r17 import BASE, BASE_HASH, BASE_ZIP, MANIFEST, ROOT, ZIP, blob, sha


def public_language(value, key=None):
    """Audit text, exempting historic trace IDs only, not titles or institutions."""
    if key in {"source_id", "source_ids", "source_refs", "upstream_source_ids", "input_source_ids"}:
        return []
    if isinstance(value, dict):
        return [s for k, v in value.items() for s in public_language(v, k)]
    if isinstance(value, list):
        return [s for v in value for s in public_language(v, key)]
    return [str(key) + ": " + value] if isinstance(value, str) and re.search(r"\bR\d+(?:\.\d+)?\b|provider_r\w*|ENGINE_CONTRACT|PUBLIC_AGENT_CONTRACT|sha256|\bpatch\b|\bWork [123]\b|\bW[123]\b", value, re.I) else []


def run(output):
    started = time.monotonic()
    baseline, candidate = blob(BASE_ZIP), ZIP.read_bytes()
    assert sha(baseline) == BASE_HASH
    oracle_bytes = previous.ORACLE.read_bytes()
    assert sha(oracle_bytes) == previous.ORACLE_HASH
    cases = previous.make_cases(baseline, json.loads(oracle_bytes))
    # Existing explicit-period tests still exercise the unchanged internal
    # engine. Separate new cases assert the reduced PUBLIC binding instead.
    for case in cases:
        if case["tool"] == "obtener_resumen_territorial" and "periodo" in case["arguments"]:
            case["route"] = "internal"
        case["keep_view"] = True
    cases.append({"id": "aduna:public", "tool": "obtener_resumen_territorial", "arguments": {"municipio": "Aduna"}, "group": "aduna", "keep_view": True})
    cases.append({"id": "aduna:engine", "tool": "obtener_resumen_territorial", "arguments": {"municipio": "Aduna", "periodo": "2025-01-01"}, "route": "internal", "group": "aduna", "keep_view": True})
    with tempfile.TemporaryDirectory(prefix="g360-r17-author-") as temporary:
        roots = [Path(temporary) / name for name in ("r16", "r17")]
        for root, data in zip(roots, (baseline, candidate), strict=True):
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
        if "oracle" in case and before.get("oracle") != after.get("oracle"):
            issues.append("oracle_changed")
        if "oracle" in case and not after.get("oracle", {}).get("pass"):
            issues.append("oracle")
        left, right = before.get("view", {}), after.get("view", {})
        if left.get("claims") != right.get("claims"):
            issues.append("claims_changed")
        for a, b in zip(left.get("mobility", {}).get("scenarios", []), right.get("mobility", {}).get("scenarios", []), strict=True):
            for key in ("status", "error", "scenario_kind", "scope", "time_basis", "itinerary", "components_s", "walking", "health_destination", "time_summary", "effective_parameters"):
                if a.get(key) != b.get(key):
                    issues.append("scenario_changed:" + key)
            if b["status"] == "ok":
                summaries += 1
                summary = b["time_summary"]
                if summary["scope_end_s"] - summary["scope_start_s"] != summary["total_s"] or sum(b["components_s"].values()) != summary["total_s"]:
                    issues.append("time_invariant")
        jargon = public_language(right)
        if jargon:
            issues.append("public_jargon")
        if issues:
            findings.append({"case": case["id"], "issues": issues, "jargon": jargon})
        records.append({"id": case["id"], "group": case["group"], "status": after["status"], "raw_sha256": after.get("raw_sha256"), "issues": issues})
    signatures = new["signatures"]
    if signatures["obtener_resumen_territorial"]["fields"] != ["municipio"]:
        findings.append({"case": "summary_signature", "issues": ["fields"]})
    for name in signatures:
        if name != "obtener_resumen_territorial" and any(old["signatures"][name][key] != signatures[name][key] for key in ("fields", "required", "types", "defaults")):
            findings.append({"case": name, "issues": ["other_signature_changed"]})
    aduna, engine = (new["records"]["aduna:" + mode] for mode in ("public", "engine"))
    if aduna["raw_sha256"] != engine["raw_sha256"] or aduna["view"]["claims"] != engine["view"]["claims"]:
        findings.append({"case": "aduna", "issues": ["explicit_engine_parity"]})
    cap = new["records"]["baseline:consultar_capacidades"]["view"]
    for item in cap["capabilities"]:
        if item["enabled"] and item["id"] in signatures and [f["name"] for f in item["input_fields"]] != signatures[item["id"]]["fields"]:
            findings.append({"case": item["id"], "issues": ["catalog_signature_mismatch"]})
    report = {
        "classification": "R17_AUTHOR_DELTA_CHECK_NOT_INDEPENDENT_NOT_REAL_AGENT", "status": "PASS" if not findings else "FAIL",
        "base_r16_head": BASE, "base_r16_zip_sha256": BASE_HASH, "r17_zip_sha256": sha(candidate), "r17_manifest_sha256": sha(MANIFEST.read_bytes()),
        "cases": len(cases), "raw_execution_parity": len(cases) - sum("unchanged_execution:raw_sha256" in r["issues"] for r in records),
        "oracle_cases": sum("oracle" in c for c in cases), "time_summaries_checked": summaries,
        "findings": findings, "records": records, "aduna": aduna["view"], "capabilities": cap,
        "model_calls": 0, "network": "socket creation denied in cold workers", "holdout": "SEALED_NOT_EXECUTED", "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {k: v for k, v in report.items() if k not in {"records", "aduna", "capabilities"}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "work/r17-audit.json")
    result = run(parser.parse_args().output)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(result["status"] != "PASS")
