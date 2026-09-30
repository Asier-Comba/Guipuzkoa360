"""Public truth fixtures, synthetic mutations and independent CSV spot checks.

No final answer text, required wording/tool sequence, holdout or runtime writes.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import zipfile

from scripts.mobility import intake_candidate_r12 as gate
from scripts.mobility.r13_properties import BASE, ORIGINS, HEALTH_ID, LEGACY_ID, check_result, check_metamorphic, metamorphic_cases, raw_spot_check
from scripts.mobility.verify_r13 import batched, dump


def truth_cases():
    return [dict(case_id=name, operation="plan", request=request, intent=intent) for name, request, intent in (
        ("MAIN", {**BASE, "appointment_time": "09:30"}, "Ida y vuelta desde las paradas de Zegama para una consulta hipotética de veinte minutos a las 09:30."),
        ("VARIATION", BASE.copy(), "Recalcular la misma visita cambiando únicamente la hora a las 09:45."),
        ("DURATION", {**BASE, "duration_minutes": 26}, "Recalcular el regreso si la consulta hipotética dura veintiséis minutos."),
        ("LIMIT_DATE", {**BASE, "date": "2026-09-30"}, "Consultar otra fecha sin sustituirla por la fecha validada."),
        ("LIMIT_SCOPE", {**BASE, "destination_id": "outside_catalog"}, "Reconocer un destino que no pertenece al catálogo disponible."),
        ("ERROR", {**BASE, "duration_minutes": "20"}, "Reconocer un parámetro numérico con tipo incorrecto sin inventar cifras."),
        ("UNKNOWN_SNAPSHOT", {**BASE, "snapshot_id": "missing_snapshot"}, "Reconocer un snapshot ausente sin caer a otro conjunto de datos."))]


def controlled_invalid_comparison(record, case):
    """One typed-input boundary, not a blanket waiver for comparison failures."""
    if case.get("case_id") != "invalid_change_no_delta" or case.get("requests") != [BASE, {**BASE, "duration_minutes": "20"}]:
        return False
    envelope, view = record.get("envelope", {}), record.get("view", {})
    if record.get("error_stage") or envelope.get("raw_result_json") is not None:
        return False
    for value in (envelope, view):
        error = value.get("error") or {}
        if value.get("status") != "error" or error.get("code") != "contract_violation" or error.get("message") != "health:invalid_duration" or not error.get("safe_next_action"):
            return False
        if value.get("claims") != [] or value.get("outcomes") != [] or value.get("effective_request") is not None:
            return False
        if (value.get("mobility") or {}).get("scenarios") or (value.get("mobility") or {}).get("comparisons"):
            return False
        if (value.get("normalized_input") or {}).get("arguments", {}).get("request") != case["requests"]:
            return False
    return True


def mutations(raw, view, labels, requirements, compared_raw, compared_view):
    from scripts.mobility.audit_r7 import mutation_matrix
    original = mutation_matrix()
    rows = original["results"][:]
    for name, edit in (("route_id", lambda x: x["itinerary"]["outbound"].update(route_id="fake")),
                       ("source_id", lambda x: x["sources"][0].update(source_id="fabricated"))):
        value = copy.deepcopy(raw)
        edit(value)
        try:
            check_result(value, BASE)
        except (AssertionError, ValueError, KeyError) as exc:
            rows.append(dict(mutation=name, classification="R13_RAW_SEMANTIC_CAUGHT", reason=str(exc)))
        else:
            rows.append(dict(mutation=name, classification="GAP", severity="HIGH", owner="W1 verifier"))
    for name in ("stop_label", "comparability", "comparison_delta"):
        value = copy.deepcopy(view if name == "stop_label" else compared_view)
        expected = raw if name == "stop_label" else compared_raw
        if name == "stop_label":
            value["mobility"]["scenarios"][0]["itinerary"]["outbound"]["to_stop_label"] = "Invented stop"
        elif name == "comparability":
            value["mobility"]["comparisons"][0]["comparability"] = "not_comparable"
        else:
            value["mobility"]["comparisons"][0]["total_difference_s"] = 999999
        findings, _, _ = gate.validate_view(value, expected, labels, requirements, dict(operation="plan" if name == "stop_label" else "compare"))
        rows.append(dict(mutation=name, classification="R12_SCOPED_VIEW_CAUGHT" if findings else "GAP", findings=findings))
    assert len({row["mutation"] for row in rows}) == len(rows), "duplicate mutation counted"
    gaps = [row for row in rows if row["classification"] == "GAP"]
    return dict(status="FAIL" if gaps else "PASS", attempted=len(rows), caught=len(rows) - len(gaps), gaps=gaps,
                synthetic_copies_only=True, candidate_bytes_changed=False, results=rows)


def run(package, manifest_path, output, stress_summary):
    # Producer imports below live only in this QA parent; candidate workers use -I
    # and their own extracted root, never inheriting this loaded module namespace.
    from scripts.mobility.audit_r7 import HEALTH
    from scripts.mobility.verify_health_r5 import read_raw
    manifest = gate.strict_json(manifest_path.read_text(encoding="utf-8"))
    verified = gate.inspect(package, manifest)
    assert verified["compatible"] and not verified["policy"]
    requirements = json.loads((gate.DOC / "MODEL_VIEW_REQUIREMENTS_R11.json").read_bytes())["requirements"]
    cases = metamorphic_cases() + truth_cases()
    oracle = batched("oracle", gate.ROOT, cases, size=2)
    with tempfile.TemporaryDirectory(prefix="g360-r13-expanded-") as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(package) as archive:
            archive.extractall(root)
        actual = batched("candidate", root, cases, size=2)
        ordinary = [case for case in cases if case["case_id"] != "invalid_change_no_delta"]
        records, errors = gate.evaluate(oracle, actual, ordinary, requirements)
        rejected_case = next(case for case in cases if case["case_id"] == "invalid_change_no_delta")
        rejected_record = next(record for record in actual["records"] if record["case_id"] == rejected_case["case_id"])
        safe_rejection = controlled_invalid_comparison(rejected_record, rejected_case)
        records.append(dict(case_id=rejected_case["case_id"], operation="compare", raw_status="PASS" if safe_rejection else "FAIL",
                            model_status="PASS" if safe_rejection else "FAIL", assertions=1,
                            raw_binding="controlled_structural_comparison_rejection_without_numeric_evidence",
                            applicability=[dict(status="NOT_APPLICABLE", reason="Consumer input contract rejects the whole comparison's string duration; producer returns per-scenario error. No projected partial result or delta is permitted.")],
                            findings=[] if safe_rejection else [gate.issue("INVALID_COMPARISON_NOT_SAFELY_REJECTED", rejected_case["case_id"], severity="critical")]))
        for batch in (*oracle["batches"], *actual["batches"]):
            errors.extend(gate.import_closure(batch, verified))
    findings = [finding for record in records for finding in record["findings"]]
    if errors or findings or not all(row["raw_status"] == row["model_status"] == "PASS" for row in records):
        dump(output / "expanded_failed_attempt.json", dict(cases=cases, records=records, oracle=oracle, candidate=actual, errors=errors, findings=findings))
        raise AssertionError((errors, findings))
    expected = {row["case_id"]: row["raw"] for row in oracle["records"]}
    observed = {row["case_id"]: row for row in actual["records"]}
    for case in metamorphic_cases():
        check_metamorphic(expected[case["case_id"]], case)
    # Metamorphic comparisons belong to the stress phase. Do not start mutation,
    # raw-source spot-check or final truth publication until mass stress is green.
    waited = time.perf_counter()
    while not stress_summary.is_file():
        if time.perf_counter() - waited > 2700:
            raise TimeoutError("mass-stress prerequisite not completed")
        time.sleep(1)
    stress = json.loads(stress_summary.read_bytes())
    assert stress["status"] == "PASS" and stress["generated_requests"] == 20000 and stress["producer_executions"] == 40000, "mass-stress prerequisite failed"
    first_comparison = metamorphic_cases()[0]["case_id"]
    mutation_report = mutations(expected["VARIATION"], observed["VARIATION"]["view"], oracle["labels"], requirements,
                                expected[first_comparison], observed[first_comparison]["view"])
    dump(output / "mutations.json", mutation_report)
    assert mutation_report["status"] == "PASS", mutation_report["gaps"]
    # Independent expected trip selection and every component are rebuilt from raw
    # CSV and measured pinned geometry. Producer values are only observed outputs.
    raw_csv = read_raw()
    spot_requests = []
    for index in range(24):
        request = {**BASE, "origin_id": ORIGINS[index % 3],
                   "appointment_time": ("09:30", "09:45", "10:15", "11:00")[(index // 3) % 4],
                   "duration_minutes": (20, 26)[index // 12]}
        if index % 2:
            request.update(arrival_margin_minutes=1, boarding_margin_minutes=7)
        spot_requests.append(dict(case_id=f"spot_{index:02d}", operation="plan", request=request))
    spot_oracle = batched("oracle", gate.ROOT, spot_requests)
    spots = []
    for case, record in zip(spot_requests, spot_oracle["records"]):
        if record["raw"]["status"] == "ok" and len(spots) < 20:
            spots.append({"case_id": case["case_id"], **raw_spot_check(case["request"], record["raw"], raw_csv, HEALTH)})
    assert len(spots) == 20 and {row["request"]["origin_id"] for row in spots} == set(ORIGINS)
    dump(output / "raw_source_spot_check.json", dict(status="PASS", cases=spots, count=len(spots), selection="First 20 successful cases of fixed 24-case stratified public list; all requests retained", requests=spot_requests,
                                                   expected_method="CSV calendar/trips/stop sequences/ordinary pickup-dropoff + independently measured pinned walking geometry/formula; provider output never used as expected",
                                                   gtfs_sha256=hashlib.sha256((gate.ROOT / "datos_originales/movilidad/goierrialdea-3276fcae.zip").read_bytes()).hexdigest()))
    public = []
    forbidden = ["Observed travel saving, causality, guaranteed punctuality, prediction or best appointment time",
                 "Available appointment, verified entrance, door-to-door journey, universal accessibility",
                 "No buses/services exist merely because evidence is missing or no modeled pair is feasible"]
    for case in truth_cases():
        result = expected[case["case_id"]]
        claims, reconstruction = [], None
        if result["status"] == "ok":
            reconstruction = raw_spot_check(case["request"], result, raw_csv, HEALTH)
            for field, value in reconstruction["reconstructed_components_s"].items():
                claims.append(dict(metric=field, value=value, unit="second", period="2026-09-29", basis="hypothetical input" if field == "appointment_s" else "scheduled/modelled calculation"))
            claims.append(dict(metric="total_s", value=reconstruction["expected"]["total_s"], unit="second", period="2026-09-29", basis="independent raw-source reconstruction"))
        public.append(dict(case_id=case["case_id"], natural_intent_description=case["intent"], structured_request=case["request"],
                           expected_status=result["status"], expected_error=result["error"],
                           expected_consumer_envelope_status=observed[case["case_id"]]["view"]["status"],
                           status_mapping_note="Producer scenario status differs from consumer envelope status; missing snapshot and invalid structure may be safely rejected without raw/numeric claims.",
                           critical_semantic_facts=dict(snapshot_id=result["snapshot_id"], time_basis=result["time_basis"], scenario_kind=result["scenario_kind"],
                                                       health_destination=result.get("health_destination"), itinerary=result["itinerary"]),
                           numeric_claims=claims, source_facts=result["sources"], limits=result["limitations"] + forbidden[1:], forbidden_claims=forbidden,
                           verification_class="INDEPENDENT_CSV_AND_PINNED_GEOMETRY" if reconstruction else "PUBLIC_CONTRACT_STATUS_FIXTURE"))
    totals = {row["case_id"]: next((claim["value"] for claim in row["numeric_claims"] if claim["metric"] == "total_s"), None) for row in public}
    assert totals["MAIN"] == 10691 and totals["VARIATION"] == 8591
    contrast = dict(left_case="MAIN", right_case="VARIATION", left_total_s=totals["MAIN"], right_total_s=totals["VARIATION"], signed_delta_s=totals["VARIATION"] - totals["MAIN"], signed_delta_minutes=-35,
                    interpretation="Conditional difference between two scheduled/modelled scenarios with other inputs held constant; not observed saving, prediction or recommendation",
                    verification="Two independent raw-source reconstructions, then right minus left")
    truth = dict(version="r13.0", public_cases_only=True, cases=public, contrast=contrast,
                 runtime_git=gate.REAL_PIN, r6_zip_sha256=gate.R6_SHA, w2_zip_sha256=gate.digest(package.read_bytes()),
                 final_natural_language_answer_included=False, required_prompt_or_tool_sequence=False, holdout_included=False,
                 llm="NOT_CLAIMED", portal="NOT_CLAIMED")
    dump(output / "FINAL_ORACLE_R13.json", truth)
    expanded = dict(status="PASS", metamorphic_cases=len(metamorphic_cases()), metamorphic_scenarios=sum(len(c["requests"]) for c in metamorphic_cases()),
                    raw=len(records), model_view=len(records), assertions=sum(r["assertions"] for r in records),
                    findings=findings, verifier_errors=errors, records=records, oracle=oracle, candidate=actual,
                    assumptions=["No monotonicity across timetable changes asserted", "A-B-A tested within each triple; explicit vs omitted defaults retain distinct provenance"],
                    support_identity={p.name: gate.digest(p.read_bytes()) for p in (Path(__file__), Path(__file__).with_name("r13_properties.py"), Path(__file__).with_name("verify_r13.py"))})
    dump(output / "expanded_intake.json", expanded)
    summary = dict(status="PASS", metamorphic_cases=len(metamorphic_cases()), metamorphic_scenarios=expanded["metamorphic_scenarios"], mutation_attempted=mutation_report["attempted"], mutation_caught=mutation_report["caught"], mutation_gaps=len(mutation_report["gaps"]),
                   raw_spots=len(spots), public_truth_cases=len(public), final_oracle_sha256=gate.digest((output / "FINAL_ORACLE_R13.json").read_bytes()), contrast=contrast)
    dump(output / "evidence_summary.json", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stress-summary", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.package.resolve(), args.manifest.resolve(), args.output.resolve(), args.stress_summary.resolve())))
