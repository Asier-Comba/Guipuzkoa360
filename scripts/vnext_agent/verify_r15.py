"""Bounded, offline audit of exact generated R15 bytes against frozen R14.

No builder, Studio, model, holdout or full test suite is invoked here. Each
package gets its own cold interpreter and socket creation is denied there.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import types
import typing
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "094745b26bc57aee5cc1a5e003401743d96a914f"
BASE_PATH = "scripts/vnext_agent/dist/r14/gipuzkoa360-r14-binding.zip"
BASE_HASH = "9c6fa5c692df178afe36366c6291e7c0e7c3da06134381b09d853f55d6707252"
ZIP = ROOT / "scripts/vnext_agent/dist/r15/gipuzkoa360-r15-final-agent.zip"
ORACLE = ROOT / "docs/vnext/w3/r14/FINAL_ORACLE_R13.json"
ORACLE_HASH = "2f57634fcab245a63c95b2a4e833895f664b8a43b52592214470b913b6b1ba53"
FIELDS = ["origin_id", "destination_id", "date", "appointment_time", "duration_minutes"]
BASES = {
    "obtener_resumen_territorial": {"municipio": "Beasain"},
    "comparar_municipios": {"municipios": ["Beasain", "Ordizia"]},
    "analizar_envejecimiento": {},
    "analizar_acceso_servicios": {"categoria_servicio": "primary_care", "municipios": ["Beasain"]},
    "analizar_coincidencia": {"categoria_servicio": "primary_care"},
    "simular_escenario": {"accion": "change_threshold", "categoria_servicio": "primary_care", "nuevo_umbral_km": 2},
    "consultar_fuente": {},
    "consultar_capacidades": {},
}
PARAMETERS = {
    "obtener_resumen_territorial": ["municipio", "periodo"],
    "comparar_municipios": ["municipios", "grupo_edad", "categoria_servicio", "umbral_km", "periodo"],
    "analizar_envejecimiento": ["grupo_edad", "medida", "periodo", "top_n"],
    "analizar_acceso_servicios": ["categoria_servicio", "umbral_km", "periodo", "municipios"],
    "analizar_coincidencia": ["categoria_servicio", "grupo_edad", "umbral_km", "periodo", "cuantil"],
    "simular_escenario": ["accion", "categoria_servicio", "umbral_km", "periodo", "latitud", "longitud", "service_id", "nuevo_umbral_km"],
    "consultar_fuente": ["source_id"],
    "consultar_capacidades": ["pregunta_o_dimension"],
    "plan_visit": FIELDS,
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def clean_public(value):
    value = json.loads(canonical(value))
    if "versions" in value:
        value["versions"].pop("code_sha256", None)
    # R15 deliberately exposes the existing raw metadata method. Verify its
    # exact provenance separately; compare every previously public field here.
    for source in value.get("source_metadata", []):
        source.pop("method", None)
    return value


def includes(actual, expected):
    """Exact recursive subset, used only for the published oracle's facts."""
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and includes(actual[k], v) for k, v in expected.items())
    return actual == expected


def oracle_check(case, view, raw):
    issues = []
    if view.get("status") != case["expected_consumer_envelope_status"]:
        issues.append("consumer_status")
    if raw is not None:
        if raw.get("status") != case["expected_status"]:
            issues.append("producer_status")
        if not includes(raw, case["critical_semantic_facts"]):
            issues.append("critical_semantic_facts")
        if raw.get("sources") != case["source_facts"]:
            issues.append("source_facts")
        for claim in case["numeric_claims"]:
            actual = (raw.get("itinerary") or {}).get("total_s") if claim["metric"] == "total_s" else (raw.get("components_s") or {}).get(claim["metric"])
            if actual != claim["value"]:
                issues.append("numeric:" + claim["metric"])
    elif case["numeric_claims"] or view.get("status") != "error":
        issues.append("missing_expected_raw")
    return {"pass": not issues, "issues": issues, "raw_available": raw is not None,
            "numeric_claims_checked": len(case["numeric_claims"]) if raw is not None else 0,
            "status_note": case["status_mapping_note"]}


def primitive(annotation):
    if annotation in (str, int, float, bool, type(None)):
        return True
    origin, args = typing.get_origin(annotation), typing.get_args(annotation)
    if origin is list:
        return args == (str,)
    return origin in (typing.Union, types.UnionType) and all(primitive(x) for x in args)


