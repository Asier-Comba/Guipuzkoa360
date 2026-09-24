from __future__ import annotations

import csv
from pathlib import Path

import pytest

from data_access import DataRepository
from schemas import DataContractError


FIXTURES = Path(__file__).parent / "fixtures"


def test_loads_codes_as_text_and_derives_sources():
    repo = DataRepository(FIXTURES)
    assert repo.municipalities()[0]["municipality_code"] == "T001"
    assert repo.demography()[0]["pct_65_plus"] == 20.0
    assert repo.source_details(["SRC_TEST_DEMO"])[0]["institution"] == "TEST_ONLY"


def test_missing_file_is_controlled(tmp_path: Path):
    with pytest.raises(DataContractError) as error:
        DataRepository(tmp_path).municipalities()
    assert error.value.code == "missing_file"


def test_missing_column_is_controlled(tmp_path: Path):
    (tmp_path / "municipios.csv").write_text("municipality_code\nT1\n", encoding="utf-8")
    with pytest.raises(DataContractError) as error:
        DataRepository(tmp_path).municipalities()
    assert error.value.code == "missing_columns"


def test_duplicate_codes_are_rejected(tmp_path: Path):
    (tmp_path / "municipios.csv").write_text(
        "municipality_code,municipality_name\nT1,TEST_A\nT1,TEST_B\n", encoding="utf-8"
    )
    with pytest.raises(DataContractError) as error:
        DataRepository(tmp_path).municipalities()
    assert error.value.code == "duplicate_keys"


def test_na_does_not_become_zero(tmp_path: Path):
    (tmp_path / "demografia.csv").write_text(
        "municipality_code,municipality_name,population_total,pct_65_plus,reference_period,source_id\n"
        "T1,TEST_A,100,,2025,SRC\n",
        encoding="utf-8",
    )
    row = DataRepository(tmp_path).demography()[0]
    assert row["pct_65_plus"] is None


def test_aliases_are_controlled(tmp_path: Path):
    (tmp_path / "municipios.csv").write_text(
        "codigo_municipio,nombre_municipio\n001,TEST_ALIAS\n", encoding="utf-8"
    )
    row = DataRepository(tmp_path).municipalities()[0]
    assert row["municipality_code"] == "001"
    assert row["municipality_name"] == "TEST_ALIAS"


def test_invalid_percentage_is_rejected(tmp_path: Path):
    (tmp_path / "demografia.csv").write_text(
        "municipality_code,municipality_name,population_total,pct_65_plus,reference_period,source_id\n"
        "T1,TEST_A,100,120,2025,SRC\n",
        encoding="utf-8",
    )
    with pytest.raises(DataContractError) as error:
        DataRepository(tmp_path).demography()
    assert error.value.code == "invalid_percentage"
