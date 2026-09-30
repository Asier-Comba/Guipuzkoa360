"""Immutable ZIP intake with separate cold producer and candidate processes.

R11 remains historical. R12 checks concrete per-scenario paths, applicability,
real nested runtime bytes and stage/owner attribution; it does not edit a ZIP.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
WORKER = Path(__file__).with_name("candidate_worker_r12.py")
DOC = ROOT / "docs/vnext/w1"
REAL_PIN = "cb061a9e00a6496c40488a596bd94834bc2c49b2"
HISTORICAL_ERRATA = "cb061a97e78d6b5c967104fef6b935132fdc450f"
R6_SHA = "c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(text):
    return json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def issue(category, detail, *, owner="W2", stage="assertions", severity="high", **extra):
    return dict(category=category, detail=detail, owner=owner, stage=stage, severity=severity, **extra)


def inventory(archive):
    names = archive.namelist()
    if not names or len(names) != len(set(names)) or len(names) != len({name.casefold() for name in names}):
        raise ValueError("empty/duplicate/case-colliding ZIP inventory")
    for info in archive.infolist():
        name = info.filename
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name or (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError("unsafe ZIP member: " + name)
    return names


def inspect(package, manifest):
    data = package.read_bytes()
    if manifest.get("sha256") != digest(data) or manifest.get("bytes") != len(data):
        raise ValueError("ZIP hash/bytes mismatch")
    with zipfile.ZipFile(package) as archive:
        names = inventory(archive)
        members = manifest.get("members")
        if type(members) is not dict or not members or set(members) != set(names):
            raise ValueError("manifest inventory is empty or does not close the ZIP")
        for name in names:
            raw = archive.read(name)
            if members[name].get("sha256") != digest(raw) or members[name].get("bytes") != len(raw):
                raise ValueError("manifest member mismatch: " + name)
        nested = archive.read("datos_preparados/vnext/w1_r6_runtime.zip")
        if digest(nested) != R6_SHA:
            raise ValueError("actual nested W1 ZIP is not frozen R6")
        with zipfile.ZipFile(io.BytesIO(nested)) as runtime:
            inventory(runtime)
            runtime_hashes = {name: digest(runtime.read(name)) for name in runtime.namelist()}
            declarations = manifest.get("w1_source_files")
            if type(declarations) is not list or not declarations or len(declarations) != len(runtime_hashes) or {row.get("path") for row in declarations} != set(runtime_hashes):
                raise ValueError("nested runtime source manifest is not closed")
            for row in declarations:
                raw = runtime.read(row["path"])
                if row.get("sha256") != digest(raw) or row.get("bytes") != len(raw):
                    raise ValueError("nested runtime source manifest mismatch: " + row["path"])
        # A self-authored manifest flag is not human redistribution permission.
        documents = [name for name in names if name.lower().endswith((".pdf", ".html", ".htm"))]
        policy = [issue("DISTRIBUTION_POLICY_FAILURE", name, stage="package", owner="W2/human owner") for name in documents]
    source = manifest.get("source_git_sha") or manifest.get("w1_runtime_commit_observed")
    compatible = source == REAL_PIN and manifest.get("w1_contract") == "0.3.1" and manifest.get("w1_package_sha256") == R6_SHA
    return {"members": len(names), "nested_runtime_verified": True, "runtime_hashes": runtime_hashes, "tools_sha256": members["tools.py"]["sha256"],
            "compatible": compatible, "source_git_sha": source, "policy": policy}


def run_worker(mode, root, cases, *, cwd=None, configured=None, pass_root=True):
    # Explicit allowlist: no inherited PYTHONPATH, product roots, model keys or candidate variables.
    permitted = {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "TMPDIR", "COMSPEC", "PATHEXT", "LANG", "LC_ALL"}
    env = {key: value for key, value in os.environ.items() if key.upper() in permitted}
    env["PYTHONIOENCODING"] = "utf-8"
    if configured is not None:
        env["GIPUZKOA360_VNEXT_ROOT"] = str(configured)
    payload = dict(mode=mode, root=str(root), cases=cases, pass_root=pass_root)
    try:
        completed = subprocess.run([sys.executable, "-I", str(WORKER)], cwd=cwd or root, env=env,
                                   input=json.dumps(payload, ensure_ascii=False), text=True, encoding="utf-8",
                                   capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error_stage": "worker_protocol", "traceback": str(exc), "records": []}
    if completed.returncode:
        return {"error_stage": "bootstrap", "traceback": completed.stderr, "records": [], "exit_code": completed.returncode}
    try:
        result = strict_json(completed.stdout)
    except Exception as exc:
        return {"error_stage": "worker_protocol", "traceback": str(exc), "records": []}
    result["exit_code"] = completed.returncode
    return result


def acceptance_cases():
    original = strict_json((DOC / "CONSUMER_CONFORMANCE_R7.json").read_text(encoding="utf-8"))["cases"]
    cases = [{"case_id": row["case_id"], "operation": "plan" if "request" in row else "compare",
              **({"request": row["request"]} if "request" in row else {"requests": row["requests"]})} for row in original]
    base = copy.deepcopy(cases[0]["request"])
    for origin in ("idiazabal_center_stops", "segura_herriko_plaza_stops"):
        cases.append(dict(case_id="origin_" + origin, operation="plan", request={**base, "origin_id": origin}))
    failed = next(row["request"] for row in cases if row["case_id"] == "health_no_feasible")
    cases.append(dict(case_id="compare_ok_and_no_feasible", operation="compare", requests=[base, failed]))
    legacy = next(row["request"] for row in cases if row["case_id"] == "legacy_r4_explicit")
    cases.extend([dict(case_id="sequence_legacy_after_health", operation="plan", request=legacy),
                  dict(case_id="sequence_health_after_legacy", operation="plan", request=base)])
    boundaries = strict_json((DOC / "BOUNDARY_CASES_R6.json").read_text(encoding="utf-8"))["cases"]
    cases.extend(dict(case_id="boundary_" + row["case_id"], operation="plan", request=row["request"])
                 for row in boundaries if "corruption" not in row)
    return cases


def at(value, path):
    current = value
    for part in path.strip("/").split("/") if path != "/" else []:
        current = current[int(part)] if type(current) is list else current[part]
    return current


def equal(left, right):
    return type(left) is type(right) and left == right


def validate_scenario(scenario, raw, labels, requirements, index):
    findings, decisions = [], []
    checks = 0
    severities = {row["requirement_id"]: row.get("severity", "critical") for row in requirements}

    def check(path, expected, requirement, projection=None):
        nonlocal checks
        checks += 1
        try:
            observed = at(scenario, path)
            if projection is not None:
                observed = projection(observed)
        except (KeyError, IndexError, TypeError, ValueError):
            findings.append(issue("MODEL_VIEW_MISSING", path, severity=severities.get(requirement, "critical"), scenario_index=index, requirement_id=requirement))
            return
        if not equal(expected, observed):
            findings.append(issue("MODEL_VIEW_WRONG_VALUE", path, severity=severities.get(requirement, "critical"), scenario_index=index,
                                  requirement_id=requirement, expected=expected, actual=observed))

    check("/index", index, "identity")
    for field in ("status", "error", "scenario_kind", "scope", "time_basis", "snapshot_id"):
        check("/" + field, raw[field], field)
    check("/effective_parameters", raw["normalized_request"] or {}, "request_binding")
    for row in requirements:
        ident, source = row["requirement_id"], row["source_path"]
        health_only = source.startswith(("/health_destination", "/walking")) or ident in {"MV-WALK-PROFILE", "MV-PROVENANCE"}
        reason = None
        if health_only and (raw.get("schema_version") != "0.3.1" or raw.get("scenario_kind") != "health_visit"):
            reason = "health requirement does not apply to contract 0.2.0 stop_only"
        elif raw["status"] != "ok" and row["applicability"] != "all":
            reason = "no successful itinerary for status " + raw["status"]
        elif ident == "MV-EFFECTIVE" and raw.get("normalized_request") is None:
            reason = "producer rejected normalization; effective_parameters={} is an explicit empty projection"
        if reason:
            decisions.append(dict(requirement_id=ident, status="NOT_APPLICABLE", reason=reason, scenario_index=index))
            continue
        if ident == "MV-PROVENANCE":
            attribution = scenario.get("parameter_attribution")
            checks += 1
            if type(attribution) is not list or len(attribution) != len(raw["parameter_provenance"]):
                findings.append(issue("MODEL_VIEW_MISSING", "parameter_attribution", severity=row.get("severity", "critical"), scenario_index=index))
            else:
                for item in raw["parameter_provenance"]:
                    matches = [a for a in attribution if a.get("field") == item["field"]]
                    checks += 1
                    if len(matches) != 1 or not equal(matches[0].get("value"), item["value"]) or matches[0].get("provider_origin") != item["origin"] or matches[0].get("w2_attribution") != ("provider_default" if item["origin"] == "model_default" else "tool_argument_origin_unverified"):
                        findings.append(issue("MODEL_VIEW_WRONG_SEMANTICS", "caller/default attribution: " + item["field"], severity=row.get("severity", "critical"), scenario_index=index))
            continue
        if ident == "MV-SOURCES":
            fields = ("source_id", "source_role", "publisher", "url", "reference_period", "transformation")

            def project_sources(observed):
                if type(observed) is not list or len(observed) != len(raw["sources"]):
                    return observed
                for original, emitted in zip(raw["sources"], observed):
                    if type(emitted) is not dict or any(key in original and key not in emitted for key in fields):
                        return observed
                # Preserve required producer facts and order, while allowing
                # extra readable catalog metadata. Legacy absent fields may be
                # absent or null, never fabricated health transformation/role.
                return [{key: item.get(key) for key in fields} for item in observed]

            check("/sources", [{key: item.get(key) for key in fields} for item in raw["sources"]], ident, project_sources)
            continue
        if ident == "MV-TIMEPOINT":
            checks += 1
            wording = json.dumps(scenario.get("limitations", []), ensure_ascii=False).lower()
            if not any(token in wording for token in ("aproxim", "interpol")):
                findings.append(issue("MODEL_VIEW_WRONG_SEMANTICS", "timepoint caveat missing", severity=row.get("severity", "critical"), scenario_index=index))
            continue
        if ident.endswith("ROUTE-LABEL"):
            for direction in ("outbound", "return"):
                route = raw["itinerary"][direction]["route_id"]
                check(f"/itinerary/{direction}/route_label", labels["routes"][route], ident)
            continue
        if ident.endswith("-LABEL") and "snapshot:" in source:
            direction = "outbound" if "OUT" in ident else "return"
            end = "from" if "FROM" in ident else "to"
            stop = raw["itinerary"][direction][end + "_stop_id"]
            check(f"/itinerary/{direction}/{end}_stop_label", labels["stops"][stop], ident)
            continue
        # Exact scoped pointers; no flattened search can borrow another scenario's value.
        target = source.replace("/normalized_request", "/effective_parameters")
        check(target, at(raw, source), ident)
    return findings, decisions, checks


def controlled_rejection(view, expected):
    error = view.get("error") or {}
    code = (expected.get("error") or {}).get("code")
    structural = expected.get("status") == "error" and code == "invalid_request" and error.get("code") in {"contract_violation", "invalid_arguments"} and "invalid" in error.get("message", "").lower()
    snapshot = expected.get("status") == "unknown" and code == "snapshot_not_found" and error.get("code") == "contract_violation" and error.get("message") == "health:unverified_requested_snapshot"
    return (structural or snapshot) and view.get("status") == "error" and bool(error.get("safe_next_action")) and not view.get("claims")


def validate_view(view, expected, labels, requirements, case):
    findings, decisions, checks = [], [], 0
    raws = expected.get("results", [expected])
    scenarios = (view.get("mobility") or {}).get("scenarios")
    if type(scenarios) is not list or not scenarios or len(scenarios) != len(raws):
        # Structurally invalid input may be safely rejected before a raw/model scenario exists.
        if controlled_rejection(view, expected):
            return [], [dict(status="NOT_APPLICABLE", reason="validated invalid-input/unverified-snapshot rejection; no computed itinerary", status_mapping={"producer": expected["status"], "consumer": "error"}, error_mapping={"producer": expected["error"]["code"], "consumer": view["error"]["code"]})], 1
        return [issue("MODEL_VIEW_MISSING", "missing/nonclosed scenario inventory")], [], 1
    for index, (scenario, raw) in enumerate(zip(scenarios, raws)):
        f, d, n = validate_scenario(scenario, raw, labels, requirements, index)
        findings.extend(f)
        decisions.extend(d)
        checks += n
    outcomes = [{"index": index, "status": raw["status"], "error": raw["error"]} for index, raw in enumerate(raws)]
    checks += 1
    if view.get("outcomes") != outcomes:
        findings.append(issue("MODEL_VIEW_WRONG_SEMANTICS", "outcomes do not bind every scenario"))
    if case["operation"] == "compare":
        comparisons = (view.get("mobility") or {}).get("comparisons")
        checks += 1
        if not expected.get("comparisons") or comparisons != expected["comparisons"]:
            findings.append(issue("COMPARISON_PARITY_FAILURE", "changed/held parameters, pair identities or delta differ"))
    # Numeric claims must agree with their concrete raw pointer, including scenario index.
    claims = view.get("claims")
    if type(claims) is not list:
        findings.append(issue("MODEL_VIEW_MISSING", "claims array absent"))
    else:
        for claim in claims:
            checks += 1
            try:
                value = at(expected, claim["evidence_path"])
            except (KeyError, TypeError, ValueError, IndexError):
                findings.append(issue("MODEL_VIEW_WRONG_VALUE", "invalid claim evidence_path", severity="critical"))
                continue
            if not equal(value, claim.get("value")):
                findings.append(issue("MODEL_VIEW_WRONG_VALUE", claim["evidence_path"], severity="critical"))
    return findings, decisions, checks


def evaluate(oracle, candidate, cases, requirements):
    records, verifier_errors = [], []
    expected_by_id = {row["case_id"]: row for row in oracle.get("records", [])}
    actual_by_id = {row["case_id"]: row for row in candidate.get("records", [])}
    for case in cases:
        row = dict(case_id=case["case_id"], operation=case["operation"], raw_status="NOT_RUN", model_status="NOT_RUN", findings=[], assertions=0)
        expected_record, actual_record = expected_by_id.get(case["case_id"]), actual_by_id.get(case["case_id"])
        if not expected_record or expected_record.get("error_stage"):
            error = issue("VERIFIER_ERROR", "missing worker/oracle result", owner="W1", stage="oracle", severity="none", case_id=case["case_id"])
            verifier_errors.append(error)
            row["findings"].append(error)
        elif not actual_record:
            if candidate.get("error_stage") == "bootstrap":
                row["model_status"] = "FAIL"
                row["findings"].append(issue("CANDIDATE_EXCEPTION", candidate.get("traceback", "bootstrap failed"), stage="bootstrap", severity="critical"))
            else:
                error = issue("VERIFIER_ERROR", candidate.get("traceback", "missing worker result"), owner="W1", stage="worker_protocol", severity="none", case_id=case["case_id"])
                verifier_errors.append(error)
                row["findings"].append(error)
        else:
            expected = expected_record["raw"]
            envelope = actual_record.get("envelope") or {}
            actual_text = envelope.get("raw_result_json")
            if actual_text is None:
                safe = controlled_rejection(envelope, expected)
                row["raw_status"] = "PASS" if safe else "FAIL"
                row["raw_binding"] = "explicit_controlled_rejection_without_numeric_evidence" if safe else "missing_raw"
            else:
                try:
                    row["raw_status"] = "PASS" if strict_json(actual_text) == expected else "FAIL"
                    row["raw_binding"] = "exact_producer_result"
                except (ValueError, TypeError):
                    row["raw_status"] = "FAIL"
                    row["raw_binding"] = "invalid_candidate_raw_json"
            if row["raw_status"] != "PASS":
                row["findings"].append(issue("RAW_PARITY_FAILURE", "raw result differs from separate frozen producer", stage="execute", severity="critical"))
            if actual_record.get("error_stage"):
                row["model_status"] = "FAIL"
                row["findings"].append(issue("CANDIDATE_EXCEPTION", actual_record["traceback"], stage=actual_record["error_stage"], severity="critical"))
            else:
                try:
                    f, decisions, count = validate_view(actual_record["view"], expected, oracle["labels"], requirements, case)
                    row.update(model_status="PASS" if not f else "FAIL", applicability=decisions, assertions=count)
                    row["findings"].extend(f)
                except Exception:
                    import traceback
                    error = issue("VERIFIER_ERROR", traceback.format_exc(), owner="W1", stage="assertions", severity="none", case_id=case["case_id"])
                    verifier_errors.append(error)
                    row["findings"].append(error)
                    row["model_status"] = "VERIFIER_ERROR"
        records.append(row)
    return records, verifier_errors


def import_closure(candidate, verified):
    problems = []
    if not candidate.get("isolated"):
        problems.append(issue("VERIFIER_ERROR", "worker is not Python isolated", owner="W1", stage="bootstrap", severity="none"))
    if "prototypes.ir_y_volver.provider_r6" not in candidate.get("import_sha256", {}):
        problems.append(issue("VERIFIER_ERROR", "frozen producer import evidence absent", owner="W1", stage="bootstrap", severity="none"))
    for name, value in candidate.get("import_sha256", {}).items():
        if name == "tools":
            if value != verified["tools_sha256"]:
                problems.append(issue("VERIFIER_ERROR", "tools import is not candidate ZIP", owner="W1", stage="bootstrap", severity="none"))
            continue
        if name == "prototypes" or name.startswith("prototypes."):
            member = name.replace(".", "/") + ("/__init__.py" if candidate["imports"][name].endswith("__init__.py") else ".py")
            if verified["runtime_hashes"].get(member) != value:
                problems.append(issue("VERIFIER_ERROR", "candidate runtime import is not nested ZIP: " + name, owner="W1", stage="bootstrap", severity="none"))
    return problems


def declared_freeze(archive):
    """Read the literal editor declaration, not a self-reported manifest claim."""
    tree = ast.parse(archive.read("main.py").decode("utf-8"))
    values = [ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == "STUDIO_CONTEXT_FILES" for target in node.targets)]
    if len(values) != 1 or type(values[0]) is not list or not values[0] or any(type(path) is not str for path in values[0]):
        raise ValueError("missing/nonliteral/nonempty STUDIO_CONTEXT_FILES")
    paths = ["main.py", "tools.py", *values[0]]
    if len(paths) != len(set(paths)) or any(path not in archive.namelist() for path in paths):
        raise ValueError("declared freeze is duplicate or references missing members")
    return paths


def intake(package, manifest_path, *, foreign_root=ROOT, extra_cases=True):
    report = {"FINAL_STATUS": "FAIL", "findings": [], "VERIFIER_ERRORS": [], "LLM_PORTAL": "NOT_RUN"}
    report["support_identity"] = {path.name: digest(path.read_bytes()) for path in (Path(__file__), WORKER, DOC / "MODEL_VIEW_REQUIREMENTS_R11.json")}
    try:
        manifest = strict_json(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        report["findings"].append(issue("MANIFEST_FAILURE", str(exc), stage="manifest", severity="critical"))
        return report
    report["identity"] = dict(package_sha256=digest(package.read_bytes()), package_bytes=package.stat().st_size,
                              manifest_sha256=digest(manifest_path.read_bytes()), source_git_sha=manifest.get("w1_runtime_commit_observed"),
                              package_sha256_w1=R6_SHA, contract=manifest.get("w1_contract"), support_sha=manifest.get("w1_support_pin"),
                              historical_pin_errata=HISTORICAL_ERRATA)
    try:
        verified = inspect(package, manifest)
    except Exception as exc:
        report["findings"].append(issue("PACKAGE_INTEGRITY_FAILURE", str(exc), stage="package", severity="critical"))
        return report
    report["integrity"] = verified
    report["findings"].extend(verified["policy"])
    if not verified["compatible"]:
        report.update(FINAL_STATUS="NOT_RUN", reason="source Git, actual nested ZIP and contract must match frozen R6")
        return report
    cases = acceptance_cases()
    if not extra_cases:
        cases = cases[:14]
    requirements = strict_json((DOC / "MODEL_VIEW_REQUIREMENTS_R11.json").read_text(encoding="utf-8"))["requirements"]
    oracle = run_worker("oracle", ROOT, cases)
    report["oracle"] = oracle
    with tempfile.TemporaryDirectory(prefix="g360-r12-") as temporary:
        directory = Path(temporary)
        with zipfile.ZipFile(package) as archive:
            archive.extractall(directory)
        candidate = run_worker("candidate", directory, cases)
        report["candidate"] = candidate
        records, errors = evaluate(oracle, candidate, cases, requirements)
        errors.extend(import_closure(candidate, verified))
        errors.extend(import_closure(oracle, verified))
        report["cases"], report["VERIFIER_ERRORS"] = records, errors
        # Reuse the original public cases on exactly the declared editor/assets
        # freeze. This is a local closure check, not portal inclusion evidence.
        try:
            frozen = directory / "declared-freeze-probe"
            frozen.mkdir()
            with zipfile.ZipFile(package) as archive:
                freeze_paths = declared_freeze(archive)
                for path in freeze_paths:
                    destination = frozen / path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(archive.read(path))
            frozen_worker = run_worker("candidate", frozen, cases[:14])
            frozen_records, frozen_errors = evaluate(oracle, frozen_worker, cases[:14], requirements)
            errors.extend(frozen_errors)
            report["declared_freeze"] = dict(paths=freeze_paths, worker=frozen_worker, cases=frozen_records,
                                             status="PASS" if frozen_records and all(row["raw_status"] == row["model_status"] == "PASS" for row in frozen_records) and not frozen_errors else "FAIL")
            if report["declared_freeze"]["status"] != "PASS":
                report["findings"].append(issue("DECLARED_FREEZE_FAILURE", "original public cases fail on exactly main.py + STUDIO_CONTEXT_FILES", stage="bootstrap/execute/public_result"))
        except Exception as exc:
            report["findings"].append(issue("DECLARED_FREEZE_FAILURE", str(exc), stage="manifest"))
        probes = [case for case in cases if case["case_id"] in {"health_defaults_omitted", "legacy_r4_explicit"}]
        report["environment_probes"] = {}
        for name, configured, explicit in (("foreign_cwd_unconfigured", None, True),
                                           ("foreign_cwd_explicit_valid_root", directory, False),
                                           ("foreign_cwd_explicit_invalid_root", directory / "nonexistent-root", False)):
            probe = run_worker("candidate", directory, probes, cwd=foreign_root, configured=configured, pass_root=explicit)
            if name.endswith("invalid_root"):
                roots = [row["root"] for rec in probe["records"] for row in rec["roots_observed"] if row["function"] == "_workspace_root"]
                probe["invalid_configuration_falls_back"] = any(Path(value).resolve() != configured.resolve() for value in roots)
                probe["controlled_error"] = len(probe["records"]) == len(probes) and all(
                    rec.get("envelope", {}).get("status") == "error" and not rec.get("envelope", {}).get("claims")
                    and rec.get("envelope", {}).get("raw_result_json") is None
                    and rec.get("view", {}).get("status") == "error" and not rec.get("view", {}).get("claims")
                    for rec in probe["records"])
                probe["classification"] = "UNSUPPORTED_ENVIRONMENT" if roots and not probe["invalid_configuration_falls_back"] and probe["controlled_error"] else "UNRESOLVED"
                if probe["classification"] == "UNRESOLVED":
                    report["findings"].append(issue("ROOT_CONFIGURATION_FAILURE", "invalid configured root is not demonstrably preserved", stage="bootstrap"))
            else:
                evaluated, verifier = evaluate(oracle, probe, probes, requirements)
                probe["evaluated"] = evaluated
                mixed_roots = any(Path(row["root"]).resolve() != directory.resolve() for rec in probe["records"] for row in rec["roots_observed"])
                probe["classification"] = "PRODUCT_DEFECT" if mixed_roots else "SUPPORTED_PACKAGE_LOCAL_ENVIRONMENT"
                if mixed_roots:
                    report["findings"].append(issue("ROOT_PROPAGATION_FAILURE", name + ": execute root and actual calculation/projection roots differ", stage="execute/public_result", environment=name))
                if name == "foreign_cwd_explicit_valid_root":
                    errors.extend(verifier)
                    report["findings"].extend({**finding, "environment": name, "case_id": row["case_id"]} for row in evaluated for finding in row["findings"])
                probe["verifier_errors"] = verifier
            report["environment_probes"][name] = probe
    for row in report["cases"]:
        report["findings"].extend({**finding, "case_id": row["case_id"]} for finding in row["findings"])
    for name, rows in (("RAW_PARITY", records), ("MODEL_VIEW_PARITY", records), ("COMPARISON_PARITY", [r for r in records if r["operation"] == "compare"])):
        key = "raw_status" if name == "RAW_PARITY" else "model_status"
        report[name] = {"status": "PASS" if rows and all(row[key] == "PASS" for row in rows) else "FAIL", "passed": sum(row[key] == "PASS" for row in rows), "total": len(rows)}
    report["counts"] = dict(plans=sum(c["operation"] == "plan" for c in cases), comparisons=sum(c["operation"] == "compare" for c in cases),
                            scenarios=sum(len(c.get("requests", [c.get("request")])) for c in cases),
                            assertions=sum(row["assertions"] for row in records), verifier_errors=len(report["VERIFIER_ERRORS"]))
    report["counts"]["declared_freeze_invocations"] = len(report.get("declared_freeze", {}).get("cases", []))
    report["counts"]["environment_probe_invocations"] = sum(len(probe.get("records", [])) for probe in report["environment_probes"].values())
    # Preserve the R11 record and explain the withdrawn ownership with a real traceback.
    from scripts.mobility.intake_candidate_r11 import validate_model_view
    import traceback
    legacy_record = next((r for r in candidate["records"] if r["case_id"] == "legacy_r4_explicit"), None)
    legacy_expected = next((r["raw"] for r in oracle["records"] if r["case_id"] == "legacy_r4_explicit"), None)
    old_verifier_trace = None
    if legacy_record and legacy_expected and legacy_record.get("view"):
        try:
            validate_model_view(legacy_record["view"], legacy_expected, requirements)
        except Exception:
            old_verifier_trace = traceback.format_exc()
    report["R11_FINDINGS_RECONCILIATION"] = {
        "health_labels": {"classification": "HARNESS_DEFECT", "owner": "W1", "evidence": "R11 mixed roots instead of testing declared isolated package mode; cold/exact-root health labels agree with effective stop IDs; alternate-root propagation defect is recorded separately"},
        "legacy_raw_failure": {"classification": "HARNESS_DEFECT", "owner": "W1", "evidence": "cold package-local legacy raw equals isolated producer; foreign cwd reaches another root during legacy validation"},
        "KeyError_transformation": {"classification": "HARNESS_DEFECT", "owner": "W1", "stage": "assertions", "traceback": old_verifier_trace},
        "legacy_health_requirements": {"classification": "HARNESS_DEFECT", "owner": "W1", "evidence": "health_destination/walking/provenance requirements now explicitly NOT_APPLICABLE to 0.2.0 stop_only"},
        "alternate_root_propagation": {"classification": report["environment_probes"]["foreign_cwd_unconfigured"]["classification"], "owner": "W2", "evidence": "actual roots recorded at execute/public_result; W2 acknowledged product ownership in Issue16 comment 5914139816; no cold-package legacy exception is inferred"},
        "remaining_findings": "see exact per-scenario findings; no blanket withdrawal or product PASS"}
    report["FINAL_STATUS"] = "VERIFIER_ERROR" if report["VERIFIER_ERRORS"] else "PASS" if not report["findings"] else "FAIL"
    return report


def exit_code(report, strict=True):
    return 0 if report["FINAL_STATUS"] == "PASS" or (report["FINAL_STATUS"] == "NOT_RUN" and not strict) else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostic", action="store_true")
    args = parser.parse_args()
    report = intake(args.package.resolve(), args.manifest.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: report.get(key) for key in ("FINAL_STATUS", "RAW_PARITY", "MODEL_VIEW_PARITY", "COMPARISON_PARITY", "counts")}))
    raise SystemExit(exit_code(report, not args.diagnostic))


if __name__ == "__main__":
    main()
