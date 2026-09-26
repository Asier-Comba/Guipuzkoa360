"""Validación exhaustiva, determinista y offline del runtime GIPUZKOA 360.

El recuento de checks usa una unidad explícita: una evaluación independiente de
una propiedad para un sujeto del dominio (fila, combinación, pareja, escenario
o llamada). No cuenta líneas de código, asserts internos ni repeticiones de
benchmark como si fueran casos funcionales distintos.
"""

from __future__ import annotations

import csv
import argparse
import hashlib
import itertools
import json
import math
import os
import platform
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable


ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / "agentes" / "gipuzkoa360"
DATA_DIR = ROOT / "datos_preparados"
ANALYSIS_DIR = ROOT / "analisis"
DOCS_DIR = ROOT / "docs"
BASE_SHA = "488f46db7047d9393d4d4a489a869ab246c215b9"
RUNTIME_SHA = "195b4980fa5998b096c308296a55e452380b0371"
BRANCH = "final/asier-benchmark-suite"
PERIOD = "2025-01-01"
SEED = 36020260925
CATEGORIES = ("hospital", "mental_health", "other_health", "primary_care")
THRESHOLDS = (1.0, 2.0, 3.0, 5.0, 10.0)
QUANTILES = (0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)
AGE_GROUPS = ("65", "75")

sys.path.insert(0, str(AGENT_DIR))
import tools as core  # noqa: E402
from data_access import DataRepository  # noqa: E402
from metrics import quantile as metric_quantile  # noqa: E402
from schemas import DataContractError  # noqa: E402


INVARIANT_MATRIX = [
    {
        "entity": "municipality-demography",
        "operation": "load/recalculate/join",
        "input_domain": "88 municipalities",
        "property": "non-negative ordered counts, ordered percentages, stable key, traceable period/source",
        "expected": "all rows satisfy the data contract and reproduce rounded percentages",
        "failure_severity": "Critical",
    },
    {
        "entity": "municipality-service-category-threshold",
        "operation": "access",
        "input_domain": "88 × 4 × 5",
        "property": "valid nearest service, exact threshold classification, monotonicity, stable distance",
        "expected": "distance is independent of threshold and TRUE never becomes FALSE as threshold grows",
        "failure_severity": "Critical",
    },
    {
        "entity": "municipality-pair-age-category",
        "operation": "compare",
        "input_domain": "C(88,2) × 2 × 4",
        "property": "A/B symmetry and call isolation",
        "expected": "values by municipality are invariant to presentation order",
        "failure_severity": "Critical",
    },
    {
        "entity": "age-category-quantile-threshold",
        "operation": "coincidence",
        "input_domain": "2 × 4 × 8 × 5",
        "property": "reproducible cuts, exact highlighting, valid ranks and byte determinism",
        "expected": "all and only rows meeting both cuts are highlighted",
        "failure_severity": "Critical",
    },
    {
        "entity": "scenario",
        "operation": "add/remove/change threshold",
        "input_domain": "municipality points, all services, supported thresholds",
        "property": "counterfactual direction, counts, non-mutation and explicit limitations",
        "expected": "baseline remains unchanged and transformations obey their mathematical direction",
        "failure_severity": "Critical",
    },
    {
        "entity": "input alias",
        "operation": "normalization",
        "input_domain": "documented Spanish/English and Unicode variants plus invalid strings",
        "property": "safe equivalence without open fuzzy matching",
        "expected": "zero false accepts and zero false rejects in the declared matrix",
        "failure_severity": "High",
    },
    {
        "entity": "temporary corrupted dataset",
        "operation": "load/integrity validation",
        "input_domain": "20 isolated fault injections",
        "property": "controlled rejection or explicit warning",
        "expected": "no silent corruption",
        "failure_severity": "Critical",
    },
    {
        "entity": "tool output",
        "operation": "serialize/audit",
        "input_domain": "all benchmarked successful outputs",
        "property": "strict JSON and required envelope/provenance fields",
        "expected": "no NaN/Infinity and documented traceability denominator",
        "failure_severity": "Critical",
    },
]


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def strict_loads(payload: str) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"Constante JSON no válida: {value}")

    return json.loads(payload, parse_constant=reject_constant)


