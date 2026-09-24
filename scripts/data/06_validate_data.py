"""Control de calidad y verificaciones de referencia."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "datos_originales"
OUT = ROOT / "datos_preparados"
ANALYSIS = ROOT / "analisis"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    demography = pd.read_csv(OUT / "demografia.csv", dtype={"municipality_code": str})
    municipalities = pd.read_csv(OUT / "municipios.csv", dtype={"municipality_code": str})
    boundaries = gpd.read_file(OUT / "municipios.geojson")
    services = pd.read_csv(OUT / "servicios.csv", dtype={"municipality_code": str})

    check(len(demography) == 88, "Cobertura demográfica distinta de 88 municipios")
    check(len(boundaries) == 88, "Cobertura geográfica distinta de 88 municipios")
    check(demography["municipality_code"].str.fullmatch(r"20\d{3}").all(), "Formato de código inválido")
    check(demography["municipality_code"].is_unique, "Códigos demográficos duplicados")
    check(set(demography["municipality_code"]) == set(boundaries["municipality_code"]), "Join demografía-geografía incompleto")
    check(set(services["municipality_code"]).issubset(set(boundaries["municipality_code"])), "Servicio sin municipio válido")
    check((demography["population_75_plus"] <= demography["population_65_plus"]).all(), "75+ supera 65+")
    check((demography["population_65_plus"] <= demography["population_total"]).all(), "65+ supera total")
    check(demography[["pct_65_plus", "pct_75_plus"]].apply(lambda s: s.between(0, 100).all()).all(), "Porcentaje fuera de 0-100")
    check(services["service_id"].notna().all() and services["service_id"].is_unique, "ID de servicio nulo o duplicado")
    check(services["latitude"].between(42.8, 43.5).all(), "Latitud fuera de Gipuzkoa")
    check(services["longitude"].between(-2.7, -1.7).all(), "Longitud fuera de Gipuzkoa")
    check(boundaries.geometry.is_valid.all(), "Geometría inválida")

    raw_age = pd.read_csv(RAW / "eustat_demografia_2025.csv", encoding="cp1252")
    raw_age.columns = ["municipality_name", "age_group", "sex", "population"]
    verifications = []
    for name in ["Donostia / San Sebastián", "Eibar", "Tolosa"]:
        source_value = int(raw_age.loc[(raw_age["municipality_name"] == name) & (raw_age["age_group"] == "Total"), "population"].iloc[0])
        pipeline_value = int(demography.loc[demography["municipality_name"] == name, "population_total"].iloc[0])
        verifications.append({
            "check": f"population_total:{name}", "source_value": source_value,
            "pipeline_value": pipeline_value, "difference": pipeline_value - source_value,
            "result": "PASS" if source_value == pipeline_value else "FAIL", "source_id": "EUSTAT_EMH_2025",
        })
    raw_health = pd.read_excel(RAW / "centros-salud.xlsx", sheet_name="Metadatos")
    source_count = int(raw_health["Provincia"].eq("Gipuzkoa").sum())
    verifications.append({
        "check": "health_services:Gipuzkoa", "source_value": source_count,
        "pipeline_value": len(services), "difference": len(services) - source_count,
        "result": "PASS" if source_count == len(services) else "FAIL", "source_id": "ODE_HEALTH_CENTRES_2026",
    })
    pd.DataFrame(verifications).to_csv(ANALYSIS / "verificaciones_manuales.csv", index=False)

    report = {
        "status": "PASS",
        "expected_municipalities": 88,
        "present_municipalities": len(municipalities),
        "missing_municipalities": [],
        "duplicate_municipality_codes": int(municipalities["municipality_code"].duplicated().sum()),
        "services": len(services),
        "service_categories": services["service_category"].value_counts().to_dict(),
        "services_missing_coordinates": int(services[["latitude", "longitude"]].isna().any(axis=1).sum()),
        "invalid_geometries": int((~boundaries.geometry.is_valid).sum()),
        "manual_checks_passed": int(sum(v["result"] == "PASS" for v in verifications)),
        "manual_checks_total": len(verifications),
    }
    (ANALYSIS / "validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