def worker(directory):
    """One fixed root and one provider binding for this entire child process."""
    def denied(*args, **kwargs):
        raise RuntimeError("R15 audit network denied")
    socket.socket = denied
    socket.create_connection = denied
    root = Path(directory).resolve()
    os.environ["GIPUZKOA360_VNEXT_ROOT"] = str(root)
    sys.path.insert(0, str(root))
    import main
    import tools
    main.uuid4 = lambda: types.SimpleNamespace(hex="R15_AUDIT_FIXED_REQUEST")
    job = json.loads(sys.stdin.read())
    signatures = {}
    for function in main.TOOLS:
        sig, hints = inspect.signature(function), typing.get_type_hints(function)
        signatures[function.__name__] = {
            "signature": str(sig), "fields": list(sig.parameters),
            "required": [k for k, p in sig.parameters.items() if p.default is inspect.Parameter.empty],
            "types": {k: str(hints[k]) for k in sig.parameters},
            "primitives_or_string_arrays_only": all(primitive(hints[k]) for k in sig.parameters),
            "defaults": {k: p.default for k, p in sig.parameters.items() if p.default is not inspect.Parameter.empty},
            "docstring": inspect.getdoc(function),
        }
    original_execute, captured = tools.execute, []
    def capture(*args, **kwargs):
        result = original_execute(*args, **kwargs)
        captured.append(result)
        return result
    tools.execute = capture
    records, executions = {}, 0
    for case in job["cases"]:
        captured.clear()
        try:
            if case.get("route", "public") == "internal":
                rendered = main._run(case["tool"], case["arguments"])
            else:
                # A binding rejection is different from a successful tool execution.
                inspect.signature(getattr(main, case["tool"])).bind(**case["arguments"])
                rendered = getattr(main, case["tool"])(**case["arguments"])
            view = json.loads(rendered)
            executions += len(captured)
            evidence = captured[-1] if captured else None
            raw_text = evidence.get("raw_result_json") if evidence else None
            raw = json.loads(raw_text) if raw_text is not None else None
            scenarios = view.get("mobility", {}).get("scenarios", [])
            raw_scenarios = raw.get("results", [raw]) if raw else []
            record = {
                "status": view.get("status"), "error": view.get("error"),
                "claims": len(view.get("claims", [])), "outcomes": view.get("outcomes", []),
                "raw_sha256": sha(raw_text) if raw_text is not None else None,
                "raw_status": raw.get("status") if raw else None,
                "raw_contains_ok": any(r.get("status") == "ok" for r in raw_scenarios),
                "public_sha256_except_code": sha(canonical(clean_public(view))),
                "public_bytes": len(rendered.encode("utf-8")), "execute_calls": len(captured),
                "raw_exposed_publicly": "raw_result_json" in view,
                "totals_s": [(r.get("itinerary") or {}).get("total_s") for r in scenarios],
                "provenance_sha256": sha(canonical([{k: r.get(k) for k in ("effective_parameters", "parameter_attribution", "sources")} for r in scenarios])),
            }
            if case.get("keep_view"):
                record["view"] = view
            if "source_metadata" in view:
                source_rows = {r["source_id"]: r for r in (raw or {}).get("data", [])}
                record["source_methods_match_raw"] = all(
                    ("method" in source) == ("method" in source_rows.get(source["source_id"], {}))
                    and source.get("method") == source_rows.get(source["source_id"], {}).get("method")
                    for source in view["source_metadata"])
            if "oracle" in case:
                record["oracle"] = oracle_check(case["oracle"], view, raw)
            records[case["id"]] = record
        except TypeError as exc:
            # Only schema binding errors are expected; TypeError inside execution fails.
            try:
                inspect.signature(getattr(main, case["tool"])).bind(**case["arguments"])
            except TypeError:
                records[case["id"]] = {"status": "binding_rejected", "error": str(exc), "claims": 0,
                    "outcomes": [], "raw_sha256": None, "raw_contains_ok": False, "execute_calls": 0}
            else:
                records[case["id"]] = {"status": "escaped_exception", "error": repr(exc)}
        except Exception as exc:
            records[case["id"]] = {"status": "escaped_exception", "error": repr(exc)}
    return {"signatures": signatures, "records": records, "execute_calls": executions,
            "prompt_sha256": sha(main.SYSTEM_PROMPT), "prompt_chars": len(main.SYSTEM_PROMPT),
            "prompt_contains_demo_gold": any(value in main.SYSTEM_PROMPT.casefold() for value in ("zegama", "09:30", "09:45", "10691", "8591", "-35", "-2100")),
            "network": "socket creation denied", "model_calls": 0,
            "interface_classification": "EXPECTED_LOCAL_GENERATED_SIGNATURE_NOT_STUDIO_SERVED"}