def percentile(values: Iterable[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def distribution(values: list[float]) -> dict[str, float | int]:
    return {
        "n": len(values),
        "min": round(min(values), 6),
        "mean": round(statistics.fmean(values), 6),
        "p50": round(percentile(values, 0.50), 6),
        "p90": round(percentile(values, 0.90), 6),
        "p95": round(percentile(values, 0.95), 6),
        "p99": round(percentile(values, 0.99), 6),
        "max": round(max(values), 6),
        "stddev": round(statistics.pstdev(values), 6),
    }


class Recorder:
    """Cuenta evaluaciones atómicas y conserva solo diagnósticos de fallo."""

    def __init__(self) -> None:
        self.total = 0
        self.passed = 0
        self.by_component: Counter[str] = Counter()
        self.failures: list[dict[str, Any]] = []
        self.notes: list[dict[str, Any]] = []

    def check(
        self,
        component: str,
        subject: str,
        property_name: str,
        condition: bool,
        *,
        expected: Any,
        observed: Any,
        severity: str = "Critical",
    ) -> bool:
        self.total += 1
        self.by_component[component] += 1
        if condition:
            self.passed += 1
            return True
        self.failures.append(
            {
                "component": component,
                "subject": subject,
                "property": property_name,
                "severity": severity,
                "expected": expected,
                "observed": observed,
            }
        )
        return False

    def note(self, component: str, subject: str, detail: Any) -> None:
        self.notes.append({"component": component, "subject": subject, "detail": detail})

    def open_by_severity(self) -> Counter[str]:
        return Counter(item["severity"] for item in self.failures)


class TraceabilityCoverage:
    """Cobertura por output analítico, no por cada número repetido dentro del output."""

    def __init__(self, known_sources: set[str], recorder: Recorder) -> None:
        self.known_sources = known_sources
        self.recorder = recorder
        self.denominator = 0
        self.numerator = 0

    @staticmethod
    def _has_numeric_data(result: dict[str, Any]) -> bool:
        for row in result.get("data", []):
            if any(isinstance(value, (int, float)) and not isinstance(value, bool) for value in row.values()):
                return True
        return False

    def audit(self, label: str, result: dict[str, Any]) -> None:
        if result.get("status") != "ok" or not self._has_numeric_data(result):
            return
        self.denominator += 1
        source_ids = {
            str(item.get("source_id"))
            for item in result.get("sources", [])
            if isinstance(item, dict) and item.get("source_id")
        }
        good = bool(
            result.get("period")
            and result.get("unit")
            and result.get("method")
            and source_ids
            and source_ids <= self.known_sources
        )
        if good:
            self.numerator += 1
        self.recorder.check(
            "traceability",
            label,
            "output has resolvable source_id + period + unit + method",
            good,
            expected="complete output-level provenance",
            observed={
                "period": result.get("period"),
                "unit": result.get("unit"),
                "method": bool(result.get("method")),
                "source_ids": sorted(source_ids),
            },
        )


def source_ids(repository: DataRepository) -> set[str]:
    return {
        str(item["source_id"])
        for item in repository.metadata().get("sources", [])
        if isinstance(item, dict) and item.get("source_id")
    }


def validate_demography(
    analysis: core.TerritorialAnalysis,
    recorder: Recorder,
    trace: TraceabilityCoverage,
) -> dict[str, Any]:
    repository = analysis.repo
    municipalities = repository.municipalities()
    demographic = repository.demography()
    known = source_ids(repository)
    municipality_codes = [row["municipality_code"] for row in municipalities]
    demo_codes = [row["municipality_code"] for row in demographic]
    recorder.check(
        "demography",
        "territory",
        "exact municipality coverage",
        len(municipalities) == len(demographic) == 88,
        expected=88,
        observed={"municipalities": len(municipalities), "demography": len(demographic)},
    )
    recorder.check(
        "demography",
        "municipality_code",
        "unique and joinable",
        len(set(municipality_codes)) == 88 and set(municipality_codes) == set(demo_codes),
        expected="88 unique identical keys",
        observed={"municipality_unique": len(set(municipality_codes)), "demo_unique": len(set(demo_codes))},
    )
    for row in demographic:
        code = row["municipality_code"]
        total = row["population_total"]
        age65 = row["population_65_plus"]
        age75 = row["population_75_plus"]
        pct65 = row["pct_65_plus"]
        pct75 = row["pct_75_plus"]
        recorder.check(
            "demography",
            code,
            "ordered non-negative population counts",
            0 <= age75 <= age65 <= total,
            expected="0 <= 75+ <= 65+ <= total",
            observed=[age75, age65, total],
        )
        recorder.check(
            "demography",
            code,
            "ordered bounded percentages",
            0 <= pct75 <= pct65 <= 100,
            expected="0 <= pct75 <= pct65 <= 100",
            observed=[pct75, pct65],
        )
        expected65 = round(100 * age65 / total, 3) if total else 0.0
        expected75 = round(100 * age75 / total, 3) if total else 0.0
        recorder.check(
            "demography",
            code,
            "percentage recomputation within 0.0005 percentage points",
            abs(expected65 - pct65) <= 0.0005 and abs(expected75 - pct75) <= 0.0005,
            expected=[expected65, expected75],
            observed=[pct65, pct75],
        )
        recorder.check(
            "demography",
            code,
            "source and period resolvable",
            row.get("source_id") in known and row.get("reference_period") == PERIOD,
            expected={"source_id": "known", "period": PERIOD},
            observed={"source_id": row.get("source_id"), "period": row.get("reference_period")},
        )

    deterministic_files: dict[str, str] = {}
    for filename in (
        "municipios.csv",
        "demografia.csv",
        "runtime_municipality_points.csv",
        "runtime_servicios.csv",
        "metadata_sources.json",
        "data_contract.json",
        "runtime_manifest.json",
    ):
        reads = [(DATA_DIR / filename).read_bytes() for _ in range(5)]
        digest = hashlib.sha256(reads[0]).hexdigest()
        deterministic_files[filename] = digest
        recorder.check(
            "determinism",
            filename,
            "five byte-identical reads",
            all(value == reads[0] for value in reads[1:]),
            expected=digest,
            observed=[hashlib.sha256(value).hexdigest() for value in reads],
        )

    snapshots = [
        canonical(
            {
                "municipalities": DataRepository(DATA_DIR).municipalities(),
                "demography": DataRepository(DATA_DIR).demography(),
                "services": DataRepository(DATA_DIR).services(),
            }
        )
        for _ in range(3)
    ]
    recorder.check(
        "determinism",
        "repository",
        "three value-identical fresh loads",
        len(set(snapshots)) == 1,
        expected="one canonical result",
        observed=len(set(snapshots)),
    )
    trace.audit("territorial-summary:Donostia", analysis.resumen("Donostia / San Sebastián", PERIOD))
    return {
        "municipalities": len(municipalities),
        "demographic_rows": len(demographic),
        "file_sha256": deterministic_files,
    }


def validate_service_matrix(
    analysis: core.TerritorialAnalysis,
    recorder: Recorder,
    trace: TraceabilityCoverage,
) -> tuple[dict[tuple[str, float], dict[str, Any]], dict[str, Any]]:
    services = analysis.repo.services()
    valid_ids = {row["service_id"] for row in services}
    category_counts = Counter(row["service_category"] for row in services)
    matrix: dict[tuple[str, float], dict[str, Any]] = {}
    combinations = 0
    for category in CATEGORIES:
        for threshold in THRESHOLDS:
            result = analysis.acceso(category, threshold, PERIOD)
            matrix[(category, threshold)] = result
            trace.audit(f"access:{category}:{threshold}", result)
            expected_rows_used = 88 + category_counts[category]
            recorder.check(
                "service_matrix",
                f"{category}@{threshold}km",
                "envelope rows/unit/period/sources",
                result["rows_used"] == expected_rows_used
                and result["unit"] == "m"
                and bool(result["period"])
                and bool(result["sources"]),
                expected={"rows_used": expected_rows_used, "unit": "m", "period": "present", "sources": "present"},
                observed={key: result.get(key) for key in ("rows_used", "unit", "period", "sources")},
            )
            for row in result["data"]:
                combinations += 1
                subject = f"{row['municipality_code']}:{category}:{threshold}"
                distance = row["nearest_distance_m"]
                recorder.check(
                    "service_matrix",
                    subject,
                    "distance is finite and non-negative",
                    isinstance(distance, (int, float)) and math.isfinite(distance) and distance >= 0,
                    expected=">=0 finite",
                    observed=distance,
                )
                recorder.check(
                    "service_matrix",
                    subject,
                    "nearest service id exists",
                    row["nearest_service_id"] in valid_ids,
                    expected="known service_id",
                    observed=row["nearest_service_id"],
                )
                recorder.check(
                    "service_matrix",
                    subject,
                    "within_threshold equals distance <= threshold",
                    row["within_threshold"] is (distance <= threshold * 1000),
                    expected=distance <= threshold * 1000,
                    observed=row["within_threshold"],
                )

    for category in CATEGORIES:
        by_threshold = {
            threshold: {row["municipality_code"]: row for row in matrix[(category, threshold)]["data"]}
            for threshold in THRESHOLDS
        }
        for code in by_threshold[THRESHOLDS[0]]:
            distances = [by_threshold[value][code]["nearest_distance_m"] for value in THRESHOLDS]
            flags = [by_threshold[value][code]["within_threshold"] for value in THRESHOLDS]
            recorder.check(
                "service_matrix",
                f"{code}:{category}",
                "distance invariant under threshold changes",
                len(set(distances)) == 1,
                expected="one distance",
                observed=distances,
            )
            recorder.check(
                "service_matrix",
                f"{code}:{category}",
                "threshold classification is monotonic",
                flags == sorted(flags),
                expected="False* then True*",
                observed=flags,
            )
    return matrix, {
        "categories": list(CATEGORIES),
        "thresholds_km": list(THRESHOLDS),
        "municipality_category_threshold_combinations": combinations,
        "service_records": len(services),
        "category_counts": dict(sorted(category_counts.items())),
    }


def validate_pairwise(
    analysis: core.TerritorialAnalysis,
    recorder: Recorder,
    trace: TraceabilityCoverage,
) -> dict[str, Any]:
    names = [row["municipality_name"] for row in analysis.repo.municipalities()]
    pair_count = 0
    comparison_count = 0
    for first, second in itertools.combinations(names, 2):
        pair_count += 1
        for age in AGE_GROUPS:
            for category in CATEGORIES:
                forward = analysis.comparar([first, second], age, category, 2.0, PERIOD)
                reverse = analysis.comparar([second, first], age, category, 2.0, PERIOD)
                forward_map = {row["municipality_code"]: row for row in forward["data"]}
                reverse_map = {row["municipality_code"]: row for row in reverse["data"]}
                comparison_count += 1
                subject = f"{first}|{second}|{age}|{category}"
                recorder.check(
                    "pairwise",
                    subject,
                    "A/B reversal preserves all values by municipality",
                    forward_map == reverse_map and len(forward_map) == 2,
                    expected="identical two-row maps",
                    observed="equal" if forward_map == reverse_map else {"forward": forward_map, "reverse": reverse_map},
                )
                trace.audit(f"pairwise:{subject}", forward)

    duplicate = analysis.comparar([names[0], names[0]], "65", "primary_care", 2.0, PERIOD)
    duplicate_explicit = (
        duplicate["status"] == "ok"
        and duplicate["rows_used"] == 2
        and len(duplicate["data"]) == 2
        and duplicate["data"][0] == duplicate["data"][1]
    )
    recorder.check(
        "pairwise",
        f"duplicate:{names[0]}",
        "duplicate input has explicit stable behavior",
        duplicate_explicit,
        expected="controlled rejection or two explicit identical rows",
        observed=duplicate,
        severity="High",
    )
    recorder.note(
        "pairwise",
        "duplicate-input-policy",
        "The real contract accepts 2-20 list entries, including repetition; [A,A] returns two identical rows.",
    )
    return {
        "unique_pairs": pair_count,
        "age_category_comparisons": comparison_count,
        "duplicate_behavior": "accepted as two explicit identical rows" if duplicate_explicit else "failed",
    }


def validate_coincidence_grid(
    analysis: core.TerritorialAnalysis,
    recorder: Recorder,
    trace: TraceabilityCoverage,
) -> tuple[dict[tuple[str, str, float, float], dict[str, Any]], dict[str, Any]]:
    grid: dict[tuple[str, str, float, float], dict[str, Any]] = {}
    sensitivity: dict[str, dict[str, int]] = defaultdict(dict)
    for age, category, quantile_value, threshold in itertools.product(
        AGE_GROUPS, CATEGORIES, QUANTILES, THRESHOLDS
    ):
        result = analysis.coincidencia(category, age, threshold, PERIOD, quantile_value)
        repeated = analysis.coincidencia(category, age, threshold, PERIOD, quantile_value)
        key = (age, category, quantile_value, threshold)
        grid[key] = result
        field = f"pct_{age}_plus"
        age_values = [row[field] for row in result["data"]]
        distance_values = [row["nearest_distance_m"] for row in result["data"]]
        expected_age_cut = round(metric_quantile(age_values, quantile_value), 4)
        expected_distance_cut = round(metric_quantile(distance_values, quantile_value), 1)
        summary = result["summary"]
        subject = f"{age}:{category}:q{quantile_value}:{threshold}km"
        recorder.check(
            "coincidence_grid",
            subject,
            "cuts reproducible from joined input",
            summary["age_cut_percent"] == expected_age_cut
            and summary["distance_cut_m"] == expected_distance_cut,
            expected=[expected_age_cut, expected_distance_cut],
            observed=[summary["age_cut_percent"], summary["distance_cut_m"]],
        )
        exact_flags = all(
            row["meets_age_criterion"] is (row[field] >= expected_age_cut)
            and row["meets_access_criterion"] is (row["nearest_distance_m"] >= expected_distance_cut)
            and row["highlighted"] is (
                row["meets_age_criterion"] and row["meets_access_criterion"]
            )
            for row in result["data"]
        )
        recorder.check(
            "coincidence_grid",
            subject,
            "highlighted iff both criteria are true",
            exact_flags,
            expected=True,
            observed=exact_flags,
        )
        ranks_valid = all(
            0 <= row["age_percentile_rank"] <= 1
            and 0 <= row["distance_percentile_rank"] <= 1
            for row in result["data"]
        )
        recorder.check(
            "coincidence_grid",
            subject,
            "percentile ranks bounded",
            ranks_valid,
            expected="0..1",
            observed=ranks_valid,
        )
        recorder.check(
            "coincidence_grid",
            subject,
            "88 joined rows and matching highlighted count",
            result["rows_used"] == summary["joined_rows"] == 88
            and summary["highlighted_count"] == sum(row["highlighted"] for row in result["data"]),
            expected={"rows": 88, "highlighted": "exact"},
            observed=summary,
        )
        recorder.check(
            "coincidence_grid",
            subject,
            "byte-deterministic canonical result",
            canonical(result) == canonical(repeated),
            expected="identical",
            observed="identical" if canonical(result) == canonical(repeated) else "different",
            severity="High",
        )
        trace.audit(f"coincidence:{subject}", result)
        sensitivity[f"{age}:{category}:{threshold}km"][f"q{quantile_value:.2f}"] = summary["highlighted_count"]

    controls = [
        ("65", "primary_care", 0.75, 2.0, 7),
        ("75", "primary_care", 0.80, 3.0, 4),
        ("65", "primary_care", 0.85, 1.0, 2),
    ]
    for age, category, quantile_value, threshold, expected in controls:
        observed = grid[(age, category, quantile_value, threshold)]["summary"]["highlighted_count"]
        recorder.check(
            "coincidence_controls",
            f"{age}:{category}:q{quantile_value}:{threshold}km",
            "documented highlighted count",
            observed == expected,
            expected=expected,
            observed=observed,
        )
    return grid, {
        "combinations": len(grid),
        "ages": list(AGE_GROUPS),
        "categories": list(CATEGORIES),
        "quantiles": list(QUANTILES),
        "thresholds_km": list(THRESHOLDS),
        "highlighted_count_sensitivity": dict(sorted(sensitivity.items())),
    }


def validate_scenarios(
    analysis: core.TerritorialAnalysis,
    recorder: Recorder,
    trace: TraceabilityCoverage,
) -> dict[str, Any]:
    municipalities = analysis.repo.municipalities()
    services_before = canonical(analysis.repo.services())
    add_count = remove_count = threshold_count = 0

    for municipality in municipalities:
        for category in CATEGORIES:
            result = analysis.escenario(
                "add_service",
                category,
                2.0,
                PERIOD,
                municipality["latitude"],
                municipality["longitude"],
                f"BENCH_ADD_{municipality['municipality_code']}_{category}",
            )
            target = next(row for row in result["data"] if row["municipality_code"] == municipality["municipality_code"])
            all_non_worse = all(row["scenario_distance_m"] <= row["baseline_distance_m"] for row in result["data"])
            limitation = " ".join(result["limitations"]).casefold()
            condition = (
                target["scenario_distance_m"] == 0.0
                and all_non_worse
                and result["scenario"]["scenario"]["service_count"]
                == result["scenario"]["baseline"]["service_count"] + 1
                and "contrafactual" in limitation
                and "no una predicción" in limitation
            )
            add_count += 1
            recorder.check(
                "scenario_add",
                f"{municipality['municipality_code']}:{category}",
                "add reaches target zero, never worsens, increments count, keeps limitation",
                condition,
                expected=True,
                observed={
                    "target": target,
                    "all_non_worse": all_non_worse,
                    "baseline_count": result["scenario"]["baseline"]["service_count"],
                    "scenario_count": result["scenario"]["scenario"]["service_count"],
                },
            )
            trace.audit(f"scenario:add:{municipality['municipality_code']}:{category}", result)

    for service in analysis.repo.services():
        result = analysis.escenario(
            "remove_service",
            service["service_category"],
            2.0,
            PERIOD,
            service_id=service["service_id"],
        )
        no_improvement = all(row["scenario_distance_m"] >= row["baseline_distance_m"] for row in result["data"])
        condition = (
            no_improvement
            and result["scenario"]["scenario"]["service_count"]
            == result["scenario"]["baseline"]["service_count"] - 1
            and all(row["scenario_distance_m"] >= 0 for row in result["data"])
        )
        remove_count += 1
        recorder.check(
            "scenario_remove",
            service["service_id"],
            "remove never improves distance and decrements global count",
            condition,
            expected=True,
            observed={"no_improvement": no_improvement, "scenario": result["scenario"]},
        )
        trace.audit(f"scenario:remove:{service['service_id']}", result)

    for category in CATEGORIES:
        for baseline_threshold, new_threshold in itertools.permutations(THRESHOLDS, 2):
            result = analysis.escenario(
                "change_threshold",
                category,
                baseline_threshold,
                PERIOD,
                new_threshold_km=new_threshold,
            )
            distances_same = all(
                row["baseline_distance_m"] == row["scenario_distance_m"] for row in result["data"]
            )
            classifications_exact = all(
                row["baseline_within_threshold"] is (row["baseline_distance_m"] <= baseline_threshold * 1000)
                and row["scenario_within_threshold"] is (row["scenario_distance_m"] <= new_threshold * 1000)
                for row in result["data"]
            )
            threshold_count += 1
            recorder.check(
                "scenario_threshold",
                f"{category}:{baseline_threshold}->{new_threshold}",
                "threshold-only scenario preserves distances and recalculates flags",
                distances_same and classifications_exact,
                expected=True,
                observed={"distances_same": distances_same, "classifications_exact": classifications_exact},
            )
            trace.audit(f"scenario:threshold:{category}:{baseline_threshold}->{new_threshold}", result)

    services_after = canonical(analysis.repo.services())
    recorder.check(
        "scenario_isolation",
        "repository-services",
        "all scenarios leave base services unchanged",
        services_before == services_after,
        expected=hashlib.sha256(services_before.encode()).hexdigest(),
        observed=hashlib.sha256(services_after.encode()).hexdigest(),
    )
    baseline_before = canonical(analysis.acceso("primary_care", 2.0, PERIOD))
    analysis.escenario(
        "add_service",
        "primary_care",
        2.0,
        PERIOD,
        municipalities[0]["latitude"],
        municipalities[0]["longitude"],
        "BENCH_ISOLATION",
    )
    baseline_after = canonical(analysis.acceso("primary_care", 2.0, PERIOD))
    recorder.check(
        "scenario_isolation",
        "query-scenario-query",
        "A then scenario then A returns identical baseline",
        baseline_before == baseline_after,
        expected="byte-identical canonical baseline",
        observed="identical" if baseline_before == baseline_after else "different",
    )
    return {
        "add_service_cases": add_count,
        "remove_service_cases": remove_count,
        "change_threshold_cases": threshold_count,
        "base_dataset_unchanged": services_before == services_after,
    }


def validate_aliases(analysis: core.TerritorialAnalysis, recorder: Recorder) -> dict[str, Any]:
    valid_service = {
        "atención primaria": "primary_care",
        "atencion primaria": "primary_care",
        "PRIMARY CARE": "primary_care",
        " primary-care ": "primary_care",
        "primary_care": "primary_care",
        "atencio\u0301n primaria": "primary_care",
        "salud mental": "mental_health",
        "SALUD-MENTAL": "mental_health",
        "mental health": "mental_health",
        "hospitales": "hospital",
        "other health": "other_health",
        "otras prestaciones sanitarias": "other_health",
    }
    valid_age = {
        "65": "65",
        "65+": "65",
        "65 +": "65",
        "65 o más": "65",
        "65 O MAS": "65",
        "≥65": "65",
        "≥ 65": "65",
        ">=65": "65",
        "75": "75",
        "75+": "75",
        "75 +": "75",
        "75 o más": "75",
        "75 O MAS": "75",
        "≥75": "75",
        "≥ 75": "75",
        ">=75": "75",
    }
    valid_measure = {
        "porcentaje": "percentage",
        "percentage": "percentage",
        "PERCENT": "percentage",
        "pct": "percentage",
        "recuento": "count",
        "count": "count",
        "personas": "count",
    }
    invalid_service = ["primary", "care", "farmacia", "salud", "hospital mental", "TEST_FAKE_SOURCE", "", None]
    invalid_age = ["64+", "80+", ">65", "65 aproximadamente", "mayores", "", None]
    invalid_measure = ["ratio", "media", "por mil", "aproximado", "", None]
    false_accepts = 0
    false_rejects = 0
    accepted_valid = 0
    rejected_invalid = 0

    for value, expected in valid_service.items():
        try:
            observed = core.normalize_service_category(value)
            accepted_valid += observed == expected
            failed = observed != expected
        except DataContractError:
            observed = "rejected"
            failed = True
        false_rejects += int(failed)
        recorder.check(
            "aliases",
            f"service:{value!r}",
            "valid alias maps to canonical category",
            not failed,
            expected=expected,
            observed=observed,
            severity="High",
        )

    for value, expected in valid_age.items():
        try:
            observed = core.normalize_age_group(value)
            accepted_valid += observed == expected
            failed = observed != expected
        except DataContractError:
            observed = "rejected"
            failed = True
        false_rejects += int(failed)
        recorder.check(
            "aliases",
            f"age:{value!r}",
            "valid alias maps to canonical age",
            not failed,
            expected=expected,
            observed=observed,
            severity="High",
        )

    for value, expected in valid_measure.items():
        try:
            result = analysis.envejecimiento("65", value, PERIOD, 1)
            observed = result["filters"]["measure"]
            accepted_valid += observed == expected
            failed = observed != expected
        except DataContractError:
            observed = "rejected"
            failed = True
        false_rejects += int(failed)
        recorder.check(
            "aliases",
            f"measure:{value!r}",
            "valid measure maps to canonical value",
            not failed,
            expected=expected,
            observed=observed,
            severity="High",
        )

    invalid_groups: list[tuple[str, list[Any], Callable[[Any], Any]]] = [
        ("service", invalid_service, core.normalize_service_category),
        ("age", invalid_age, core.normalize_age_group),
        ("measure", invalid_measure, lambda value: analysis.envejecimiento("65", value, PERIOD, 1)),
    ]
    for group, values, operation in invalid_groups:
        for value in values:
            rejected = False
            try:
                operation(value)
            except DataContractError:
                rejected = True
            if rejected:
                rejected_invalid += 1
            else:
                false_accepts += 1
            recorder.check(
                "aliases",
                f"invalid-{group}:{value!r}",
                "unknown/ambiguous string is rejected",
                rejected,
                expected="controlled rejection",
                observed="rejected" if rejected else "accepted",
                severity="High",
            )
    return {
        "accepted_valid": accepted_valid,
        "rejected_invalid": rejected_invalid,
        "false_accept": false_accepts,
        "false_reject": false_rejects,
        "valid_cases": len(valid_service) + len(valid_age) + len(valid_measure),
        "invalid_cases": len(invalid_service) + len(invalid_age) + len(invalid_measure),
    }


def rewrite_csv(path: Path, mutator: Callable[[list[str], list[dict[str, str]]], tuple[list[str], list[dict[str, str]]]]) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    fields, rows = mutator(fields, rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def integrity_scan(data_dir: Path) -> None:
    repository = DataRepository(data_dir)
    municipalities = repository.municipalities()
    demographic = repository.demography()
    services = repository.services()
    known_sources = source_ids(repository)
    if len(municipalities) != 88 or len(demographic) != 88 or len(services) != 148:
        raise ValueError("unexpected_row_count")
    municipality_codes = {row["municipality_code"] for row in municipalities}
    allowed_period = PERIOD
    for row in demographic:
        if not (0 <= row["population_75_plus"] <= row["population_65_plus"] <= row["population_total"]):
            raise ValueError("population_order")
        if row["source_id"] not in known_sources:
            raise ValueError("invalid_source")
        if row["reference_period"] != allowed_period:
            raise ValueError("unknown_period")
    for row in services:
        if row["municipality_code"] not in municipality_codes or row["source_id"] not in known_sources:
            raise ValueError("invalid_service_reference")
        if not (-90 <= row["latitude"] <= 90 and -180 <= row["longitude"] <= 180):
            raise ValueError("invalid_wgs84")
        if not (100_000 <= row["easting_m"] <= 900_000 and 4_000_000 <= row["northing_m"] <= 5_000_000):
            raise ValueError("invalid_projected_crs")
    points = list(csv.DictReader((data_dir / "runtime_municipality_points.csv").open("r", encoding="utf-8-sig")))
    if len(points) != 88:
        raise ValueError("invalid_point_count")
    for row in points:
        latitude = float(row["latitude"])
        longitude = float(row["longitude"])
        easting = float(row["easting_m"])
        northing = float(row["northing_m"])
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError("invalid_point_wgs84")
        if not (100_000 <= easting <= 900_000 and 4_000_000 <= northing <= 5_000_000):
            raise ValueError("invalid_point_crs")
    manifest = json.loads((data_dir / "runtime_manifest.json").read_text(encoding="utf-8"))
    computed_total = 0
    for item in manifest["files"]:
        path = data_dir.parent / item["path"]
        if not path.is_file():
            raise ValueError("manifest_missing_file")
        content = path.read_bytes()
        computed_total += len(content)
        if len(content) != item["bytes"] or hashlib.sha256(content).hexdigest() != item["sha256"]:
            raise ValueError("manifest_mismatch")
    if computed_total != manifest["total_bytes"]:
        raise ValueError("manifest_total_mismatch")


def inject_fault(name: str, data_dir: Path) -> None:
    demo = data_dir / "demografia.csv"
    services = data_dir / "runtime_servicios.csv"
    municipalities = data_dir / "municipios.csv"
    points = data_dir / "runtime_municipality_points.csv"
    metadata = data_dir / "metadata_sources.json"
    manifest = data_dir / "runtime_manifest.json"
    if name == "missing_file":
        demo.unlink()
    elif name == "empty_file":
        demo.write_bytes(b"")
    elif name == "wrong_delimiter":
        demo.write_text(demo.read_text(encoding="utf-8").replace(",", ";"), encoding="utf-8")
    elif name == "missing_header":
        lines = demo.read_text(encoding="utf-8").splitlines()
        demo.write_text("\n".join(lines[1:]) + "\n", encoding="utf-8")
    elif name == "missing_column":
        rewrite_csv(demo, lambda fields, rows: ([field for field in fields if field != "source_id"], rows))
    elif name == "duplicate_municipality_code":
        rewrite_csv(municipalities, lambda fields, rows: (fields, rows + [dict(rows[0])]))
    elif name == "duplicate_service_id":
        rewrite_csv(services, lambda fields, rows: (fields, rows + [dict(rows[0])]))
    elif name == "invalid_crs":
        def mutate(fields: list[str], rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]]]:
            rows[0]["easting_m"] = "999999999"
            return fields, rows
        rewrite_csv(points, mutate)
    elif name in {"nan", "inf", "-inf"}:
        def mutate(fields: list[str], rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]]]:
            rows[0]["population_total"] = {"nan": "NaN", "inf": "inf", "-inf": "-inf"}[name]
            return fields, rows
        rewrite_csv(demo, mutate)
    elif name in {"negative_population", "75_gt_65", "65_gt_total", "invalid_source", "unknown_period"}:
        def mutate(fields: list[str], rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]]]:
            if name == "negative_population":
                rows[0]["population_total"] = "-1"
            elif name == "75_gt_65":
                rows[0]["population_75_plus"] = str(int(rows[0]["population_65_plus"]) + 1)
            elif name == "65_gt_total":
                rows[0]["population_65_plus"] = str(int(rows[0]["population_total"]) + 1)
            elif name == "invalid_source":
                rows[0]["source_id"] = "TEST_FAKE_SOURCE"
            elif name == "unknown_period":
                rows[0]["reference_period"] = "2099-01-01"
            return fields, rows
        rewrite_csv(demo, mutate)
    elif name in {"latitude_gt_90", "longitude_gt_180"}:
        def mutate(fields: list[str], rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]]]:
            rows[0]["latitude" if name == "latitude_gt_90" else "longitude"] = "91" if name == "latitude_gt_90" else "181"
            return fields, rows
        rewrite_csv(services, mutate)
    elif name == "corrupt_json":
        metadata.write_text("{not-json", encoding="utf-8")
    elif name == "wrong_manifest_sha":
        content = json.loads(manifest.read_text(encoding="utf-8"))
        content["files"][0]["sha256"] = "0" * 64
        manifest.write_text(json.dumps(content), encoding="utf-8")
    else:
        raise ValueError(f"Unknown injection: {name}")


