"""Carga, normalización y validación de los datos preparados."""

from __future__ import annotations

import csv
import json
import math
import unicodedata
from pathlib import Path
from typing import Any, Iterable

try:
    from .schemas import DataContractError
except ImportError:  # Compatibilidad con Studio cuando ejecuta la carpeta directamente.
    from schemas import DataContractError


ALIASES: dict[str, tuple[str, ...]] = {
    "municipality_code": ("municipality_code", "codigo_municipio", "cod_municipio", "ine_code"),
    "municipality_name": ("municipality_name", "municipio", "nombre_municipio", "name"),
    "population_total": ("population_total", "poblacion_total", "total_population"),
    "population_65_plus": ("population_65_plus", "poblacion_65_mas", "pop_65_plus"),
    "population_75_plus": ("population_75_plus", "poblacion_75_mas", "pop_75_plus"),
    "pct_65_plus": ("pct_65_plus", "porcentaje_65_mas", "percentage_65_plus"),
    "pct_75_plus": ("pct_75_plus", "porcentaje_75_mas", "percentage_75_plus"),
    "reference_period": ("reference_period", "periodo_referencia", "period", "year"),
    "source_id": ("source_id", "id_fuente", "source"),
    "service_id": ("service_id", "id_servicio"),
    "service_name": ("service_name", "nombre_servicio"),
    "service_category": ("service_category", "categoria_servicio", "category"),
    "latitude": ("latitude", "latitud", "lat"),
    "longitude": ("longitude", "longitud", "lon", "lng"),
}


NUMERIC_FIELDS = {
    "population_total",
    "population_65_plus",
    "population_75_plus",
    "pct_65_plus",
    "pct_75_plus",
    "latitude",
    "longitude",
}


