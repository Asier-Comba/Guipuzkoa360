"""Verifica los tres resultados canónicos del jurado y, opcionalmente, una salida visual.

Uso:
    python scripts/benchmark/verify_jury_results.py
    python scripts/benchmark/verify_jury_results.py --candidate ruta/al/resultado.json

El candidato debe contener ``{"cases": [...]}``. Cada caso necesita ``id`` y
``municipalities``; puede añadir ``age_cut_percent``, ``distance_cut_m``,
``joined_rows`` y ``highlighted_count`` para validarlos también.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / "agentes" / "gipuzkoa360"
DATA_DIR = ROOT / "datos_preparados"
PERIOD = "2025-01-01"

sys.path.insert(0, str(AGENT_DIR))
from data_access import DataRepository  # noqa: E402
from metrics import quantile  # noqa: E402
from tools import TerritorialAnalysis  # noqa: E402


CASES = (
    {
        "id": "Q75_65_PRIMARY_2KM",
        "age_group": "65",
        "quantile": 0.75,
        "threshold_km": 2.0,
        "expected_age_cut_percent": 23.973,
        "expected_distance_cut_m": 2019.2,
        "expected_municipalities": (
            "Legazpi",
            "Ezkio-Itsaso",
            "Hondarribia",
            "Hernialde",
            "Oñati",
            "Idiazabal",
            "Errenteria",
        ),
    },
    {
        "id": "Q80_75_PRIMARY_3KM",
        "age_group": "75",
        "quantile": 0.80,
        "threshold_km": 3.0,
        "expected_age_cut_percent": 12.9796,
        "expected_distance_cut_m": 2138.6,
        "expected_municipalities": (
            "Legazpi",
            "Errenteria",
            "Hondarribia",
            "Idiazabal",
        ),
    },
    {
        "id": "Q85_65_PRIMARY_2KM",
        "age_group": "65",
        "quantile": 0.85,
        "threshold_km": 2.0,
        "expected_age_cut_percent": 25.3557,
        "expected_distance_cut_m": 2308.7,
        "expected_municipalities": (
            "Legazpi",
            "Hondarribia",
        ),
    },
)


def compute_cases() -> list[dict[str, Any]]:
    analysis = TerritorialAnalysis(DataRepository(DATA_DIR))
    computed: list[dict[str, Any]] = []
    for specification in CASES:
        result = analysis.coincidencia(
            "primary_care",
            specification["age_group"],
            specification["threshold_km"],
            PERIOD,
            specification["quantile"],
        )
        age_field = f"pct_{specification['age_group']}_plus"
        age_values = [row[age_field] for row in result["data"]]
        distance_values = [row["nearest_distance_m"] for row in result["data"]]
        direct_age_cut = round(quantile(age_values, specification["quantile"]), 4)
        direct_distance_cut = round(quantile(distance_values, specification["quantile"]), 1)
        highlighted = [row["municipality_name"] for row in result["data"] if row["highlighted"]]
        summary = result["summary"]
        checks = {
            "joined_rows_88": result["rows_used"] == summary["joined_rows"] == 88,
            "cut_recomputed_from_requested_quantile": (
                summary["age_cut_percent"] == direct_age_cut
                and summary["distance_cut_m"] == direct_distance_cut
            ),
            "exact_expected_cuts": (
                math.isclose(summary["age_cut_percent"], specification["expected_age_cut_percent"], abs_tol=1e-4)
                and math.isclose(summary["distance_cut_m"], specification["expected_distance_cut_m"], abs_tol=0.1)
            ),
            "exact_expected_municipalities": highlighted == list(specification["expected_municipalities"]),
            "highlighted_count_matches": summary["highlighted_count"] == len(highlighted),
            "every_highlighted_meets_both_cuts": all(
                row[age_field] >= direct_age_cut and row["nearest_distance_m"] >= direct_distance_cut
                for row in result["data"]
                if row["highlighted"]
            ),
            "no_non_highlighted_meets_both_cuts": all(
                not (row[age_field] >= direct_age_cut and row["nearest_distance_m"] >= direct_distance_cut)
                for row in result["data"]
                if not row["highlighted"]
            ),
        }
        computed.append(
            {
                "id": specification["id"],
                "age_group": specification["age_group"],
                "quantile": specification["quantile"],
                "threshold_km": specification["threshold_km"],
                "age_cut_percent": summary["age_cut_percent"],
                "distance_cut_m": summary["distance_cut_m"],
                "joined_rows": summary["joined_rows"],
                "highlighted_count": summary["highlighted_count"],
                "municipalities": highlighted,
                "checks": checks,
                "status": "PASS" if all(checks.values()) else "FAIL",
            }
        )
    return computed


def verify_quantile_sensitivity(computed: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {item["id"]: item for item in computed}
    q75 = by_id["Q75_65_PRIMARY_2KM"]
    q85 = by_id["Q85_65_PRIMARY_2KM"]
    checks = {
        "q75_and_q85_have_different_age_cuts": q75["age_cut_percent"] != q85["age_cut_percent"],
        "q75_and_q85_have_different_distance_cuts": q75["distance_cut_m"] != q85["distance_cut_m"],
        "q75_and_q85_have_different_highlighted_sets": q75["municipalities"] != q85["municipalities"],
        "implemented_quantiles_are_not_a_fixed_top_quartile": (
            q75["highlighted_count"] == 7 and q85["highlighted_count"] == 2
        ),
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def compare_candidate(path: Path, computed: list[dict[str, Any]]) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidate_cases = {item["id"]: item for item in payload.get("cases", [])}
    comparisons: list[dict[str, Any]] = []
    for expected in computed:
        candidate = candidate_cases.get(expected["id"])
        checks = {
            "case_present": candidate is not None,
            "municipalities_exact_order": bool(candidate) and candidate.get("municipalities") == expected["municipalities"],
        }
        if candidate:
            for field in ("age_cut_percent", "distance_cut_m", "joined_rows", "highlighted_count"):
                if field in candidate:
                    checks[f"{field}_matches"] = candidate[field] == expected[field]
        comparisons.append(
            {
                "id": expected["id"],
                "checks": checks,
                "status": "PASS" if all(checks.values()) else "FAIL",
            }
        )
    return {
        "candidate": path.as_posix(),
        "comparisons": comparisons,
        "status": "PASS" if all(item["status"] == "PASS" for item in comparisons) else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    os.environ["GIPUZKOA360_DATA_DIR"] = str(DATA_DIR)
    computed = compute_cases()
    sensitivity = verify_quantile_sensitivity(computed)
    candidate = compare_candidate(arguments.candidate, computed) if arguments.candidate else None
    status = "PASS" if (
        all(item["status"] == "PASS" for item in computed)
        and sensitivity["status"] == "PASS"
        and (candidate is None or candidate["status"] == "PASS")
    ) else "FAIL"
    report = {
        "status": status,
        "period": PERIOD,
        "service_category": "primary_care",
        "cases": computed,
        "quantile_sensitivity": sensitivity,
        "candidate_comparison": candidate,
    }
    serialized = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