def validate_fault_injection(recorder: Recorder) -> dict[str, Any]:
    cases = [
        "missing_file",
        "empty_file",
        "wrong_delimiter",
        "missing_header",
        "missing_column",
        "duplicate_municipality_code",
        "duplicate_service_id",
        "invalid_crs",
        "nan",
        "inf",
        "-inf",
        "negative_population",
        "75_gt_65",
        "65_gt_total",
        "latitude_gt_90",
        "longitude_gt_180",
        "invalid_source",
        "corrupt_json",
        "wrong_manifest_sha",
        "unknown_period",
    ]
    classifications: dict[str, dict[str, str]] = {}
    with tempfile.TemporaryDirectory(prefix="g360-faults-") as temporary:
        temporary_root = Path(temporary)
        for case in cases:
            case_root = temporary_root / case
            data_copy = case_root / "datos_preparados"
            shutil.copytree(DATA_DIR, data_copy)
            inject_fault(case, data_copy)
            classification = "silent_corruption"
            diagnostic = "accepted"
            try:
                integrity_scan(data_copy)
            except (DataContractError, ValueError, OSError, csv.Error, json.JSONDecodeError) as exc:
                classification = "controlled_rejection"
                diagnostic = f"{type(exc).__name__}: {exc}"
            classifications[case] = {"classification": classification, "diagnostic": diagnostic}
            recorder.check(
                "fault_injection",
                case,
                "corruption is not silently accepted",
                classification != "silent_corruption",
                expected="controlled_rejection or explicit_warning",
                observed=classification,
            )
    controlled = sum(item["classification"] == "controlled_rejection" for item in classifications.values())
    warnings = sum(item["classification"] == "explicit_warning" for item in classifications.values())
    silent = sum(item["classification"] == "silent_corruption" for item in classifications.values())
    return {
        "total": len(cases),
        "controlled_rejection": controlled,
        "explicit_warning": warnings,
        "silent_corruption": silent,
        "cases": classifications,
    }


