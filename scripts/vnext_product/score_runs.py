"""Score observed W3 runs; never execute an LLM or fabricate a missing run."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEVELOPMENT = ROOT / "tests/vnext_redteam/development_cases.json"
SCENARIOS = ROOT / "tests/vnext_redteam/conversation_scenarios.json"
REQUIRED = {"case_id", "system", "attempt", "version", "package_hash", "model_config",
            "data_identity", "prompt", "context", "tool_calls", "final_response",
            "started_at", "ended_at", "error_class", "verdict", "reviewer", "evidence_path",
            "llm_executed"}
ERROR_CLASSES = {None, "agent", "contract", "data", "platform", "unknown"}
VERDICTS = {"correct", "incorrect", "not_scored"}


def timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def latency_ms(start: str, end: str) -> float:
    result = (timestamp(end) - timestamp(start)).total_seconds() * 1000
    if result < 0:
        raise ValueError("Negative elapsed time")
    return result


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(fraction * len(ordered)) - 1)], 3)


def load_cases(holdout: Path | None) -> dict[str, dict]:
    dev = json.loads(DEVELOPMENT.read_text(encoding="utf-8"))["cases"]
    cases = {item["id"]: item for item in dev}
    if holdout:
        secret = json.loads(holdout.read_text(encoding="utf-8"))["cases"]
        cases.update({item["id"]: item for item in secret})
    if len(cases) != (60 if holdout else 48):
        raise ValueError("Corpus count or unique IDs changed")
    return cases


def validate(record: dict, cases: dict[str, dict]) -> tuple[float, list[float]]:
    missing = REQUIRED - record.keys()
    if missing:
        raise ValueError(f"Missing run fields: {sorted(missing)}")
    if record["case_id"] not in cases:
        raise ValueError(f"Unknown case_id {record['case_id']}")
    if record["system"] not in {"v4", "candidate"}:
        raise ValueError("system must be v4 or candidate")
    if type(record["attempt"]) is not int or record["attempt"] < 1:
        raise ValueError("attempt must be positive integer")
    if record["verdict"] not in VERDICTS or record["error_class"] not in ERROR_CLASSES:
        raise ValueError("Invalid verdict or error class")
    if not isinstance(record["tool_calls"], list) or not isinstance(record["context"], list):
        raise ValueError("tool_calls and context must be arrays")
    if not isinstance(record["model_config"], dict) or not record["model_config"]:
        raise ValueError("model_config must identify the model and settings")
    if not isinstance(record["final_response"], str):
        raise ValueError("final_response must be text, possibly empty on failure")
    frozen = cases[record["case_id"]]
    if record["prompt"] != frozen["prompt"]:
        raise ValueError("Observed prompt differs from frozen corpus")
    if record["context"] != frozen.get("seed_user_prompts", []):
        raise ValueError("Observed context differs from frozen seed")
    if not isinstance(record["llm_executed"], bool):
        raise ValueError("llm_executed must be boolean")
    if not record["llm_executed"] and record["verdict"] != "not_scored":
        raise ValueError("An attempt without LLM execution cannot be scored")
    if not record["version"] or not record["package_hash"] or not record["data_identity"]:
        raise ValueError("Version, package and data identity are required")
    if record["verdict"] != "not_scored" and not record["reviewer"]:
        raise ValueError("A scored verdict needs an identified reviewer")
    if not record["evidence_path"]:
        raise ValueError("Every attempt needs an evidence path")
    total = latency_ms(record["started_at"], record["ended_at"])
    tools = []
    for call in record["tool_calls"]:
        for field in ("name", "arguments", "started_at", "ended_at", "output_or_error"):
            if field not in call:
                raise ValueError(f"Tool trace missing {field}")
        if not isinstance(call["name"], str) or not call["name"]:
            raise ValueError("Tool name must be nonempty text")
        if timestamp(call["started_at"]) < timestamp(record["started_at"]) or timestamp(call["ended_at"]) > timestamp(record["ended_at"]):
            raise ValueError("Tool trace falls outside attempt interval")
        tools.append(latency_ms(call["started_at"], call["ended_at"]))
    return total, tools


def summarize(rows: list[dict], cases: dict[str, dict]) -> dict:
    if not rows:
        return {"status": "NOT_RUN", "attempts": 0, "unique_cases_scored": 0,
                "target_cases": len(cases), "llm_executed": 0}
    by_system: dict[str, list[dict]] = defaultdict(list)
    durations: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"complete_ms": [], "tool_ms": []})
    for record in rows:
        complete, tools = validate(record, cases)
        by_system[record["system"]].append(record)
        durations[record["system"]]["complete_ms"].append(complete)
        durations[record["system"]]["tool_ms"].extend(tools)
    report = {"status": "PARTIAL", "target_cases": len(cases), "attempts": len(rows), "systems": {}}
    firsts: dict[str, dict[str, dict]] = {}
    for system, records in by_system.items():
        grouped: dict[str, list[dict]] = defaultdict(list)
        for item in records:
            grouped[item["case_id"]].append(item)
        first: dict[str, dict] = {}
        for case_id, attempts in grouped.items():
            numbers = [item["attempt"] for item in attempts]
            if len(numbers) != len(set(numbers)):
                raise ValueError(f"Duplicate attempt number for {system}/{case_id}")
            if sorted(numbers) != list(range(1, max(numbers) + 1)):
                raise ValueError(f"Missing earlier attempt for {system}/{case_id}")
            first[case_id] = min(attempts, key=lambda item: item["attempt"])
        firsts[system] = first
        scored = {key: value for key, value in first.items() if value["verdict"] != "not_scored"}
        correct = sum(item["verdict"] == "correct" for item in scored.values())
        critical_failures = sorted(key for key, item in scored.items()
                                   if cases[key].get("critical") and item["verdict"] == "incorrect")
        d = durations[system]
        report["systems"][system] = {
            "attempts": len(records), "unique_cases_attempted": len(first),
            "unique_cases_scored": len(scored), "first_attempt_correct": correct,
            "first_attempt_incorrect": len(scored) - correct,
            "critical_failures": critical_failures,
            "error_classes_all_attempts": dict(Counter(item["error_class"] or "none" for item in records)),
            "complete_ms": {"n": len(d["complete_ms"]), "p50": percentile(d["complete_ms"], .5),
                            "p95": percentile(d["complete_ms"], .95)},
            "tool_ms": {"n": len(d["tool_ms"]), "p50": percentile(d["tool_ms"], .5),
                        "p95": percentile(d["tool_ms"], .95)},
        }
    paired = set(firsts.get("v4", {})) & set(firsts.get("candidate", {}))
    comparable = [case_id for case_id in paired
                  if firsts["v4"][case_id]["model_config"] == firsts["candidate"][case_id]["model_config"]
                  and firsts["v4"][case_id]["data_identity"] == firsts["candidate"][case_id]["data_identity"]
                  and firsts["v4"][case_id]["context"] == firsts["candidate"][case_id]["context"]
                  and firsts["v4"][case_id]["verdict"] != "not_scored"
                  and firsts["candidate"][case_id]["verdict"] != "not_scored"]
    report["paired"] = {"observed": len(paired), "comparable": len(comparable),
                        "candidate_additional_correct": sum(firsts["candidate"][key]["verdict"] == "correct" and firsts["v4"][key]["verdict"] == "incorrect" for key in comparable),
                        "candidate_regressions": sum(firsts["candidate"][key]["verdict"] == "incorrect" and firsts["v4"][key]["verdict"] == "correct" for key in comparable)}
    report["llm_executed"] = sum(item["llm_executed"] for item in rows)
    if all(system in report["systems"] and report["systems"][system]["unique_cases_scored"] == len(cases)
           for system in ("v4", "candidate")):
        report["status"] = "EVALUATED_REVIEW_REQUIRED"
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path)
    parser.add_argument("--holdout", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cases = load_cases(args.holdout)
    rows = [] if not args.runs else [json.loads(line) for line in args.runs.read_text(encoding="utf-8").splitlines() if line.strip()]
    report = summarize(rows, cases)
    data = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data, encoding="utf-8")
    print(data)


if __name__ == "__main__":
    main()