def make_cases(baseline, oracle):
    with zipfile.ZipFile(io.BytesIO(baseline)) as archive:
        conformance = json.loads(archive.read("datos_preparados/vnext/w1_conformance_r7.json"))
        catalog = json.loads(archive.read("datos_preparados/vnext/operational_catalog_r6.json"))
        sources = json.loads(archive.read("datos_preparados/metadata_sources.json")) + json.loads(archive.read("datos_preparados/vnext/mobility_sources.json"))
    cases = []
    def add(ident, tool, args, group, *, expected=None, parity=False, route="public", **extra):
        cases.append({"id": ident, "tool": tool, "arguments": args, "group": group,
                      "expected": expected, "parity": parity, "route": route, **extra})
    base = oracle["cases"][0]["structured_request"]
    for origin in catalog["origins"]:
        for clock in ("09:30", "09:45"):
            for duration in (1, 20, 27, 90, 720):
                args = {**base, "origin_id": origin["origin_id"], "appointment_time": clock, "duration_minutes": duration}
                add(f"health:{origin['origin_id']}:{clock}:{duration}", "plan_visit", args, "supported_health", parity=True)
    for fixture in conformance["cases"]:
        add("conformance:" + fixture["case_id"], "plan_visit", {"request": fixture.get("request", fixture.get("requests"))},
            "internal_conformance", route="internal", parity=True)
    for fixture in oracle["cases"]:
        request = fixture["structured_request"]
        public = set(request) <= set(FIELDS)
        add("oracle:" + fixture["case_id"], "plan_visit", request if public else {"request": request},
            "oracle", route="public" if public else "internal", parity=True, oracle=fixture)
    for tool, args in BASES.items():
        add("baseline:" + tool, tool, args, "territorial_baseline", expected="valid", parity=tool != "consultar_capacidades", keep_view=tool == "consultar_capacidades")
    for source in sources:
        add("source:" + source["source_id"], "consultar_fuente", {"source_id": source["source_id"]}, "source_resolution", expected="valid", parity=True, keep_view=True)
    # All these values are unambiguously invalid for every indicated public field.
    for tool, args in BASES.items():
        for field in PARAMETERS[tool]:
            for index, value in enumerate(("", "   ", {}, [], True)):
                add(f"malformed:{tool}:{field}:{index}", tool, {**args, field: value}, "malformed", expected="safe_error")
    for field in FIELDS:
        for index, value in enumerate(("", "   ", None, {}, [], True, 0)):
            add(f"malformed:plan_visit:{field}:{index}", "plan_visit", {**base, field: value}, "malformed", expected="safe_error")
    for tool, args in BASES.items():
        if "periodo" not in PARAMETERS[tool]:
            continue
        valid = "2026-09-20" if tool in {"analizar_acceso_servicios", "simular_escenario"} else "2025-01-01"
        for label, value in (("omitted", "OMIT"), ("none", None), ("valid", valid), ("empty", ""), ("whitespace", "   "), ("wrong_type", 2025), ("unsupported", "1900-01-01")):
            request = dict(args) if label == "omitted" else {**args, "periodo": value}
            supported = label in {"omitted", "none", "valid"}
            add(f"period:{tool}:{label}", tool, request, "period_matrix", expected="valid" if supported else "safe_error", parity=supported)
    extra = [
        ("threshold_zero", "comparar_municipios", {**BASES["comparar_municipios"], "umbral_km": 0}, "safe_error"),
        ("threshold_none", "comparar_municipios", {**BASES["comparar_municipios"], "umbral_km": None}, "safe_error"),
        ("threshold_above", "analizar_acceso_servicios", {**BASES["analizar_acceso_servicios"], "umbral_km": 100.01}, "safe_error"),
        ("threshold_limit", "analizar_acceso_servicios", {**BASES["analizar_acceso_servicios"], "umbral_km": 100}, "valid"),
        ("top_zero", "analizar_envejecimiento", {"top_n": 0}, "safe_error"),
        ("top_none", "analizar_envejecimiento", {"top_n": None}, "safe_error"),
        ("top_limit", "analizar_envejecimiento", {"top_n": 100}, "valid"),
        ("quantile_zero", "analizar_coincidencia", {**BASES["analizar_coincidencia"], "cuantil": 0}, "safe_error"),
        ("quantile_limit", "analizar_coincidencia", {**BASES["analizar_coincidencia"], "cuantil": .95}, "valid"),
        ("unknown_municipality", "obtener_resumen_territorial", {"municipio": "TEST_UNKNOWN_ID"}, "safe_error"),
        ("array_whitespace", "comparar_municipios", {"municipios": ["Beasain", "   "]}, "safe_error"),
        ("array_prose", "comparar_municipios", {"municipios": "Beasain, Ordizia"}, "safe_error"),
        ("unsupported_category", "analizar_acceso_servicios", {"categoria_servicio": "pharmacy"}, "safe_error"),
        ("unsupported_source", "consultar_fuente", {"source_id": "TEST_UNKNOWN_ID"}, "safe_error"),
        ("add_id_whitespace", "simular_escenario", {"accion": "add_service", "categoria_servicio": "primary_care", "latitud": 43, "longitud": -2, "service_id": "   "}, "safe_error"),
        ("unused_coordinates", "simular_escenario", {**BASES["simular_escenario"], "latitud": 43, "longitud": -2}, "safe_error"),
        ("unused_invalid_coordinates", "simular_escenario", {**BASES["simular_escenario"], "latitud": 999, "longitud": -999}, "safe_error"),
        ("valid_add", "simular_escenario", {"accion": "add_service", "categoria_servicio": "primary_care", "latitud": 43, "longitud": -2}, "valid"),
    ]
    for ident, tool, args, expected in extra:
        add("boundary:" + ident, tool, args, "boundaries", expected=expected, parity=expected == "valid")
    add("regression:R13_nested", "plan_visit", {"request": base}, "binding_regression", expected="binding_rejected")
    add("regression:R13_prose", "plan_visit", {"request": "Organiza una visita sanitaria"}, "binding_regression", expected="binding_rejected")
    for field in ("return_deadline", "snapshot_id", "walking_profile_id", "arrival_margin_minutes", "boarding_margin_minutes"):
        add("regression:R14_public:" + field, "plan_visit", {**base, field: ""}, "binding_regression", expected="binding_rejected")
    add("regression:M05_internal", "plan_visit", {"request": {**base, "return_deadline": ""}}, "historical_engine_rejection", expected="safe_error", route="internal", parity=True)
    for tool in ("consultar_capacidades", "consultar_fuente", "obtener_resumen_territorial"):
        add("recovery:" + tool, tool, BASES[tool], "failure_recovery", expected="valid", parity=tool != "consultar_capacidades", keep_view=tool == "consultar_capacidades")
    add("recovery:plan_visit", "plan_visit", base, "failure_recovery", expected="valid", parity=True, keep_view=True)
    assert len({c["id"] for c in cases}) == len(cases)
    return cases