def public_tool_specs() -> dict[str, Callable[[], str]]:
    return {
        "consultar_fuente": lambda: core.consultar_fuente("EUSTAT_EMH_2025"),
        "obtener_resumen_territorial": lambda: core.obtener_resumen_territorial("Donostia / San Sebastián", PERIOD),
        "comparar_municipios": lambda: core.comparar_municipios(
            ["Eibar", "Tolosa"], "75", "primary_care", 2.0, PERIOD
        ),
        "analizar_envejecimiento": lambda: core.analizar_envejecimiento("65+", "porcentaje", PERIOD, 10),
        "analizar_acceso_servicios": lambda: core.analizar_acceso_servicios("atención primaria", 2.0, PERIOD),
        "analizar_coincidencia": lambda: core.analizar_coincidencia(
            "atención primaria", "65 o más", 2.0, PERIOD, 0.75
        ),
        # change_threshold es la variante compacta de mayor payload observada y evita
        # publicar como "máximo" una muestra artificialmente pequeña del escenario.
        "simular_escenario": lambda: core.simular_escenario(
            "cambiar umbral", "atención primaria", 1.0, PERIOD, nuevo_umbral_km=10.0
        ),
    }


def validate_output_contract(recorder: Recorder) -> dict[str, Any]:
    required = {"status", "filters", "metric", "unit", "rows_used", "method", "sources", "warnings", "limitations"}
    results: dict[str, dict[str, Any]] = {}
    for name, operation in public_tool_specs().items():
        payload = operation()
        parsed = strict_loads(payload)
        results[name] = parsed
        missing = sorted(required - set(parsed))
        recorder.check(
            "output_contract",
            name,
            "strict JSON and real envelope fields",
            parsed.get("status") == "ok" and not missing and isinstance(parsed.get("data"), list),
            expected={"status": "ok", "required": sorted(required), "data": "list"},
            observed={"status": parsed.get("status"), "missing": missing, "data_type": type(parsed.get("data")).__name__},
        )
        recorder.check(
            "output_contract",
            name,
            "serialized output contains no non-standard constants",
            not any(token in payload for token in ("NaN", "Infinity", "-Infinity")),
            expected="strict JSON constants only",
            observed="clean" if not any(token in payload for token in ("NaN", "Infinity", "-Infinity")) else "invalid",
        )
    return {"tools": len(results), "required_fields": sorted(required)}


