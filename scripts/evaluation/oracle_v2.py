"""Independent numeric oracle for the GIPUZKOA 360 research benchmark.

This module intentionally reads versioned files directly.  It must not import
``agentes.gipuzkoa360`` or any production calculation, percentile, scenario or
data-access helper.
"""

from __future__ import annotations

import csv
import json
import math
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "datos_preparados"
AGE_FIELDS = {"65": "pct_65_plus", "75": "pct_75_plus"}
SERVICE_CATEGORIES = ("primary_care", "hospital", "mental_health", "other_health")


def _rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value).strip())
    return "".join(char for char in text if not unicodedata.combining(char)).casefold()


def linear_quantile(values: Iterable[float], q: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("empty quantile input")
    position = (len(ordered) - 1) * float(q)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def percentile_rank(values: Iterable[float], value: float) -> float:
    ordered = sorted(float(item) for item in values)
    if len(ordered) <= 1:
        return 1.0
    below = sum(item < value for item in ordered)
    equal = sum(item == value for item in ordered)
    return (below + (equal - 1) / 2) / (len(ordered) - 1)


@dataclass(frozen=True)
class OracleData:
    municipalities: tuple[dict[str, Any], ...]
    demography: tuple[dict[str, Any], ...]
    services: tuple[dict[str, Any], ...]
    sources: tuple[dict[str, Any], ...]

    @classmethod
    def load(cls) -> "OracleData":
        names = {row["municipality_code"]: row for row in _rows("municipios.csv")}
        points = {row["municipality_code"]: row for row in _rows("runtime_municipality_points.csv")}
        municipalities: list[dict[str, Any]] = []
        for code, source in sorted(names.items()):
            point = points[code]
            municipalities.append(
                {
                    "municipality_code": code,
                    "municipality_name": source["municipality_name"],
                    "easting_m": float(point["easting_m"]),
                    "northing_m": float(point["northing_m"]),
                    "latitude": float(point["latitude"]),
                    "longitude": float(point["longitude"]),
                    "reference_period": point["reference_period"],
                    "source_id": point["source_id"],
                }
            )
        demography = []
        for row in _rows("demografia.csv"):
            demography.append(
                {
                    **row,
                    "population_total": int(row["population_total"]),
                    "population_65_plus": int(row["population_65_plus"]),
                    "population_75_plus": int(row["population_75_plus"]),
                    "pct_65_plus": float(row["pct_65_plus"]),
                    "pct_75_plus": float(row["pct_75_plus"]),
                }
            )
        services = []
        for row in _rows("runtime_servicios.csv"):
            services.append(
                {
                    **row,
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                    "easting_m": float(row["easting_m"]),
                    "northing_m": float(row["northing_m"]),
                }
            )
        metadata = json.loads((DATA / "metadata_sources.json").read_text(encoding="utf-8"))
        sources = metadata["sources"] if isinstance(metadata, dict) else metadata
        return cls(tuple(municipalities), tuple(demography), tuple(services), tuple(sources))


class IndependentOracle:
    def __init__(self, data: OracleData | None = None) -> None:
        self.data = data or OracleData.load()
        self.municipalities = {row["municipality_code"]: row for row in self.data.municipalities}
        self.demography = {row["municipality_code"]: row for row in self.data.demography}
        self.services = {row["service_id"]: row for row in self.data.services}
        self.sources = {row["source_id"]: row for row in self.data.sources}

    def municipality(self, query: str) -> dict[str, Any]:
        wanted = _key(query)
        exact = [
            row
            for row in self.data.municipalities
            if wanted in {_key(row["municipality_code"]), _key(row["municipality_name"])}
        ]
        if len(exact) == 1:
            return dict(exact[0])
        partial = [row for row in self.data.municipalities if wanted and wanted in _key(row["municipality_name"])]
        if len(partial) == 1:
            return dict(partial[0])
        raise KeyError(query)

    def nearest(self, municipality: dict[str, Any], category: str, services: Iterable[dict[str, Any]] | None = None) -> tuple[float, dict[str, Any]]:
        candidates = [
            row for row in (services or self.data.services) if row["service_category"] == category
        ]
        if not candidates:
            raise ValueError(f"no services for {category}")
        pairs = [
            (
                math.hypot(
                    float(row["easting_m"]) - municipality["easting_m"],
                    float(row["northing_m"]) - municipality["northing_m"],
                ),
                row,
            )
            for row in candidates
        ]
        return min(pairs, key=lambda pair: pair[0])

    def access(
        self,
        category: str,
        threshold_km: float,
        services: Iterable[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        output = []
        for municipality in self.data.municipalities:
            distance, service = self.nearest(municipality, category, services)
            output.append(
                {
                    "municipality_code": municipality["municipality_code"],
                    "municipality_name": municipality["municipality_name"],
                    "nearest_service_id": service["service_id"],
                    "nearest_distance_m": round(distance, 1),
                    "within_threshold": distance <= float(threshold_km) * 1000.0,
                }
            )
        return sorted(output, key=lambda row: (-row["nearest_distance_m"], row["municipality_name"]))

    def coincidence(self, category: str, age_group: str, threshold_km: float, q: float) -> dict[str, Any]:
        metric = AGE_FIELDS[age_group]
        rows = []
        for access_row in self.access(category, threshold_km):
            demo = self.demography[access_row["municipality_code"]]
            rows.append({**access_row, metric: demo[metric], "age_source_id": demo["source_id"]})
        ages = [row[metric] for row in rows]
        distances = [row["nearest_distance_m"] for row in rows]
        age_cut = linear_quantile(ages, q)
        distance_cut = linear_quantile(distances, q)
        for row in rows:
            row["age_percentile_rank"] = round(percentile_rank(ages, row[metric]), 4)
            row["distance_percentile_rank"] = round(percentile_rank(distances, row["nearest_distance_m"]), 4)
            row["meets_age_criterion"] = row[metric] >= age_cut
            row["meets_access_criterion"] = row["nearest_distance_m"] >= distance_cut
            row["highlighted"] = row["meets_age_criterion"] and row["meets_access_criterion"]
        rows.sort(
            key=lambda row: (
                not row["highlighted"],
                -row[metric],
                -row["nearest_distance_m"],
                row["municipality_name"],
            )
        )
        return {
            "age_group": age_group,
            "category": category,
            "threshold_km": float(threshold_km),
            "quantile": float(q),
            "age_cut_percent": round(age_cut, 4),
            "distance_cut_m": round(distance_cut, 1),
            "highlighted_count": sum(row["highlighted"] for row in rows),
            "rows": rows,
        }

    def summary(self, municipality_query: str) -> dict[str, Any]:
        municipality = self.municipality(municipality_query)
        code = municipality["municipality_code"]
        demo = self.demography[code]
        counts = {category: 0 for category in SERVICE_CATEGORIES}
        for service in self.data.services:
            if service["municipality_code"] == code:
                counts[service["service_category"]] += 1
        return {
            "municipality_code": code,
            "municipality_name": municipality["municipality_name"],
            "population_total": demo["population_total"],
            "population_65_plus": demo["population_65_plus"],
            "population_75_plus": demo["population_75_plus"],
            "pct_65_plus": demo["pct_65_plus"],
            "pct_75_plus": demo["pct_75_plus"],
            "services_in_municipality": counts,
        }

    def scenario_add_at_municipality(self, category: str, municipality_query: str, threshold_km: float) -> list[dict[str, Any]]:
        from pyproj import Transformer

        municipality = self.municipality(municipality_query)
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:25830", always_xy=True)
        easting, northing = transformer.transform(municipality["longitude"], municipality["latitude"])
        hypothetical = {
            "service_id": "ORACLE_HYPOTHETICAL",
            "service_name": "Oracle hypothetical",
            "service_category": category,
            "municipality_code": municipality["municipality_code"],
            "latitude": municipality["latitude"],
            "longitude": municipality["longitude"],
            "easting_m": easting,
            "northing_m": northing,
            "reference_period": "scenario",
            "source_id": "SCENARIO_INPUT",
        }
        return self.access(category, threshold_km, [*self.data.services, hypothetical])

    def scenario_remove(self, service_id: str, threshold_km: float) -> list[dict[str, Any]]:
        service = self.services[service_id]
        remaining = [row for row in self.data.services if row["service_id"] != service_id]
        return self.access(service["service_category"], threshold_km, remaining)
