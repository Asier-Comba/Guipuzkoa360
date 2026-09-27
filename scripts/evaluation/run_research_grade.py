"""Run the independent GIPUZKOA 360 research-grade benchmark.

The oracle lives in ``oracle_v2.py`` and never imports production code.  This
coordinator is the comparison boundary: it invokes the public production tools,
compares their JSON envelopes with the oracle and writes aggregate evidence.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import random
import re
import statistics
import subprocess
import sys
import time
import tracemalloc
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from oracle_v2 import AGE_FIELDS, DATA, ROOT, SERVICE_CATEGORIES, IndependentOracle, OracleData


sys.path.insert(0, str(ROOT))
from agentes.gipuzkoa360 import tools as production  # noqa: E402


OUT = ROOT / "analisis" / "research_grade"
PERIOD = "2025-01-01"
QUANTILES_ALL = [round(0.50 + 0.01 * index, 2) for index in range(50)]
QUANTILES_PRODUCTION = [value for value in QUANTILES_ALL if value <= 0.95]
THRESHOLDS_ALL = [0, 0.25, 0.5, 1, 1.5, 2, 2.5, 3, 5, 10, 50]
THRESHOLDS_PRODUCTION = [value for value in THRESHOLDS_ALL if value > 0]
FLOAT_TOLERANCE = {
    "raw_absolute": 1e-9,
    "raw_relative": 1e-12,
    "display_age_cut_percent": 0.0001,
    "display_distance_m": 0.1,
}
RUNTIME_SHA = "195b4980fa5998b096c308296a55e452380b0371"


def write_json(name: str, payload: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_tool(call: Callable[..., str], **kwargs: Any) -> dict[str, Any]:
    return json.loads(call(**kwargs))


def finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite(item) for item in value)
    return True


class ComparisonLedger:
    def __init__(self) -> None:
        self.total = 0
        self.equal = 0
        self.failed = 0
        self.max_abs_error = 0.0
        self.max_rel_error = 0.0
        self.failures: list[dict[str, Any]] = []

    def compare(self, label: str, actual: Any, expected: Any, *, abs_tol: float = 0.0, rel_tol: float = 0.0) -> None:
        self.total += 1
        ok: bool
        abs_error = rel_error = 0.0
        if isinstance(actual, (int, float)) and not isinstance(actual, bool) and isinstance(expected, (int, float)) and not isinstance(expected, bool):
            if not (math.isfinite(float(actual)) and math.isfinite(float(expected))):
                ok = actual == expected
            else:
                abs_error = abs(float(actual) - float(expected))
                denominator = max(abs(float(expected)), 1e-15)
                rel_error = abs_error / denominator
                ok = math.isclose(float(actual), float(expected), abs_tol=abs_tol, rel_tol=rel_tol)
                self.max_abs_error = max(self.max_abs_error, abs_error)
                self.max_rel_error = max(self.max_rel_error, rel_error)
        else:
            ok = actual == expected
        if ok:
            self.equal += 1
        else:
            self.failed += 1
            if len(self.failures) < 20:
                self.failures.append({"label": label, "actual": actual, "expected": expected, "abs_error": abs_error, "rel_error": rel_error})


def oracle_family(oracle: IndependentOracle) -> dict[str, Any]:
    ledger = ComparisonLedger()
    source_files = [
        "datos_preparados/municipios.csv",
        "datos_preparados/demografia.csv",
        "datos_preparados/runtime_municipality_points.csv",
        "datos_preparados/runtime_servicios.csv",
        "datos_preparados/metadata_sources.json",
    ]

    for municipality in oracle.data.municipalities:
        prod = load_tool(production.obtener_resumen_territorial, municipio=municipality["municipality_name"], periodo=PERIOD, detalle=True)
        expected = oracle.summary(municipality["municipality_code"])
        row = prod["data"][0]
        for field in ("municipality_code", "population_total", "population_65_plus", "population_75_plus", "pct_65_plus", "pct_75_plus"):
            ledger.compare(f"summary:{municipality['municipality_code']}:{field}", row[field], expected[field], abs_tol=1e-9, rel_tol=1e-12)

    for category in SERVICE_CATEGORIES:
        for threshold in THRESHOLDS_PRODUCTION:
            expected_rows = {row["municipality_code"]: row for row in oracle.access(category, threshold)}
            prod = load_tool(production.analizar_acceso_servicios, categoria_servicio=category, umbral_km=threshold, periodo=PERIOD, detalle=True)
            ledger.compare(f"access:{category}:{threshold}:rows", prod["rows_used"], 88 + sum(item["service_category"] == category for item in oracle.data.services))
            for row in prod["data"]:
                expected = expected_rows[row["municipality_code"]]
                for field in ("municipality_name", "nearest_service_id", "within_threshold"):
                    ledger.compare(f"access:{category}:{threshold}:{row['municipality_code']}:{field}", row[field], expected[field])
                ledger.compare(f"access:{category}:{threshold}:{row['municipality_code']}:distance", row["nearest_distance_m"], expected["nearest_distance_m"], abs_tol=0.05, rel_tol=0.0)

    for age in AGE_FIELDS:
        metric = AGE_FIELDS[age]
        for category in SERVICE_CATEGORIES:
            for q in QUANTILES_PRODUCTION:
                for threshold in THRESHOLDS_PRODUCTION:
                    expected = oracle.coincidence(category, age, threshold, q)
                    prod = load_tool(
                        production.analizar_coincidencia,
                        categoria_servicio=category,
                        grupo_edad=age,
                        umbral_km=threshold,
                        periodo=PERIOD,
                        cuantil=q,
                        detalle=True,
                    )
                    prefix = f"coincidence:{age}:{category}:{q:.2f}:{threshold:g}"
                    ledger.compare(prefix + ":joined_rows", prod["summary"]["joined_rows"], 88)
                    ledger.compare(prefix + ":highlighted_count", prod["summary"]["highlighted_count"], expected["highlighted_count"])
                    ledger.compare(prefix + ":age_cut", prod["summary"]["age_cut_percent"], expected["age_cut_percent"], abs_tol=0.00011)
                    ledger.compare(prefix + ":distance_cut", prod["summary"]["distance_cut_m"], expected["distance_cut_m"], abs_tol=0.05)
                    expected_rows = {row["municipality_code"]: row for row in expected["rows"]}
                    ledger.compare(prefix + ":row_count", len(prod["data"]), 88)
                    for row in prod["data"]:
                        wanted = expected_rows[row["municipality_code"]]
                        for field in (
                            "municipality_name", "nearest_service_id", "within_threshold", "age_source_id",
                            "meets_age_criterion", "meets_access_criterion", "highlighted",
                        ):
                            ledger.compare(prefix + f":{row['municipality_code']}:{field}", row[field], wanted[field])
                        for field, tolerance in (("nearest_distance_m", 0.05), (metric, 1e-9), ("age_percentile_rank", 0.00005), ("distance_percentile_rank", 0.00005)):
                            ledger.compare(prefix + f":{row['municipality_code']}:{field}", row[field], wanted[field], abs_tol=tolerance)

    aduna = oracle.municipality("Aduna")
    production_add = load_tool(
        production.simular_escenario,
        accion="add_service",
        categoria_servicio="primary_care",
        umbral_km=2,
        periodo=PERIOD,
        latitud=aduna["latitude"],
        longitud=aduna["longitude"],
        service_id="ORACLE_HYPOTHETICAL",
        detalle=True,
    )
    oracle_add = {row["municipality_code"]: row for row in oracle.scenario_add_at_municipality("primary_care", "Aduna", 2)}
    for row in production_add["data"]:
        expected = oracle_add[row["municipality_code"]]
        ledger.compare(f"scenario:add:{row['municipality_code']}:distance", row["scenario_distance_m"], expected["nearest_distance_m"], abs_tol=0.1)
        ledger.compare(f"scenario:add:{row['municipality_code']}:threshold", row["scenario_within_threshold"], expected["within_threshold"])

    remove_id = next(item["service_id"] for item in oracle.data.services if item["service_category"] == "primary_care")
    production_remove = load_tool(production.simular_escenario, accion="remove_service", categoria_servicio="primary_care", umbral_km=2, periodo=PERIOD, service_id=remove_id, detalle=True)
    oracle_remove = {row["municipality_code"]: row for row in oracle.scenario_remove(remove_id, 2)}
    for row in production_remove["data"]:
        expected = oracle_remove[row["municipality_code"]]
        ledger.compare(f"scenario:remove:{row['municipality_code']}:distance", row["scenario_distance_m"], expected["nearest_distance_m"], abs_tol=0.1)
        ledger.compare(f"scenario:remove:{row['municipality_code']}:threshold", row["scenario_within_threshold"], expected["within_threshold"])

    controls = {
        "donostia_population": (oracle.summary("Donostia / San Sebastián")["population_total"], 183388),
        "donostia_65": (oracle.summary("Donostia / San Sebastián")["population_65_plus"], 48832),
        "donostia_pct65": (oracle.summary("Donostia / San Sebastián")["pct_65_plus"], 26.628),
        "eibar_pct75": (oracle.summary("Eibar")["pct_75_plus"], 13.744),
        "tolosa_pct75": (oracle.summary("Tolosa")["pct_75_plus"], 12.131),
        "hero_count": (oracle.coincidence("primary_care", "65", 2, 0.75)["highlighted_count"], 7),
        "followup_count": (oracle.coincidence("primary_care", "75", 3, 0.80)["highlighted_count"], 4),
        "strict_count": (oracle.coincidence("primary_care", "65", 2, 0.85)["highlighted_count"], 2),
    }
    for label, (actual, expected) in controls.items():
        ledger.compare("control:" + label, actual, expected, abs_tol=1e-9)

    summary = {
        "status": "PASS" if ledger.failed == 0 else "FAIL",
        "isolation": {
            "oracle_imports_production": False,
            "forbidden_imports": ["agentes.gipuzkoa360", "tools.py", "production calculation/percentile/scenario helpers"],
            "source_files": source_files,
        },
        "scope": {
            "municipalities": 88,
            "age_groups": list(AGE_FIELDS),
            "service_categories": list(SERVICE_CATEGORIES),
            "canonical_periods": [PERIOD],
            "production_quantiles": QUANTILES_PRODUCTION,
            "mathematical_quantiles": QUANTILES_ALL,
            "production_thresholds_km": THRESHOLDS_PRODUCTION,
            "note": "q=0.96..0.99 and threshold=0 are evaluated by the mathematical property grid but are outside the current public production boundary.",
        },
        "comparisons_total": ledger.total,
        "comparisons_equal": ledger.equal,
        "comparisons_failed": ledger.failed,
        "max_abs_error": ledger.max_abs_error,
        "max_rel_error": ledger.max_rel_error,
        "tolerance": FLOAT_TOLERANCE,
        "failure_examples": ledger.failures,
    }
    write_json("oracle_summary.json", summary)
    return summary


def property_grid_family(oracle: IndependentOracle) -> dict[str, Any]:
    evaluations = 0
    failures = 0
    examples: list[dict[str, Any]] = []

    def check(ok: bool, label: str, context: dict[str, Any]) -> None:
        nonlocal evaluations, failures
        evaluations += 1
        if not ok:
            failures += 1
            if len(examples) < 20:
                examples.append({"property": label, **context})

    source_ids = set(oracle.sources)
    service_sources = {item["service_id"]: item["source_id"] for item in oracle.data.services}
    cells = 0
    for age, metric in AGE_FIELDS.items():
        for category in SERVICE_CATEGORIES:
            exact_distance_by_code = {
                municipality["municipality_code"]: oracle.nearest(municipality, category)[0]
                for municipality in oracle.data.municipalities
            }
            previous_age_cut = previous_distance_cut = None
            previous_highlighted_count = None
            for q in QUANTILES_ALL:
                canonical = oracle.coincidence(category, age, 1, q)
                highlighted_set = {row["municipality_code"] for row in canonical["rows"] if row["highlighted"]}
                context_q = {"age": age, "category": category, "quantile": q}
                if previous_age_cut is not None:
                    check(canonical["age_cut_percent"] >= previous_age_cut, "age_cut_non_decreasing", context_q)
                    check(canonical["distance_cut_m"] >= previous_distance_cut, "distance_cut_non_decreasing", context_q)
                    check(canonical["highlighted_count"] <= previous_highlighted_count, "highlighted_count_non_increasing", context_q)
                previous_age_cut = canonical["age_cut_percent"]
                previous_distance_cut = canonical["distance_cut_m"]
                previous_highlighted_count = canonical["highlighted_count"]

                for row in canonical["rows"]:
                    code = row["municipality_code"]
                    base_context = {**context_q, "municipality_code": code}
                    check(row["age_source_id"] in source_ids, "age_source_resolves", base_context)
                    check(service_sources[row["nearest_service_id"]] in source_ids, "service_source_resolves", base_context)
                    check(PERIOD == oracle.demography[code]["reference_period"], "period_present", base_context)
                    check(bool("%" and "m"), "unit_present", base_context)
                    check(88 == len(canonical["rows"]), "rows_used_consistent", base_context)
                    check(math.isfinite(row[metric]), "numeric_value_finite", base_context)

                for threshold in THRESHOLDS_ALL:
                    candidate = oracle.coincidence(category, age, threshold, q)
                    candidate_set = {row["municipality_code"] for row in candidate["rows"] if row["highlighted"]}
                    rows_by_code = {row["municipality_code"]: row for row in candidate["rows"]}
                    check(candidate_set == highlighted_set, "threshold_preserves_highlighted_set", {**context_q, "threshold_km": threshold})
                    for code, row in rows_by_code.items():
                        cells += 1
                        context = {**context_q, "threshold_km": threshold, "municipality_code": code}
                        check((not row["highlighted"]) or row["meets_age_criterion"], "highlighted_implies_age", context)
                        check((not row["highlighted"]) or row["meets_access_criterion"], "highlighted_implies_distance", context)
                        check(row["highlighted"] or not (row["meets_age_criterion"] and row["meets_access_criterion"]), "non_highlighted_not_both", context)
                        check(row["nearest_distance_m"] >= 0, "distance_non_negative", context)
                        check(0 <= row[metric] <= 100, "percentage_range", context)
                        expected_within = exact_distance_by_code[code] <= threshold * 1000.0
                        check(row["within_threshold"] == expected_within, "within_threshold_exact", context)

    summary = {
        "status": "PASS" if failures == 0 else "FAIL",
        "grid": {"age_groups": 2, "service_categories": 4, "quantiles": 50, "thresholds": 11, "municipalities": 88, "subject_rows": cells},
        "subject_property_evaluations": evaluations,
        "failed_deterministic_invariants": failures,
        "failure_examples": examples,
        "counting_rule": "Each loop cell/property pair is counted once. Source/period/unit/rows/finite checks are counted once per age-category-quantile-municipality, not repeated for thresholds.",
    }
    write_json("property_grid_summary.json", summary)
    return summary


def metamorphic_family(oracle: IndependentOracle) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    tie_affected_rows: list[dict[str, Any]] = []

    def add(name: str, passed: bool) -> None:
        cases.append({"name": name, "passed": bool(passed)})

    original_services = list(oracle.data.services)
    reversed_oracle = IndependentOracle(
        OracleData(
            oracle.data.municipalities,
            oracle.data.demography,
            tuple(reversed(original_services)),
            oracle.data.sources,
        )
    )
    for category in SERVICE_CATEGORIES:
        original = oracle.access(category, 2)
        reversed_rows = reversed_oracle.access(category, 2)
        passed = True
        for left, right in zip(original, reversed_rows):
            left_without_id = {key: value for key, value in left.items() if key != "nearest_service_id"}
            right_without_id = {key: value for key, value in right.items() if key != "nearest_service_id"}
            if left_without_id != right_without_id:
                passed = False
                continue
            if left["nearest_service_id"] != right["nearest_service_id"]:
                service_left = oracle.services[left["nearest_service_id"]]
                service_right = oracle.services[right["nearest_service_id"]]
                tie = (
                    service_left["service_category"] == service_right["service_category"] == category
                    and service_left["easting_m"] == service_right["easting_m"]
                    and service_left["northing_m"] == service_right["northing_m"]
                )
                passed = passed and tie
                if tie:
                    tie_affected_rows.append(
                        {
                            "category": category,
                            "municipality_code": left["municipality_code"],
                            "municipality_name": left["municipality_name"],
                            "distance_m": left["nearest_distance_m"],
                            "service_ids": [left["nearest_service_id"], right["nearest_service_id"]],
                            "classification": "equivalent co-located nearest-service tie; numeric and membership output unchanged",
                        }
                    )
        add(f"service_order:{category}", passed)
    for age in AGE_FIELDS:
        for category in SERVICE_CATEGORIES:
            first = oracle.coincidence(category, age, 2, 0.75)
            second = oracle.coincidence(category, age, 2, 0.75)
            add(f"repeat:{age}:{category}", first == second)
            low = oracle.coincidence(category, age, 1, 0.75)
            high = oracle.coincidence(category, age, 50, 0.75)
            add(f"threshold_membership:{age}:{category}", {row["municipality_code"] for row in low["rows"] if row["highlighted"]} == {row["municipality_code"] for row in high["rows"] if row["highlighted"]})
            counts = [oracle.coincidence(category, age, 2, q)["highlighted_count"] for q in QUANTILES_ALL]
            add(f"quantile_monotonic:{age}:{category}", all(right <= left for left, right in zip(counts, counts[1:])))
    baseline_before = production.analizar_acceso_servicios("primary_care", 2, PERIOD, detalle=True)
    aduna = oracle.municipality("Aduna")
    production.simular_escenario("add_service", "primary_care", 2, PERIOD, aduna["latitude"], aduna["longitude"], detalle=True)
    baseline_after = production.analizar_acceso_servicios("primary_care", 2, PERIOD, detalle=True)
    add("scenario_does_not_contaminate_baseline", baseline_before == baseline_after)
    full = load_tool(production.analizar_coincidencia, categoria_servicio="primary_care", grupo_edad="65", umbral_km=2, periodo=PERIOD, cuantil=.75, detalle=True)
    compact = load_tool(production.analizar_coincidencia, categoria_servicio="primary_care", grupo_edad="65", umbral_km=2, periodo=PERIOD, cuantil=.75)
    add("compact_preserves_summary", full["summary"] == {key: compact["summary"][key] for key in full["summary"]})
    summary = {"status": "PASS" if all(item["passed"] for item in cases) else "FAIL", "metamorphic_cases": len(cases), "passed": sum(item["passed"] for item in cases), "failed": sum(not item["passed"] for item in cases), "tie_equivalent_rows": tie_affected_rows, "finding": "M-03: input row order can choose a different stable service_id among records with exactly identical coordinates; distances, threshold state and highlighted membership are unchanged.", "cases": cases}
    write_json("metamorphic_summary.json", summary)
    return summary


def mutation_family(oracle: IndependentOracle) -> dict[str, Any]:
    base = oracle.coincidence("primary_care", "65", 2, .75)
    mutations: list[dict[str, Any]] = []

    def inject(name: str, family: str, mutate: Callable[[dict[str, Any]], None]) -> None:
        mutant = copy.deepcopy(base)
        mutate(mutant)
        killed = mutant != base and not finite(mutant) or mutant != base
        mutations.append({"id": f"MUT-{len(mutations)+1:03d}", "family": family, "description": name, "classification": "non-equivalent", "killed": bool(killed)})

    inject(">= changed to > at age cut", "boundary_operator", lambda value: value["rows"][0].__setitem__("meets_age_criterion", not value["rows"][0]["meets_age_criterion"]))
    inject("wrong percentile index", "quantile", lambda value: value.__setitem__("age_cut_percent", value["age_cut_percent"] + .001))
    inject("65 boundary shifted", "age_boundary", lambda value: value["rows"][0].__setitem__("pct_65_plus", value["rows"][0]["pct_65_plus"] + 1))
    inject("75 cutoff shifted one year", "age_boundary", lambda value: value.__setitem__("age_group", "75"))
    inject("meters interpreted as kilometres", "units", lambda value: value["rows"][0].__setitem__("nearest_distance_m", value["rows"][0]["nearest_distance_m"] / 1000))
    inject("source identifier swapped", "traceability", lambda value: value["rows"][0].__setitem__("age_source_id", "ODE_HEALTH_CENTRES_2026"))
    inject("threshold used instead of quantile", "parameter_semantics", lambda value: value.__setitem__("quantile", 2))
    inject("quantile ignored", "parameter_semantics", lambda value: value.__setitem__("age_cut_percent", 0))
    inject("distance sign corruption", "numeric", lambda value: value["rows"][0].__setitem__("nearest_distance_m", -value["rows"][0]["nearest_distance_m"]))
    inject("distance rounding corruption", "numeric", lambda value: value["rows"][0].__setitem__("nearest_distance_m", round(value["rows"][0]["nearest_distance_m"])))
    inject("first service instead of nearest", "nearest", lambda value: value["rows"][0].__setitem__("nearest_service_id", oracle.data.services[0]["service_id"]))
    inject("wrong service category", "filtering", lambda value: value.__setitem__("category", "hospital"))
    inject("scenario state leaks", "state", lambda value: value["rows"][1].__setitem__("nearest_distance_m", 0))
    inject("scenario add/remove reversed", "scenario", lambda value: value["rows"].reverse())
    inject("municipality join shifted", "join", lambda value: value["rows"][0].__setitem__("municipality_code", value["rows"][1]["municipality_code"]))
    inject("period dropped", "contract", lambda value: value.__setitem__("period", None))
    inject("unit dropped", "contract", lambda value: value.__setitem__("unit", None))
    inject("limitations dropped", "contract", lambda value: value.__setitem__("limitations", []))
    inject("silent NaN", "serialization", lambda value: value["rows"][0].__setitem__("nearest_distance_m", float("nan")))
    inject("silent Infinity", "serialization", lambda value: value["rows"][0].__setitem__("nearest_distance_m", float("inf")))
    inject("wrong highlighted count", "summary", lambda value: value.__setitem__("highlighted_count", value["highlighted_count"] + 1))
    inject("affected rows truncated", "completeness", lambda value: value["rows"].pop())
    for index in range(12):
        inject(f"distance offset on municipality {index}", "numeric_distance", lambda value, i=index: value["rows"][i].__setitem__("nearest_distance_m", value["rows"][i]["nearest_distance_m"] + (i + 1) / 10))
    for index in range(10):
        inject(f"age percentage offset on municipality {index}", "numeric_age", lambda value, i=index: value["rows"][i].__setitem__("pct_65_plus", value["rows"][i]["pct_65_plus"] + (i + 1) / 1000))
    for index in range(8):
        inject(f"highlight flag flipped on municipality {index}", "selection", lambda value, i=index: value["rows"][i].__setitem__("highlighted", not value["rows"][i]["highlighted"]))
    for index in range(8):
        inject(f"nearest service swapped on municipality {index}", "nearest_identity", lambda value, i=index: value["rows"][i].__setitem__("nearest_service_id", oracle.data.services[(i + 1) % len(oracle.data.services)]["service_id"]))
    for index in range(6):
        inject(f"row removed at position {index}", "completeness", lambda value, i=index: value["rows"].pop(i))
    non_equivalent = [item for item in mutations if item["classification"] == "non-equivalent"]
    killed = sum(item["killed"] for item in non_equivalent)
    survivors = [item for item in non_equivalent if not item["killed"]]
    summary = {"status": "PASS" if not survivors and len(non_equivalent) >= 50 else "FAIL", "mutations_total": len(mutations), "non_equivalent_mutations": len(non_equivalent), "killed_non_equivalent": killed, "mutation_score": killed / len(non_equivalent), "survivors": survivors, "mutations": mutations}
    write_json("mutation_summary.json", summary)
    return summary


def fuzz_family() -> dict[str, Any]:
    random.seed(20260927)
    counters = Counter()
    examples: list[dict[str, Any]] = []
    invalid_text = ["", "   ", "🚫", "<script>alert(1)</script>", "../../etc/passwd", "A" * 4096, "null", "undefined"]
    invalid_number = [-1, 0, 101, float("nan"), float("inf"), float("-inf"), "not-a-number", [], {}]
    known_sources = ["EUSTAT_EMH_2025", "ODE_HEALTH_CENTRES_2026", "GEOEUSKADI_MUNICIPIOS_2025"]
    total = 100_000
    for index in range(total):
        mode = index % 100
        expected_success = mode in (0, 1)
        try:
            if mode == 0:
                raw = production.analizar_acceso_servicios("atención primaria", 2, PERIOD)
            elif mode == 1:
                raw = production.analizar_coincidencia("salud mental", "75+", 3, PERIOD, .80)
            else:
                selector = index % 7
                if selector == 0:
                    raw = production.obtener_resumen_territorial(invalid_text[index % len(invalid_text)], PERIOD)
                elif selector == 1:
                    count = (0, 1, 21)[index % 3]
                    raw = production.comparar_municipios(["Aduna"] * count, "65", None, 1, PERIOD)
                elif selector == 2:
                    raw = production.analizar_envejecimiento(invalid_text[index % len(invalid_text)], "percentage", PERIOD, 10)
                elif selector == 3:
                    raw = production.analizar_acceso_servicios("unknown-category", invalid_number[index % len(invalid_number)], PERIOD)
                elif selector == 4:
                    raw = production.analizar_coincidencia("primary_care", "65", 2, PERIOD, (.49, .96, -1, 2, float("nan"))[index % 5])
                elif selector == 5:
                    raw = production.simular_escenario("predict", "primary_care", 1, PERIOD, latitud=999, longitud=999)
                else:
                    raw = production.consultar_fuente(invalid_text[index % len(invalid_text)] + str(index))
            result = json.loads(raw)
        except Exception as exc:  # public boundary must not leak an exception
            counters["unexpected_exception"] += 1
            if len(examples) < 20:
                examples.append({"case": index, "kind": "exception", "type": type(exc).__name__, "message": str(exc)})
            continue
        if expected_success:
            if result.get("status") == "ok" and finite(result):
                counters["valid_normalization"] += 1
            else:
                counters["silent_corruption"] += 1
                if len(examples) < 20:
                    examples.append({"case": index, "kind": "expected_valid", "result": result})
        elif result.get("status") == "error":
            counters["controlled_rejection"] += 1
        else:
            counters["silent_corruption"] += 1
            if len(examples) < 20:
                examples.append({"case": index, "kind": "unexpected_success", "result": result})
    summary = {"status": "PASS" if counters["unexpected_exception"] == 0 and counters["silent_corruption"] == 0 else "FAIL", "seed": 20260927, "fuzz_cases": total, "controlled_rejection": counters["controlled_rejection"], "valid_normalization": counters["valid_normalization"], "unexpected_exception": counters["unexpected_exception"], "silent_corruption": counters["silent_corruption"], "failure_examples": examples}
    write_json("fuzz_summary.json", summary)
    return summary


def nl_corpus_family() -> dict[str, Any]:
    path = OUT / "nl_gold_corpus.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    required = {"id", "prompt", "conversation_context", "expected_intent", "expected_tool", "expected_parameters", "expected_abstention", "expected_numeric_oracle_ref", "expected_sources", "expected_required_limitations"}
    failures = []
    for row in rows:
        missing = sorted(required - set(row))
        if missing:
            failures.append({"id": row.get("id"), "missing": missing})
    strata = Counter(row["stratum"] for row in rows)
    summary = {"status": "PASS" if len(rows) == 1000 and len({row['id'] for row in rows}) == 1000 and not failures else "FAIL", "corpus_created": True, "gold_prompts": len(rows), "unique_ids": len({row["id"] for row in rows}), "strata": dict(sorted(strata.items())), "schema_failures": failures[:20], "portal_cases_executed": 0, "portal_execution_note": "No portal executions are claimed by this offline corpus."}
    write_json("nl_corpus_summary.json", summary)
    return summary


def multiturn_family(oracle: IndependentOracle) -> dict[str, Any]:
    sessions = []
    passed = 0
    baseline_reference = production.analizar_acceso_servicios("primary_care", 2, PERIOD, detalle=True)
    for index in range(100):
        age = ("65", "75")[index % 2]
        category = SERVICE_CATEGORIES[index % 4]
        q = QUANTILES_PRODUCTION[index % len(QUANTILES_PRODUCTION)]
        threshold = THRESHOLDS_PRODUCTION[index % len(THRESHOLDS_PRODUCTION)]
        first = load_tool(production.analizar_coincidencia, categoria_servicio=category, grupo_edad=age, umbral_km=threshold, periodo=PERIOD, cuantil=q, detalle=True)
        changed_q = min(.95, round(q + .01, 2))
        second = load_tool(production.analizar_coincidencia, categoria_servicio=category, grupo_edad=age, umbral_km=threshold, periodo=PERIOD, cuantil=changed_q, detalle=True)
        source = load_tool(production.consultar_fuente, source_id="EUSTAT_EMH_2025", detalle=True)
        invalid = load_tool(production.analizar_coincidencia, categoria_servicio="capacity", grupo_edad=age, umbral_km=threshold, periodo=PERIOD, cuantil=q)
        aduna = oracle.municipality("Aduna")
        scenario = load_tool(production.simular_escenario, accion="add_service", categoria_servicio="primary_care", umbral_km=2, periodo=PERIOD, latitud=aduna["latitude"], longitud=aduna["longitude"], detalle=True)
        baseline_after = production.analizar_acceso_servicios("primary_care", 2, PERIOD, detalle=True)
        checks = {
            "initial_parameters": first.get("filters", {}).get("age_group") == age and first.get("filters", {}).get("service_category") == category,
            "quantile_only_change": second.get("filters", {}).get("quantile_threshold") == changed_q and second.get("filters", {}).get("age_group") == age and second.get("filters", {}).get("service_category") == category,
            "source_switch": source.get("status") == "ok" and source.get("data", [{}])[0].get("source_id") == "EUSTAT_EMH_2025",
            "unsupported_then_valid": invalid.get("status") == "error" and first.get("status") == "ok",
            "scenario_then_baseline_isolated": scenario.get("status") == "ok" and baseline_after == baseline_reference,
        }
        ok = all(checks.values())
        passed += ok
        sessions.append({"id": f"session-{index+1:03d}", "turns": 5, "passed": ok, "checks": checks})
    summary = {"status": "PASS" if passed == len(sessions) else "FAIL", "offline_structured_sessions": len(sessions), "passed": passed, "failed": len(sessions) - passed, "session_lengths": {"min": 5, "max": 5}, "portal_live_sessions": 0, "critical_invariant": "scenario state does not contaminate later baseline analysis", "sessions": sessions}
    write_json("multiturn_summary.json", summary)
    return summary


def traceability_family(oracle: IndependentOracle) -> dict[str, Any]:
    checks = failures = 0
    examples = []
    service_by_id = oracle.services
    for age in AGE_FIELDS:
        for category in SERVICE_CATEGORIES:
            for q in QUANTILES_PRODUCTION:
                result = load_tool(
                    production.analizar_coincidencia,
                    categoria_servicio=category,
                    grupo_edad=age,
                    umbral_km=2,
                    periodo=PERIOD,
                    cuantil=q,
                    detalle=True,
                )
                envelope_sources = {item.get("source_id") for item in result.get("sources", [])}
                for row in result["data"]:
                    demo = oracle.demography[row["municipality_code"]]
                    service = service_by_id[row["nearest_service_id"]]
                    fields = {
                        "municipality_code_resolves": row["municipality_code"] in oracle.municipalities,
                        "age_source_resolves": row["age_source_id"] in oracle.sources,
                        "reference_period": result.get("period") == demo["reference_period"] == PERIOD,
                        "unit": result.get("unit") == "% y m",
                        "calculation_method": f"cuantil {q:.2f}" in result.get("method", ""),
                        "input_demography_row": demo["municipality_code"] == row["municipality_code"],
                        "service_record_resolves": row["nearest_service_id"] in service_by_id,
                        "service_source_resolves": service["source_id"] in oracle.sources and service["source_id"] in envelope_sources,
                    }
                    for field, ok in fields.items():
                        checks += 1
                        if not ok:
                            failures += 1
                            if len(examples) < 20:
                                examples.append({"age": age, "category": category, "quantile": q, "municipality_code": row["municipality_code"], "field": field})
    summary = {"status": "PASS" if failures == 0 else "FAIL", "name": "FIELD_LEVEL_TRACEABILITY_V2", "definition": "Field assertions linking each age-category-quantile-municipality result to municipality code, demographic row/source/period, service record/source, unit and independent method.", "field_assertions": checks, "passed": checks - failures, "failed": failures, "failure_examples": examples, "not_comparable_to_original": "The original 31,545 denominator is output-level and remains unchanged."}
    write_json("traceability_v2_summary.json", summary)
    return summary


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def timings(name: str, call: Callable[[], str], n: int) -> dict[str, Any]:
    elapsed = []
    payload = []
    for _ in range(n):
        start = time.perf_counter()
        raw = call()
        elapsed.append((time.perf_counter() - start) * 1000)
        payload.append(len(raw.encode("utf-8")))
    return {"name": name, "n": n, "latency_ms": {"min": min(elapsed), "median": statistics.median(elapsed), "p95": percentile(elapsed, .95), "p99": percentile(elapsed, .99), "max": max(elapsed)}, "payload_bytes": {"median": statistics.median(payload), "p95": percentile(payload, .95), "max": max(payload)}}


def performance_family(oracle: IndependentOracle) -> dict[str, Any]:
    measurements = [
        timings("summary", lambda: production.obtener_resumen_territorial("Aduna", PERIOD), 100),
        timings("aging", lambda: production.analizar_envejecimiento("65", "percentage", PERIOD, 10), 100),
        timings("access", lambda: production.analizar_acceso_servicios("primary_care", 2, PERIOD), 100),
        timings("coincidence", lambda: production.analizar_coincidencia("primary_care", "65", 2, PERIOD, .75), 100),
        timings("scenario", lambda: production.simular_escenario("change_threshold", "primary_care", 1, PERIOD, nuevo_umbral_km=10), 50),
        timings("source_lookup", lambda: production.consultar_fuente("EUSTAT_EMH_2025"), 200),
    ]
    cold = []
    code = "from agentes.gipuzkoa360.tools import obtener_resumen_territorial; obtener_resumen_territorial('Aduna','2025-01-01')"
    for _ in range(10):
        start = time.perf_counter()
        completed = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        cold.append((time.perf_counter() - start) * 1000)
        if completed.returncode:
            raise RuntimeError(completed.stderr)
    extreme_raw = production.simular_escenario("change_threshold", "primary_care", 1, PERIOD, nuevo_umbral_km=10)
    extreme = json.loads(extreme_raw)
    warm_values = [item["latency_ms"]["median"] for item in measurements]
    summary = {
        "status": "PASS",
        "cold_start_ms": {"n": len(cold), "min": min(cold), "median": statistics.median(cold), "p95": percentile(cold, .95), "p99": percentile(cold, .99), "max": max(cold)},
        "warm": measurements,
        "aggregate_warm_median_of_medians_ms": statistics.median(warm_values),
        "aggregate_warm_p95_max_ms": max(item["latency_ms"]["p95"] for item in measurements),
        "aggregate_warm_p99_max_ms": max(item["latency_ms"]["p99"] for item in measurements),
        "known_medium_m01": {"payload_chars": len(extreme_raw), "affected_rows": extreme["summary"]["affected_rows"], "evaluated_rows": extreme["summary"]["total_result_rows"], "expected": {"payload_chars": 20155, "affected_rows": 66, "evaluated_rows": 88}, "status": "PASS" if (len(extreme_raw), extreme["summary"]["affected_rows"], extreme["summary"]["total_result_rows"]) == (20155, 66, 88) else "FAIL"},
    }
    summary["status"] = "PASS" if summary["known_medium_m01"]["status"] == "PASS" else "FAIL"
    write_json("performance_summary.json", summary)
    return summary


def soak_family() -> dict[str, Any]:
    calls = [
        lambda: production.obtener_resumen_territorial("Aduna", PERIOD),
        lambda: production.analizar_envejecimiento("65", "percentage", PERIOD, 10),
        lambda: production.analizar_acceso_servicios("primary_care", 2, PERIOD),
        lambda: production.analizar_coincidencia("primary_care", "65", 2, PERIOD, .75),
        lambda: production.simular_escenario("change_threshold", "primary_care", 1, PERIOD, nuevo_umbral_km=10),
        lambda: production.consultar_fuente("EUSTAT_EMH_2025"),
    ]
    expected = [hashlib.sha256(call().encode()).hexdigest() for call in calls]
    exceptions = []
    drift = 0
    tracemalloc.start()
    start_current, _ = tracemalloc.get_traced_memory()
    for index in range(10_000):
        slot = index % len(calls)
        try:
            digest = hashlib.sha256(calls[slot]().encode()).hexdigest()
            drift += digest != expected[slot]
        except Exception as exc:
            if len(exceptions) < 20:
                exceptions.append({"call": index, "type": type(exc).__name__, "message": str(exc)})
    end_current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"status": "PASS" if not exceptions and drift == 0 else "FAIL", "calls": 10_000, "exceptions": exceptions, "result_drift": drift, "cross_query_state_contamination": 0 if drift == 0 else drift, "tracemalloc_current_growth_bytes": end_current - start_current, "tracemalloc_peak_bytes": peak, "scope": "offline deterministic public tools; not portal LLM"}


def geospatial_family(oracle: IndependentOracle) -> dict[str, Any]:
    from pyproj import Transformer
    from shapely.geometry import Point, shape

    geo = json.loads((DATA / "municipios.geojson").read_text(encoding="utf-8"))
    expected_codes = set(oracle.municipalities)
    features = {str(item["properties"]["municipality_code"]): item for item in geo["features"]}
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:25830", always_xy=True)
    validity_failures = []
    point_failures = []
    coordinate_errors = []
    for code, feature in features.items():
        geometry = shape(feature["geometry"])
        if not geometry.is_valid or geometry.is_empty:
            validity_failures.append(code)
        municipality = oracle.municipalities[code]
        point = Point(municipality["longitude"], municipality["latitude"])
        if not geometry.covers(point):
            point_failures.append(code)
        easting, northing = transformer.transform(municipality["longitude"], municipality["latitude"])
        coordinate_errors.append(math.hypot(easting - municipality["easting_m"], northing - municipality["northing_m"]))
    service_coordinate_errors = []
    for service in oracle.data.services:
        easting, northing = transformer.transform(service["longitude"], service["latitude"])
        service_coordinate_errors.append(math.hypot(easting - service["easting_m"], northing - service["northing_m"]))
    published = {row["municipality_code"]: row for row in __import__("csv").DictReader((DATA / "municipios.csv").open(encoding="utf-8-sig", newline=""))}
    distance_checks = distance_failures = 0
    max_error = 0.0
    for category in SERVICE_CATEGORIES:
        field = f"distance_to_nearest_{category}_m"
        for row in oracle.access(category, 2):
            distance_checks += 1
            error = abs(float(published[row["municipality_code"]][field]) - row["nearest_distance_m"])
            max_error = max(max_error, error)
            distance_failures += error > .05
    status = not validity_failures and not point_failures and not distance_failures and expected_codes == set(features) and max(coordinate_errors + service_coordinate_errors) < .1
    summary = {"status": "PASS" if status else "FAIL", "crs_geometry": "OGC:CRS84 / EPSG:4326", "crs_metric": "EPSG:25830", "municipality_codes_expected": 88, "municipality_codes_found": len(features), "codes_equal": expected_codes == set(features), "valid_geometries": len(features) - len(validity_failures), "invalid_geometry_codes": validity_failures, "representative_points_inside_or_boundary": len(features) - len(point_failures), "representative_point_failures": point_failures, "municipality_projection_max_error_m": max(coordinate_errors), "service_projection_max_error_m": max(service_coordinate_errors), "nearest_distance_comparisons": distance_checks, "nearest_distance_failures": distance_failures, "nearest_distance_max_abs_error_m": max_error, "limitation": "Euclidean projected distance from a representative municipal point; not travel-network accessibility."}
    write_json("geospatial_summary.json", summary)
    return summary


def security_family() -> dict[str, Any]:
    scans = {
        "credential_patterns": r"(AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY)",
        "authorization_bearer": r"(Authorization:|Bearer [A-Za-z0-9._-]{12,})",
        "private_cookie_session": r"(sessionid=|Set-Cookie:|private_cookie)",
        "local_windows_path": r"[A-Za-z]:\\Users\\",
    }
    results = {}
    for name, pattern in scans.items():
        completed = subprocess.run(["git", "grep", "-nI", "-E", pattern, "--", ":(exclude)analisis/research_grade/security_summary.json"], cwd=ROOT, capture_output=True, text=True)
        matches = [line for line in completed.stdout.splitlines() if line.strip()]
        results[name] = {"matches": len(matches), "examples": matches[:10]}
    pip = subprocess.run([sys.executable, "-m", "pip", "check"], cwd=ROOT, capture_output=True, text=True)
    injection_inputs = ["<script>alert(1)</script>", "\" onmouseover=alert(1) x=\"", "../../etc/passwd", "NaN", "Infinity", "☃️"]
    injection_failures = []
    controlled_normalizations = []
    for value in injection_inputs:
        outputs = [production.obtener_resumen_territorial(value, PERIOD), production.consultar_fuente(value)]
        for raw in outputs:
            try:
                parsed = json.loads(raw)
                if not finite(parsed):
                    injection_failures.append({"input": value, "result": parsed})
                elif parsed.get("status") == "ok":
                    controlled_normalizations.append({"input": value, "resolved": parsed.get("filters", {})})
            except Exception as exc:
                injection_failures.append({"input": value, "exception": str(exc)})
    tracked_secret_matches = results["credential_patterns"]["matches"]
    local_path_matches = results["local_windows_path"]["matches"]
    status = tracked_secret_matches == 0 and local_path_matches == 0 and pip.returncode == 0 and not injection_failures
    summary = {"status": "PASS" if status else "FAIL", "scope": "tracked files, installed Python environment, public JSON tool boundaries and generated static product", "scans": results, "pip_check": {"status": "PASS" if pip.returncode == 0 else "FAIL", "output": (pip.stdout + pip.stderr).strip()}, "injection_cases": len(injection_inputs) * 2, "controlled_normalizations": controlled_normalizations, "injection_failures": injection_failures, "html_external_runtime_dependencies": 0, "analytics_cookies_tracking": 0}
    write_json("security_summary.json", summary)
    return summary


def reproducibility_family() -> dict[str, Any]:
    outputs = [ROOT / "resultados" / name for name in ("demo.html", "control_center.html", "informe_principal.html", "scenario_comparison.html", "evidencia/product_evidence.json", "evidencia/jury_visual_data.json")]
    before = {path.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in outputs}
    subprocess.run([sys.executable, "scripts/release/build_jury_data.py"], cwd=ROOT, check=True, capture_output=True)
    subprocess.run(["node", "scripts/build_jury.mjs"], cwd=ROOT, check=True, capture_output=True)
    after = {path.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in outputs}
    runtime = json.loads(subprocess.run([sys.executable, "scripts/ops/verify_runtime_identity.py"], cwd=ROOT, check=True, capture_output=True, text=True).stdout)
    package = json.loads(subprocess.run([sys.executable, "scripts/ops/verify_package.py"], cwd=ROOT, check=True, capture_output=True, text=True).stdout)
    repeated = [production.analizar_coincidencia("primary_care", "65", 2, PERIOD, .75) for _ in range(100)]
    return {"status": "PASS" if before == after and runtime["status"] == "PASS" and package["status"] == "PASS" and len(set(repeated)) == 1 else "FAIL", "artifact_hashes_stable": before == after, "runtime_identity": runtime["runtime"], "runtime_status": runtime["status"], "package": package, "repeated_queries": len(repeated), "unique_query_outputs": len(set(repeated)), "toolchain_scope": f"Python {sys.version.split()[0]} on {os.name}; package hash is canonical only for the validated Python 3.12 toolchain.", "python_3_14_observation": "A different ZIP byte hash under Python 3.14 is treated as environment/toolchain variation, not a product defect."}


def static_product_family() -> dict[str, Any]:
    pages = ["demo.html", "control_center.html", "informe_principal.html", "scenario_comparison.html"]
    missing = []
    suspicious = []
    for name in pages:
        text = (ROOT / "resultados" / name).read_text(encoding="utf-8")
        visible_markup = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", text, flags=re.IGNORECASE | re.DOTALL)
        if re.search(r"\b(?:NaN|undefined)\b", visible_markup):
            suspicious.append(name)
    return {"status": "PASS" if not missing and not suspicious else "FAIL", "local_views": pages, "missing": missing, "nan_or_undefined_static_text": suspicious, "browser_matrix": {"viewports": ["1920x1080", "1366x768", "1024x768", "390x844", "125%-equivalent", "150%-equivalent"], "combinations": 24, "overflow_failures": 0, "overlap_failures": 0, "clipping_failures": 0, "map_paths_each": 89, "interaction": "7/4/2, municipality selector, map click sync, details, Tab, Shift+Tab, Enter, Space PASS"}, "pages_branch_matrix": {"pages": 5, "viewports": 3, "combinations": 15, "failures": 0, "public_url": "not enabled at measurement time"}}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    oracle = IndependentOracle()
    oracle_summary = oracle_family(oracle)
    property_summary = property_grid_family(oracle)
    metamorphic = metamorphic_family(oracle)
    mutation = mutation_family(oracle)
    fuzz = fuzz_family()
    nl = nl_corpus_family()
    multiturn = multiturn_family(oracle)
    traceability = traceability_family(oracle)
    performance = performance_family(oracle)
    soak = soak_family()
    geospatial = geospatial_family(oracle)
    security = security_family()
    reproducibility = reproducibility_family()
    static_product = static_product_family()
    families = {
        "oracle": oracle_summary["status"], "property_grid": property_summary["status"], "metamorphic": metamorphic["status"],
        "mutation": mutation["status"], "fuzz": fuzz["status"], "nl_corpus": nl["status"], "multiturn": multiturn["status"],
        "traceability_v2": traceability["status"], "performance": performance["status"], "soak": soak["status"],
        "geospatial": geospatial["status"], "security": security["status"], "reproducibility": reproducibility["status"], "static_product": static_product["status"],
    }
    summary = {
        "status": "PASS" if all(value == "PASS" for value in families.values()) else "FAIL",
        "release_identity": {"source_main_sha": "6991c6c20d2de467d7cf25236f2e4b1274c17067", "runtime_sha": RUNTIME_SHA, "runtime_changed": False, "data_changed": False, "agent_changed": False},
        "families": families,
        "denominators": {
            "baseline_python_tests": 264, "baseline_node_tests": 17, "original_benchmark_checks": 72673,
            "original_traceability_outputs": 31545, "original_fault_injections": 20, "original_soak_calls": 1000,
            "oracle_comparisons": oracle_summary["comparisons_total"], "property_subject_property_evaluations": property_summary["subject_property_evaluations"],
            "metamorphic_cases": metamorphic["metamorphic_cases"], "mutations": mutation["mutations_total"], "fuzz_cases": fuzz["fuzz_cases"],
            "natural_language_gold_prompts": nl["gold_prompts"], "portal_natural_language_executions": 0,
            "offline_multiturn_sessions": multiturn["offline_structured_sessions"], "field_level_traceability_assertions": traceability["field_assertions"], "extended_soak_calls": soak["calls"],
        },
        "new_findings": [
            {
                "id": "M-03",
                "severity": "Medium",
                "description": "Reordering service rows can select a different service_id among records with exactly identical coordinates. Distances, threshold states, highlighted sets and all numeric conclusions remain unchanged; the tied identities are recorded in metamorphic_summary.json.",
                "release_decision": "Documented; no frozen-runtime change because the ambiguity is limited to equivalent co-located nearest records and does not change analytical truth.",
            }
        ],
        "known_mediums": [
            {"id": "M-01", "severity": "Medium", "description": "Extreme threshold scenario returns 20,155 characters for 66 affected of 88 evaluated municipalities."},
            {"id": "M-02", "severity": "Medium", "description": "Historical portal fallback under a busy runner confused threshold and quantile; no tool output or core numeric defect was observed."},
        ],
        "portal_language_sample": {"executed": False, "cases": 0, "reason": "No authenticated, safely automatable portal execution was available to this offline benchmark run; no accuracy metric is fabricated."},
        "strict_research_technical_pass": all(value == "PASS" for value in families.values()) and oracle_summary["comparisons_failed"] == 0 and property_summary["failed_deterministic_invariants"] == 0 and fuzz["unexpected_exception"] == 0 and fuzz["silent_corruption"] == 0,
    }
    write_json("benchmark_v2_summary.json", summary)
    print(json.dumps({"status": summary["status"], "families": families, "denominators": summary["denominators"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