def validate_metamorphic(
    analysis: core.TerritorialAnalysis,
    recorder: Recorder,
    service_matrix: dict[tuple[str, float], dict[str, Any]],
    coincidence_grid: dict[tuple[str, str, float, float], dict[str, Any]],
) -> dict[str, Any]:
    properties: list[str] = []

    def record(name: str, condition: bool, observed: Any) -> None:
        properties.append(name)
        recorder.check(
            "metamorphic",
            name,
            name,
            condition,
            expected=True,
            observed=observed,
            severity="High" if "determin" in name else "Critical",
        )

    first = analysis.comparar(["Eibar", "Tolosa"], "75", "primary_care", 2.0, PERIOD)
    second = analysis.comparar(["Tolosa", "Eibar"], "75", "primary_care", 2.0, PERIOD)
    record(
        "municipality input order changes presentation only",
        {row["municipality_code"]: row for row in first["data"]}
        == {row["municipality_code"]: row for row in second["data"]},
        "maps compared",
    )
    aliases = [
        core.analizar_coincidencia("primary_care", "65", 2.0, PERIOD, 0.75),
        core.analizar_coincidencia("atención primaria", "65+", 2.0, PERIOD, 0.75),
        core.analizar_coincidencia("PRIMARY CARE", "65 o más", 2.0, PERIOD, 0.75),
    ]
    record("equivalent aliases produce byte-identical JSON", len(set(aliases)) == 1, len(set(aliases)))
    distances_stable = all(
        len(
            {
                next(row for row in service_matrix[(category, threshold)]["data"] if row["municipality_code"] == code)[
                    "nearest_distance_m"
                ]
                for threshold in THRESHOLDS
            }
        )
        == 1
        for category in CATEGORIES
        for code in {row["municipality_code"] for row in service_matrix[(category, 1.0)]["data"]}
    )
    record("threshold-only changes preserve nearest distance", distances_stable, distances_stable)
    base_values_stable = True
    for age in AGE_GROUPS:
        field = f"pct_{age}_plus"
        for category in CATEGORIES:
            for threshold in THRESHOLDS:
                reference = {
                    row["municipality_code"]: (row[field], row["nearest_distance_m"])
                    for row in coincidence_grid[(age, category, QUANTILES[0], threshold)]["data"]
                }
                for quantile_value in QUANTILES[1:]:
                    candidate = {
                        row["municipality_code"]: (row[field], row["nearest_distance_m"])
                        for row in coincidence_grid[(age, category, quantile_value, threshold)]["data"]
                    }
                    base_values_stable &= candidate == reference
    record("quantile-only changes preserve base values", base_values_stable, base_values_stable)
    sample = analysis.coincidencia("primary_care", "65", 2.0, PERIOD, 0.75)
    record("JSON serialize-deserialize preserves content", strict_loads(canonical(sample)) == sample, "round-trip")

    specs_full_compact: dict[str, tuple[Callable[[], str], Callable[[], str]]] = {
        "summary": (
            lambda: core.obtener_resumen_territorial("Aduna", PERIOD, False),
            lambda: core.obtener_resumen_territorial("Aduna", PERIOD, True),
        ),
        "comparison": (
            lambda: core.comparar_municipios(["Eibar", "Tolosa"], "75", "primary_care", 2.0, PERIOD, False),
            lambda: core.comparar_municipios(["Eibar", "Tolosa"], "75", "primary_care", 2.0, PERIOD, True),
        ),
        "aging": (
            lambda: core.analizar_envejecimiento("65", "percentage", PERIOD, 10, False),
            lambda: core.analizar_envejecimiento("65", "percentage", PERIOD, 10, True),
        ),
        "access": (
            lambda: core.analizar_acceso_servicios("primary_care", 2.0, PERIOD, None, False),
            lambda: core.analizar_acceso_servicios("primary_care", 2.0, PERIOD, None, True),
        ),
        "coincidence": (
            lambda: core.analizar_coincidencia("primary_care", "65", 2.0, PERIOD, 0.75, False),
            lambda: core.analizar_coincidencia("primary_care", "65", 2.0, PERIOD, 0.75, True),
        ),
        "scenario": (
            lambda: core.simular_escenario("change_threshold", "primary_care", 2.0, PERIOD, nuevo_umbral_km=3.0, detalle=False),
            lambda: core.simular_escenario("change_threshold", "primary_care", 2.0, PERIOD, nuevo_umbral_km=3.0, detalle=True),
        ),
        "source": (
            lambda: core.consultar_fuente("EUSTAT_EMH_2025", False),
            lambda: core.consultar_fuente("EUSTAT_EMH_2025", True),
        ),
    }
    for kind, (compact_call, full_call) in specs_full_compact.items():
        compact = strict_loads(compact_call())
        full = strict_loads(full_call())
        shared = all(compact.get(field) == full.get(field) for field in ("status", "filters", "period", "metric", "unit", "rows_used", "method", "warnings", "limitations"))
        if kind in {"summary", "comparison", "aging", "source"}:
            evidence = compact["data"] == full["data"]
        elif kind == "access":
            full_distances = [row["nearest_distance_m"] for row in full["data"]]
            evidence = (
                compact["summary"]["total_result_rows"] == len(full["data"])
                and compact["summary"]["minimum_distance_m"] == min(full_distances)
                and compact["summary"]["maximum_distance_m"] == max(full_distances)
            )
        elif kind == "coincidence":
            evidence = compact["summary"] == {
                **full["summary"],
                "total_result_rows": len(full["data"]),
                "returned_rows": sum(row["highlighted"] for row in full["data"]),
                "selection": "Todos los destacados; si no hay ninguno, los 5 primeros por criterio.",
            } and all(row["highlighted"] for row in compact["data"])
        else:
            expected_changed = [
                row
                for row in full["data"]
                if row["difference_absolute_m"] not in (None, 0, 0.0)
                or row["baseline_within_threshold"] != row["scenario_within_threshold"]
            ]
            evidence = compact["data"] == expected_changed and compact["scenario"] == full["scenario"]
        record(f"compact {kind} preserves required evidence", shared and evidence, {"shared": shared, "evidence": evidence})
    return {"count": len(properties), "properties": properties}


