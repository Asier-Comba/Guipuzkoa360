import copy

import pytest

from prototypes.ir_y_volver import provider_r6
from scripts.mobility import r13_properties as qa


def test_seeded_generator_reproduces_and_covers_declared_families():
    left, right = list(qa.generated_requests(120)), list(qa.generated_requests(120))
    assert left == right
    assert len(left) == 120
    assert {row[2].get("origin_id") for row in left if type(row[2]) is dict and type(row[2].get("origin_id")) is str} >= set(qa.ORIGINS)
    families = {family for _, family, _ in left}
    assert len(families) == 18
    assert {"duration_boundary", "arrival_boundary", "boarding_boundary", "return_deadline_boundary", "legacy_explicit", "missing_field", "extra_field", "wrong_top_level"} <= families
    # Four modulo shards partition exactly the same generator indices.
    shards = [{index for index, _, _ in left if index % 4 == shard} for shard in range(4)]
    assert set.union(*shards) == set(range(120))
    assert sum(map(len, shards)) == 120


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), True, [], {}, "20", None])
def test_nonfinite_and_wrong_numeric_input_is_controlled(value):
    request = {**qa.BASE, "duration_minutes": value}
    result = provider_r6.plan_visit(request)
    assert result["status"] == "error" and result["itinerary"] is None
    qa.check_result(result, request)
    qa.canonical(result)


@pytest.mark.parametrize("mutant", ["route_id", "total", "source", "extra", "nan"])
def test_property_checker_rejects_distinct_corruptions(mutant):
    request = qa.BASE
    result = copy.deepcopy(provider_r6.plan_visit(request))
    if mutant == "route_id":
        result["itinerary"]["outbound"]["route_id"] = "fake"
    elif mutant == "total":
        result["itinerary"]["total_s"] += 1
    elif mutant == "source":
        result["sources"][0]["source_sha256"] = "0" * 64
    elif mutant == "extra":
        result["extra"] = True
    else:
        result["walking"]["outbound"]["total_metres"] = float("nan")
    with pytest.raises((AssertionError, ValueError, KeyError)):
        qa.check_result(result, request)


def test_metamorphic_cases_keep_one_variable_or_explicit_default_equivalence():
    cases = qa.metamorphic_cases()
    assert len(cases) == 23
    for case in cases:
        if "changed_field" not in case:
            continue
        left, right = case["requests"][:2]
        differences = {key for key in left.keys() | right.keys() if left.get(key) != right.get(key)}
        assert differences == {case["changed_field"]}
    default = next(case for case in cases if case.get("default_pair"))
    qa.check_metamorphic(provider_r6.compare_visits(default["requests"]), default)


def test_comparison_truth_rejects_a_fabricated_cross_origin_delta():
    case = next(case for case in qa.metamorphic_cases() if case.get("changed_field") == "origin_id")
    raw = provider_r6.compare_visits(case["requests"])
    qa.check_metamorphic(raw, case)
    raw["comparisons"][0]["total_difference_s"] = 0
    with pytest.raises(AssertionError):
        qa.check_metamorphic(raw, case)


@pytest.mark.parametrize("change", [None, "claims", "outcomes", "raw", "comparison", "message", "input", "case"])
def test_structural_comparison_rejection_is_narrow_and_never_has_numeric_truth(change):
    from scripts.mobility.evidence_r13 import controlled_invalid_comparison
    case = next(c for c in qa.metamorphic_cases() if c["case_id"] == "invalid_change_no_delta")
    value = dict(status="error", error=dict(code="contract_violation", message="health:invalid_duration", safe_next_action="Correct request"),
                 claims=[], outcomes=[], effective_request=None, normalized_input={"arguments": {"request": copy.deepcopy(case["requests"])}})
    record = dict(envelope=copy.deepcopy(value), view=copy.deepcopy(value))
    if change == "claims":
        record["view"]["claims"] = [{"value": 42}]
    elif change == "outcomes":
        record["view"]["outcomes"] = [{"status": "ok"}]
    elif change == "raw":
        record["envelope"]["raw_result_json"] = "{}"
    elif change == "comparison":
        record["view"]["mobility"] = {"comparisons": [{"total_difference_s": 0}]}
    elif change == "message":
        record["view"]["error"]["message"] = "data_unavailable"
    elif change == "input":
        record["view"]["normalized_input"]["arguments"]["request"][1]["duration_minutes"] = 20
    elif change == "case":
        case = {**case, "case_id": "another_failure"}
    assert controlled_invalid_comparison(record, case) == (change is None)