def run_worker(directory, cases):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
    process = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(directory)],
                             input=canonical({"cases": cases}), text=True, encoding="utf-8",
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=directory, env=env)
    if process.returncode:
        raise RuntimeError(f"Cold worker failed ({process.returncode}): {process.stderr}")
    return json.loads(process.stdout)


def run(package, oracle_path, output):
    started = time.monotonic()
    baseline = subprocess.check_output(["git", "show", f"{BASE_SHA}:{BASE_PATH}"], cwd=ROOT)
    assert sha(baseline) == BASE_HASH, "R14 identity changed"
    oracle_bytes = oracle_path.read_bytes()
    assert sha(oracle_bytes) == ORACLE_HASH, "Published W1 oracle identity changed"
    candidate = package.read_bytes()
    cases = make_cases(baseline, json.loads(oracle_bytes))
    with tempfile.TemporaryDirectory(prefix="g360-r15-audit-") as temporary:
        roots = [Path(temporary) / name for name in ("r14", "r15")]
        for root, data in zip(roots, (baseline, candidate)):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                assert all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in archive.namelist())
                archive.extractall(root)
        with ThreadPoolExecutor(max_workers=2) as pool:
            old, new = list(pool.map(lambda root: run_worker(root, cases), roots))
    findings, records = [], []
    parity_count, oracle_count, invalid_count = 0, 0, 0
    for case in cases:
        ident = case["id"]
        before, after = old["records"][ident], new["records"][ident]
        errors = []
        if before["status"] == "escaped_exception" or after["status"] == "escaped_exception":
            errors.append("escaped_exception")
        if case["parity"]:
            parity_count += 1
            for key in ("raw_sha256", "public_sha256_except_code", "provenance_sha256"):
                if before.get(key) != after.get(key):
                    errors.append("parity:" + key)
        expected = case["expected"]
        if expected == "valid" and after["status"] != "valid":
            errors.append("expected_valid")
        if expected == "binding_rejected" and after["status"] != "binding_rejected":
            errors.append("expected_binding_rejection")
        if expected in {"safe_error", "binding_rejected"}:
            invalid_count += 1
            if after["status"] not in {"error", "unsupported", "binding_rejected"} or after.get("claims") or any(r.get("status") in {"ok", "valid"} for r in after.get("outcomes", [])) or after.get("raw_contains_ok") or not after.get("error"):
                errors.append("authoritative_or_uncontrolled_invalid_input")
        if after.get("raw_exposed_publicly"):
            errors.append("raw_exposed_publicly")
        if "oracle" in case:
            oracle_count += 1
            for label, observed in (("r14", before), ("r15", after)):
                if not observed.get("oracle", {}).get("pass"):
                    errors.append(label + ":oracle:" + canonical(observed.get("oracle")))
        if errors:
            findings.append({"case": ident, "issues": errors})
        records.append({k: case[k] for k in ("id", "tool", "arguments", "route", "group", "expected", "parity")} | {
            "r14": {k: v for k, v in before.items() if k != "view"},
            "r15": {k: v for k, v in after.items() if k != "view"}, "issues": errors})
    signatures = new["signatures"]
    signature_issues = []
    if set(signatures) != set(PARAMETERS):
        signature_issues.append("nine_tool_inventory")
    for name, expected in PARAMETERS.items():
        record = signatures.get(name, {})
        if record.get("fields") != expected or not record.get("primitives_or_string_arrays_only"):
            signature_issues.append(name + ":fields_or_types")
    if signatures.get("plan_visit", {}).get("required") != FIELDS:
        signature_issues.append("plan_visit:required")
    cap_view = new["records"]["recovery:consultar_capacidades"].get("view", {})
    capabilities = {c["id"]: c for c in cap_view.get("capabilities", []) if c["enabled"]}
    for name, fields in PARAMETERS.items():
        if [f["name"] for f in capabilities.get(name, {}).get("input_fields", [])] != fields:
            signature_issues.append(name + ":advertised_fields")
        if "periodo" in fields:
            item = capabilities.get(name, {})
            policy = item.get("period_policy", {})
            period_field = next((f for f in item.get("input_fields", []) if f["name"] == "periodo"), {})
            meaning = "source_reference_only_not_historical_filter" if name in {"analizar_acceso_servicios", "simular_escenario"} else "demographic_selector"
            if not policy.get("allowed_values") or policy.get("allowed_values") != period_field.get("allowed_values") or policy.get("meaning") != meaning or policy.get("explicit_invalid") != "reject_without_numeric_claims" or period_field.get("nullable") is not True:
                signature_issues.append(name + ":period_policy")
    mobility = cap_view.get("mobility_catalog", {})
    if mobility.get("request_fields") != FIELDS or mobility.get("required_fields") != FIELDS or "comparison_size" in mobility:
        signature_issues.append("mobility:public_fields_or_batch")
    comparison = mobility.get("comparison", {})
    if comparison.get("mode") != "individual_calls" or comparison.get("batch_supported") is not False or comparison.get("cross_origin_comparison") != "side_by_side_only; numeric delta is not supported across origins":
        signature_issues.append("mobility:comparison_scope")
    if "request" in [f["name"] for f in capabilities.get("plan_visit", {}).get("input_fields", [])]:
        signature_issues.append("mobility:nested_binding")
    with zipfile.ZipFile(io.BytesIO(baseline)) as archive:
        frozen_catalog = json.loads(archive.read("datos_preparados/vnext/operational_catalog_r6.json"))
    if mobility.get("provider_defaults") != frozen_catalog["defaults"]:
        signature_issues.append("mobility:producer_defaults_changed")
    if new.get("prompt_contains_demo_gold"):
        signature_issues.append("prompt:demo_gold")
    historical_error = new["records"]["regression:M05_internal"].get("error", {})
    if historical_error.get("code") != "contract_violation" or historical_error.get("message") != "mobility:invalid_clock":
        findings.append({"case": "regression:M05_internal", "issues": ["historical_error_changed"]})
    for ident, observed in new["records"].items():
        if ident.startswith("source:"):
            metadata = observed.get("view", {}).get("source_metadata", [])
            if len(metadata) != 1 or metadata[0].get("source_id") != ident.removeprefix("source:") or not metadata[0].get("title") or not metadata[0].get("reference_period") or not observed.get("source_methods_match_raw"):
                findings.append({"case": ident, "issues": ["source_metadata_incomplete"]})
    if signature_issues:
        findings.append({"case": "public_contract", "issues": signature_issues})
    main = new["records"]["oracle:MAIN"]["totals_s"]
    variation = new["records"]["oracle:VARIATION"]["totals_s"]
    sequential = main == [10691] and variation == [8591] and variation[0] - main[0] == -2100
    if not sequential:
        findings.append({"case": "sequential_comparison", "issues": ["oracle_conditional_delta"]})
    with zipfile.ZipFile(io.BytesIO(baseline)) as left, zipfile.ZipFile(io.BytesIO(candidate)) as right:
        inventory_equal = left.namelist() == right.namelist()
        changed = [name for name in left.namelist() if name not in right.namelist() or left.read(name) != right.read(name)]
        if not inventory_equal or changed != ["main.py", "tools.py"]:
            findings.append({"case": "package", "issues": ["unexpected_member_change"]})
    report = {
        "classification": "BOUNDED_GENERATED_PACKAGE_OFFLINE_NOT_LLM_NOT_INDEPENDENT_ACCEPTANCE",
        "status": "PASS" if not findings else "FAIL", "base_sha": BASE_SHA,
        "r14_zip_sha256": BASE_HASH, "r15_zip_sha256": sha(candidate), "oracle_sha256": ORACLE_HASH,
        "audit_script_sha256": sha(Path(__file__).read_bytes()), "python": sys.version,
        "cold_package_processes": 2, "network": "socket creation denied in both workers", "model_calls": 0,
        "holdout": "SEALED", "studio": "NOT_USED", "portal_real_agent": "NOT_RETESTED",
        "case_count": len(cases), "executions": {"r14": old["execute_calls"], "r15": new["execute_calls"]},
        "group_counts": {group: sum(c["group"] == group for c in cases) for group in sorted({c["group"] for c in cases})},
        "full_raw_and_public_parity_cases": parity_count,
        "parity_normalization": "Public versions.code_sha256 removed; newly exposed source_metadata.method removed only for old-field equality and checked exactly against raw; fixed identical request_id in both workers; raw_result_json byte digest unchanged",
        "deliberate_public_metadata_change": "Capabilities input_fields, period_policy and mobility public/engine separation independently checked; source_metadata.method must match original raw metadata; raw catalogue bytes preserved",
        "oracle_cases": oracle_count, "invalid_input_cases": invalid_count,
        "source_count": sum(c["group"] == "source_resolution" for c in cases),
        "public_contract": {"status": "PASS" if not signature_issues else "FAIL", "issues": signature_issues,
                            "signature_classification": new["interface_classification"], "signatures": signatures,
                            "mobility_catalog": mobility, "prompt_sha256": new["prompt_sha256"],
                            "prompt_chars": new["prompt_chars"], "demo_gold_detected": new["prompt_contains_demo_gold"]},
        "sequential_comparison": {"pass": sequential, "main_total_s": main, "variation_total_s": variation,
                                  "conditional_delta_s": variation[0] - main[0] if main and variation else None,
                                  "meaning": "conditional modelled difference; not observed saving or recommendation"},
        "changed_members": changed, "member_inventory_identical": inventory_equal,
        "findings": findings, "records": records, "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {k: report[k] for k in ("status", "case_count", "executions", "full_raw_and_public_parity_cases", "oracle_cases", "invalid_input_cases", "findings", "r15_zip_sha256", "elapsed_seconds")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--package", type=Path, default=ZIP)
    parser.add_argument("--oracle", type=Path, default=ORACLE)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/vnext/w2/R15_AUDIT.json")
    args = parser.parse_args()
    result = worker(args.worker) if args.worker else run(args.package, args.oracle, args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if not args.worker and result["status"] != "PASS":
        raise SystemExit(1)