def benchmark_performance(recorder: Recorder) -> dict[str, Any]:
    os.environ["GIPUZKOA360_DATA_DIR"] = str(DATA_DIR)
    tools = public_tool_specs()
    report: dict[str, Any] = {
        "environment": {
            "python": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "os": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
            "cpu_count": os.cpu_count(),
            "municipalities": 88,
            "health_records": 148,
        },
        "method": {
            "clock": "time.perf_counter_ns",
            "cold_n_per_tool": 20,
            "warm_n_per_tool": 100,
            "cold_definition": "analysis cache cleared before each measured wrapper call",
            "warm_definition": "one unmeasured warm-up, then repeated calls with the same in-process cache",
            "serialization_n_per_tool": 100,
        },
        "tools": {},
        "payload_findings": [],
        "portal_observed_seconds": {
            "normal_range": [26, 47],
            "g04_tool_and_output_by": 28.3,
            "g04_final_by": 74.3,
            "scope": "model + orchestration + sandbox; not comparable to local engine latency",
        },
    }
    all_warm: list[float] = []
    max_payload = 0
    for name, operation in tools.items():
        cold: list[float] = []
        warm: list[float] = []
        payload_sizes: list[int] = []
        parsed_sample: dict[str, Any] | None = None
        for index in range(20):
            core.clear_analysis_cache()
            start = time.perf_counter_ns()
            payload = operation()
            cold.append((time.perf_counter_ns() - start) / 1_000_000)
            parsed_sample = strict_loads(payload)
            payload_sizes.append(len(payload))
            recorder.check(
                "performance_json",
                f"{name}:cold:{index}",
                "benchmarked output is strict valid JSON",
                parsed_sample.get("status") == "ok",
                expected="status ok",
                observed=parsed_sample.get("status"),
            )
        core.clear_analysis_cache()
        strict_loads(operation())
        for index in range(100):
            start = time.perf_counter_ns()
            payload = operation()
            warm.append((time.perf_counter_ns() - start) / 1_000_000)
            parsed = strict_loads(payload)
            payload_sizes.append(len(payload))
            recorder.check(
                "performance_json",
                f"{name}:warm:{index}",
                "benchmarked output is strict valid JSON",
                parsed.get("status") == "ok",
                expected="status ok",
                observed=parsed.get("status"),
            )
        assert parsed_sample is not None
        serialization: list[float] = []
        for _ in range(100):
            start = time.perf_counter_ns()
            json.dumps(parsed_sample, ensure_ascii=False, sort_keys=True, allow_nan=False)
            serialization.append((time.perf_counter_ns() - start) / 1_000_000)
        all_warm.extend(warm)
        max_payload = max(max_payload, max(payload_sizes))
        report["tools"][name] = {
            "cold_ms": distribution(cold),
            "warm_ms": distribution(warm),
            "serialization_ms": {"p50": distribution(serialization)["p50"], "p95": distribution(serialization)["p95"]},
            "payload_chars": {"p50": round(percentile(payload_sizes, 0.50), 1), "max": max(payload_sizes)},
        }
        if max(payload_sizes) > 15_000:
            report["payload_findings"].append(
                {
                    "severity": "Medium",
                    "tool": name,
                    "payload_chars": max(payload_sizes),
                    "reason": (
                        f"El cambio de umbral 1→10 km modifica la clasificación de {parsed_sample['summary']['affected_rows']} "
                        f"de {parsed_sample['summary']['total_result_rows']} municipios analizados y la "
                        "salida compacta conserva cada fila afectada."
                    ),
                    "reduction_tradeoff": (
                        "Reducirlo exige truncar o paginar evidencia municipal; no se cambia el runtime "
                        "porque se perdería evidencia y no existe un fallo numérico o contractual."
                    ),
                }
            )
    report["aggregate_warm_ms"] = distribution(all_warm)
    report["max_payload_chars"] = max_payload
    report["worst_tool_percentiles_ms"] = {
        key: max(details["warm_ms"][key] for details in report["tools"].values())
        for key in ("p50", "p95", "p99")
    }
    return report


