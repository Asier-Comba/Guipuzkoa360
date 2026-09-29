"""Validate and score observed W3 traces. This module never invokes a model."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEVELOPMENT = ROOT / "tests/vnext_redteam/development_cases.json"
SCENARIOS = ROOT / "tests/vnext_redteam/conversation_scenarios.json"
VERSION = "W3_TRACE_2.0.0"
SCORING_VERSION = "2.0.0"
COMMON = {"schema_version", "record_type", "record_id", "system", "identity",
          "attempt", "started_at", "ended_at", "llm_executed", "error_class",
          "error_observation", "verdict", "reviewer", "review_notes", "evidence",
          "tool_calls", "final_response", "prompt", "history_before"}
SINGLE = COMMON | {"case_id", "initial_context_protocol"}
CONVERSATION = COMMON | {"conversation_id", "turn_index", "session_id",
                         "history_after", "semantic_checks"}
IDENTITY = {"runtime_commit", "package_sha256", "package_file", "model_id",
            "model_config", "data_manifest_sha256", "data_manifest_file",
            "context_mode", "corpus_sha256", "scoring_version"}
CALL = {"call_id", "name", "arguments", "arguments_sha256", "output_or_error",
        "output_sha256", "request_id", "result_request_id", "started_at", "ended_at"}
CHECK = {"kind", "expected", "observed", "passed", "evidence_call_id", "review_note"}
ERROR_CLASSES = {None, "agent", "contract", "data", "platform", "unknown"}
VERDICTS = {"correct", "incorrect", "not_scored"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_safe(value: Any) -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("All numbers must be finite")
        return
    if type(value) is list:
        for part in value:
            json_safe(part)
        return
    if type(value) is dict:
        for key, part in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be text")
            json_safe(part)
        return
    raise ValueError("Only JSON types are accepted")


def canonical(value: Any) -> bytes:
    json_safe(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def exact_keys(value: Any, expected: set[str], label: str) -> None:
    if type(value) is not dict:
        raise ValueError(f"{label} must be an object")
    missing, extra = expected - value.keys(), value.keys() - expected
    if missing:
        raise ValueError(f"Missing {label} fields: {sorted(missing)}")
    if extra:
        raise ValueError(f"Unexpected {label} fields: {sorted(extra)}")


def nonempty(value: Any, label: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{label} must be nonempty text")


def hex_hash(value: Any, length: int, label: str) -> None:
    if type(value) is not str or not re.fullmatch(rf"[a-f0-9]{{{length}}}", value):
        raise ValueError(f"{label} must be {length} lowercase hex characters")


def timestamp(value: Any) -> datetime:
    nonempty(value, "timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid ISO timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Every timestamp needs a timezone")
    return result


def elapsed(start: Any, end: Any) -> float:
    ms = (timestamp(end) - timestamp(start)).total_seconds() * 1000
    if ms < 0 or not math.isfinite(ms):
        raise ValueError("Invalid interval: end precedes start")
    return ms


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
        for item in secret:
            if item["id"] in cases:
                raise ValueError("Duplicate case ID between development and holdout")
            cases[item["id"]] = item
    if len(cases) != (60 if holdout else 48):
        raise ValueError("Corpus count or unique IDs changed")
    return cases


def load_scenarios() -> dict[str, dict]:
    items = json.loads(SCENARIOS.read_text(encoding="utf-8"))["scenarios"]
    result = {item["id"]: item for item in items}
    if len(items) != 20 or len(result) != 20:
        raise ValueError("Conversation corpus count or IDs changed")
    return result


def verified_file(root: Path, relative: Any, expected_sha: Any, label: str) -> Path:
    nonempty(relative, f"{label} path")
    hex_hash(expected_sha, 64, f"{label} hash")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or path.drive:
        raise ValueError(f"{label} path must stay inside evidence root")
    root = root.resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise ValueError(f"{label} file is missing or outside evidence root: {relative}")
    if sha(target.read_bytes()) != expected_sha:
        raise ValueError(f"{label} hash mismatch: {relative}")
    return target


@lru_cache(maxsize=64)
def git_commit_exists(commit: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=ROOT,
                          capture_output=True, check=False).returncode == 0


def validate_identity(identity: Any, corpus_hash: str, evidence_root: Path,
                      llm_executed: bool) -> None:
    exact_keys(identity, IDENTITY, "identity")
    hex_hash(identity["runtime_commit"], 40, "runtime_commit")
    for key in ("package_sha256", "data_manifest_sha256", "corpus_sha256"):
        hex_hash(identity[key], 64, key)
    if identity["corpus_sha256"] != corpus_hash:
        raise ValueError("Corpus hash does not match frozen family")
    if identity["scoring_version"] != SCORING_VERSION:
        raise ValueError("Scoring version changed")
    nonempty(identity["model_id"], "model_id")
    if type(identity["model_config"]) is not dict or not identity["model_config"]:
        raise ValueError("model_config must identify model settings")
    if identity["context_mode"] not in {"portal_memory", "local_memory", "isolated"}:
        raise ValueError("Invalid context_mode")
    if llm_executed:
        if any(set(identity[key]) == {"0"} for key in
               ("runtime_commit", "package_sha256", "data_manifest_sha256")):
            raise ValueError("Synthetic zero hashes cannot identify an LLM run")
        if not git_commit_exists(identity["runtime_commit"]):
            raise ValueError("Runtime commit is not present in Git")
        verified_file(evidence_root, identity["package_file"],
                      identity["package_sha256"], "Package")
        verified_file(evidence_root, identity["data_manifest_file"],
                      identity["data_manifest_sha256"], "Data manifest")
    elif identity["package_file"] is not None or identity["data_manifest_file"] is not None:
        verified_file(evidence_root, identity["package_file"],
                      identity["package_sha256"], "Package")
        verified_file(evidence_root, identity["data_manifest_file"],
                      identity["data_manifest_sha256"], "Data manifest")


def validate_messages(messages: Any, label: str) -> None:
    if type(messages) is not list:
        raise ValueError(f"{label} must be an array")
    for item in messages:
        exact_keys(item, {"role", "content", "sha256"}, "message")
        if item["role"] not in {"user", "assistant", "tool"}:
            raise ValueError("Invalid message role")
        if type(item["content"]) is not str:
            raise ValueError("Message content must be text")
        hex_hash(item["sha256"], 64, "message hash")
        if sha(item["content"].encode("utf-8")) != item["sha256"]:
            raise ValueError("Message hash mismatch")


def validate_calls(calls: Any, start: datetime, end: datetime) -> tuple[list[float], set[str]]:
    if type(calls) is not list:
        raise ValueError("tool_calls must be an array")
    durations, ids = [], set()
    for call in calls:
        exact_keys(call, CALL, "tool call")
        nonempty(call["call_id"], "call_id")
        nonempty(call["name"], "tool name")
        if call["call_id"] in ids:
            raise ValueError("Duplicate tool call ID")
        ids.add(call["call_id"])
        if type(call["arguments"]) is not dict:
            raise ValueError("Tool arguments must be an object")
        for key, payload in (("arguments_sha256", call["arguments"]),
                             ("output_sha256", call["output_or_error"])):
            hex_hash(call[key], 64, key)
            if call[key] != sha(canonical(payload)):
                raise ValueError(f"Tool {key} does not match observed payload")
        a, b = timestamp(call["started_at"]), timestamp(call["ended_at"])
        if a < start or b > end:
            raise ValueError("Tool trace falls outside attempt interval")
        durations.append(elapsed(call["started_at"], call["ended_at"]))
        request, result = call["request_id"], call["result_request_id"]
        if (request is None) != (result is None):
            raise ValueError("Partial request/result binding")
        if request is not None:
            nonempty(request, "request_id")
            if request != result:
                raise ValueError("Request/result binding mismatch")
    return durations, ids


def validate_single(row: dict, cases: dict[str, dict]) -> None:
    exact_keys(row, SINGLE, "SINGLE_CASE")
    case = cases.get(row["case_id"])
    if case is None:
        raise ValueError("Unknown case_id")
    if row["prompt"] != case["prompt"]:
        raise ValueError("Observed prompt differs from frozen corpus")
    exact_keys(row["initial_context_protocol"], {"id", "seed_user_prompts"},
               "initial_context_protocol")
    protocol = row["initial_context_protocol"]
    if protocol["id"] != "seed_user_prompts_v1" or protocol["seed_user_prompts"] != case.get("seed_user_prompts", []):
        raise ValueError("Initial context protocol differs from frozen seed")
    history = row["history_before"]
    actual_users = [item["content"] for item in history if item["role"] == "user"]
    if actual_users != protocol["seed_user_prompts"]:
        raise ValueError("Actual seed history differs from plan")
    for index, item in enumerate(history):
        if item["role"] == "user":
            next_user = next((position for position in range(index + 1, len(history))
                              if history[position]["role"] == "user"), len(history))
            if not any(message["role"] == "assistant" for message in history[index + 1:next_user]):
                raise ValueError("Every seed user message needs a real assistant history")


def validate_conversation(row: dict, scenarios: dict[str, dict], call_ids: set[str]) -> None:
    exact_keys(row, CONVERSATION, "CONVERSATION")
    scenario = scenarios.get(row["conversation_id"])
    if scenario is None:
        raise ValueError("Unknown conversation_id")
    if type(row["turn_index"]) is not int or not 1 <= row["turn_index"] <= len(scenario["turns"]):
        raise ValueError("Invalid turn_index")
    nonempty(row["session_id"], "session_id")
    if row["prompt"] != scenario["turns"][row["turn_index"] - 1]["prompt"]:
        raise ValueError("Conversation prompt differs from frozen scenario")
    validate_messages(row["history_after"], "history_after")
    before, after = row["history_before"], row["history_after"]
    if after[:len(before)] != before:
        raise ValueError("Conversation history continuity broken")
    appended = after[len(before):]
    if not appended or appended[0]["role"] != "user" or appended[0]["content"] != row["prompt"]:
        raise ValueError("Conversation turn must append its frozen user prompt")
    if row["llm_executed"]:
        if appended[-1]["role"] != "assistant" or appended[-1]["content"] != row["final_response"]:
            raise ValueError("Conversation history lacks observed assistant response")
    if type(row["semantic_checks"]) is not list:
        raise ValueError("semantic_checks must be an array")
    if row["turn_index"] > 1 and row["llm_executed"] and not row["semantic_checks"]:
        raise ValueError("Follow-up needs semantic checks")
    for check in row["semantic_checks"]:
        exact_keys(check, CHECK, "semantic check")
        if check["kind"] not in {"reference", "parameter", "recalculation", "topic_return",
                                 "session_isolation", "limit"}:
            raise ValueError("Invalid semantic check kind")
        if type(check["passed"]) is not bool:
            raise ValueError("Semantic check passed must be boolean")
        nonempty(check["review_note"], "semantic review_note")
        if check["evidence_call_id"] is not None and check["evidence_call_id"] not in call_ids:
            raise ValueError("Semantic check references missing tool call")
        if check["kind"] == "parameter" and check["passed"] and check["expected"] != check["observed"]:
            raise ValueError("Changed parameter was not observed")
        if row["verdict"] == "correct" and not check["passed"]:
            raise ValueError("Correct verdict contradicts failed semantic check")


def validate(row: dict, cases: dict[str, dict], scenarios: dict[str, dict],
             evidence_root: Path, case_hash: str) -> tuple[float, list[float]]:
    json_safe(row)
    if type(row) is not dict:
        raise ValueError("Trace must be an object")
    kind = row.get("record_type")
    if kind not in {"SINGLE_CASE", "CONVERSATION"}:
        raise ValueError("Invalid record_type")
    exact_keys(row, SINGLE if kind == "SINGLE_CASE" else CONVERSATION, "trace")
    if row["schema_version"] != VERSION:
        raise ValueError("Unsupported trace schema_version")
    nonempty(row["record_id"], "record_id")
    if row["system"] not in {"v4", "candidate"}:
        raise ValueError("system must be v4 or candidate")
    if type(row["attempt"]) is not int or row["attempt"] < 1:
        raise ValueError("attempt must be positive integer")
    if type(row["llm_executed"]) is not bool:
        raise ValueError("llm_executed must be boolean")
    if row["verdict"] not in VERDICTS or row["error_class"] not in ERROR_CLASSES:
        raise ValueError("Invalid verdict or error class")
    if row["error_class"] == "platform":
        nonempty(row["error_observation"], "platform error_observation")
    elif row["error_observation"] is not None and type(row["error_observation"]) is not str:
        raise ValueError("error_observation must be text or null")
    if not row["llm_executed"] and row["verdict"] != "not_scored":
        raise ValueError("An attempt without LLM execution cannot be scored")
    if row["verdict"] != "not_scored":
        nonempty(row["reviewer"], "reviewer")
        nonempty(row["review_notes"], "review_notes")
    elif row["reviewer"] is not None and type(row["reviewer"]) is not str:
        raise ValueError("reviewer must be text or null")
    if type(row["final_response"]) is not str:
        raise ValueError("final_response must be text")
    start, end = timestamp(row["started_at"]), timestamp(row["ended_at"])
    duration = elapsed(row["started_at"], row["ended_at"])
    corpus_hash = case_hash if kind == "SINGLE_CASE" else sha(SCENARIOS.read_bytes())
    validate_identity(row["identity"], corpus_hash, evidence_root, row["llm_executed"])
    exact_keys(row["evidence"], {"path", "sha256"}, "evidence")
    verified_file(evidence_root, row["evidence"]["path"], row["evidence"]["sha256"], "Evidence")
    validate_messages(row["history_before"], "history_before")
    tool_durations, call_ids = validate_calls(row["tool_calls"], start, end)
    if kind == "SINGLE_CASE":
        validate_single(row, cases)
    else:
        validate_conversation(row, scenarios, call_ids)
    return duration, tool_durations


def summary_times(values: list[float]) -> dict:
    return {"n": len(values), "p50_ms": percentile(values, .5), "p95_ms": percentile(values, .95)}


def summarize(rows: list[dict], cases: dict[str, dict], scenarios: dict[str, dict] | None = None,
              evidence_root: Path = ROOT, case_hash: str | None = None) -> dict:
    scenarios = load_scenarios() if scenarios is None else scenarios
    case_hash = case_hash or sha(DEVELOPMENT.read_bytes())
    if not rows:
        return {"status": "NOT_RUN", "scoring_version": SCORING_VERSION,
                "single_cases": {"target": len(cases), "scored": 0},
                "conversations": {"planned": len(scenarios), "executed": 0, "complete": 0,
                                  "turns_scored": 0},
                "attempts": 0, "llm_executed": 0, "systems": {},
                "paired_single": {"observed": 0, "calculation_comparable": 0}}
    seen_records, identities = set(), {}
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    durations: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"complete": [], "tool": []})
    for row in rows:
        duration, tool_durations = validate(row, cases, scenarios, evidence_root, case_hash)
        if row["record_id"] in seen_records:
            raise ValueError("Duplicate record_id")
        seen_records.add(row["record_id"])
        cohort_key = (row["system"], row["record_type"])
        identity_token = canonical(row["identity"])
        if cohort_key in identities and identities[cohort_key] != identity_token:
            raise ValueError(f"Mixed identity for {cohort_key}; split or reject cohorts")
        identities[cohort_key] = identity_token
        item_id = row["case_id"] if row["record_type"] == "SINGLE_CASE" else row["conversation_id"]
        key = (row["system"], row["record_type"], item_id,
               row.get("turn_index", 0))
        grouped[key].append(row)
        if row["llm_executed"]:
            durations[row["system"]]["complete"].append(duration)
            durations[row["system"]]["tool"].extend(tool_durations)
    first: dict[tuple, dict] = {}
    for key, attempts in grouped.items():
        numbers = [row["attempt"] for row in attempts]
        if len(numbers) != len(set(numbers)):
            raise ValueError(f"Duplicate attempt number for {key}")
        if sorted(numbers) != list(range(1, max(numbers) + 1)):
            raise ValueError(f"Missing earlier attempt for {key}")
        first[key] = min(attempts, key=lambda row: row["attempt"])
    sessions: dict[tuple[str, str], tuple[str, int]] = {}
    for (system, kind, item_id, turn), attempts in grouped.items():
        if kind != "CONVERSATION":
            continue
        for row in attempts:
            session_key = (system, row["session_id"])
            owner = (item_id, row["attempt"])
            if session_key in sessions and sessions[session_key] != owner:
                raise ValueError("Session contamination across conversations or attempts")
            sessions[session_key] = owner
            if turn == 1 and row["history_before"]:
                raise ValueError("New conversation must start with empty history")
            if turn > 1:
                prior = next((previous for previous in grouped.get((system, kind, item_id, turn - 1), [])
                              if previous["attempt"] == row["attempt"]), None)
                if prior is None or row["history_before"] != prior["history_after"]:
                    raise ValueError("Conversation history continuity broken or prior turn missing")
                if row["session_id"] != prior["session_id"]:
                    raise ValueError("Conversation session changed mid-run")
    systems: dict[str, dict] = {}
    for system in {row["system"] for row in rows}:
        system_rows = [row for row in rows if row["system"] == system]
        singles = [row for key, row in first.items() if key[0] == system and key[1] == "SINGLE_CASE"]
        conv = [row for key, row in first.items() if key[0] == system and key[1] == "CONVERSATION"]
        systems[system] = {
            "attempts": len(system_rows),
            "single_first_scored": sum(row["verdict"] != "not_scored" for row in singles),
            "single_first_correct": sum(row["verdict"] == "correct" for row in singles),
            "single_first_incorrect": sum(row["verdict"] == "incorrect" for row in singles),
            "conversation_first_turns_scored": sum(row["verdict"] != "not_scored" for row in conv),
            "repeat_attempts": sum(row["attempt"] > 1 for row in system_rows),
            "repeat_correct": sum(row["attempt"] > 1 and row["verdict"] == "correct" for row in system_rows),
            "errors_all_attempts": dict(Counter(row["error_class"] or "none" for row in system_rows)),
            "complete_response": summary_times(durations[system]["complete"]),
            "tool_calls": summary_times(durations[system]["tool"]),
        }
    single_ids = {row["case_id"] for row in rows if row["record_type"] == "SINGLE_CASE"}
    conv_ids = {row["conversation_id"] for row in rows if row["record_type"] == "CONVERSATION" and row["llm_executed"]}
    completed = 0
    for system in systems:
        for conv_id in conv_ids:
            turns = [first.get((system, "CONVERSATION", conv_id, index))
                     for index in range(1, len(scenarios[conv_id]["turns"]) + 1)]
            if all(row is not None and row["verdict"] != "not_scored" for row in turns):
                completed += 1
    comparable = []
    paired = []
    for case_id in single_ids:
        v4 = first.get(("v4", "SINGLE_CASE", case_id, 0))
        candidate = first.get(("candidate", "SINGLE_CASE", case_id, 0))
        if not v4 or not candidate or any(row["verdict"] == "not_scored" for row in (v4, candidate)):
            continue
        paired.append(case_id)
        a, b = v4["identity"], candidate["identity"]
        if (a["model_id"] == b["model_id"] and a["model_config"] == b["model_config"]
                and a["data_manifest_sha256"] == b["data_manifest_sha256"]
                and a["context_mode"] == b["context_mode"]
                and v4["initial_context_protocol"] == candidate["initial_context_protocol"]):
            comparable.append(case_id)
    llm_count = sum(row["llm_executed"] for row in rows)
    report = {
        "status": "PARTIAL" if llm_count else "NOT_RUN",
        "scoring_version": SCORING_VERSION,
        "single_cases": {"target": len(cases),
                         "scored": sum(row["verdict"] != "not_scored" for key, row in first.items()
                                       if key[1] == "SINGLE_CASE")},
        "conversations": {"planned": len(scenarios), "executed": len(conv_ids),
                          "complete": completed,
                          "turns_scored": sum(row["verdict"] != "not_scored" for key, row in first.items()
                                              if key[1] == "CONVERSATION")},
        "attempts": len(rows), "llm_executed": llm_count, "systems": systems,
        "paired_single": {
            "observed": len(paired), "calculation_comparable": len(comparable),
            "candidate_additional_correct": sum(
                first[("candidate", "SINGLE_CASE", key, 0)]["verdict"] == "correct" and
                first[("v4", "SINGLE_CASE", key, 0)]["verdict"] == "incorrect"
                for key in comparable),
            "candidate_regressions": sum(
                first[("candidate", "SINGLE_CASE", key, 0)]["verdict"] == "incorrect" and
                first[("v4", "SINGLE_CASE", key, 0)]["verdict"] == "correct"
                for key in comparable),
        },
    }
    if all(system in systems and systems[system]["single_first_scored"] == len(cases)
           for system in ("v4", "candidate")) and completed == 2 * len(scenarios):
        report["status"] = "EVALUATED_REVIEW_REQUIRED"
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path)
    parser.add_argument("--holdout", type=Path)
    parser.add_argument("--evidence-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cases, scenarios = load_cases(args.holdout), load_scenarios()
    rows = [] if not args.runs else [json.loads(line) for line in args.runs.read_text(encoding="utf-8").splitlines() if line.strip()]
    case_hash = sha(DEVELOPMENT.read_bytes() + args.holdout.read_bytes()) if args.holdout else sha(DEVELOPMENT.read_bytes())
    report = summarize(rows, cases, scenarios, args.evidence_root, case_hash)
    output = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