def _key(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    return "".join(c for c in text if not unicodedata.combining(c)).casefold().strip()


def _blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _float(value: Any, field: str, row_number: int, allow_blank: bool = True) -> float | None:
    if _blank(value):
        if allow_blank:
            return None
        raise DataContractError("missing_value", f"Falta {field} en la fila {row_number}.")
    try:
        parsed = float(str(value).replace("%", "").replace(",", "."))
    except (TypeError, ValueError) as exc:
        raise DataContractError(
            "invalid_type", f"{field} debe ser numérico en la fila {row_number}: {value!r}."
        ) from exc
    if not math.isfinite(parsed):
        raise DataContractError("invalid_type", f"{field} no puede ser infinito o NaN.")
    return parsed


def _canonical_columns(fieldnames: Iterable[str] | None) -> dict[str, str]:
    available = list(fieldnames or [])
    normalized = {_key(name): name for name in available}
    result: dict[str, str] = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            if _key(alias) in normalized:
                result[canonical] = normalized[_key(alias)]
                break
    return result


def _require_columns(mapping: dict[str, str], required: Iterable[str], filename: str) -> None:
    missing = [name for name in required if name not in mapping]
    if missing:
        raise DataContractError(
            "missing_columns",
            f"{filename} no contiene columnas requeridas: {', '.join(missing)}.",
            sorted(mapping),
        )


def _polygon_centroid(ring: list[list[float]]) -> tuple[float, float] | None:
    if len(ring) < 3:
        return None
    area2 = cx = cy = 0.0
    for a, b in zip(ring, ring[1:] + ring[:1]):
        cross = a[0] * b[1] - b[0] * a[1]
        area2 += cross
        cx += (a[0] + b[0]) * cross
        cy += (a[1] + b[1]) * cross
    if abs(area2) < 1e-12:
        return None
    return cx / (3 * area2), cy / (3 * area2)


class DataRepository:
    """Acceso a archivos preparados con validación temprana y trazabilidad."""

    def __init__(self, data_dir: str | Path = "datos_preparados") -> None:
        self.data_dir = Path(data_dir)
        self.warnings: list[str] = []
        self._municipalities: list[dict[str, Any]] | None = None
        self._demography: list[dict[str, Any]] | None = None
        self._services: list[dict[str, Any]] | None = None
        self._metadata: dict[str, Any] | None = None

    def _csv(self, filename: str, required: Iterable[str]) -> list[dict[str, Any]]:
        path = self.data_dir / filename
        if not path.is_file():
            raise DataContractError("missing_file", f"No se encuentra el archivo preparado {path.as_posix()}.")
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            mapping = _canonical_columns(reader.fieldnames)
            _require_columns(mapping, required, filename)
            rows: list[dict[str, Any]] = []
            for number, raw in enumerate(reader, start=2):
                row: dict[str, Any] = {}
                for canonical, original in mapping.items():
                    value: Any = raw.get(original)
                    if canonical in NUMERIC_FIELDS:
                        value = _float(value, canonical, number)
                    elif value is not None:
                        value = str(value).strip()
                    row[canonical] = value
                for required_field in required:
                    if _blank(row.get(required_field)):
                        raise DataContractError(
                            "missing_value",
                            f"Falta {required_field} en la fila {number} de {filename}.",
                        )
                row["_row_number"] = number
                row["_file"] = path.as_posix()
                rows.append(row)
        return rows

    @staticmethod
    def _duplicates(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> list[str]:
        seen: set[tuple[Any, ...]] = set()
        duplicates: list[str] = []
        for row in rows:
            key = tuple(row.get(field) for field in fields)
            if key in seen:
                duplicates.append(" / ".join(str(value) for value in key))
            seen.add(key)
        return duplicates

    def municipalities(self) -> list[dict[str, Any]]:
        if self._municipalities is None:
            rows = self._csv("municipios.csv", ("municipality_code", "municipality_name"))
            duplicates = self._duplicates(rows, ("municipality_code",))
            if duplicates:
                raise DataContractError("duplicate_keys", "Códigos municipales duplicados: " + ", ".join(duplicates))
            self._apply_geojson_centroids(rows)
            self._municipalities = rows
        return self._municipalities

    def demography(self) -> list[dict[str, Any]]:
        if self._demography is None:
            rows = self._csv(
                "demografia.csv",
                ("municipality_code", "municipality_name", "reference_period", "source_id"),
            )
            for row in rows:
                total = row.get("population_total")
                for population_field in ("population_total", "population_65_plus", "population_75_plus"):
                    value = row.get(population_field)
                    if value is not None and value < 0:
                        raise DataContractError(
                            "invalid_population",
                            f"{population_field} no puede ser negativo en la fila {row['_row_number']}.",
                        )
                for age in ("65", "75"):
                    count_key, pct_key = f"population_{age}_plus", f"pct_{age}_plus"
                    count, pct = row.get(count_key), row.get(pct_key)
                    if pct is not None and not 0 <= pct <= 100:
                        raise DataContractError(
                            "invalid_percentage",
                            f"{pct_key} debe estar entre 0 y 100 en la fila {row['_row_number']}.",
                        )
                    if count is not None and total is not None and count > total:
                        raise DataContractError(
                            "invalid_population",
                            f"{count_key} supera population_total en la fila {row['_row_number']}.",
                        )
                    if pct is None and count is not None and total not in (None, 0):
                        row[pct_key] = 100.0 * count / total
                        self.warnings.append(f"{pct_key} calculado a partir de recuento y población total.")
                    if count is None and pct is None:
                        self.warnings.append(
                            f"Sin métrica >= {age} para {row.get('municipality_name')} ({row.get('reference_period')})."
                        )
            duplicates = self._duplicates(rows, ("municipality_code", "reference_period"))
            if duplicates:
                raise DataContractError("duplicate_keys", "Filas demográficas duplicadas: " + ", ".join(duplicates))
            self._demography = rows
        return self._demography

    def services(self) -> list[dict[str, Any]]:
        if self._services is None:
            rows = self._csv(
                "servicios.csv",
                (
                    "service_id",
                    "service_name",
                    "service_category",
                    "municipality_code",
                    "latitude",
                    "longitude",
                    "reference_period",
                    "source_id",
                ),
            )
            duplicates = self._duplicates(rows, ("service_id",))
            if duplicates:
                raise DataContractError("duplicate_keys", "Identificadores de servicio duplicados: " + ", ".join(duplicates))
            for row in rows:
                lat, lon = row.get("latitude"), row.get("longitude")
                if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    raise DataContractError(
                        "invalid_coordinates", f"Coordenadas inválidas para {row.get('service_id')}.")
            self._services = rows
        return self._services

    def metadata(self) -> dict[str, Any]:
        if self._metadata is None:
            path = self.data_dir / "metadata_sources.json"
            if not path.is_file():
                self.warnings.append("Falta metadata_sources.json; la procedencia se limita a source_id.")
                self._metadata = {"sources": []}
            else:
                try:
                    content = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    raise DataContractError("invalid_metadata", f"No se puede leer {path.as_posix()}: {exc}.") from exc
                self._metadata = content if isinstance(content, dict) else {"sources": content}
        return self._metadata

    def source_details(self, source_ids: Iterable[str]) -> list[dict[str, Any]]:
        ids = {str(value) for value in source_ids if not _blank(value)}
        raw_sources = self.metadata().get("sources", [])
        by_id = {str(item.get("source_id")): item for item in raw_sources if isinstance(item, dict)}
        return [by_id.get(source_id, {"source_id": source_id, "warning": "Sin metadatos detallados."}) for source_id in sorted(ids)]

    def municipality_lookup(self, query: str) -> dict[str, Any]:
        wanted = _key(query)
        rows = self.municipalities()
        exact = [row for row in rows if wanted in {_key(row["municipality_name"]), _key(row["municipality_code"])}]
        if len(exact) == 1:
            return exact[0]
        partial = [row for row in rows if wanted and wanted in _key(row["municipality_name"])]
        if len(partial) == 1:
            return partial[0]
        options = sorted(row["municipality_name"] for row in partial or rows)
        raise DataContractError("municipality_not_found", f"No se pudo resolver el municipio {query!r} de forma inequívoca.", options[:20])

    def available_periods(self) -> list[str]:
        return sorted({str(row["reference_period"]) for row in self.demography() if row.get("reference_period")})

    def choose_period(self, period: str | None) -> str:
        periods = self.available_periods()
        if not periods:
            raise DataContractError("missing_period", "Los datos demográficos no contienen un periodo utilizable.")
        if period is None:
            if len(periods) == 1:
                return periods[0]
            raise DataContractError("period_required", "Hay varios periodos disponibles; indica cuál usar.", periods)
        if str(period) not in periods:
            raise DataContractError("period_not_found", f"No existe el periodo {period}.", periods)
        return str(period)

    def _apply_geojson_centroids(self, municipalities: list[dict[str, Any]]) -> None:
        if all(row.get("latitude") is not None and row.get("longitude") is not None for row in municipalities):
            return
        path = self.data_dir / "municipios.geojson"
        if not path.is_file():
            return
        try:
            geo = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.warnings.append("municipios.geojson no pudo leerse; no se derivaron centroides.")
            return
        centroids: dict[str, tuple[float, float]] = {}
        for feature in geo.get("features", []):
            props = feature.get("properties", {})
            mapping = _canonical_columns(props.keys())
            code_key = mapping.get("municipality_code")
            if not code_key:
                continue
            geometry = feature.get("geometry") or {}
            coordinates = geometry.get("coordinates") or []
            rings: list[list[list[float]]] = []
            if geometry.get("type") == "Polygon" and coordinates:
                rings = [coordinates[0]]
            elif geometry.get("type") == "MultiPolygon":
                rings = [polygon[0] for polygon in coordinates if polygon]
            computed = [_polygon_centroid(ring) for ring in rings]
            valid = [item for item in computed if item]
            if valid:
                lon = sum(item[0] for item in valid) / len(valid)
                lat = sum(item[1] for item in valid) / len(valid)
                centroids[str(props[code_key]).strip()] = (lat, lon)
        for row in municipalities:
            pair = centroids.get(str(row["municipality_code"]))
            if pair:
                row["latitude"], row["longitude"] = pair
