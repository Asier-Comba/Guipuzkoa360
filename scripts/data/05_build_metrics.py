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
    service_cols = [column for column in metrics if column.startswith("services_")]
    metrics[service_cols] = metrics[service_cols].fillna(0).astype(int)
    metrics["primary_care_per_10000_65_plus"] = (
        metrics.get("services_primary_care", 0) / metrics["population_65_plus"] * 10_000
    ).round(3)

    representative_points = boundaries.geometry.representative_point()
    representative_wgs84 = gpd.GeoSeries(representative_points, crs=25830).to_crs(4326)
    pd.DataFrame({
        "municipality_code": boundaries["municipality_code"].astype(str).str.zfill(5),
        "municipality_name": boundaries["municipality_name"],
        "latitude": representative_wgs84.y,
        "longitude": representative_wgs84.x,
        "easting_m": representative_points.x,
        "northing_m": representative_points.y,
        "reference_period": "2025-05-07",
        "source_id": "GEOEUSKADI_MUNICIPIOS_2025",
    }).to_csv(OUT / "runtime_municipality_points.csv", index=False)
    for category_name in ["primary_care", "hospital"]:
        destinations = service_points.loc[service_points["service_category"].eq(category_name), "geometry"]
        metrics[f"distance_to_nearest_{category_name}_m"] = nearest_distance(representative_points, destinations).round(1)

    metrics["metrics_reference_period"] = "demography=2025-01-01;services=2026-09-20;geography=2025-05-07"
    metrics["source_id"] = "G360_DERIVED_MUNICIPAL_METRICS_V1"
    metrics.to_csv(OUT / "municipios.csv", index=False)
    metrics.to_csv(RESULTS / "metricas_municipales.csv", index=False)

    runtime = boundaries[["municipality_code", "municipality_name", "geometry"]].merge(
        metrics.drop(columns="municipality_name"), on="municipality_code", validate="one_to_one"
    )
    runtime["geometry"] = runtime.geometry.simplify(25, preserve_topology=True)
    runtime.to_crs(4326).to_file(OUT / "runtime_municipios.geojson", driver="GeoJSON")

    temporal = pd.DataFrame([
        {"dataset": "demografia.csv", "reference_period": "2025-01-01", "difference_from_demography_days": 0},
        {"dataset": "municipios.geojson", "reference_period": "2025-05-07", "difference_from_demography_days": 126},
        {"dataset": "servicios.csv", "reference_period": "2026-09-20", "difference_from_demography_days": 627},
    ])
    temporal.to_csv(ANALYSIS / "compatibilidad_temporal.csv", index=False)
    print(f"Métricas construidas para {len(metrics)} municipios.")


if __name__ == "__main__":
    main()

