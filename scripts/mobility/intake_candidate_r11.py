"""Single-command R11 intake for a concrete W2 candidate package.

The gate imports the package's real adapter and calls its real ``tools.public_result``.
It never rewrites or rebuilds the candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from prototypes.ir_y_volver import provider_r6
from scripts.mobility.verify_candidate_parity_r10 import cases, differences, raw_from_envelope


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PIN = "cb061a97e78d6b5c967104fef6b935132fdc450f"
RUNTIME_PACKAGE_SHA = "c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910"
CONTRACT = "0.3.1"
REQUIREMENTS = ROOT / "docs/vnext/w1/MODEL_VIEW_REQUIREMENTS_R11.json"
FAILURE_CATALOG = {
    "PACKAGE_INTEGRITY_FAILURE": ("critical", "W2", "Package bytes/members", "Rebuild and publish a matching package+manifest."),
    "MANIFEST_FAILURE": ("critical", "W2", "Candidate manifest", "Publish a valid manifest for the exact ZIP."),
    "INCOMPATIBLE_W1_PIN": ("high", "W2", "w1_pin and w1_contract", "Consume frozen W1 R6 and publish a new candidate."),
    "ADAPTER_IMPORT_FAILURE": ("critical", "W2", "Extracted package import", "Repair package-local imports without depending on the checkout."),
    "PRODUCER_ADAPTER_PARITY_FAILURE": ("critical", "W2", "W1 raw result versus adapter raw_result_json", "Preserve the exact producer facts or explicitly reject the case."),
    "MODEL_VIEW_MISSING": ("high", "W2", "tools.public_result(envelope)", "Expose the required verified fact to the model."),
    "MODEL_VIEW_WRONG_VALUE": ("critical", "W2", "tools.public_result(envelope)", "Bind the projected value to the producer evidence."),
    "MODEL_VIEW_WRONG_SEMANTICS": ("critical", "W2", "tools.public_result(envelope)", "Preserve scope, caveats, error meaning and provenance."),
    "DISTRIBUTION_POLICY_FAILURE": ("high", "W2/human owner", "ZIP member inventory", "Remove raw third-party documents or record explicit redistribution authorization."),
    "NOT_RUN": ("none", "W2", "Candidate compatibility precondition", "Publish DEPLOYABLE_PACKAGE_READY pinned to W1 R6."),
}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def finding(category: str, detail: str, **extra: Any) -> dict:
    severity, owner, evidence, safe_next = FAILURE_CATALOG[category]
    return {"category": category, "severity": severity, "owner": owner, "evidence": evidence,
            "detail": detail, "safe_next_action": safe_next, **extra}


def load_manifest(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"manifest cannot be parsed: {exc}") from exc
    if type(value) is not dict:
        raise ValueError("manifest root must be an object")
    return value


def inspect_package(package: Path, manifest: dict) -> tuple[list[str], list[dict]]:
    raw = package.read_bytes()
    if manifest.get("sha256") != digest(raw) or manifest.get("bytes") != len(raw):
        raise ValueError("package bytes/hash do not match manifest")
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate package member")
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name:
                raise ValueError(f"unsafe package member: {name}")
        for name, expected in manifest.get("members", {}).items():
            if name not in names:
                raise ValueError(f"manifest member missing: {name}")
            data = archive.read(name)
            if expected.get("bytes") != len(data) or expected.get("sha256") != digest(data):
                raise ValueError(f"manifest member mismatch: {name}")
    authorized = set(manifest.get("authorized_raw_evidence", []))
    raw_documents = [name for name in names if name.casefold().endswith((".pdf", ".html", ".htm"))]
    policy = [finding("DISTRIBUTION_POLICY_FAILURE", f"raw external document lacks explicit authorization: {name}", member=name)
              for name in raw_documents if name not in authorized]
    return names, policy


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_candidate(directory: Path):
    tools_path = directory / "tools.py"
    adapter_path = directory / "mobility_adapter.py"
    if not tools_path.is_file() or not adapter_path.is_file():
        raise ImportError("tools.py and mobility_adapter.py are required at package root")
    prior_path = list(sys.path)
    prior_modules = {name: sys.modules.get(name) for name in ("tools", "mobility_adapter")}
    for name in prior_modules:
        sys.modules.pop(name, None)
    sys.path.insert(0, str(directory))
    try:
        tools = _load_module("tools", tools_path)
        adapter = _load_module("mobility_adapter", adapter_path)
        if not callable(getattr(tools, "public_result", None)):
            raise ImportError("tools.public_result is missing")
        if not callable(getattr(adapter, "consume_plan_visit", None)) or not callable(getattr(adapter, "consume_compare_visits", None)):
            raise ImportError("candidate adapter interfaces are missing")
        return tools, adapter, prior_path, prior_modules
    except Exception:
        unload_candidate(prior_path, prior_modules)
        raise


def unload_candidate(prior_path: list[str], prior_modules: dict) -> None:
    sys.path[:] = prior_path
    for name in ("mobility_adapter", "tools"):
        sys.modules.pop(name, None)
        if prior_modules.get(name) is not None:
            sys.modules[name] = prior_modules[name]


def flatten(value: Any, path: str = "") -> list[tuple[str, Any]]:
    rows = [(path or "/", value)]
    if type(value) is dict:
        for key, child in value.items():
            rows.extend(flatten(child, f"{path}/{key}"))
    elif type(value) is list:
        for index, child in enumerate(value):
            rows.extend(flatten(child, f"{path}/{index}"))
    return rows


def pointer(value: Any, path: str) -> Any:
    current = value
    for token in path.strip("/").split("/") if path != "/" else []:
        current = current[int(token)] if type(current) is list else current[token]
    return current


def expected_value(requirement: dict, raw: dict) -> Any:
    if requirement["requirement_id"] == "MV-SOURCES":
        return [row["source_id"] for row in raw.get("sources", [])]
    source = requirement["source_path"]
    if source.startswith("/"):
        return pointer(raw, source)
    return requirement.get("expected_value")


def values_match(expected: Any, actual: Any) -> bool:
    if type(expected) in (dict, list):
        return actual == expected
    return type(actual) is type(expected) and actual == expected


def projected(view: dict, requirement: dict, expected: Any) -> bool:
    rows = flatten(view)
    if requirement["requirement_id"] == "MV-SOURCES":
        source_values = [value for path, value in rows if ("/sources/" in path and path.endswith("/source_id")) or
                         ("/claims/" in path and (path.endswith("/source_ids") or path.endswith("/source_refs")))]
        return all(any(values_match(source, value) or (type(value) is list and source in value) for value in source_values) for source in expected)
    if requirement["requirement_id"] == "MV-PROVENANCE":
        args = (view.get("normalized_input") or {}).get("arguments")
        effective = view.get("effective_request") or {}
        return type(args) is dict and type(effective) is dict and (
            type(effective.get("defaults_applied")) is list or type(effective.get("parameters")) is dict)
    if type(expected) in (dict, list) and any(values_match(expected, value) for _, value in rows):
        return True
    source = requirement["source_path"]
    for path, value in rows:
        if not values_match(expected, value):
            continue
        compact = "/".join(part for part in path.strip("/").split("/") if not part.isdigit())
        for allowed in requirement["allowed_projection"]:
            if allowed == "claims.value":
                continue
            suffix = allowed.replace(".", "/")
            if compact.endswith(suffix):
                return True
    for _, value in rows:
        if type(value) is dict and value.get("evidence_path") == source and values_match(expected, value.get("value")):
            return True
    return False


def validate_caller_provenance(view: dict, raw: dict) -> list[dict]:
    args = (view.get("normalized_input") or {}).get("arguments")
    effective = view.get("effective_request") or {}
    defaults = effective.get("defaults_applied")
    if type(args) is not dict or type(defaults) is not list:
        return [finding("MODEL_VIEW_MISSING", "caller/default provenance cannot be reconstructed", requirement_id="MV-PROVENANCE")]
    gaps = []
    for row in raw.get("parameter_provenance", []):
        field = row["field"]
        if row["origin"] == "human_explicit" and field not in args:
            gaps.append(finding("MODEL_VIEW_WRONG_SEMANTICS", f"caller-supplied field lost: {field}", requirement_id="MV-PROVENANCE"))
        if row["origin"] == "model_default" and (field in args or field not in defaults):
            gaps.append(finding("MODEL_VIEW_WRONG_SEMANTICS", f"default-applied field misclassified: {field}", requirement_id="MV-PROVENANCE"))
    rendered = json.dumps(view, ensure_ascii=False).casefold()
    forbidden = ("human-authored", "human authored", "escrito por una persona", "elegido por el humano")
    if any(token in rendered for token in forbidden):
        gaps.append(finding("MODEL_VIEW_WRONG_SEMANTICS", "caller-supplied was converted into human-authored", requirement_id="MV-PROVENANCE"))
    return gaps


def validate_model_view(view: dict, raw: dict, requirements: list[dict]) -> list[dict]:
    gaps = []
    status = raw.get("status")
    if status != "ok":
        error = view.get("error")
        observed_code = (raw.get("error") or {}).get("code")
        text = json.dumps(view, ensure_ascii=False).casefold()
        safe = type(error) is dict and error.get("code") == observed_code and bool(error.get("safe_next_action") or error.get("message"))
        if not safe:
            gaps.append(finding("MODEL_VIEW_WRONG_SEMANTICS", "failure view does not preserve observed status+error.code and a safe explanation",
                                requirement_id="MV-FAILURE", expected_error_code=observed_code))
        if status not in text:
            gaps.append(finding("MODEL_VIEW_MISSING", "producer status absent from failure view", requirement_id="MV-STATUS"))
        return gaps
    for requirement in requirements:
        if requirement["applicability"] not in {"all", "ok"}:
            continue
        semantic = requirement.get("semantic_match_any")
        if semantic:
            rendered = json.dumps(view, ensure_ascii=False).casefold()
            if not any(token.casefold() in rendered for token in semantic):
                gaps.append(finding("MODEL_VIEW_WRONG_SEMANTICS", requirement["forbidden_omission"], requirement_id=requirement["requirement_id"]))
            continue
        expected = expected_value(requirement, raw)
        if not projected(view, requirement, expected):
            gaps.append(finding("MODEL_VIEW_MISSING", requirement["forbidden_omission"], requirement_id=requirement["requirement_id"], expected=expected))
    gaps.extend(validate_caller_provenance(view, raw))
    return gaps


def classify_mutated_view(view: dict, raw: dict, requirements: list[dict]) -> list[dict]:
    """Public helper used by mutation regressions; correct totals cannot mask wrong identity."""
    return validate_model_view(view, raw, requirements)


def intake(package: Path, manifest_path: Path, expected_pin: str, *, strict: bool) -> dict:
    report = {"CANDIDATE_IDENTITY": {}, "PACKAGE_INTEGRITY": {}, "W1_PIN_STATUS": {}, "RAW_PARITY": {},
              "MODEL_VIEW_PARITY": {}, "SOURCE_POLICY": {}, "SEMANTIC_LIMITS": {}, "FINAL_STATUS": "FAIL",
              "mode": "strict" if strict else "diagnostic", "findings": []}
    try:
        manifest = load_manifest(manifest_path)
    except Exception as exc:
        report["findings"].append(finding("MANIFEST_FAILURE", str(exc)))
        report["PACKAGE_INTEGRITY"] = {"status": "NOT_RUN"}
        return report
    package_raw = package.read_bytes() if package.is_file() else b""
    report["CANDIDATE_IDENTITY"] = {"package": package.name, "bytes": len(package_raw), "sha256": digest(package_raw),
                                    "manifest": manifest_path.name, "expected_w1_pin": expected_pin,
                                    "package_w1_pin": manifest.get("w1_pin"), "package_w1_contract": manifest.get("w1_contract")}
    try:
        names, policy = inspect_package(package, manifest)
        report["PACKAGE_INTEGRITY"] = {"status": "PASS", "members": len(names)}
        report["SOURCE_POLICY"] = {"status": "PASS" if not policy else "FAIL", "findings": policy}
        report["findings"].extend(policy)
    except Exception as exc:
        report["PACKAGE_INTEGRITY"] = {"status": "FAIL"}
        report["SOURCE_POLICY"] = {"status": "NOT_RUN"}
        report["findings"].append(finding("PACKAGE_INTEGRITY_FAILURE", str(exc)))
        return report
    compatible = expected_pin == RUNTIME_PIN and manifest.get("w1_pin") == expected_pin and manifest.get("w1_contract") == CONTRACT
    report["W1_PIN_STATUS"] = {"status": "PASS" if compatible else "INCOMPATIBLE", "required_contract": CONTRACT,
                               "frozen_runtime_package_sha256": RUNTIME_PACKAGE_SHA}
    if not compatible:
        report["findings"].append(finding("INCOMPATIBLE_W1_PIN", "candidate does not pin frozen W1 R6 contract 0.3.1"))
        report["findings"].append(finding("NOT_RUN", "producer/adapter/model-view parity requires a compatible candidate"))
        report["RAW_PARITY"] = {"status": "NOT_RUN", "cases": []}
        report["MODEL_VIEW_PARITY"] = {"status": "NOT_RUN", "cases": []}
        report["SEMANTIC_LIMITS"] = {"scope": "No compatibility claim; package identity and distribution were inspected only."}
        report["FINAL_STATUS"] = "NOT_RUN"
        return report
    requirements = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))["requirements"]
    raw_cases, model_cases = [], []
    with tempfile.TemporaryDirectory(prefix="g360-r11-intake-") as temporary:
        directory = Path(temporary)
        with zipfile.ZipFile(package) as archive:
            archive.extractall(directory)
        try:
            tools, adapter, prior_path, prior_modules = load_candidate(directory)
        except Exception as exc:
            report["findings"].append(finding("ADAPTER_IMPORT_FAILURE", f"{type(exc).__name__}: {exc}"))
            report["RAW_PARITY"] = {"status": "NOT_RUN", "cases": []}
            report["MODEL_VIEW_PARITY"] = {"status": "NOT_RUN", "cases": []}
            return report
        try:
            for case in cases():
                raw_record = {"case_id": case["case_id"], "findings": []}
                model_record = {"case_id": case["case_id"], "findings": []}
                try:
                    if case["operation"] == "plan":
                        expected = provider_r6.plan_visit(case["request"])
                        envelope = adapter.consume_plan_visit(provider_r6, case["request"], f"R11_{case['case_id']}")
                    else:
                        expected = provider_r6.compare_visits(case["requests"])
                        envelope = adapter.consume_compare_visits(provider_r6, case["requests"], f"R11_{case['case_id']}")
                    actual = raw_from_envelope(envelope)
                    if actual is None:
                        raw_record["findings"].append(finding("PRODUCER_ADAPTER_PARITY_FAILURE", "raw_result_json missing"))
                    elif case["operation"] == "compare":
                        if actual != expected:
                            raw_record["findings"].append(finding("PRODUCER_ADAPTER_PARITY_FAILURE", "comparison raw result differs"))
                    else:
                        for diff in differences(expected, actual):
                            raw_record["findings"].append(finding("PRODUCER_ADAPTER_PARITY_FAILURE", f"raw field differs: {diff['field']}", expected=diff.get("expected"), actual=diff.get("actual")))
                    rendered = tools.public_result(envelope)
                    if type(rendered) is not str:
                        raise TypeError("tools.public_result did not return a string")
                    view = tools.strict_loads(rendered) if callable(getattr(tools, "strict_loads", None)) else json.loads(rendered)
                    if type(view) is not dict:
                        raise TypeError("public model view is not an object")
                    if actual is not None:
                        if case["operation"] == "plan":
                            model_record["findings"].extend(validate_model_view(view, actual, requirements))
                        elif not isinstance(view.get("outcomes"), list):
                            model_record["findings"].append(finding("MODEL_VIEW_MISSING", "comparison outcomes absent"))
                except Exception as exc:
                    model_record["findings"].append(finding("MODEL_VIEW_WRONG_VALUE", f"{type(exc).__name__}: {exc}"))
                raw_record["status"] = "PASS" if not raw_record["findings"] else "FAIL"
                model_record["status"] = "PASS" if not model_record["findings"] else "FAIL"
                raw_cases.append(raw_record)
                model_cases.append(model_record)
        finally:
            unload_candidate(prior_path, prior_modules)
    for record in raw_cases + model_cases:
        report["findings"].extend(record["findings"])
    report["RAW_PARITY"] = {"status": "PASS" if all(row["status"] == "PASS" for row in raw_cases) else "FAIL", "cases": raw_cases}
    report["MODEL_VIEW_PARITY"] = {"status": "PASS" if all(row["status"] == "PASS" for row in model_cases) else "FAIL", "cases": model_cases,
                                   "projection_function": "tools.public_result"}
    report["SEMANTIC_LIMITS"] = {"scope": "scheduled modelled health journey; not realtime, appointment availability, verified entrance or universal accessibility",
                                 "independent_llm_acceptance": "NOT_RUN"}
    report["FINAL_STATUS"] = "PASS" if not report["findings"] else "FAIL"
    return report


def exit_code(report: dict, strict: bool) -> int:
    if report["FINAL_STATUS"] == "PASS":
        return 0
    if report["FINAL_STATUS"] == "NOT_RUN" and not strict:
        return 0
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect an immutable W2 candidate and its exact public model view.")
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--expected-w1-pin", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--mode", choices=("diagnostic", "strict"), default="diagnostic")
    parser.add_argument("--require-compatible-candidate", action="store_true")
    args = parser.parse_args()
    strict = args.require_compatible_candidate or args.mode == "strict"
    report = intake(args.package, args.manifest, args.expected_w1_pin, strict=strict)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "candidate_intake_r11.json"
    output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"FINAL_STATUS": report["FINAL_STATUS"], "mode": "strict" if strict else "diagnostic", "output": str(output)}, allow_nan=False))
    raise SystemExit(exit_code(report, strict))


if __name__ == "__main__":
    main()
