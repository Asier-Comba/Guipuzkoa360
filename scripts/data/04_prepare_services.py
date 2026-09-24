"""Normaliza y asigna espacialmente los centros sanitarios públicos de Gipuzkoa."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "datos_originales"
OUT = ROOT / "datos_preparados"


def slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def category(value: str) -> str:
    if value in {"Centro de Salud", "Consultorio", "Ambulatorio", "PAC"}:
        return "primary_care"
    if value in {"Hospital", "Hospital de Día"}:
        return "hospital"
    if value == "Centro de Salud Mental":
        return "mental_health"
    return "other_health"


def main() -> None:
    raw = pd.read_excel(RAW / "centros-salud.xlsx", sheet_name="Metadatos")
    raw = raw.loc[raw["Provincia"].eq("Gipuzkoa")].copy()
    raw = raw.loc[raw["LATWGS84"].notna() & raw["LONWGS84"].notna()].copy()
    points = gpd.GeoDataFrame(
        raw,
        geometry=gpd.points_from_xy(raw["LONWGS84"], raw["LATWGS84"]),
        crs=4326,
    )
    boundaries = gpd.read_file(OUT / "municipios.geojson")[["municipality_code", "municipality_name", "geometry"]]
    joined = gpd.sjoin(points, boundaries, how="left", predicate="within")
    if joined["municipality_code"].isna().any():
        missing = joined.loc[joined["municipality_code"].isna(), ["Nombre", "Municipio"]]
        raise ValueError(f"Centros de Gipuzkoa fuera de límites municipales:\n{missing}")

    projected = points.to_crs(25830).loc[joined.index].geometry
    result = pd.DataFrame({
        "service_id": joined["Código del centro"].astype(str),
        "service_name": joined["Nombre"].astype(str),
        "service_category": joined["Tipo de centro"].map(category),
        "service_type_original": joined["Tipo de centro"].astype(str),
        "municipality_code": joined["municipality_code"].astype(str).str.zfill(5),
        "municipality_name": joined["municipality_name"],
        "latitude": joined["LATWGS84"].astype(float),
        "longitude": joined["LONWGS84"].astype(float),
        "address": joined["Dirección"].fillna(""),
        "reference_period": "2026-09-20",
        "source_id": "ODE_HEALTH_CENTRES_2026",
    })
    result["_easting_m"] = projected.x.to_numpy()
    result["_northing_m"] = projected.y.to_numpy()
    result = result.sort_values(["municipality_code", "service_category", "service_name"])
    result.drop(columns=["_easting_m", "_northing_m"]).to_csv(OUT / "servicios.csv", index=False)
    runtime = result[[
        "service_id", "service_name", "service_category", "municipality_code",
        "latitude", "longitude", "reference_period", "source_id"
    ]].copy()
    runtime["easting_m"] = result["_easting_m"].to_numpy()
    runtime["northing_m"] = result["_northing_m"].to_numpy()
    runtime.to_csv(OUT / "runtime_servicios.csv", index=False)
    print(f"Servicios: {len(result)} centros; {result['service_id'].nunique()} IDs únicos.")


if __name__ == "__main__":
    main()

