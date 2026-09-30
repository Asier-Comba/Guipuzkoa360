"""Verify semantic parity from frozen W1 producer through a concrete W2 adapter package."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from prototypes.ir_y_volver import provider_r6


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PIN = "cb061a97e78d6b5c967104fef6b935132fdc450f"
PACKAGE_SHA = "c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910"
FIELDS = ("status", "normalized_request", "itinerary", "components_s", "walking",
          "health_destination", "sources", "limitations", "assumptions", "error")
CLASSES = {"INTENDED_PROJECTION", "MISSING_REQUIRED_INFORMATION", "WRONG_VALUE", "WRONG_SEMANTICS", "NOT_RUN"}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def safe_members(archive: zipfile.ZipFile) -> list[str]:
    names = archive.namelist()
    if len(names) != len(set(names)):
        raise ValueError("duplicate package member")
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name:
            raise ValueError(f"unsafe package member: {name}")
    return names


def verify_package(package: Path, manifest: dict, expected_pin: str) -> tuple[list[str], str | None]:
    raw = package.read_bytes()
    if manifest.get("sha256") != digest(raw) or manifest.get("bytes") != len(raw):
        raise ValueError("package bytes/hash do not match manifest")
    if expected_pin != RUNTIME_PIN:
        raise ValueError("requested W1 pin is not frozen R6")
    with zipfile.ZipFile(package) as archive:
        names = safe_members(archive)
        for name, expected in manifest.get("members", {}).items():
            if name not in names:
                raise ValueError(f"manifest member missing: {name}")
            data = archive.read(name)
            if len(data) != expected["bytes"] or digest(data) != expected["sha256"]:
                raise ValueError(f"manifest member mismatch: {name}")
    raw_external = [name for name in names if name.casefold().endswith((".pdf", ".html", ".htm"))]
    return names, None if not raw_external else f"raw external documents bundled: {raw_external}"


def cases() -> list[dict]:
    conformance = json.loads((ROOT / "docs/vnext/w1/CONSUMER_CONFORMANCE_R7.json").read_text(encoding="utf-8"))
    result = []
    for row in conformance["cases"]:
        if row.get("request") is not None:
            result.append({"case_id": row["case_id"], "operation": "plan", "request": row["request"]})
        elif row.get("requests") is not None:
            result.append({"case_id": row["case_id"], "operation": "compare", "requests": row["requests"]})
    return result


def load_adapter(directory: Path):
    path = directory / "mobility_adapter.py"
    if not path.is_file():
        raise ValueError("mobility_adapter.py missing")
    prior_path = list(sys.path)
    prior_modules = {name: module for name, module in sys.modules.items()
                     if name == "tools" or name == "mobility_adapter"}
    for name in prior_modules:
        del sys.modules[name]
    sys.path.insert(0, str(directory))
    try:
        spec = importlib.util.spec_from_file_location("mobility_adapter", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["mobility_adapter"] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module, prior_path, prior_modules
    except Exception:
        sys.path[:] = prior_path
        sys.modules.pop("mobility_adapter", None)
        sys.modules.update(prior_modules)
        raise


def unload_adapter(prior_path: list[str], prior_modules: dict) -> None:
    sys.path[:] = prior_path
    for name in ("mobility_adapter", "tools"):
        sys.modules.pop(name, None)
    sys.modules.update(prior_modules)


def raw_from_envelope(envelope: dict) -> dict | None:
    value = envelope.get("raw_result_json")
    return json.loads(value) if isinstance(value, str) else None


def differences(expected: dict, actual: dict) -> list[dict]:
    result = []
    for field in FIELDS:
        if expected.get(field) != actual.get(field):
            result.append({"field": field, "classification": "WRONG_VALUE",
                           "expected": expected.get(field), "actual": actual.get(field)})
    return result


def model_view_gaps(envelope: dict, raw: dict) -> list[dict]:
    gaps = []
    outcomes = envelope.get("outcomes")
    if not isinstance(outcomes, list) or not outcomes or outcomes[0].get("status") != raw["status"]:
        gaps.append({"field": "outcomes.status", "classification": "WRONG_SEMANTICS"})
    if raw["status"] == "ok":
        claims = envelope.get("claims") if isinstance(envelope.get("claims"), list) else []
        values = {claim.get("evidence_path"): claim.get("value") for claim in claims}
        required = {"/itinerary/total_s": raw["itinerary"]["total_s"]}
        required.update({f"/components_s/{key}": value for key, value in raw["components_s"].items()})
        for pointer, value in required.items():
            if values.get(pointer) != value:
                gaps.append({"field": pointer, "classification": "MISSING_REQUIRED_INFORMATION",
                             "expected": value, "actual": values.get(pointer)})
    if not isinstance(envelope.get("limitations"), list) or not isinstance(envelope.get("assumptions"), list):
        gaps.append({"field": "limitations_or_assumptions", "classification": "MISSING_REQUIRED_INFORMATION"})
    return gaps


def run(package: Path, manifest_path: Path, w1_pin: str) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    names, distribution_problem = verify_package(package, manifest, w1_pin)
    identity = {"package": package.name, "bytes": package.stat().st_size, "sha256": digest(package.read_bytes()),
                "manifest": manifest_path.name, "w1_pin_requested": w1_pin,
                "w1_runtime_package_sha256": PACKAGE_SHA, "package_w1_pin": manifest.get("w1_pin"),
                "package_w1_contract": manifest.get("w1_contract")}
    if manifest.get("w1_pin") != w1_pin or manifest.get("w1_contract") != "0.3.1":
        return {"status": "NOT_RUN", "reason": "candidate does not pin frozen W1 R6 contract 0.3.1",
                "identity": identity, "distribution_problem": distribution_problem, "cases": [],
                "classifications": {"NOT_RUN": 1}, "candidate_package_tested": False}
    findings = []
    with tempfile.TemporaryDirectory(prefix="g360-r10-parity-") as temporary:
        directory = Path(temporary)
        with zipfile.ZipFile(package) as archive:
            archive.extractall(directory)
        adapter, prior_path, prior_modules = load_adapter(directory)
        try:
            if not hasattr(adapter, "consume_plan_visit") or not hasattr(adapter, "consume_compare_visits"):
                return {"status": "FAIL", "reason": "candidate adapter lacks required real interfaces",
                        "identity": identity, "distribution_problem": distribution_problem, "cases": [],
                        "classifications": {"MISSING_REQUIRED_INFORMATION": 1}, "candidate_package_tested": True}
            for item in cases():
                record = {"case_id": item["case_id"], "operation": item["operation"], "findings": []}
                expected = None
                try:
                    if item["operation"] == "plan":
                        expected = provider_r6.plan_visit(item["request"])
                        envelope = adapter.consume_plan_visit(provider_r6, item["request"], f"R10_{item['case_id']}")
                        actual = raw_from_envelope(envelope)
                        if actual is None:
                            record["findings"].append({"field": "raw_result_json", "classification": "MISSING_REQUIRED_INFORMATION"})
                        else:
                            record["findings"] += differences(expected, actual)
                            record["findings"] += model_view_gaps(envelope, actual)
                    else:
                        expected = provider_r6.compare_visits(item["requests"])
                        envelope = adapter.consume_compare_visits(provider_r6, item["requests"], f"R10_{item['case_id']}")
                        actual = raw_from_envelope(envelope)
                        if actual is None:
                            record["findings"].append({"field": "raw_result_json", "classification": "MISSING_REQUIRED_INFORMATION"})
                        elif expected != actual:
                            record["findings"].append({"field": "comparison", "classification": "WRONG_VALUE"})
                except Exception as exc:
                    expected_status = expected.get("status") if isinstance(expected, dict) else None
                    record["findings"].append({"field": "adapter_exception", "classification":
                        "INTENDED_PROJECTION" if expected_status == "error" else "MISSING_REQUIRED_INFORMATION",
                        "type": type(exc).__name__, "message": str(exc)})
                record["status"] = "PASS" if not [f for f in record["findings"] if f["classification"] != "INTENDED_PROJECTION"] else "FAIL"
                findings.append(record)
        finally:
            unload_adapter(prior_path, prior_modules)
    counts = {name: 0 for name in sorted(CLASSES)}
    for record in findings:
        for finding in record["findings"]:
            counts[finding["classification"]] += 1
    if distribution_problem:
        counts["WRONG_SEMANTICS"] += 1
    status = "PASS" if all(record["status"] == "PASS" for record in findings) and not distribution_problem else "FAIL"
    return {"status": status, "identity": identity, "distribution_problem": distribution_problem,
            "candidate_package_tested": True, "cases": findings, "classifications": counts,
            "scope": "producer-to-adapter tool parity; not W3 independent acceptance or a real LLM conversation"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--w1-pin", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = run(args.package, args.manifest, args.w1_pin)
    except Exception as exc:
        report = {"status": "FAIL", "candidate_package_tested": False,
                  "classifications": {"WRONG_VALUE": 1}, "error": {"type": type(exc).__name__, "message": str(exc)}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "output": str(args.output)}))
    raise SystemExit(0 if report["status"] in {"PASS", "NOT_RUN"} else 1)


if __name__ == "__main__":
    main()
