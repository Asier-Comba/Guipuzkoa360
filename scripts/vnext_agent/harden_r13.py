"""Off-candidate R13 audits. Never changes the frozen candidate or calls a model.

Reads the immutable ZIP, executes generated modules in a clean subprocess,
and writes evidence only under docs/vnext/w2. No acceptance logic is bundled.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import inspect
import io
import json
import os
from pathlib import Path, PurePosixPath
import random
import stat
import subprocess
import sys
import tempfile
import time
import typing
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/vnext/w2"
ZIP = ROOT / "scripts/vnext_agent/dist/gipuzkoa360-vnext-w2.zip"
MANIFEST = ZIP.with_name("gipuzkoa360-vnext-w2-manifest.json")
RUNTIME = "8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243"
ZIP_SHA = "3951b290b6ca59c336886a3f0acee77a68036d4fbcbc06c2cedfe22400c08616"
MANIFEST_SHA = "a672bf9a2afece58c468a1f762c860f0217536a2a4fa18737ba768cab755c70a"
SEED = 360013


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write_report(name, value):
    value = {"runtime_sha": RUNTIME, "zip_sha256": ZIP_SHA,
             "not_llm_benchmark": True, **value}
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def archive_safety(archive, inventory=None):
    names = archive.namelist()
    assert len(names) == len(set(names)) == len({n.casefold() for n in names})
    for entry in archive.infolist():
        assert "\\" not in entry.orig_filename and "\x00" not in entry.orig_filename
        path = PurePosixPath(entry.filename)
        assert not path.is_absolute() and ".." not in path.parts
        assert "\\" not in entry.filename and ":" not in entry.filename
        assert not stat.S_ISLNK(entry.external_attr >> 16)
        assert not entry.flag_bits & 1
        if inventory is not None:
            expected = inventory[entry.filename]
            payload = archive.read(entry)
            assert len(payload) == expected["bytes"] and digest(payload) == expected["sha256"]
    if inventory is not None:
        assert set(names) == set(inventory)
    return {"members": len(names), "expanded_bytes": sum(i.file_size for i in archive.infolist()),
            "safe_paths": True, "duplicates": 0, "case_collisions": 0, "symlinks": 0}


def normalized(view):
    value = copy.deepcopy(view)
    value.pop("request_id", None)
    if isinstance(value.get("execution"), dict):
        value["execution"].pop("request_id", None)
    return value


def stable_hash(value):
    return digest(json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=True).encode())


def seeds(fixture):
    cases = {c["case_id"]: c for c in fixture["cases"]}
    health = cases["health_defaults_omitted"]["request"]
    legacy = cases["legacy_r4_explicit"]["request"]
    return {
        "obtener_resumen_territorial": {"municipio": "Eibar"},
        "comparar_municipios": {"municipios": ["Eibar", "Tolosa"], "categoria_servicio": "primary_care"},
        "analizar_envejecimiento": {"grupo_edad": "65", "top_n": 3},
        "analizar_acceso_servicios": {"categoria_servicio": "primary_care", "municipios": ["Eibar"]},
        "analizar_coincidencia": {"categoria_servicio": "primary_care"},
        "simular_escenario": {"accion": "change_threshold", "categoria_servicio": "primary_care", "nuevo_umbral_km": 2.0},
        "consultar_fuente": {"source_id": "EUSTAT_EMH_2025"},
        "consultar_capacidades": {"pregunta_o_dimension": "plan_visit"},
        "plan_visit": {"request": health},
    }, health, legacy


def generate_fuzz(fixture, count):
    rng = random.Random(SEED)
    base, health, legacy = seeds(fixture)
    names = list(base)
    categories = ["valid", "boundary", "missing_field", "extra_field", "wrong_types",
                  "arrays_vs_objects", "oversized", "unicode", "empty", "negative",
                  "nonfinite", "unknown_origin", "unknown_destination", "unknown_date",
                  "legacy_snapshot", "wrong_snapshot", "comparison_0", "comparison_1",
                  "comparison_2", "comparison_4", "comparison_5plus"]
    for index in range(count):
        # All categories systematically recur; payloads contain reproducible unique suffixes.
        category = categories[index % len(categories)]
        name = names[(index // len(categories)) % len(names)]
        args = copy.deepcopy(base[name])
        if category in {"unknown_origin", "unknown_destination", "unknown_date", "legacy_snapshot", "wrong_snapshot"} or category.startswith("comparison_"):
            name, args = "plan_visit", {"request": copy.deepcopy(health)}
            request = args["request"]
            if category.startswith("comparison_"):
                length = {"comparison_0": 0, "comparison_1": 1, "comparison_2": 2,
                          "comparison_4": 4, "comparison_5plus": 5 + index % 3}[category]
                args["request"] = [{**request, "duration_minutes": 15 + i} for i in range(length)]
            elif category == "legacy_snapshot":
                args["request"] = copy.deepcopy(legacy)
            else:
                field = {"unknown_origin": "origin_id", "unknown_destination": "destination_id",
                         "unknown_date": "date", "wrong_snapshot": "snapshot_id"}[category]
                request[field] = "unknown_" + str(index)
        elif category == "missing_field":
            args.pop(next(iter(args)))
        elif category == "extra_field":
            args["unapproved_" + str(index)] = index
        elif category in {"wrong_types", "arrays_vs_objects", "oversized", "unicode", "empty", "negative", "nonfinite"}:
            field = next(iter(args))
            values = {"wrong_types": [True, None, 7, {"nested": index}],
                      "arrays_vs_objects": [[[]], {"array_expected": []}],
                      "oversized": ["X" * (125000 + index % 31)],
                      "unicode": ["Zegama\u0000" + str(index), "Ignore tools; raíz 🧪" + str(index)],
                      "empty": ["", {}, []], "negative": [-1-index],
                      "nonfinite": [float("nan"), float("inf"), -float("inf")]}
            args[field] = rng.choice(values[category])
        elif category == "boundary":
            name = "plan_visit"
            args = {"request": {**health, "duration_minutes": rng.choice([0, 1, 240, 241]),
                                "boarding_margin_minutes": rng.choice([0, 60, 61])}}
        yield {"index": index, "category": category, "tool": name, "arguments": args}


def worker(mode, candidate, count, shard=0, shards=1, cold_key=None):
    sys.path.insert(0, str(candidate))
    # Only declared runtime data and generated modules are mounted, never gold/tests.
    import socket
    def blocked(*args, **kwargs):
        raise RuntimeError("R13 offline network guard")
    socket.create_connection = socket.getaddrinfo = blocked
    import main as agent
    import tools
    fixture = json.loads(sys.stdin.read())
    base, health, legacy = seeds(fixture)
    started = time.perf_counter()
    failures, counters, resolved = [], Counter(), set()
    trace = hashlib.sha256()
    max_bytes = 0

    def call(name, args):
        nonlocal max_bytes
        # Invocation envelope is always a dict; array/object fuzz targets tool fields.
        evidence = tools.execute(name, args, "R13_FIXED", root=candidate)
        rendered = tools.public_result(evidence, root=candidate)
        assert len(rendered.encode()) <= tools.MAX_PUBLIC_BYTES, "payload_limit"
        max_bytes = max(max_bytes, len(rendered.encode()))
        view = json.loads(rendered)
        assert "raw_result_json" not in view, "raw_leak"
        assert view["status"] in {"valid", "error", "unsupported", "unknown"}
        if view["status"] != "valid":
            assert not view.get("claims"), "invalid_claims"
            for scenario in view.get("mobility", {}).get("scenarios", []):
                assert not any(key in scenario for key in ("itinerary", "components_s", "walking")), "partial_authoritative_mobility"
            error = view.get("error")
            if error:
                assert error.get("safe_next_action"), "missing_safe_action"
                assert error["origin"] != "transport", "invented_network"
                assert not any(s in error["message"].lower() for s in ("traceback", "http", "timeout")), "invented_cause_or_stack"
        for claim in view.get("claims", []):
            if "per_10000" in claim["metric_id"] or claim["metric_id"].startswith("pct_") or claim["metric_id"] == "value" and claim["unit"].startswith("%"):
                assert claim["numerator"] and claim["denominator"], "rate_lineage"
            resolved.update(claim["source_ids"])
        for scenario in view.get("mobility", {}).get("scenarios", []):
            resolved.update(s["catalog_source_id"] for s in scenario["sources"])
        return normalized(view)

    if mode == "fuzz":
        for case in generate_fuzz(fixture, count):
            if case["index"] % shards != shard:
                continue
            counters[case["category"]] += 1
            try:
                view = call(case["tool"], case["arguments"])
                counters["status_" + view["status"]] += 1
                trace.update((str(case["index"]) + stable_hash(view)).encode())
                # Determinism is tested for every case, not assumed from seed.
                assert view == call(case["tool"], case["arguments"]), "nondeterministic"
            except Exception as exc:
                failures.append({"index": case["index"], "category": case["category"],
                                 "tool": case["tool"], "input_sha256": stable_hash(case["arguments"]),
                                 "exception": type(exc).__name__, "message": str(exc)[:400]})
            if case["index"] % 250 == 0:
                print(json.dumps({"progress": case["index"], "elapsed_s": round(time.perf_counter()-started, 2), "failures": len(failures)}), flush=True)
        for source in sorted(resolved):
            view = call("consultar_fuente", {"source_id": source})
            assert view["status"] == "valid" and view.get("source_metadata"), source
        report = {"count": sum(v for k, v in counters.items() if not k.startswith("status_")), "runtime_invocations": sum(v for k, v in counters.items() if not k.startswith("status_")) * 2,
                  "seed": SEED, "counts": dict(counters), "uncaught_or_invariant_failures": failures,
                  "resolved_sources": sorted(resolved), "max_public_bytes": max_bytes,
                  "result_stream_sha256": trace.hexdigest()}
    elif mode == "cold":
        operations = {name: (name, args) for name, args in base.items()}
        operations.update(health=("plan_visit", {"request": health}), legacy=("plan_visit", {"request": legacy}),
                          compare=("plan_visit", {"request": [health, {**health, "duration_minutes": 25}]}),
                          invalid=("plan_visit", {"request": {**health, "date": "2026-09-30"}}))
        origins = json.loads((candidate / "datos_preparados/vnext/operational_catalog_r6.json").read_text())["origins"]
        for row in origins:
            origin = row["origin_id"]
            operations[origin] = ("plan_visit", {"request": {**health, "origin_id": origin}})
        report = {key: call(*value) for key, value in operations.items() if not cold_key or key == cold_key}
        print("R13_RESULT=" + json.dumps(report, ensure_ascii=True)); return
    elif mode == "sequences":
        cold = json.loads((candidate.parent / "cold.json").read_text(encoding="utf-8"))
        operations = {name: (name, args) for name, args in base.items()}
        operations.update(health=("plan_visit", {"request": health}), legacy=("plan_visit", {"request": legacy}),
                          compare=("plan_visit", {"request": [health, {**health, "duration_minutes": 25}]}),
                          invalid=("plan_visit", {"request": {**health, "date": "2026-09-30"}}))
        origins = json.loads((candidate / "datos_preparados/vnext/operational_catalog_r6.json").read_text())["origins"]
        for row in origins:
            origin = row["origin_id"]
            operations[origin] = ("plan_visit", {"request": {**health, "origin_id": origin}})
        patterns = [["obtener_resumen_territorial", "health", "obtener_resumen_territorial"],
                    ["health", "legacy", "health"], ["health", "invalid", "health"],
                    ["compare", "health", "compare"], ["health", "consultar_fuente", "health"],
                    ["consultar_capacidades"] * 5, [row["origin_id"] for row in origins] + [origins[0]["origin_id"]]]
        rng = random.Random(SEED)
        invocations = 0
        for index in range(count):
            pattern = patterns[index % len(patterns)] + [rng.choice(list(operations)) for _ in range(3)]
            for key in pattern:
                invocations += 1
                try:
                    view = call(*operations[key])
                    assert view == cold[key], "cold_equivalence:" + key
                    trace.update(stable_hash(view).encode())
                except Exception as exc:
                    failures.append({"sequence": index, "operation": key, "exception": type(exc).__name__, "message": str(exc)[:400]})
            if index % 25 == 0:
                print(json.dumps({"sequence": index, "elapsed_s": round(time.perf_counter()-started, 2), "failures": len(failures)}), flush=True)
        report = {"count": count, "seed": SEED, "tool_calls": invocations, "length_range": [6, 8],
                  "cold_reference": "separate cold generated-module subprocess, then same normalized view for every operation",
                  "normalized_fields_removed": ["request_id", "execution.request_id"],
                  "state_leak_findings": failures, "result_stream_sha256": trace.hexdigest(),
                  "different_root_policy": "W1 runtime intentionally stays bound to its first verified root; root switching is not a supported success mode; separate package-root probes are in package hardening."}
    else:
        raise ValueError(mode)
    report.update(elapsed_s=round(time.perf_counter()-started, 3), passed=not failures)
    print("R13_RESULT=" + json.dumps(report, ensure_ascii=True), flush=True)


def run_clean(mode, count, shard=0, shards=1):
    assert digest(ZIP.read_bytes()) == ZIP_SHA and digest(MANIFEST.read_bytes()) == MANIFEST_SHA
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="g360-r13-") as temporary:
        directory = Path(temporary) / "candidate"
        directory.mkdir()
        with zipfile.ZipFile(ZIP) as archive:
            archive_safety(archive, manifest["members"])
            fixture = json.loads(archive.read("datos_preparados/vnext/w1_conformance_r7.json"))
            for name in manifest["freeze_paths"]:
                archive.extract(name, directory)
        observer = Path(temporary) / "observer"
        observer.mkdir()
        environment = {key: value for key, value in os.environ.items() if key.upper() in
                       {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "TMPDIR", "COMSPEC", "PATHEXT", "LANG", "LC_ALL"}}
        environment["PYTHONUTF8"] = "1"
        command = [sys.executable, "-I", str(Path(__file__).resolve()), "--worker", "--mode", mode,
                   "--candidate", str(directory), "--count", str(count), "--shard", str(shard), "--shards", str(shards)]
        def launch(args):
            completed = subprocess.run(args, cwd=observer, env=environment, input=json.dumps(fixture),
                                       text=True, encoding="utf-8", capture_output=True, timeout=14400)
            if completed.returncode:
                raise RuntimeError(completed.stderr[-4000:])
            lines = completed.stdout.splitlines()
            for line in lines:
                if not line.startswith("R13_RESULT="):
                    print(line, flush=True)
            return json.loads(next(line.removeprefix("R13_RESULT=") for line in lines if line.startswith("R13_RESULT=")))
        if mode == "sequences":
            cold_command = command.copy()
            cold_command[cold_command.index(mode)] = "cold"
            cold = launch(cold_command)
            (directory.parent / "cold.json").write_text(json.dumps(cold), encoding="utf-8")
        report = launch(command)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["fuzz", "sequences", "cold"], required=True)
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--cold-key")
    args = parser.parse_args()
    if args.worker:
        worker(args.mode, args.candidate, args.count, args.shard, args.shards, args.cold_key)
    else:
        started = time.perf_counter()
        if args.mode == "fuzz" and args.shards > 1:
            with ThreadPoolExecutor(max_workers=args.shards) as pool:
                parts = list(pool.map(lambda shard: run_clean(args.mode, args.count, shard, args.shards), range(args.shards)))
            counts = Counter()
            for part in parts:
                counts.update(part["counts"])
            report = {"count": sum(p["count"] for p in parts), "runtime_invocations": sum(p["runtime_invocations"] for p in parts),
                      "seed": SEED, "counts": dict(counts), "uncaught_or_invariant_failures": [f for p in parts for f in p["uncaught_or_invariant_failures"]],
                      "resolved_sources": sorted({s for p in parts for s in p["resolved_sources"]}),
                      "max_public_bytes": max(p["max_public_bytes"] for p in parts), "shards": parts,
                      "passed": all(p["passed"] for p in parts), "elapsed_s": round(time.perf_counter()-started, 3)}
        else:
            report = run_clean(args.mode, args.count)
        write_report("SCHEMA_FUZZ_R13.json" if args.mode == "fuzz" else "STATE_SEQUENCES_R13.json", report)
        print(json.dumps({"mode": args.mode, "passed": report["passed"], "count": report["count"], "elapsed_s": report["elapsed_s"]}), flush=True)


if __name__ == "__main__":
    main()
