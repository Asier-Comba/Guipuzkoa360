"""R13 bounded-batch reconfirmation with the frozen R12 checks/worker."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import time
import zipfile

from scripts.mobility import intake_candidate_r12 as gate


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def batched(mode, root, cases, size=4, **kwargs):
    combined = {"records": [], "batches": []}
    for offset in range(0, len(cases), size):
        started = time.perf_counter()
        report = gate.run_worker(mode, root, cases[offset:offset + size], **kwargs)
        print(json.dumps({"mode": mode, "batch_offset": offset, "cases": len(report.get("records", [])), "elapsed_s": round(time.perf_counter() - started, 3)}), flush=True)
        if report.get("error_stage") or len(report.get("records", [])) != len(cases[offset:offset + size]):
            raise RuntimeError("R13 worker protocol failure: " + str(report.get("traceback", report)))
        combined["records"].extend(report["records"])
        combined["batches"].append({key: value for key, value in report.items() if key != "records"})
        if mode == "oracle":
            combined["labels"] = report["labels"]
    return combined


def parity(package, manifest_path):
    start = time.perf_counter()
    manifest = gate.strict_json(manifest_path.read_text(encoding="utf-8"))
    verified = gate.inspect(package, manifest)
    assert verified["compatible"] and not verified["policy"]
    cases = gate.acceptance_cases()
    requirements = gate.strict_json((gate.DOC / "MODEL_VIEW_REQUIREMENTS_R11.json").read_text(encoding="utf-8"))["requirements"]
    oracle = batched("oracle", gate.ROOT, cases)
    with tempfile.TemporaryDirectory(prefix="g360-r13-parity-") as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(package) as archive:
            archive.extractall(root)
        actual = batched("candidate", root, cases)
        records, errors = gate.evaluate(oracle, actual, cases, requirements)
        for batch in (*oracle["batches"], *actual["batches"]):
            errors.extend(gate.import_closure(batch, verified))
        frozen = root / "declared-freeze"
        with zipfile.ZipFile(package) as archive:
            paths = gate.declared_freeze(archive)
            for name in paths:
                path = frozen / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.read(name))
        freeze_worker = batched("candidate", frozen, cases[:14])
        freeze_records, freeze_errors = gate.evaluate(oracle, freeze_worker, cases[:14], requirements)
        errors.extend(freeze_errors)
        for batch in freeze_worker["batches"]:
            errors.extend(gate.import_closure(batch, verified))
        probes = [case for case in cases if case["case_id"] in {"health_defaults_omitted", "legacy_r4_explicit"}]
        environments = {}
        for name, configured, pass_root in (("foreign_cwd", None, True), ("valid_root", root, False), ("invalid_root", root / "absent", False)):
            probe = gate.run_worker("candidate", root, probes, cwd=gate.ROOT, configured=configured, pass_root=pass_root)
            assert len(probe.get("records", [])) == 2 and not probe.get("error_stage"), "probe protocol"
            if name == "invalid_root":
                roots = [Path(row["root"]).resolve() for r in probe["records"] for row in r["roots_observed"] if row["function"] == "_workspace_root"]
                assert roots and all(value == configured.resolve() for value in roots), "invalid-root fallback"
                assert all(r["envelope"]["status"] == r["view"]["status"] == "error" and not r["envelope"]["claims"] and not r["view"]["claims"] and r["envelope"].get("raw_result_json") is None for r in probe["records"])
                probe["verdict"] = "CONTROLLED_REJECTION_NO_FALLBACK"
            else:
                checked, probe_errors = gate.evaluate(oracle, probe, probes, requirements)
                errors.extend(probe_errors)
                assert all(row["raw_status"] == row["model_status"] == "PASS" for row in checked), "environment parity"
                roots = [Path(row["root"]).resolve() for r in probe["records"] for row in r["roots_observed"]]
                assert roots and all(value == root.resolve() for value in roots), "mixed roots"
                probe["evaluated"] = checked
                probe["verdict"] = "PASS"
            environments[name] = probe
    findings = [finding for row in records + freeze_records for finding in row["findings"]]
    passed = not errors and not findings and all(r["raw_status"] == r["model_status"] == "PASS" for r in records + freeze_records)
    return dict(status="PASS" if passed else "FAIL", runtime_s=round(time.perf_counter() - start, 3),
                package_sha256=gate.digest(package.read_bytes()), manifest_sha256=gate.digest(manifest_path.read_bytes()),
                integrity=verified, raw=sum(r["raw_status"] == "PASS" for r in records), model_view=sum(r["model_status"] == "PASS" for r in records),
                comparisons=sum(r["operation"] == "compare" and r["model_status"] == "PASS" for r in records), scenarios=37,
                assertions=sum(r["assertions"] for r in records), verifier_errors=errors, findings=findings,
                batching=dict(size=4, reason="Original 32-case traced worker exceeded unchanged 300-second protocol timeout; no acceptance assertion or candidate byte changed.",
                              limitation="Cold reset at batch boundaries; A-B-A isolation is separately checked inside expanded metamorphic calls."),
                records=records, oracle=oracle, candidate=actual, declared_freeze=dict(paths=paths, records=freeze_records, worker=freeze_worker, status="PASS" if all(r["raw_status"] == r["model_status"] == "PASS" for r in freeze_records) else "FAIL"),
                environment_probes=environments,
                support_identity={path.name: gate.digest(path.read_bytes()) for path in (Path(__file__), gate.WORKER, Path(gate.__file__), gate.DOC / "MODEL_VIEW_REQUIREMENTS_R11.json")},
                llm="NOT_CLAIMED", portal="NOT_CLAIMED")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = parity(args.package.resolve(), args.manifest.resolve())
    dump(args.output, report)
    print(json.dumps({key: report[key] for key in ("status", "raw", "model_view", "comparisons", "scenarios", "assertions", "runtime_s")}))
    raise SystemExit(0 if report["status"] == "PASS" else 1)
