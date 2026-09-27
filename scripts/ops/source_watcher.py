"""Compare supplied metadata, never fetch URLs, change datasets or promote a candidate."""
from __future__ import annotations
import argparse
import json
import re
from datetime import date
from pathlib import Path

def detect(known, candidate):
    if not isinstance(known, dict) or not isinstance(candidate, dict):
        raise ValueError("Known and candidate metadata must be JSON objects")
    proposal = {"source_id": known.get("source_id"), "old_period": known.get("period"),
                "new_period": candidate.get("period"), "schema_diff": {},
                "rows_added": None, "rows_removed": None, "rows_changed": None, "coverage_change": None,
                "validation_status": "NOT_RUN", "benchmark_status": "NOT_RUN", "risk": "UNKNOWN",
                "human_actions": ["Review candidate provenance; validate, transform, QA and benchmark in isolation.",
                                  "Approve a new version explicitly; never overwrite stable data."]}
    def result(status, reason):
        return {"status": status, "reason": reason, "proposal": proposal, "automatic_promotion": False}
    if candidate.get("available") is False:
        return result("SOURCE_UNAVAILABLE", "Candidate explicitly unavailable; cached data remain unchanged.")
    required = {"source_id", "official_url", "period", "sha256", "schema", "primary_key"}
    if not required <= known.keys() or not required <= candidate.keys():
        return result("REVIEW_REQUIRED", "Incomplete metadata; cannot infer no change.")
    for item in (known, candidate):
        if any(not isinstance(item[k], str) or not item[k].strip() for k in ('source_id','official_url','primary_key')):
            return result("REVIEW_REQUIRED", "Invalid identity metadata.")
        if isinstance(item['schema'], dict) and any(not isinstance(k, str) or not isinstance(v, str) or not v for k,v in item['schema'].items()):
            return result("REVIEW_REQUIRED", "Schema must map field names to explicit type names.")
    if any(candidate[k] != known[k] for k in ("source_id", "official_url", "primary_key")):
        return result("REVIEW_REQUIRED", "Identity, provenance URL or primary key changed.")
    try:
        if date.fromisoformat(candidate["period"]) < date.fromisoformat(known["period"]):
            return result("REVIEW_REQUIRED", "Reference period moved backwards.")
        for item in (known, candidate):
            if not isinstance(item["schema"], dict) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
                return result("REVIEW_REQUIRED", "Invalid schema/hash representation.")
    except (ValueError, TypeError):
        return result("REVIEW_REQUIRED", "Invalid period metadata.")
    proposal["schema_diff"] = {k: {"old": known["schema"].get(k), "new": candidate["schema"].get(k)}
                               for k in sorted(set(known["schema"]) | set(candidate["schema"]))
                               if known["schema"].get(k) != candidate["schema"].get(k)}
    if proposal["schema_diff"]:
        proposal["risk"] = "HIGH"
        return result("SCHEMA_CHANGE", "Transform compatibility must be reviewed before use.")
    if "rows" in known and "rows" in candidate:
        key = known["primary_key"]
        try:
            def index(rows):
                if not isinstance(rows, list):
                    raise ValueError("Expected records")
                result = {r[key]: r for r in rows}
                if len(result) != len(rows) or any(k in (None, "") for k in result):
                    raise ValueError("Duplicate/missing key")
                return result
            a, b = index(known["rows"]), index(candidate["rows"])
            proposal.update(rows_added=len(b.keys()-a.keys()), rows_removed=len(a.keys()-b.keys()),
                            rows_changed=sum(a[k] != b[k] for k in a.keys() & b.keys()),
                            coverage_change=len(b)-len(a))
        except (KeyError, TypeError, ValueError):
            return result("REVIEW_REQUIRED", "Malformed row metadata; no safe keyed diff.")
    changed = candidate["sha256"] != known["sha256"] or candidate["period"] != known["period"]
    row_change = any(proposal[k] for k in ("rows_added", "rows_removed", "rows_changed"))
    if row_change and not changed:
        return result("REVIEW_REQUIRED", "Rows differ but declared content identity does not.")
    proposal["risk"] = "REVIEW" if changed else "NONE"
    return result("POTENTIAL_UPDATE" if changed else "NO_CHANGE", "Metadata comparison only; no remote availability or content verification.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--known", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(detect(json.loads(args.known.read_text(encoding="utf-8")), json.loads(args.candidate.read_text(encoding="utf-8"))),
                     ensure_ascii=False, indent=2, allow_nan=False))

if __name__ == "__main__":
    main()
