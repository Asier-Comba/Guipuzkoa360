from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def test_municipal_coverage_and_keys():
    demography = pd.read_csv(ROOT / "datos_preparados" / "demografia.csv", dtype={"municipality_code": str})
    geography = gpd.read_file(ROOT / "datos_preparados" / "municipios.geojson")
    assert len(demography) == 88
    assert len(geography) == 88
    assert demography["municipality_code"].is_unique
    assert set(demography["municipality_code"]) == set(geography["municipality_code"])


def test_demographic_logic():
    data = pd.read_csv(ROOT / "datos_preparados" / "demografia.csv")
    assert (data.population_75_plus <= data.population_65_plus).all()
    assert (data.population_65_plus <= data.population_total).all()
    assert data.pct_65_plus.between(0, 100).all()
    assert data.pct_75_plus.between(0, 100).all()


def test_services_have_valid_location_and_category():
    services = pd.read_csv(ROOT / "datos_preparados" / "servicios.csv", dtype={"municipality_code": str})
    assert len(services) == 148
    assert services.service_id.is_unique
    assert services.latitude.between(42.8, 43.5).all()
    assert services.longitude.between(-2.7, -1.7).all()
    assert set(services.service_category) <= {"primary_care", "hospital", "mental_health", "other_health"}


def test_geometry_is_valid_wgs84():
    geography = gpd.read_file(ROOT / "datos_preparados" / "municipios.geojson")
    assert geography.crs.to_epsg() == 4326
    assert geography.geometry.is_valid.all()


def test_manual_reference_checks_pass():
    checks = pd.read_csv(ROOT / "analisis" / "verificaciones_manuales.csv")
    assert len(checks) >= 3
    assert checks.result.eq("PASS").all()

