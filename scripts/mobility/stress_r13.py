"""Cold, offline generated/property stress of the unchanged W1 producer.

Invoked with python -I and an explicit root. Not a portal/LLM/load test.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback


def run(count=20000, seed=360013, budget_seconds=2640, shard_index=0, shards=1):
    from prototypes.ir_y_volver import provider_r6 as producer
    from scripts.mobility.r13_properties import canonical, generated_requests, check_result
    start = time.perf_counter()
    statuses, families, origins, hours = Counter(), Counter(), Counter(), Counter()
    input_digest, output_digest = hashlib.sha256(), hashlib.sha256()
    unique = set()
    executed, crashes, counterexamples = 0, [], []
    import_paths = {}
    target = len(range(shard_index, count, shards))
    producer_executions = 0
    for index, family, request in generated_requests(count, seed):
        if index % shards != shard_index:
            continue
        if time.perf_counter() - start >= budget_seconds:
            break
        encoded = canonical(request)
        unique.add(hashlib.sha256(encoded).hexdigest())
        input_digest.update(encoded + b"\n")
        try:
            producer_executions += 1
            left = producer.plan_visit(request)
            producer_executions += 1
            right = producer.plan_visit(request)
        except Exception:
            crashes.append(dict(index=index, family=family, request=request, traceback=traceback.format_exc()))
            break
        try:
            assert canonical(left) == canonical(right), "same request different semantic bytes"
            check_result(left, request)
        except Exception:
            counterexamples.append(dict(index=index, family=family, request=request, result=left, traceback=traceback.format_exc()))
            break
        output_digest.update(canonical(left) + b"\n")
        statuses[left["status"]] += 1
        families[family] += 1
        if type(request) is dict:
            if type(request.get("origin_id")) is str:
                origins[request["origin_id"]] += 1
            if type(request.get("appointment_time")) is str and request["appointment_time"]:
                hours[request["appointment_time"].split(":")[0]] += 1
        executed += 1
        if executed % 250 == 0:
            print(json.dumps({"progress": executed, "target": target, "shard": shard_index, "elapsed_s": round(time.perf_counter() - start, 3)}), file=sys.stderr, flush=True)
    for name, module in sys.modules.items():
        if name == "prototypes" or name.startswith("prototypes."):
            path = Path(module.__file__)
            import_paths[name] = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    return dict(status="FAIL" if crashes or counterexamples else "PASS" if executed == target else "BUDGET_LIMITED",
                classification="generated/property stress; not independent tests or real users",
                seed=seed, requested=target, global_requested=count, shard_index=shard_index, shards=shards,
                generated_requests=executed, unique_request_bytes=len(unique), producer_executions=producer_executions,
                runtime_s=round(time.perf_counter() - start, 3), budget_seconds=budget_seconds,
                distribution=dict(statuses), families=dict(families), origin_distribution=dict(origins), hour_distribution=dict(hours),
                crashes=crashes, counterexamples=counterexamples,
                input_stream_sha256=input_digest.hexdigest(), output_stream_sha256=output_digest.hexdigest(),
                environment=dict(python=sys.version, isolated=bool(sys.flags.isolated), cwd=str(Path.cwd()),
                                 root=str(Path(producer.__file__).resolve().parents[2]), network="BLOCKED_BY_AUDIT_HOOK",
                                 configured_root=os.environ.get("GIPUZKOA360_VNEXT_ROOT"), imports=import_paths),
                limits=["Repeated outputs checked for every generated input; no producer cache or monkeypatch.",
                        "Bounded static catalog/date/network; not general transport coverage or LLM/portal acceptance.",
                        "No new independent source evidence: generated properties use pinned assets; raw-source sample reported separately."])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=360013)
    parser.add_argument("--budget-seconds", type=int, default=2640)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root))
    def offline(event, arguments):
        if event in {"socket.connect", "socket.getaddrinfo"}:
            raise RuntimeError("R13 offline worker: network disabled")
    sys.addaudithook(offline)
    report = run(args.count, args.seed, args.budget_seconds, args.shard_index, args.shards)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: report[key] for key in ("status", "generated_requests", "unique_request_bytes", "producer_executions", "runtime_s", "distribution")}))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
