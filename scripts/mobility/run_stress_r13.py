"""Run disjoint generated inputs in four cold producer processes, <=45 min."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from scripts.mobility.r13_properties import ROOT, SEED, canonical, generated_requests


def run(output, count=20000, shards=4, budget=2640):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    allowed = {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "TMPDIR", "COMSPEC", "PATHEXT", "LANG", "LC_ALL"}
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    env["PYTHONIOENCODING"] = "utf-8"
    script = Path(__file__).with_name("stress_r13.py")
    start = time.perf_counter()
    processes, handles = [], []
    for index in range(shards):
        handle = (output / f"progress-{index}.log").open("w", encoding="utf-8")
        handles.append(handle)
        command = [sys.executable, "-I", str(script), "--root", str(ROOT), "--output", str(output / f"shard-{index}.json"),
                   "--count", str(count), "--seed", str(SEED), "--budget-seconds", str(budget), "--shards", str(shards), "--shard-index", str(index)]
        processes.append(subprocess.Popen(command, cwd=ROOT, env=env, stdout=handle, stderr=handle))
    protocol_failure = None
    try:
        while any(process.poll() is None for process in processes):
            failed = next((i for i, process in enumerate(processes) if process.poll() not in (None, 0)), None)
            if failed is not None:
                protocol_failure = "shard_failed:" + str(failed)
                break
            if time.perf_counter() - start > budget + 45:
                protocol_failure = "bounded_worker_timeout"
                break
            time.sleep(1)
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=15)
        for handle in handles:
            handle.close()
    reports = [json.loads((output / f"shard-{i}.json").read_bytes()) for i in range(shards) if (output / f"shard-{i}.json").is_file()]
    counts = {}
    for field in ("distribution", "families", "origin_distribution", "hour_distribution"):
        merged = Counter()
        for report in reports:
            merged.update(report[field])
        counts[field] = dict(merged)
    unique = {hashlib.sha256(canonical(q)).hexdigest() for _, _, q in generated_requests(count, SEED)}
    passed = len(reports) == shards and all(report["status"] == "PASS" for report in reports) and not protocol_failure
    result = dict(status="PASS" if passed else "FAIL", classification="generated/property stress; not independent tests",
                  seed=SEED, target=count, shards=shards, partition="global generator index modulo shards; no overlapping invocations",
                  generated_requests=sum(r["generated_requests"] for r in reports),
                  unique_request_bytes=len(unique) if passed else None,
                  producer_executions=sum(r["producer_executions"] for r in reports),
                  wall_runtime_s=round(time.perf_counter() - start, 3), max_wall_budget_s=budget + 45,
                  crashes=sum(len(r["crashes"]) for r in reports), counterexamples=sum(len(r["counterexamples"]) for r in reports),
                  protocol_failure=protocol_failure, worker_exit_codes=[p.returncode for p in processes], **counts,
                  reports=[dict(path=f"shard-{r['shard_index']}.json", sha256=hashlib.sha256((output / f"shard-{r['shard_index']}.json").read_bytes()).hexdigest()) for r in reports],
                  support_identity={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), script, Path(__file__).with_name("r13_properties.py"))},
                  llm="NOT_CLAIMED", portal="NOT_CLAIMED")
    (output / "stress_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=20000)
    parser.add_argument("--shards", type=int, default=4)
    parser.add_argument("--budget", type=int, default=2640)
    args = parser.parse_args()
    if args.count < 1 or not 1 <= args.shards <= 4 or not 1 <= args.budget <= 2640:
        parser.error("invalid count/shards/budget")
    raise SystemExit(0 if run(args.output, args.count, args.shards, args.budget)["status"] == "PASS" else 1)
