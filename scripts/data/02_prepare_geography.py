"""Prepara la geometría municipal y excluye entidades no municipales."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "datos_originales"
OUT = ROOT / "datos_preparados"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    metadata = json.loads((RAW / "eustat_ep06b_metadata.json").read_text(encoding="utf-8"))
    territory = metadata["variables"][0]
    names = dict(zip(territory["values"], territory["valueTexts"]))
    official_codes = {code for code in names if len(code) == 5 and code.startswith("20")}

    source = gpd.read_file(RAW / "municipios_etrs89" / "MUNICIPIOS_5000_ETRS89.shp")
    if source.crs.to_epsg() != 25830:
        raise ValueError(f"CRS original inesperado: {source.crs}")
    gipuzkoa_entities = source.loc[source["TERRITORIO"].eq("GIPUZKOA")].copy()
    municipalities = gipuzkoa_entities.loc[gipuzkoa_entities["EUSTAT"].isin(official_codes)].copy()
    municipalities["municipality_code"] = municipalities["EUSTAT"].astype(str).str.zfill(5)
    municipalities["municipality_name"] = municipalities["municipality_code"].map(names)
    municipalities["area_km2"] = municipalities.geometry.area / 1_000_000
    municipalities["source_id"] = "GEOEUSKADI_MUNICIPIOS_2025"
    municipalities["reference_period"] = "2025-05-07"
    municipalities = municipalities[
        ["municipality_code", "municipality_name", "area_km2", "reference_period", "source_id", "geometry"]
    ].sort_values("municipality_code")

    if len(municipalities) != 88 or not municipalities["municipality_code"].is_unique:
        raise ValueError("La geometría preparada no contiene 88 códigos municipales únicos")
    if not municipalities.geometry.is_valid.all():
        raise ValueError("Hay geometrías municipales inválidas")

    municipalities.to_crs(4326).to_file(OUT / "municipios.geojson", driver="GeoJSON")
    excluded = gipuzkoa_entities.loc[~gipuzkoa_entities["EUSTAT"].isin(official_codes), ["EUSTAT", "NOMBRE_TOP"]]
    excluded.rename(columns={"EUSTAT": "territory_code", "NOMBRE_TOP": "territory_name"}).to_csv(
        ROOT / "analisis" / "entidades_no_municipales_excluidas.csv", index=False
    )
    print(f"Geografía: {len(municipalities)} municipios; {len(excluded)} entidades no municipales excluidas.")


if __name__ == "__main__":
    main()