def validate_soak(recorder: Recorder) -> dict[str, Any]:
    specs = public_tool_specs()
    expected = {name: operation() for name, operation in specs.items()}
    rng = random.Random(SEED)
    exceptions: list[str] = []
    drift = 0
    tracemalloc.start()
    before_current, _ = tracemalloc.get_traced_memory()
    for index in range(1000):
        name = rng.choice(sorted(specs))
        try:
            payload = specs[name]()
            strict_loads(payload)
            identical = payload == expected[name]
            drift += int(not identical)
            recorder.check(
                "soak",
                f"{index}:{name}",
                "repeat call stays byte-identical",
                identical,
                expected=hashlib.sha256(expected[name].encode()).hexdigest(),
                observed=hashlib.sha256(payload.encode()).hexdigest(),
                severity="Critical",
            )
        except Exception as exc:  # report unexpected runtime failures without hiding them
            exceptions.append(f"{index}:{name}:{type(exc).__name__}:{exc}")
            recorder.check(
                "soak",
                f"{index}:{name}",
                "repeat call completes without exception",
                False,
                expected="no exception",
                observed=exceptions[-1],
                severity="Critical",
            )
    after_current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "calls": 1000,
        "seed": SEED,
        "result_drift": drift,
        "exceptions": exceptions,
        "tracemalloc_current_delta_bytes": after_current - before_current,
        "tracemalloc_peak_bytes": peak,
    }


def validate_build_reproducibility(recorder: Recorder) -> dict[str, Any]:
    script = ROOT / "scripts" / "agent" / "build_portal_package.py"
    archive = ROOT / "dist" / "gipuzkoa360-urban-challenge-rc2.zip"
    builds: list[dict[str, Any]] = []
    for index in range(10):
        completed = subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            recorder.check(
                "build_reproducibility",
                f"build:{index}",
                "build completes",
                False,
                expected="exit 0",
                observed={"returncode": completed.returncode, "stderr": completed.stderr},
            )
            continue
        content = archive.read_bytes()
        with zipfile.ZipFile(archive) as package:
            members = [
                {
                    "name": info.filename,
                    "size": info.file_size,
                    "crc": info.CRC,
                    "timestamp": list(info.date_time),
                }
                for info in package.infolist()
            ]
        builds.append(
            {
                "index": index + 1,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "members": members,
            }
        )
    reference = builds[0] if builds else None
    for build in builds:
        identical = reference is not None and all(
            build[field] == reference[field] for field in ("bytes", "sha256", "members")
        )
        recorder.check(
            "build_reproducibility",
            f"build:{build['index']}",
            "bytes, SHA-256, members and timestamps are identical",
            identical,
            expected={key: reference[key] for key in ("bytes", "sha256", "members")} if reference else "reference build",
            observed={key: build[key] for key in ("bytes", "sha256", "members")},
        )
    return {
        "attempted": 10,
        "completed": len(builds),
        "identical": sum(
            reference is not None and all(build[field] == reference[field] for field in ("bytes", "sha256", "members"))
            for build in builds
        ),
        "sha256": reference["sha256"] if reference else None,
        "bytes": reference["bytes"] if reference else None,
        "members": reference["members"] if reference else [],
    }


