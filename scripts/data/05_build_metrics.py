"""Construye métricas municipales transparentes de disponibilidad y proximidad geométrica."""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "datos_preparados"
ANALYSIS = ROOT / "analisis"
RESULTS = ROOT / "resultados"
SERVICE_CATEGORIES = ("primary_care", "hospital", "mental_health", "other_health")
UPSTREAM_SOURCE_IDS = (
    "EUSTAT_EMH_2025",
    "ODE_HEALTH_CENTRES_2026",
    "GEOEUSKADI_MUNICIPIOS_2025",
)


def nearest_distance(origins: gpd.GeoSeries, destinations: gpd.GeoSeries) -> np.ndarray:
    destination_xy = np.array([[point.x, point.y] for point in destinations])
    values = []
    for origin in origins:
        delta = destination_xy - np.array([origin.x, origin.y])
        values.append(float(np.sqrt((delta * delta).sum(axis=1)).min()))
    return np.array(values)


def main() -> None:
    demography = pd.read_csv(OUT / "demografia.csv", dtype={"municipality_code": str})
    boundaries = gpd.read_file(OUT / "municipios.geojson").to_crs(25830)
    services = pd.read_csv(OUT / "servicios.csv", dtype={"municipality_code": str})
    service_points = gpd.GeoDataFrame(
        services,
        geometry=gpd.points_from_xy(services["longitude"], services["latitude"]),
        crs=4326,
    ).to_crs(25830)

    metrics = demography.merge(
        boundaries.drop(columns="geometry")[["municipality_code", "area_km2"]],
        on="municipality_code", how="left", validate="one_to_one",
    )
    counts = services.pivot_table(
        index="municipality_code", columns="service_category", values="service_id", aggfunc="count", fill_value=0
    )
    counts.columns = [f"services_{column}" for column in counts.columns]
    metrics = metrics.merge(counts.reset_index(), on="municipality_code", how="left", validate="one_to_one")
    for category_name in SERVICE_CATEGORIES:
        column = f"services_{category_name}"
        if column not in metrics:
            metrics[column] = 0
    service_cols = [f"services_{category_name}" for category_name in SERVICE_CATEGORIES]
    metrics[service_cols] = metrics[service_cols].fillna(0).astype(int)
    metrics["services_total"] = metrics[service_cols].sum(axis=1).astype(int)
    for category_name in SERVICE_CATEGORIES:
        for age_group in ("65", "75"):
            metrics[f"{category_name}_per_10000_{age_group}_plus"] = (
                metrics[f"services_{category_name}"] / metrics[f"population_{age_group}_plus"] * 10_000
            ).round(3)

    representative_points = boundaries.geometry.representative_point()
    representative_wgs84 = gpd.GeoSeries(representative_points, crs=25830).to_crs(4326)
    metrics["representative_point_longitude"] = representative_wgs84.x.round(7).to_numpy()
    metrics["representative_point_latitude"] = representative_wgs84.y.round(7).to_numpy()
    pd.DataFrame({
        "municipality_code": boundaries["municipality_code"].astype(str).str.zfill(5),
        "municipality_name": boundaries["municipality_name"],
        "latitude": representative_wgs84.y.round(7).to_numpy(),
        "longitude": representative_wgs84.x.round(7).to_numpy(),
        "easting_m": representative_points.x.round(3).to_numpy(),
        "northing_m": representative_points.y.round(3).to_numpy(),
        "reference_period": "2025-05-07",
        "source_id": "GEOEUSKADI_MUNICIPIOS_2025",
    }).to_csv(OUT / "runtime_municipality_points.csv", index=False, lineterminator="\n")
    for category_name in SERVICE_CATEGORIES:
        destinations = service_points.loc[service_points["service_category"].eq(category_name), "geometry"]
        if destinations.empty:
            raise ValueError(f"No hay destinos para la categoría {category_name}")
        metrics[f"distance_to_nearest_{category_name}_m"] = nearest_distance(representative_points, destinations).round(1)

    metrics["metrics_reference_period"] = "demography=2025-01-01;services=2026-09-20;geography=2025-05-07"
    metrics["source_id"] = "G360_DERIVED_MUNICIPAL_METRICS_V1"
    metrics["source_ids"] = "|".join(UPSTREAM_SOURCE_IDS)
    metrics.to_csv(OUT / "municipios.csv", index=False, lineterminator="\n")
    metrics.to_csv(RESULTS / "metricas_municipales.csv", index=False, lineterminator="\n")

    runtime = boundaries[["municipality_code", "municipality_name", "geometry"]].merge(
        metrics.drop(columns="municipality_name"), on="municipality_code", validate="one_to_one"
    )
    runtime["geometry"] = runtime.geometry.simplify(25, preserve_topology=True)
    runtime_path = OUT / "runtime_municipios.geojson"
    runtime.to_crs(4326).to_file(runtime_path, driver="GeoJSON")
    runtime_path.write_text(runtime_path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

    temporal = pd.DataFrame([
        {"dataset": "demografia.csv", "reference_period": "2025-01-01", "difference_from_demography_days": 0},
        {"dataset": "municipios.geojson", "reference_period": "2025-05-07", "difference_from_demography_days": 126},
        {"dataset": "servicios.csv", "reference_period": "2026-09-20", "difference_from_demography_days": 627},
    ])
    temporal.to_csv(ANALYSIS / "compatibilidad_temporal.csv", index=False, lineterminator="\n")
    print(f"Métricas construidas para {len(metrics)} municipios.")


if __name__ == "__main__":
    main()
