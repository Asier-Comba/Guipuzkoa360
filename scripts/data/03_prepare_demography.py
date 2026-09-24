"""Prepara población total, 65+ y una estimación reproducible de 75+."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "datos_originales"
OUT = ROOT / "datos_preparados"


def metadata_name_to_code(path: Path) -> dict[str, str]:
    metadata = json.loads(path.read_text(encoding="utf-8"))
    territory = metadata["variables"][0]
    return {
        label: code
        for code, label in zip(territory["values"], territory["valueTexts"])
        if len(code) == 5 and code.startswith("20")
    }


def main() -> None:
    name_to_code = metadata_name_to_code(RAW / "eustat_ep06b_metadata.json")
    age = pd.read_csv(RAW / "eustat_demografia_2025.csv", encoding="cp1252")
    age.columns = ["municipality_name", "age_group", "sex", "population"]
    age["municipality_code"] = age["municipality_name"].map(name_to_code)
    if age["municipality_code"].isna().any():
        raise ValueError("Eustat devolvió nombres municipales sin código en metadatos")
    pivot = age.pivot(index=["municipality_code", "municipality_name"], columns="age_group", values="population")
    pivot = pivot.reset_index().rename(columns={"Total": "population_total", ">= 65": "population_65_plus"})

    birth = pd.read_csv(RAW / "eustat_nacimientos_hasta_1949_2025.csv", encoding="cp1252")
    birth.columns = ["municipality_name", "birth_year", "sex", "population"]
    birth["municipality_code"] = birth["municipality_name"].map(name_to_code)
    older = birth.groupby("municipality_code", as_index=False)["population"].sum().rename(
        columns={"population": "population_75_plus"}
    )

    result = pivot.merge(older, on="municipality_code", how="left", validate="one_to_one")
    result["pct_65_plus"] = result["population_65_plus"] / result["population_total"] * 100
    result["pct_75_plus"] = result["population_75_plus"] / result["population_total"] * 100
    result["reference_period"] = "2025-01-01"
    result["source_id"] = "EUSTAT_EMH_2025"
    result = result[
        [
            "municipality_code", "municipality_name", "population_total", "population_65_plus",
            "population_75_plus", "pct_65_plus", "pct_75_plus", "reference_period", "source_id",
        ]
    ].sort_values("municipality_code")
    integer_cols = ["population_total", "population_65_plus", "population_75_plus"]
    result[integer_cols] = result[integer_cols].astype("int64")
    result[["pct_65_plus", "pct_75_plus"]] = result[["pct_65_plus", "pct_75_plus"]].round(3)
    result.to_csv(OUT / "demografia.csv", index=False, lineterminator="\n")
    print(f"Demografía: {len(result)} municipios; referencia 2025-01-01.")


if __name__ == "__main__":
    main()