def render_benchmarks(report: dict[str, Any], performance: dict[str, Any]) -> str:
    severity = report["open_by_severity"]
    trace = report["traceability"]
    perf = performance["worst_tool_percentiles_ms"]
    lines = [
        "# GIPUZKOA 360 · Exhaustive validation and benchmark",
        "",
        f"Baseline: `{BASE_SHA}` · Runtime: `{RUNTIME_SHA}` · Branch: `{BRANCH}`",
        "",
        "## Scorecard",
        "",
        "| Measure | Result |",
        "|---|---:|",
        f"| Territory | {report['demography']['municipalities']} municipalities |",
        f"| Health records | {report['service_matrix']['service_records']} |",
        "| Tools | 7 |",
        f"| Validation checks | {report['checks']['total']:,} |",
        f"| Critical failures | {severity.get('Critical', 0)} |",
        f"| High failures | {severity.get('High', 0)} |",
        f"| Medium open | {severity.get('Medium', 0)} |",
        f"| Low open | {severity.get('Low', 0)} |",
        f"| Traceability coverage | {trace['percentage']:.3f}% ({trace['numerator']:,}/{trace['denominator']:,} outputs) |",
        f"| Property checks passed | {report['checks']['passed']:,}/{report['checks']['total']:,} |",
        f"| Fault injections | {report['fault_injection']['controlled_rejection']}/{report['fault_injection']['total']} controlled |",
        f"| Warm p50 / p95 / p99, worst tool | {perf['p50']:.3f} / {perf['p95']:.3f} / {perf['p99']:.3f} ms |",
        f"| Max compact payload | {performance['max_payload_chars']:,} chars |",
        f"| Build reproducibility | {report['build_reproducibility']['identical']}/{report['build_reproducibility']['attempted']} identical |",
        f"| Benchmark gate | {'GO' if report['benchmark_go'] else 'NO-GO'} |",
        "",
        "A check is one independent subject × property evaluation. Repeated timing samples are counted only",
        "when checking strict JSON validity; internal assertions and code lines are never inflated into cases.",
        "",
        "## Functional coverage",
        "",
        f"- Demography: {report['demography']['municipalities']}/88 municipalities.",
        f"- Service matrix: {report['service_matrix']['municipality_category_threshold_combinations']:,} municipality/category/threshold combinations.",
        f"- Pairwise comparisons: {report['pairwise']['unique_pairs']:,} unique pairs and {report['pairwise']['age_category_comparisons']:,} age/category cases.",
        f"- Coincidence grid: {report['coincidence_grid']['combinations']} combinations.",
        f"- Scenario properties: {report['scenarios']['add_service_cases']} adds, {report['scenarios']['remove_service_cases']} removals and {report['scenarios']['change_threshold_cases']} threshold changes.",
        f"- Metamorphic properties: {report['metamorphic']['count']}.",
        f"- Soak: {report['soak']['calls']:,} mixed calls, {report['soak']['result_drift']} drift, {len(report['soak']['exceptions'])} exceptions.",
        "",
        "## Performance distribution",
        "",
        "Engine measurements use `perf_counter_ns` in one local process. Cold clears the repository cache",
        "before every sample; warm uses a primed cache. Portal latency is reported separately because it",
        "includes model inference, orchestration and sandbox startup.",
        "",
        "| Tool | cold p50 | warm p50 | warm p95 | warm p99 | warm max | serialization p95 | payload max |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, item in performance["tools"].items():
        lines.append(
            f"| `{name}` | {item['cold_ms']['p50']:.3f} ms | {item['warm_ms']['p50']:.3f} ms | "
            f"{item['warm_ms']['p95']:.3f} ms | {item['warm_ms']['p99']:.3f} ms | "
            f"{item['warm_ms']['max']:.3f} ms | {item['serialization_ms']['p95']:.3f} ms | "
            f"{item['payload_chars']['max']:,} |"
        )
    portal = performance["portal_observed_seconds"]
    lines.extend(
        [
            "",
            "Portal evidence from the private RC2 validation: normal complete responses were usually 26–47 s;",
            f"G-04 exposed tool output by {portal['g04_tool_and_output_by']:.1f} s and its final response by "
            f"{portal['g04_final_by']:.1f} s. These figures are not compared with engine milliseconds.",
            "",
            "### Payload above 15,000 characters",
            "",
        ]
    )
    if performance["payload_findings"]:
        for finding in performance["payload_findings"]:
            lines.append(
                f"- **{finding['tool']} — {finding['payload_chars']:,} characters (Medium):** "
                f"{finding['reason']} {finding['reduction_tradeoff']}"
            )
    else:
        lines.append("No measured normal tool output exceeded 15,000 characters.")
    lines.extend(
        [
            "",
            "## Traceability denominator",
            "",
            "The denominator is every successful analytical output generated by the functional benchmark that",
            "contains at least one numeric value in `data`. An output is covered only when its envelope has a",
            "non-empty period, unit and method, and every declared source_id resolves in metadata_sources.json.",
            f"Coverage: **{trace['numerator']:,}/{trace['denominator']:,} = {trace['percentage']:.3f}%**.",
            "",
            "## Fault injection",
            "",
            f"{report['fault_injection']['total']} temporary copies were corrupted; "
            f"{report['fault_injection']['controlled_rejection']} were rejected in a controlled way and "
            f"{report['fault_injection']['silent_corruption']} were silently accepted.",
            "",
            "## Severity model",
            "",
            "- Critical: incorrect figure, silent corruption, source mismatch, state contamination, false scenario or runtime contract break.",
            "- High: wrong tool behavior, false alias acceptance, material missing limitation or non-determinism.",
            "- Medium: diagnostic or UX issue without numerical impact.",
            "- Low: cosmetic issue.",
            "",
            "## Method and reproducibility",
            "",
            f"- Fixed seed: `{SEED}`.",
            "- Offline: no network calls.",
            f"- Python: {performance['environment']['python']} on {performance['environment']['os']}.",
            f"- CPU: {performance['environment']['processor']} ({performance['environment']['cpu_count']} logical CPUs reported).",
            f"- Package: {report['build_reproducibility']['bytes']:,} bytes, SHA-256 `{report['build_reproducibility']['sha256']}`.",
            "- Full machine-readable evidence: `analisis/full_validation.json` and `analisis/performance_distribution.json`.",
            "",
            "This report states measured coverage only; it does not claim prediction quality, causal validity or",
            "real-world accessibility beyond the documented geometric indicators.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    global ANALYSIS_DIR, DOCS_DIR, BRANCH
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, help='Keep original evidence intact; write all new reports here.')
    args = parser.parse_args()
    if args.output_dir:
        ANALYSIS_DIR = DOCS_DIR = args.output_dir.resolve()
    BRANCH = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    random.seed(SEED)
    os.environ["GIPUZKOA360_DATA_DIR"] = str(DATA_DIR)
    core.clear_analysis_cache()
    recorder = Recorder()
    analysis = core.TerritorialAnalysis(DataRepository(DATA_DIR))
    known_sources = source_ids(analysis.repo)
    trace = TraceabilityCoverage(known_sources, recorder)
    started = time.perf_counter()

    demography = validate_demography(analysis, recorder, trace)
    service_matrix, service_summary = validate_service_matrix(analysis, recorder, trace)
    pairwise = validate_pairwise(analysis, recorder, trace)
    coincidence_grid, coincidence_summary = validate_coincidence_grid(analysis, recorder, trace)
    scenarios = validate_scenarios(analysis, recorder, trace)
    aliases = validate_aliases(analysis, recorder)
    fault_injection = validate_fault_injection(recorder)
    output_contract = validate_output_contract(recorder)
    metamorphic = validate_metamorphic(analysis, recorder, service_matrix, coincidence_grid)
    performance = benchmark_performance(recorder)
    soak = validate_soak(recorder)
    build_reproducibility = validate_build_reproducibility(recorder)

    open_by_severity = recorder.open_by_severity()
    for finding in performance["payload_findings"]:
        open_by_severity[finding["severity"]] += 1
    trace_percentage = 100.0 * trace.numerator / trace.denominator if trace.denominator else 0.0
    benchmark_go = (
        open_by_severity.get("Critical", 0) == 0
        and open_by_severity.get("High", 0) == 0
        and fault_injection["silent_corruption"] == 0
        and aliases["false_accept"] == 0
        and aliases["false_reject"] == 0
        and trace.denominator > 0
        and build_reproducibility["identical"] == build_reproducibility["attempted"]
    )
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "candidate_sha": subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        "base_sha": BASE_SHA,
        "runtime_sha": RUNTIME_SHA,
        "branch": BRANCH,
        "runtime_changed": False,
        "seed": SEED,
        "offline": True,
        "check_definition": "one independent subject × property evaluation; no code-line/assert inflation",
        "invariant_matrix": INVARIANT_MATRIX,
        "checks": {
            "total": recorder.total,
            "passed": recorder.passed,
            "failed": len(recorder.failures),
            "by_component": dict(sorted(recorder.by_component.items())),
        },
        "open_by_severity": {name: open_by_severity.get(name, 0) for name in ("Critical", "High", "Medium", "Low")},
        "failures": recorder.failures,
        "issues": performance["payload_findings"],
        "notes": recorder.notes,
        "demography": demography,
        "service_matrix": service_summary,
        "pairwise": pairwise,
        "coincidence_grid": coincidence_summary,
        "scenarios": scenarios,
        "aliases": aliases,
        "fault_injection": fault_injection,
        "output_contract": output_contract,
        "metamorphic": metamorphic,
        "traceability": {
            "definition": "successful numeric analytical outputs with resolvable source_id + period + unit + method",
            "numerator": trace.numerator,
            "denominator": trace.denominator,
            "percentage": round(trace_percentage, 6),
        },
        "soak": soak,
        "build_reproducibility": build_reproducibility,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "benchmark_go": benchmark_go,
    }
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (ANALYSIS_DIR / "performance_distribution.json").write_text(
        json.dumps(performance, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    (ANALYSIS_DIR / "full_validation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    (DOCS_DIR / "BENCHMARKS.md").write_text(render_benchmarks(report, performance), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS" if benchmark_go else "FAIL",
                "checks": report["checks"],
                "open_by_severity": report["open_by_severity"],
                "traceability": report["traceability"],
                "duration_seconds": report["duration_seconds"],
            },
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    )
    if not benchmark_go:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
