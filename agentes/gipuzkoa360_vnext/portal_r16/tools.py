"""Generated two-editor Studio tool bundle. Edit source modules, not this file."""

from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass
class ResultEnvelope:
    status: str = 'ok'
    question: str = ''
    filters: dict[str, Any] = field(default_factory=dict)
    period: str | None = None
    metric: str | None = None
    unit: str | None = None
    rows_used: int = 0
    data: list[dict[str, Any]] = field(default_factory=list)
    method: str = ''
    sources: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def error_result(code: str, message: str, available_options: list[str] | None=None) -> dict[str, Any]:
    return {'status': 'error', 'error_code': code, 'message': message, 'available_options': available_options or []}

class DataContractError(ValueError):
    """Error de datos esperado y presentable al usuario."""

    def __init__(self, code: str, message: str, available_options: list[str] | None=None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.available_options = available_options or []

    def as_result(self) -> dict[str, Any]:
        return error_result(self.code, self.message, self.available_options)
import math
from typing import Any, Iterable

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    p1, p2 = (math.radians(lat1), math.radians(lat2))
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def percentile_rank(values: Iterable[float], value: float) -> float:
    ordered = sorted(values)
    if len(ordered) <= 1:
        return 1.0
    below = sum((item < value for item in ordered))
    equal = sum((item == value for item in ordered))
    return (below + (equal - 1) / 2) / (len(ordered) - 1)

def quantile(values: Iterable[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError('No hay valores para calcular el cuantil.')
    position = (len(ordered) - 1) * q
    lower, upper = (math.floor(position), math.ceil(position))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

def nearest_service(latitude: float, longitude: float, services: list[dict[str, Any]]) -> tuple[float | None, dict[str, Any] | None]:
    if not services:
        return (None, None)
    pairs = [(haversine_km(latitude, longitude, item['latitude'], item['longitude']), item) for item in services]
    return min(pairs, key=lambda pair: pair[0])

def nearest_service_projected(easting_m: float, northing_m: float, services: list[dict[str, Any]]) -> tuple[float | None, dict[str, Any] | None]:
    """Distancia euclídea en EPSG:25830, en metros."""
    projected = [item for item in services if item.get('easting_m') is not None and item.get('northing_m') is not None]
    if not projected:
        return (None, None)
    pairs = [(math.hypot(item['easting_m'] - easting_m, item['northing_m'] - northing_m), item) for item in projected]
    return min(pairs, key=lambda pair: pair[0])

def wgs84_to_utm30(latitude: float, longitude: float) -> tuple[float, float]:
    """Convierte WGS84 a ETRS89/UTM 30N con precisión suficiente para escenarios locales.

    Para la escala de Gipuzkoa, WGS84 y ETRS89 son equivalentes a efectos del indicador.
    Implementa la serie Transverse Mercator estándar para evitar dependencias runtime.
    """
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    k0 = 0.9996
    phi = math.radians(latitude)
    lam = math.radians(longitude)
    lam0 = math.radians(-3.0)
    n = a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    t = math.tan(phi) ** 2
    c = ep2 * math.cos(phi) ** 2
    aa = math.cos(phi) * (lam - lam0)
    m = a * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * phi - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * phi) + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * phi) - 35 * e2 ** 3 / 3072 * math.sin(6 * phi))
    easting = 500000 + k0 * n * (aa + (1 - t + c) * aa ** 3 / 6 + (5 - 18 * t + t ** 2 + 72 * c - 58 * ep2) * aa ** 5 / 120)
    northing = k0 * (m + n * math.tan(phi) * (aa ** 2 / 2 + (5 - t + 9 * c + 4 * c ** 2) * aa ** 4 / 24 + (61 - 58 * t + t ** 2 + 600 * c - 330 * ep2) * aa ** 6 / 720))
    return (easting, northing)
import csv
import json
import math
import unicodedata
from pathlib import Path
from typing import Any, Iterable
ALIASES: dict[str, tuple[str, ...]] = {'municipality_code': ('municipality_code', 'codigo_municipio', 'cod_municipio', 'ine_code'), 'municipality_name': ('municipality_name', 'municipio', 'nombre_municipio', 'name'), 'population_total': ('population_total', 'poblacion_total', 'total_population'), 'population_65_plus': ('population_65_plus', 'poblacion_65_mas', 'pop_65_plus'), 'population_75_plus': ('population_75_plus', 'poblacion_75_mas', 'pop_75_plus'), 'pct_65_plus': ('pct_65_plus', 'porcentaje_65_mas', 'percentage_65_plus'), 'pct_75_plus': ('pct_75_plus', 'porcentaje_75_mas', 'percentage_75_plus'), 'reference_period': ('reference_period', 'periodo_referencia', 'period', 'year'), 'source_id': ('source_id', 'id_fuente', 'source'), 'service_id': ('service_id', 'id_servicio'), 'service_name': ('service_name', 'nombre_servicio'), 'service_category': ('service_category', 'categoria_servicio', 'category'), 'latitude': ('latitude', 'latitud', 'lat'), 'longitude': ('longitude', 'longitud', 'lon', 'lng'), 'easting_m': ('easting_m', 'reference_easting_m', 'x_25830'), 'northing_m': ('northing_m', 'reference_northing_m', 'y_25830'), 'area_km2': ('area_km2',), 'services_primary_care': ('services_primary_care',), 'services_hospital': ('services_hospital',), 'services_mental_health': ('services_mental_health',), 'services_other_health': ('services_other_health',), 'primary_care_per_10000_65_plus': ('primary_care_per_10000_65_plus',), 'distance_to_nearest_primary_care_m': ('distance_to_nearest_primary_care_m',), 'distance_to_nearest_hospital_m': ('distance_to_nearest_hospital_m',), 'metrics_reference_period': ('metrics_reference_period',), 'services_total': ('services_total',), 'primary_care_per_10000_75_plus': ('primary_care_per_10000_75_plus',), 'hospital_per_10000_65_plus': ('hospital_per_10000_65_plus',), 'hospital_per_10000_75_plus': ('hospital_per_10000_75_plus',), 'mental_health_per_10000_65_plus': ('mental_health_per_10000_65_plus',), 'mental_health_per_10000_75_plus': ('mental_health_per_10000_75_plus',), 'other_health_per_10000_65_plus': ('other_health_per_10000_65_plus',), 'other_health_per_10000_75_plus': ('other_health_per_10000_75_plus',), 'distance_to_nearest_mental_health_m': ('distance_to_nearest_mental_health_m',), 'distance_to_nearest_other_health_m': ('distance_to_nearest_other_health_m',)}
NUMERIC_FIELDS = {'population_total', 'population_65_plus', 'population_75_plus', 'pct_65_plus', 'pct_75_plus', 'latitude', 'longitude', 'easting_m', 'northing_m', 'area_km2', 'services_primary_care', 'services_hospital', 'services_mental_health', 'services_other_health', 'primary_care_per_10000_65_plus', 'distance_to_nearest_primary_care_m', 'distance_to_nearest_hospital_m', 'services_total', 'primary_care_per_10000_75_plus', 'hospital_per_10000_65_plus', 'hospital_per_10000_75_plus', 'mental_health_per_10000_65_plus', 'mental_health_per_10000_75_plus', 'other_health_per_10000_65_plus', 'other_health_per_10000_75_plus', 'distance_to_nearest_mental_health_m', 'distance_to_nearest_other_health_m'}
INTEGER_FIELDS = {'population_total', 'population_65_plus', 'population_75_plus', 'services_primary_care', 'services_hospital', 'services_mental_health', 'services_other_health', 'services_total'}

def _key(value: str) -> str:
    text = unicodedata.normalize('NFKD', str(value))
    return ''.join((c for c in text if not unicodedata.combining(c))).casefold().strip()

def _blank(value: Any) -> bool:
    return value is None or str(value).strip() == ''

def _float(value: Any, field: str, row_number: int, allow_blank: bool=True) -> float | None:
    if _blank(value):
        if allow_blank:
            return None
        raise DataContractError('missing_value', f'Falta {field} en la fila {row_number}.')
    try:
        parsed = float(str(value).replace('%', '').replace(',', '.'))
    except (TypeError, ValueError) as exc:
        raise DataContractError('invalid_type', f'{field} debe ser numérico en la fila {row_number}: {value!r}.') from exc
    if not math.isfinite(parsed):
        raise DataContractError('invalid_type', f'{field} no puede ser infinito o NaN.')
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
        raise DataContractError('missing_columns', f"{filename} no contiene columnas requeridas: {', '.join(missing)}.", sorted(mapping))

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
    return (cx / (3 * area2), cy / (3 * area2))

class DataRepository:
    """Acceso a archivos preparados con validación temprana y trazabilidad."""

    def __init__(self, data_dir: str | Path='datos_preparados') -> None:
        self.data_dir = Path(data_dir)
        self.warnings: list[str] = []
        self._municipalities: list[dict[str, Any]] | None = None
        self._demography: list[dict[str, Any]] | None = None
        self._services: list[dict[str, Any]] | None = None
        self._metadata: dict[str, Any] | None = None

    def _csv(self, filename: str, required: Iterable[str]) -> list[dict[str, Any]]:
        path = self.data_dir / filename
        if not path.is_file():
            raise DataContractError('missing_file', f'No se encuentra el archivo preparado {path.as_posix()}.')
        with path.open('r', encoding='utf-8-sig', newline='') as handle:
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
                        if canonical in INTEGER_FIELDS and value is not None:
                            if not value.is_integer():
                                raise DataContractError('invalid_type', f'{canonical} debe ser entero en la fila {number}: {value!r}.')
                            value = int(value)
                    elif value is not None:
                        value = str(value).strip()
                    row[canonical] = value
                for required_field in required:
                    if _blank(row.get(required_field)):
                        raise DataContractError('missing_value', f'Falta {required_field} en la fila {number} de {filename}.')
                row['_row_number'] = number
                row['_file'] = path.as_posix()
                rows.append(row)
        return rows

    @staticmethod
    def _duplicates(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> list[str]:
        seen: set[tuple[Any, ...]] = set()
        duplicates: list[str] = []
        for row in rows:
            key = tuple((row.get(field) for field in fields))
            if key in seen:
                duplicates.append(' / '.join((str(value) for value in key)))
            seen.add(key)
        return duplicates

    def municipalities(self) -> list[dict[str, Any]]:
        if self._municipalities is None:
            rows = self._csv('municipios.csv', ('municipality_code', 'municipality_name'))
            duplicates = self._duplicates(rows, ('municipality_code',))
            if duplicates:
                raise DataContractError('duplicate_keys', 'Códigos municipales duplicados: ' + ', '.join(duplicates))
            self._apply_runtime_reference_points(rows)
            self._apply_geojson_centroids(rows)
            self._municipalities = rows
        return self._municipalities

    def demography(self) -> list[dict[str, Any]]:
        if self._demography is None:
            rows = self._csv('demografia.csv', ('municipality_code', 'municipality_name', 'reference_period', 'source_id'))
            for row in rows:
                total = row.get('population_total')
                for population_field in ('population_total', 'population_65_plus', 'population_75_plus'):
                    value = row.get(population_field)
                    if value is not None and value < 0:
                        raise DataContractError('invalid_population', f"{population_field} no puede ser negativo en la fila {row['_row_number']}.")
                for age in ('65', '75'):
                    count_key, pct_key = (f'population_{age}_plus', f'pct_{age}_plus')
                    count, pct = (row.get(count_key), row.get(pct_key))
                    if pct is not None and (not 0 <= pct <= 100):
                        raise DataContractError('invalid_percentage', f"{pct_key} debe estar entre 0 y 100 en la fila {row['_row_number']}.")
                    if count is not None and total is not None and (count > total):
                        raise DataContractError('invalid_population', f"{count_key} supera population_total en la fila {row['_row_number']}.")
                    if pct is None and count is not None and (total not in (None, 0)):
                        row[pct_key] = 100.0 * count / total
                        self.warnings.append(f'{pct_key} calculado a partir de recuento y población total.')
                    if count is None and pct is None:
                        self.warnings.append(f"Sin métrica >= {age} para {row.get('municipality_name')} ({row.get('reference_period')}).")
            duplicates = self._duplicates(rows, ('municipality_code', 'reference_period'))
            if duplicates:
                raise DataContractError('duplicate_keys', 'Filas demográficas duplicadas: ' + ', '.join(duplicates))
            self._demography = rows
        return self._demography

    def services(self) -> list[dict[str, Any]]:
        if self._services is None:
            filename = 'runtime_servicios.csv' if (self.data_dir / 'runtime_servicios.csv').is_file() else 'servicios.csv'
            rows = self._csv(filename, ('service_id', 'service_name', 'service_category', 'municipality_code', 'latitude', 'longitude', 'reference_period', 'source_id'))
            duplicates = self._duplicates(rows, ('service_id',))
            if duplicates:
                raise DataContractError('duplicate_keys', 'Identificadores de servicio duplicados: ' + ', '.join(duplicates))
            for row in rows:
                lat, lon = (row.get('latitude'), row.get('longitude'))
                if lat is None or lon is None or (not -90 <= lat <= 90) or (not -180 <= lon <= 180):
                    raise DataContractError('invalid_coordinates', f"Coordenadas inválidas para {row.get('service_id')}.")
            self._services = rows
        return self._services

    def metadata(self) -> dict[str, Any]:
        if self._metadata is None:
            path = self.data_dir / 'metadata_sources.json'
            if not path.is_file():
                self.warnings.append('Falta metadata_sources.json; la procedencia se limita a source_id.')
                self._metadata = {'sources': []}
            else:
                try:
                    content = json.loads(path.read_text(encoding='utf-8'))
                except (OSError, json.JSONDecodeError) as exc:
                    raise DataContractError('invalid_metadata', f'No se puede leer {path.as_posix()}: {exc}.') from exc
                self._metadata = content if isinstance(content, dict) else {'sources': content}
        return self._metadata

    def source_details(self, source_ids: Iterable[str]) -> list[dict[str, Any]]:
        ids = {str(value) for value in source_ids if not _blank(value)}
        raw_sources = self.metadata().get('sources', [])
        by_id = {str(item.get('source_id')): item for item in raw_sources if isinstance(item, dict)}
        return [by_id.get(source_id, {'source_id': source_id, 'warning': 'Sin metadatos detallados.'}) for source_id in sorted(ids)]

    def municipality_lookup(self, query: str) -> dict[str, Any]:
        wanted = _key(query)
        rows = self.municipalities()
        exact = [row for row in rows if wanted in {_key(row['municipality_name']), _key(row['municipality_code'])}]
        if len(exact) == 1:
            return exact[0]
        partial = [row for row in rows if wanted and wanted in _key(row['municipality_name'])]
        if len(partial) == 1:
            return partial[0]
        options = sorted((row['municipality_name'] for row in partial or rows))
        raise DataContractError('municipality_not_found', f'No se pudo resolver el municipio {query!r} de forma inequívoca.', options[:20])

    def available_periods(self) -> list[str]:
        return sorted({str(row['reference_period']) for row in self.demography() if row.get('reference_period')})

    def choose_period(self, period: str | None) -> str:
        periods = self.available_periods()
        if not periods:
            raise DataContractError('missing_period', 'Los datos demográficos no contienen un periodo utilizable.')
        if period is None:
            if len(periods) == 1:
                return periods[0]
            raise DataContractError('period_required', 'Hay varios periodos disponibles; indica cuál usar.', periods)
        if str(period) not in periods:
            raise DataContractError('period_not_found', f'No existe el periodo {period}.', periods)
        return str(period)

    def _apply_geojson_centroids(self, municipalities: list[dict[str, Any]]) -> None:
        if all((row.get('latitude') is not None and row.get('longitude') is not None for row in municipalities)):
            return
        path = self.data_dir / 'municipios.geojson'
        if not path.is_file():
            return
        try:
            geo = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            self.warnings.append('municipios.geojson no pudo leerse; no se derivaron centroides.')
            return
        centroids: dict[str, tuple[float, float]] = {}
        for feature in geo.get('features', []):
            props = feature.get('properties', {})
            mapping = _canonical_columns(props.keys())
            code_key = mapping.get('municipality_code')
            if not code_key:
                continue
            geometry = feature.get('geometry') or {}
            coordinates = geometry.get('coordinates') or []
            rings: list[list[list[float]]] = []
            if geometry.get('type') == 'Polygon' and coordinates:
                rings = [coordinates[0]]
            elif geometry.get('type') == 'MultiPolygon':
                rings = [polygon[0] for polygon in coordinates if polygon]
            computed = [_polygon_centroid(ring) for ring in rings]
            valid = [item for item in computed if item]
            if valid:
                lon = sum((item[0] for item in valid)) / len(valid)
                lat = sum((item[1] for item in valid)) / len(valid)
                centroids[str(props[code_key]).strip()] = (lat, lon)
        for row in municipalities:
            pair = centroids.get(str(row['municipality_code']))
            if pair:
                row['latitude'], row['longitude'] = pair

    def _apply_runtime_reference_points(self, municipalities: list[dict[str, Any]]) -> None:
        path = self.data_dir / 'runtime_municipality_points.csv'
        if not path.is_file():
            return
        points = self._csv('runtime_municipality_points.csv', ('municipality_code', 'latitude', 'longitude', 'easting_m', 'northing_m'))
        duplicates = self._duplicates(points, ('municipality_code',))
        if duplicates:
            raise DataContractError('duplicate_keys', 'Puntos municipales duplicados: ' + ', '.join(duplicates))
        by_code = {row['municipality_code']: row for row in points}
        missing: list[str] = []
        for municipality in municipalities:
            point = by_code.get(municipality['municipality_code'])
            if point is None:
                missing.append(municipality['municipality_name'])
                continue
            for field in ('latitude', 'longitude', 'easting_m', 'northing_m'):
                municipality[field] = point[field]
            municipality['reference_point_source_id'] = point.get('source_id')
            municipality['reference_point_period'] = point.get('reference_period')
        if missing:
            self.warnings.append('Sin punto representativo runtime para: ' + ', '.join(missing))
import json
import math
import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

def _default_data_dir() -> Path:
    configured = os.environ.get('GIPUZKOA360_DATA_DIR')
    if configured:
        return Path(configured)
    workspace_path = Path('datos_preparados')
    if workspace_path.exists():
        return workspace_path
    return Path(__file__).resolve().parents[2] / 'datos_preparados'

def _json(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False)

def _compact_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    audit_fields = ('source_id', 'institution', 'title', 'reference_period', 'unit', 'url', 'limitations')
    return [{field: item[field] for field in audit_fields if field in item} for item in sources]

def compact_result(result: dict[str, Any], result_kind: str) -> dict[str, Any]:
    """Reduce transporte al LLM sin alterar métricas ni la salida completa del core."""
    compact = dict(result)
    rows = list(result.get('data', []))
    summary = dict(result.get('summary', {}))
    summary.setdefault('total_result_rows', len(rows))
    if result_kind == 'access' and len(rows) > 20:
        within = sum((bool(row.get('within_threshold')) for row in rows))
        distances = [row['nearest_distance_m'] for row in rows if row.get('nearest_distance_m') is not None]
        summary.update({'within_threshold_count': within, 'outside_threshold_count': len(rows) - within, 'minimum_distance_m': min(distances) if distances else None, 'maximum_distance_m': max(distances) if distances else None, 'returned_rows': min(10, len(rows)), 'selection': '10 municipios con mayor distancia; indique municipios concretos para acotar la consulta.'})
        compact['data'] = rows[:10]
    elif result_kind == 'coincidence':
        highlighted = [row for row in rows if row.get('highlighted')]
        selected = highlighted or rows[:5]
        summary.update({'highlighted_count': len(highlighted), 'returned_rows': len(selected), 'selection': 'Todos los destacados; si no hay ninguno, los 5 primeros por criterio.'})
        compact['data'] = selected
    elif result_kind == 'scenario':
        changed = [row for row in rows if row.get('difference_absolute_m') not in (None, 0, 0.0) or row.get('baseline_within_threshold') != row.get('scenario_within_threshold')]
        summary.update({'affected_rows': len(changed), 'improved_distance_rows': sum(((row.get('difference_absolute_m') or 0) < 0 for row in changed)), 'worsened_distance_rows': sum(((row.get('difference_absolute_m') or 0) > 0 for row in changed)), 'threshold_status_changes': sum((row.get('baseline_within_threshold') != row.get('scenario_within_threshold') for row in changed)), 'returned_rows': len(changed), 'selection': 'Solo municipios con distancia o estado de umbral modificado.'})
        compact['data'] = changed
    compact['summary'] = summary
    compact['detail_level'] = 'compact'
    if result_kind == 'source':
        compact['sources'] = [{'source_id': item.get('source_id')} for item in result.get('sources', [])]
    else:
        compact['sources'] = _compact_sources(result.get('sources', []))
    return compact

def _safe(operation: Callable[[], dict[str, Any]], *, result_kind: str | None=None, detail: bool=False) -> str:
    try:
        result = operation()
        if detail:
            result = dict(result)
            result['detail_level'] = 'full'
        elif result_kind:
            result = compact_result(result, result_kind)
        return _json(result)
    except DataContractError as exc:
        return _json(exc.as_result())
    except (ValueError, TypeError) as exc:
        return _json({'status': 'error', 'error_code': 'invalid_request', 'message': str(exc), 'available_options': []})

def _normalized_key(value: Any) -> str:
    """Normaliza texto humano sin convertir entradas ausentes en valores válidos."""
    if value is None:
        return ''
    text = unicodedata.normalize('NFKD', str(value).strip().casefold())
    text = ''.join((character for character in text if not unicodedata.combining(character)))
    return re.sub('[\\s_-]+', ' ', text).strip()

def normalize_service_category(value: Any) -> str:
    aliases = {'primary_care': {'atencion primaria', 'primary care'}, 'mental_health': {'salud mental', 'mental health'}, 'hospital': {'hospital', 'hospitals', 'hospitales'}, 'other_health': {'other health', 'otros', 'otra salud', 'otras prestaciones sanitarias', 'otros servicios sanitarios'}}
    key = _normalized_key(value)
    for canonical, choices in aliases.items():
        if key == _normalized_key(canonical) or key in choices:
            return canonical
    raise DataContractError('invalid_service_category', f'Categoría de servicio no reconocida: {value!r}.', list(aliases))

def normalize_age_group(value: Any) -> str:
    key = _normalized_key(value).replace('≥', '>=')
    compact = re.sub('\\s+', '', key)
    aliases = {'65': {'65', '65+', '>=65', '65omas'}, '75': {'75', '75+', '>=75', '75omas'}}
    for canonical, choices in aliases.items():
        if compact in choices:
            return canonical
    raise DataContractError('invalid_age_group', f'Grupo de edad no reconocido: {value!r}.', ['65', '65+', '65 o más', '≥65', '>=65', '75', '75+', '75 o más', '≥75', '>=75'])

def normalize_scenario_action(value: Any) -> str:
    aliases = {'add_service': {'add service', 'anadir', 'anadir servicio', 'agregar', 'agregar servicio'}, 'remove_service': {'remove', 'remove service', 'eliminar', 'eliminar servicio', 'quitar servicio'}, 'change_threshold': {'change threshold', 'cambiar umbral', 'cambio de umbral'}}
    key = _normalized_key(value)
    for canonical, choices in aliases.items():
        if key == _normalized_key(canonical) or key in choices:
            return canonical
    raise DataContractError('invalid_scenario', f'Acción de escenario no reconocida: {value!r}.', list(aliases))

class TerritorialAnalysis:

    def __init__(self, repository: DataRepository) -> None:
        self.repo = repository

    def _service_category(self, value: Any) -> str:
        categories = sorted({row['service_category'] for row in self.repo.services()})
        try:
            return normalize_service_category(value)
        except DataContractError:
            key = _normalized_key(value)
            exact = [category for category in categories if _normalized_key(category) == key]
            if len(exact) == 1:
                return exact[0]
            raise DataContractError('service_category_not_found', f'No hay una categoría de servicio inequívoca para {value!r}.', categories) from None

    @staticmethod
    def _threshold(value: Any) -> float:
        try:
            threshold = float(value)
        except (TypeError, ValueError) as exc:
            raise DataContractError('invalid_threshold', 'threshold_km debe ser un número mayor que 0 y no superar 100.') from exc
        if not math.isfinite(threshold) or threshold <= 0 or threshold > 100:
            raise DataContractError('invalid_threshold', 'threshold_km debe ser mayor que 0 y no superar 100.')
        return threshold

    @staticmethod
    def _age_fields(age_group: str, measure: str='percentage') -> tuple[str, str]:
        age = normalize_age_group(age_group)
        normalized_measure = {'percentage': 'percentage', 'percent': 'percentage', 'pct': 'percentage', 'porcentaje': 'percentage', 'count': 'count', 'recuento': 'count', 'conteo': 'count', 'personas': 'count'}.get(_normalized_key(measure))
        if normalized_measure is None:
            raise DataContractError('invalid_measure', 'La medida debe ser percentage o count.', ['percentage', 'count'])
        return (f'pct_{age}_plus' if normalized_measure == 'percentage' else f'population_{age}_plus', age)

    def _demography_for_period(self, period: str | None) -> tuple[str, list[dict[str, Any]]]:
        selected = self.repo.choose_period(period)
        rows = [row for row in self.repo.demography() if str(row.get('reference_period')) == selected]
        return (selected, rows)

    def _sources(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return self.repo.source_details((row.get('source_id') for row in rows))

    def resumen(self, municipality: str, period: str | None=None) -> dict[str, Any]:
        selected, demo_rows = self._demography_for_period(period)
        municipality_row = self.repo.municipality_lookup(municipality)
        code = municipality_row['municipality_code']
        matches = [row for row in demo_rows if row.get('municipality_code') == code]
        if not matches:
            raise DataContractError('missing_demography', f"No hay demografía para {municipality_row['municipality_name']} en {selected}.")
        demo = matches[0]
        service_rows = [row for row in self.repo.services() if row.get('municipality_code') == code]
        categories: dict[str, int] = {}
        for row in service_rows:
            category = row['service_category']
            categories[category] = categories.get(category, 0) + 1
        data = {'municipality_code': code, 'municipality_name': municipality_row['municipality_name'], 'population_total': demo.get('population_total'), 'population_65_plus': demo.get('population_65_plus'), 'population_75_plus': demo.get('population_75_plus'), 'pct_65_plus': demo.get('pct_65_plus'), 'pct_75_plus': demo.get('pct_75_plus'), 'services_in_municipality': categories, 'service_indicators': {category: {'registered_service_count': municipality_row.get(f'services_{category}'), 'rate_per_10000_65_plus': municipality_row.get(f'{category}_per_10000_65_plus'), 'rate_per_10000_75_plus': municipality_row.get(f'{category}_per_10000_75_plus'), 'nearest_distance_m': municipality_row.get(f'distance_to_nearest_{category}_m')} for category in ('primary_care', 'hospital', 'mental_health', 'other_health')}, 'metrics_reference_period': municipality_row.get('metrics_reference_period')}
        used = [demo] + service_rows
        return ResultEnvelope(question=f"Resumen territorial de {municipality_row['municipality_name']}", filters={'municipality_code': code, 'period': selected}, period=selected, metric='territorial_summary', unit='varias; ver cada campo', rows_used=len(used), data=[data], method='Selección por código municipal; recuento de registros por categoría; tasas por 10.000 personas del grupo de edad y mínima distancia euclídea EPSG:25830 desde el punto representativo municipal.', sources=self._sources(used), warnings=list(dict.fromkeys(self.repo.warnings)), limitations=['La presencia de un servicio no acredita capacidad, horario, calidad ni acceso real.', 'Los periodos de demografía y servicios pueden ser distintos; se muestran en las fuentes.']).to_dict()

    def envejecimiento(self, age_group: str='65', measure: str='percentage', period: str | None=None, top_n: int=10) -> dict[str, Any]:
        metric, age = self._age_fields(age_group, measure)
        normalized_measure = 'percentage' if metric.startswith('pct_') else 'count'
        if not 1 <= int(top_n) <= 100:
            raise DataContractError('invalid_top_n', 'top_n debe estar entre 1 y 100.')
        selected, rows = self._demography_for_period(period)
        available = [row for row in rows if row.get(metric) is not None]
        omitted = len(rows) - len(available)
        if not available:
            raise DataContractError('missing_metric', f'No hay valores disponibles para {metric} en {selected}.')
        ordered = sorted(available, key=lambda row: (-row[metric], row['municipality_name']))[:int(top_n)]
        data = [{'rank': rank, 'municipality_code': row['municipality_code'], 'municipality_name': row['municipality_name'], 'value': round(row[metric], 4), 'source_id': row.get('source_id')} for rank, row in enumerate(ordered, start=1)]
        warnings = list(dict.fromkeys(self.repo.warnings))
        if omitted:
            warnings.append(f'Se omitieron {omitted} filas sin {metric}; no se trataron como cero.')
        return ResultEnvelope(question=f'Envejecimiento de población >= {age}', filters={'age_group': age, 'measure': normalized_measure, 'period': selected, 'top_n': int(top_n)}, period=selected, metric=metric, unit='% de población' if normalized_measure == 'percentage' else 'personas', rows_used=len(available), data=data, method=f'Orden descendente de {metric}; empates por nombre municipal.', sources=self._sources(available), warnings=warnings, limitations=['El indicador describe estructura demográfica; no explica sus causas.']).to_dict()

    def acceso(self, service_category: str, threshold_km: float=1.0, period: str | None=None, municipality_names: list[str] | None=None, service_override: list[dict[str, Any]] | None=None) -> dict[str, Any]:
        service_category = self._service_category(service_category)
        threshold_km = self._threshold(threshold_km)
        municipalities = self.repo.municipalities()
        if municipality_names:
            selected_codes = {self.repo.municipality_lookup(name)['municipality_code'] for name in municipality_names}
            municipalities = [row for row in municipalities if row['municipality_code'] in selected_codes]
        missing_centroids = [row['municipality_name'] for row in municipalities if row.get('easting_m') is None or row.get('northing_m') is None]
        municipalities = [row for row in municipalities if row.get('easting_m') is not None and row.get('northing_m') is not None]
        if not municipalities:
            raise DataContractError('missing_coordinates', 'No hay coordenadas o centroides municipales para calcular distancia geométrica.')
        all_services = service_override if service_override is not None else self.repo.services()
        services = [row for row in all_services if row.get('service_category', '').casefold() == service_category.casefold()]
        categories = sorted({row['service_category'] for row in all_services})
        if not services:
            raise DataContractError('service_category_not_found', f'No hay servicios de categoría {service_category!r}.', categories)
        data: list[dict[str, Any]] = []
        for municipality in municipalities:
            distance, service = nearest_service_projected(municipality['easting_m'], municipality['northing_m'], services)
            data.append({'municipality_code': municipality['municipality_code'], 'municipality_name': municipality['municipality_name'], 'nearest_service_id': service['service_id'] if service else None, 'nearest_distance_m': round(distance, 1) if distance is not None else None, 'within_threshold': bool(distance is not None and distance <= threshold_km * 1000)})
        data.sort(key=lambda item: (-item['nearest_distance_m'], item['municipality_name']))
        warnings = list(dict.fromkeys(self.repo.warnings))
        if missing_centroids:
            warnings.append('Municipios omitidos por falta de coordenadas: ' + ', '.join(missing_centroids))
        service_periods = sorted({str(row.get('reference_period')) for row in services if row.get('reference_period')})
        geography_periods = sorted({str(row.get('reference_point_period')) for row in municipalities if row.get('reference_point_period')})
        provenance_rows = services + [{'source_id': row.get('reference_point_source_id')} for row in municipalities]
        return ResultEnvelope(question=f'Acceso geométrico a {service_category}', filters={'service_category': service_category, 'threshold_km': threshold_km, 'period_requested': period}, period='; '.join(service_periods + geography_periods) or None, metric='distance_geométrica_aproximada_desde_punto_representativo_municipal', unit='m', rows_used=len(municipalities) + len(services), data=data, method='Distancia euclídea en EPSG:25830 desde representative_point() del polígono municipal al punto del servicio más cercano de la categoría.', sources=self._sources(provenance_rows), warnings=warnings, limitations=['Es distancia geométrica aproximada, no distancia de red, tiempo de viaje ni acceso peatonal real.', 'El punto representativo municipal no está ponderado por población y no representa dónde vive cada persona.', 'La existencia registrada no acredita apertura, capacidad ni accesibilidad universal.']).to_dict()

    def comparar(self, municipality_names: list[str], age_group: str='65', service_category: str | None=None, threshold_km: float=1.0, period: str | None=None) -> dict[str, Any]:
        if not 2 <= len(municipality_names) <= 20:
            raise DataContractError('invalid_municipality_count', 'Indica entre 2 y 20 municipios.')
        metric, age = self._age_fields(age_group, 'percentage')
        selected, demo_rows = self._demography_for_period(period)
        resolved = [self.repo.municipality_lookup(name) for name in municipality_names]
        codes = {row['municipality_code'] for row in resolved}
        by_code = {row['municipality_code']: row for row in demo_rows if row['municipality_code'] in codes}
        missing = [row['municipality_name'] for row in resolved if row['municipality_code'] not in by_code]
        if missing:
            raise DataContractError('missing_demography', 'Falta demografía para: ' + ', '.join(missing))
        access_by_code: dict[str, dict[str, Any]] = {}
        access_result: dict[str, Any] | None = None
        if service_category:
            access_result = self.acceso(service_category, threshold_km, selected, municipality_names)
            service_category = access_result['filters']['service_category']
            access_by_code = {row['municipality_code']: row for row in access_result['data']}
        data = []
        for municipality in resolved:
            demo = by_code[municipality['municipality_code']]
            item = {'municipality_code': municipality['municipality_code'], 'municipality_name': municipality['municipality_name'], metric: demo.get(metric), 'population_total': demo.get('population_total'), 'source_id': demo.get('source_id')}
            item.update(access_by_code.get(municipality['municipality_code'], {}))
            data.append(item)
        sources = self._sources([by_code[code] for code in codes])
        if access_result:
            sources = list({item.get('source_id', str(index)): item for index, item in enumerate(sources + access_result['sources'])}.values())
        return ResultEnvelope(question='Comparación municipal', filters={'municipalities': [row['municipality_name'] for row in resolved], 'age_group': age, 'service_category': service_category, 'threshold_km': threshold_km if service_category else None}, period=selected, metric=metric + (' + distance_geométrica_aproximada' if service_category else ''), unit='% y m' if service_category else '%', rows_used=len(data), data=data, method='Selección por código municipal y comparación campo a campo; sin agregación opaca.', sources=sources, warnings=list(dict.fromkeys(self.repo.warnings)), limitations=(access_result or {}).get('limitations', []) + ['La comparación no demuestra causalidad.']).to_dict()

    def coincidencia(self, service_category: str, age_group: str='65', threshold_km: float=1.0, period: str | None=None, quantile_threshold: float=0.75) -> dict[str, Any]:
        service_category = self._service_category(service_category)
        if not 0.5 <= quantile_threshold <= 0.95:
            raise DataContractError('invalid_quantile', 'quantile_threshold debe estar entre 0.5 y 0.95.')
        metric, age = self._age_fields(age_group, 'percentage')
        selected, demo_rows = self._demography_for_period(period)
        access = self.acceso(service_category, threshold_km, selected)
        by_code = {row['municipality_code']: row for row in demo_rows if row.get(metric) is not None}
        joined = []
        for row in access['data']:
            demo = by_code.get(row['municipality_code'])
            if demo:
                joined.append({**row, metric: demo[metric], 'age_source_id': demo.get('source_id')})
        if not joined:
            raise DataContractError('no_joined_rows', 'No hay municipios con ambas métricas disponibles.')
        age_values = [row[metric] for row in joined]
        distance_values = [row['nearest_distance_m'] for row in joined]
        age_cut = quantile(age_values, quantile_threshold)
        distance_cut = quantile(distance_values, quantile_threshold)
        for row in joined:
            row['age_percentile_rank'] = round(percentile_rank(age_values, row[metric]), 4)
            row['distance_percentile_rank'] = round(percentile_rank(distance_values, row['nearest_distance_m']), 4)
            row['meets_age_criterion'] = row[metric] >= age_cut
            row['meets_access_criterion'] = row['nearest_distance_m'] >= distance_cut
            row['highlighted'] = row['meets_age_criterion'] and row['meets_access_criterion']
        joined.sort(key=lambda row: (not row['highlighted'], -row[metric], -row['nearest_distance_m'], row['municipality_name']))
        used_demo = [by_code[row['municipality_code']] for row in joined]
        sources = self._sources(used_demo) + access['sources']
        deduped = {str(item.get('source_id', item)): item for item in sources}
        result = ResultEnvelope(question=f'Coincidencia de envejecimiento >= {age} y peor acceso a {service_category}', filters={'age_group': age, 'service_category': service_category, 'threshold_km': threshold_km, 'period': selected, 'quantile_threshold': quantile_threshold}, period=selected, metric=f'{metric} + distance_geométrica_aproximada', unit='% y m', rows_used=len(joined), data=joined, method=f'Cruce por código municipal. Se destacan valores >= cuantil {quantile_threshold:.2f} en ambas métricas (cortes: {age_cut:.4f}% y {distance_cut:.1f} m). Se muestran ambos componentes y no se usa una puntuación compuesta.', sources=list(deduped.values()), warnings=list(dict.fromkeys(self.repo.warnings + access['warnings'])), limitations=access['limitations'] + ['La coincidencia estadística no demuestra causalidad ni identifica necesidades individuales.', 'Los resultados dependen del cuantil, grupo de edad, categoría y periodo elegidos.']).to_dict()
        result['summary'] = {'age_cut_percent': round(age_cut, 4), 'distance_cut_m': round(distance_cut, 1), 'joined_rows': len(joined), 'highlighted_count': sum((row['highlighted'] for row in joined))}
        return result

    def escenario(self, action: str, service_category: str, threshold_km: float=1.0, period: str | None=None, latitude: float | None=None, longitude: float | None=None, service_id: str | None=None, new_threshold_km: float | None=None) -> dict[str, Any]:
        action = normalize_scenario_action(action)
        service_category = self._service_category(service_category)
        threshold_km = self._threshold(threshold_km)
        services = list(self.repo.services())
        changed: dict[str, Any]
        scenario_services = list(services)
        scenario_threshold = threshold_km
        if action == 'add_service':
            try:
                latitude = float(latitude) if latitude is not None else None
                longitude = float(longitude) if longitude is not None else None
            except (TypeError, ValueError) as exc:
                raise DataContractError('invalid_coordinates', 'add_service requiere latitud y longitud numéricas y válidas.') from exc
            if latitude is None or longitude is None or (not math.isfinite(latitude)) or (not math.isfinite(longitude)) or (not -90 <= latitude <= 90) or (not -180 <= longitude <= 180):
                raise DataContractError('invalid_coordinates', 'add_service requiere latitud y longitud válidas.')
            hypothetical_id = service_id or 'HYPOTHETICAL_SERVICE'
            easting_m, northing_m = wgs84_to_utm30(float(latitude), float(longitude))
            scenario_services.append({'service_id': hypothetical_id, 'service_name': 'Servicio hipotético', 'service_category': service_category, 'latitude': float(latitude), 'longitude': float(longitude), 'easting_m': easting_m, 'northing_m': northing_m, 'reference_period': 'escenario', 'source_id': 'SCENARIO_INPUT'})
            changed = {'action': action, 'service_id': hypothetical_id, 'latitude': latitude, 'longitude': longitude}
        elif action == 'remove_service':
            if not service_id:
                raise DataContractError('service_id_required', 'remove_service requiere service_id.')
            if not any((row['service_id'] == service_id for row in scenario_services)):
                raise DataContractError('service_not_found', f'No existe el servicio {service_id}.', [row['service_id'] for row in services])
            scenario_services = [row for row in scenario_services if row['service_id'] != service_id]
            changed = {'action': action, 'service_id': service_id}
        elif action == 'change_threshold':
            if new_threshold_km is None:
                raise DataContractError('threshold_required', 'change_threshold requiere new_threshold_km.')
            scenario_threshold = self._threshold(new_threshold_km)
            changed = {'action': action, 'threshold_km': threshold_km, 'new_threshold_km': scenario_threshold}
        else:
            raise DataContractError('invalid_scenario', 'Escenario no compatible.', ['add_service', 'remove_service', 'change_threshold'])
        baseline = self.acceso(service_category, threshold_km, period, service_override=services)
        scenario = self.acceso(service_category, scenario_threshold, period, service_override=scenario_services)
        baseline_by_code = {row['municipality_code']: row for row in baseline['data']}
        differences = []
        for item in scenario['data']:
            original = baseline_by_code[item['municipality_code']]
            before, after = (original['nearest_distance_m'], item['nearest_distance_m'])
            absolute = after - before
            differences.append({'municipality_code': item['municipality_code'], 'municipality_name': item['municipality_name'], 'baseline_distance_m': before, 'scenario_distance_m': after, 'difference_absolute_m': round(absolute, 1), 'difference_relative_pct': round(100 * absolute / before, 4) if before else None, 'baseline_within_threshold': original['within_threshold'], 'scenario_within_threshold': item['within_threshold']})
        result = ResultEnvelope(question=f'Escenario {action} para {service_category}', filters={'period': period, 'service_category': service_category}, period=scenario.get('period'), metric='distance_geométrica_aproximada_desde_punto_representativo_municipal', unit='m', rows_used=scenario['rows_used'], data=differences, method='Recalculo determinista del mismo indicador antes y después del cambio hipotético.', sources=baseline['sources'], warnings=list(dict.fromkeys(baseline['warnings'] + scenario['warnings'])), limitations=scenario['limitations'] + ['Es un contrafactual analítico, no una predicción de uso, conducta, coste o impacto social.', 'No constituye una recomendación de ubicación ni una decisión administrativa.']).to_dict()
        result['scenario'] = {'baseline': {'threshold_km': threshold_km, 'service_count': len(services)}, 'scenario': {'threshold_km': scenario_threshold, 'service_count': len(scenario_services)}, 'changed_parameters': changed, 'affected_metric': 'distance_geométrica_aproximada_desde_punto_representativo_municipal / within_threshold', 'assumptions': ['El resto de datos permanece constante.', 'Las coordenadas representan puntos válidos.'], 'limitations': result['limitations']}
        return result

    def fuente(self, source_id: str | None=None) -> dict[str, Any]:
        all_sources = self.repo.metadata().get('sources', [])
        if source_id:
            matches = [item for item in all_sources if str(item.get('source_id')) == str(source_id)]
            if not matches:
                available = [str(item.get('source_id')) for item in all_sources]
                raise DataContractError('source_not_found', f'No hay metadatos para {source_id}.', available)
            data = matches
        else:
            data = all_sources
        warnings = list(dict.fromkeys(self.repo.warnings))
        if not data:
            warnings.append('No hay metadatos de fuente disponibles; no se debe inventar procedencia.')
        return ResultEnvelope(question='Consulta de procedencia', filters={'source_id': source_id}, metric='source_metadata', unit='no aplica', rows_used=len(data), data=data, method='Lectura directa de metadata_sources.json.', sources=data, warnings=warnings, limitations=['La ficha de fuente describe procedencia; no valida por sí sola la calidad del dato.']).to_dict()

@lru_cache(maxsize=8)
def _analysis_for_data_dir(data_dir: str) -> TerritorialAnalysis:
    """Una instancia inmutable por ruta evita releer CSV en cada llamada del mismo proceso."""
    return TerritorialAnalysis(DataRepository(Path(data_dir)))

def _analysis() -> TerritorialAnalysis:
    return _analysis_for_data_dir(str(_default_data_dir().resolve()))

def clear_analysis_cache() -> None:
    """Gancho explícito para tests o recargas controladas de datasets."""
    _analysis_for_data_dir.cache_clear()

def obtener_resumen_territorial(municipio: str, periodo: str | None=None, detalle: bool=False) -> str:
    """Resume demografía y servicios de un municipio; no interpreta ausencia como cero."""
    return _safe(lambda: _analysis().resumen(municipio, periodo), result_kind='summary', detail=detalle)

def comparar_municipios(municipios: list[str], grupo_edad: str='65', categoria_servicio: str | None=None, umbral_km: float=1.0, periodo: str | None=None, detalle: bool=False) -> str:
    """Compara 2-20 municipios con porcentaje de edad y, opcionalmente, distancia a servicios."""
    return _safe(lambda: _analysis().comparar(municipios, grupo_edad, categoria_servicio, umbral_km, periodo), result_kind='comparison', detail=detalle)

def analizar_envejecimiento(grupo_edad: str='65', medida: str='percentage', periodo: str | None=None, top_n: int=10, detalle: bool=False) -> str:
    """Calcula ranking de población >=65 o >=75 por porcentaje o recuento."""
    return _safe(lambda: _analysis().envejecimiento(grupo_edad, medida, periodo, top_n), result_kind='aging', detail=detalle)

def analizar_acceso_servicios(categoria_servicio: str, umbral_km: float=1.0, periodo: str | None=None, municipios: list[str] | None=None, detalle: bool=False) -> str:
    """Calcula distancia euclídea EPSG:25830 desde punto representativo; no acceso real."""
    return _safe(lambda: _analysis().acceso(categoria_servicio, umbral_km, periodo, municipios), result_kind='access', detail=detalle)

def analizar_coincidencia(categoria_servicio: str, grupo_edad: str='65', umbral_km: float=1.0, periodo: str | None=None, cuantil: float=0.75, detalle: bool=False) -> str:
    """Cruza envejecimiento y distancia mostrando ambos componentes y criterios de corte."""
    return _safe(lambda: _analysis().coincidencia(categoria_servicio, grupo_edad, umbral_km, periodo, cuantil), result_kind='coincidence', detail=detalle)

def simular_escenario(accion: str, categoria_servicio: str, umbral_km: float=1.0, periodo: str | None=None, latitud: float | None=None, longitud: float | None=None, service_id: str | None=None, nuevo_umbral_km: float | None=None, detalle: bool=False) -> str:
    """Recalcula un contrafactual: add_service, remove_service o change_threshold."""
    return _safe(lambda: _analysis().escenario(accion, categoria_servicio, umbral_km, periodo, latitud, longitud, service_id, nuevo_umbral_km), result_kind='scenario', detail=detalle)

def consultar_fuente(source_id: str | None=None, detalle: bool=False) -> str:
    """Devuelve procedencia, periodo, institución, unidad, licencia y limitaciones disponibles."""
    return _safe(lambda: _analysis().fuente(source_id), result_kind='source', detail=detalle)
from types import SimpleNamespace
territorial = SimpleNamespace(DataRepository=DataRepository, TerritorialAnalysis=TerritorialAnalysis, _safe=_safe, normalize_service_category=normalize_service_category, normalize_age_group=normalize_age_group, normalize_scenario_action=normalize_scenario_action, obtener_resumen_territorial=obtener_resumen_territorial, comparar_municipios=comparar_municipios, analizar_envejecimiento=analizar_envejecimiento, analizar_acceso_servicios=analizar_acceso_servicios, analizar_coincidencia=analizar_coincidencia, simular_escenario=simular_escenario, consultar_fuente=consultar_fuente)
import hashlib
import inspect
import json
import math
import os
import zipfile
from functools import wraps
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4
VERSION = '1.1.0'
_DEFAULT_WORKSPACE_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parent.parent.name == 'agentes' else Path(__file__).resolve().parent
_BUNDLED_VALIDATION_INDEX: dict[str, Any] = {}
CAPABILITY_VERSION = '1.1.0'
MAX_EVIDENCE_BYTES = 500000
MAX_PUBLIC_BYTES = 120000
DEFAULT_PUBLIC_ENTITIES = 10
SHA256_KEYS = {'data_sha256', 'code_sha256', 'contract_sha256', 'arguments_sha256', 'raw_result_sha256'}
EVIDENCE_KEYS = {'schema_version', 'request_id', 'capability_id', 'normalized_input', 'effective_request', 'execution', 'status', 'outcomes', 'claims', 'method', 'assumptions', 'limitations', 'error', 'versions', 'raw_result_json', 'raw_result_sha256'}
CAPABILITY_KEYS = {'schema_version', 'id', 'description', 'derivation', 'enabled', 'validation_status', 'handler', 'input_fields', 'required_data', 'coverage', 'source_ids', 'allowed_transformations', 'preconditions', 'precondition_checks', 'validation_evidence', 'restrictions', 'semantic_limits'}
RESULT_KEYS = {'status', 'question', 'filters', 'period', 'metric', 'unit', 'rows_used', 'data', 'method', 'sources', 'warnings', 'limitations', 'summary', 'scenario', 'detail_level'}
TERRITORIAL_HANDLERS = {'obtener_resumen_territorial', 'comparar_municipios', 'analizar_envejecimiento', 'analizar_acceso_servicios', 'analizar_coincidencia', 'simular_escenario', 'consultar_fuente'}
LOCAL_HANDLERS = {'consultar_capacidades'}
MOBILITY_HANDLERS = {'plan_visit'}

class ContractViolation(ValueError):
    pass

class ObservedTransportError(RuntimeError):
    """Only an explicitly observed transport failure may use this origin."""

def _reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractViolation(f'duplicate_key:{key}')
        result[key] = value
    return result

def _reject_constant(value: str) -> Any:
    raise ContractViolation(f'non_finite:{value}')

def strict_loads(raw: str) -> Any:
    value = json.loads(raw, object_pairs_hook=_reject_duplicate, parse_constant=_reject_constant)
    _finite(value)
    return value

def _finite(value: Any) -> None:
    if isinstance(value, float) and (not math.isfinite(value)):
        raise ContractViolation('non_finite')
    if isinstance(value, dict):
        for child in value.values():
            _finite(child)
    elif isinstance(value, list):
        for child in value:
            _finite(child)

def canonical(value: Any) -> str:
    _finite(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def digest(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode('utf-8')
    return hashlib.sha256(value).hexdigest()

def _keys(value: Any, required: set[str], where: str, *, optional: set[str] | None=None) -> dict[str, Any]:
    if type(value) is not dict:
        raise ContractViolation(f'{where}:expected_object')
    missing = required - set(value)
    unexpected = set(value) - required - (optional or set())
    if missing or unexpected:
        raise ContractViolation(f'{where}:missing={sorted(missing)}:unexpected={sorted(unexpected)}')
    return value

def _text(value: Any, where: str, *, nullable: bool=False) -> None:
    if nullable and value is None:
        return
    if type(value) is not str or not value:
        raise ContractViolation(f'{where}:expected_nonempty_string')

def _strings(value: Any, where: str, *, nonempty: bool=False) -> None:
    if type(value) is not list or (nonempty and (not value)) or any((type(item) is not str or not item for item in value)):
        raise ContractViolation(f'{where}:expected_string_array')

def _hex(value: Any, where: str) -> None:
    if type(value) is not str or len(value) != 64 or any((char not in '0123456789abcdef' for char in value)):
        raise ContractViolation(f'{where}:expected_sha256')

def _workspace_root(root: Path | None=None) -> Path:
    """One declared root, independent of cwd; invalid configuration fails closed."""
    if root is not None:
        candidate = Path(root).resolve()
    elif 'GIPUZKOA360_VNEXT_ROOT' in os.environ:
        configured = os.environ['GIPUZKOA360_VNEXT_ROOT']
        if not configured.strip():
            raise ContractViolation('workspace:invalid_configured_root')
        candidate = Path(configured).resolve()
    else:
        candidate = _DEFAULT_WORKSPACE_ROOT
    required = ('datos_preparados/metadata_sources.json', 'datos_preparados/vnext/capabilities.json', 'contracts/vnext/evidence-v1.1.schema.json')
    if not candidate.is_dir() or any((not (candidate / path).is_file() for path in required)):
        raise ContractViolation('workspace:invalid_data_root')
    return candidate

def _territorial_handler(name: str, root: Path) -> Callable[..., str]:
    """Use the unchanged v4 calculation with an explicitly bound repository."""
    method, kind = {'obtener_resumen_territorial': ('resumen', 'summary'), 'comparar_municipios': ('comparar', 'comparison'), 'analizar_envejecimiento': ('envejecimiento', 'aging'), 'analizar_acceso_servicios': ('acceso', 'access'), 'analizar_coincidencia': ('coincidencia', 'coincidence'), 'simular_escenario': ('escenario', 'scenario'), 'consultar_fuente': ('fuente', 'source')}[name]
    original = getattr(territorial, name)

    @wraps(original)
    def bound_handler(**arguments: Any) -> str:
        bound = inspect.signature(original).bind(**arguments)
        bound.apply_defaults()
        values = [value for key, value in bound.arguments.items() if key != 'detalle']
        analysis = territorial.TerritorialAnalysis(territorial.DataRepository(root / 'datos_preparados'))
        return territorial._safe(lambda: getattr(analysis, method)(*values), result_kind=kind, detail=bound.arguments['detalle'])
    return bound_handler

def _catalog(root: Path) -> dict[str, dict[str, Any]]:
    payload = strict_loads((root / 'datos_preparados/metadata_sources.json').read_text(encoding='utf-8'))
    if type(payload) is not list:
        raise ContractViolation('source_catalog:expected_array')
    extra = root / 'datos_preparados/vnext/mobility_sources.json'
    if extra.is_file():
        additional = strict_loads(extra.read_text(encoding='utf-8'))
        if type(additional) is not list:
            raise ContractViolation('source_catalog:invalid_additional_sources')
        payload += additional
    result = {}
    for item in payload:
        if type(item) is not dict or type(item.get('source_id')) is not str:
            raise ContractViolation('source_catalog:invalid_source')
        if item['source_id'] in result:
            raise ContractViolation('source_catalog:duplicate_source')
        result[item['source_id']] = item
    return result

def _registry(root: Path) -> list[dict[str, Any]]:
    path = root / 'datos_preparados/vnext/capabilities.json'
    payload = strict_loads(path.read_text(encoding='utf-8'))
    _keys(payload, {'schema_version', 'capabilities'}, 'registry')
    if payload['schema_version'] != CAPABILITY_VERSION or type(payload['capabilities']) is not list:
        raise ContractViolation('registry:version_or_type')
    catalog = _catalog(root)
    for item in payload['capabilities']:
        validate_capability(item, root, catalog)
    ids = [item['id'] for item in payload['capabilities']]
    if len(ids) != len(set(ids)):
        raise ContractViolation('registry:duplicate_capability')
    return payload['capabilities']

def validate_capability(item: Any, root: Path, catalog: dict[str, Any]) -> None:
    _keys(item, CAPABILITY_KEYS, 'capability')
    if item['schema_version'] != CAPABILITY_VERSION:
        raise ContractViolation('capability:version')
    for field in ('id', 'description'):
        _text(item[field], f'capability.{field}')
    if item['derivation'] not in {'direct', 'derived_exact', 'estimated_with_assumptions', 'unavailable'}:
        raise ContractViolation('capability:derivation')
    if type(item['enabled']) is not bool or item['validation_status'] not in {'tested', 'pending', 'failed'}:
        raise ContractViolation('capability:state')
    if item['enabled']:
        if item['validation_status'] != 'tested' or item['derivation'] == 'unavailable':
            raise ContractViolation('capability:unverified_enabled')
        if item['handler'] not in TERRITORIAL_HANDLERS | LOCAL_HANDLERS | MOBILITY_HANDLERS:
            raise ContractViolation('capability:missing_handler')
        if item['handler'] in TERRITORIAL_HANDLERS and (not callable(getattr(territorial, item['handler'], None))):
            raise ContractViolation('capability:missing_handler')
        handler = consultar_capacidades if item['handler'] in LOCAL_HANDLERS else plan_visit if item['handler'] in MOBILITY_HANDLERS else getattr(territorial, item['handler'])
        signature = inspect.signature(handler)
        provided = {field['name'] for field in item['input_fields']}
        expected = set(signature.parameters) - {'detalle', 'root'}
        if provided != expected:
            raise ContractViolation('capability:handler_schema_mismatch')
    elif item['handler'] is not None and type(item['handler']) is not str:
        raise ContractViolation('capability:handler_type')
    if type(item['input_fields']) is not list:
        raise ContractViolation('capability:input_fields')
    names = set()
    for field in item['input_fields']:
        _keys(field, {'name', 'type', 'required', 'allowed_values'}, 'capability.input_field')
        _text(field['name'], 'capability.input_field.name')
        if field['name'] in names or field['type'] not in {'string', 'number', 'integer', 'boolean', 'string_array', 'object_or_array'} or type(field['required']) is not bool or (type(field['allowed_values']) is not list):
            raise ContractViolation('capability:bad_input_field')
        names.add(field['name'])
    if type(item['required_data']) is not list or (item['enabled'] and (not item['required_data'])):
        raise ContractViolation('capability:required_data')
    for data in item['required_data']:
        _keys(data, {'path', 'sha256'}, 'capability.data')
        _text(data['path'], 'capability.data.path')
        _hex(data['sha256'], 'capability.data.sha256')
        path = (root / data['path']).resolve()
        if root not in path.parents or not path.is_file() or digest(path.read_bytes()) != data['sha256']:
            raise ContractViolation(f"capability:stale_data:{data['path']}")
    coverage = _keys(item['coverage'], {'territory', 'periods', 'entities', 'scope'}, 'capability.coverage')
    _text(coverage['territory'], 'capability.coverage.territory')
    _text(coverage['scope'], 'capability.coverage.scope')
    _strings(coverage['periods'], 'capability.coverage.periods')
    if type(coverage['entities']) is not int or coverage['entities'] < 0:
        raise ContractViolation('capability.coverage.entities')
    if item['enabled'] and coverage['territory'] == 'Gipuzkoa':
        municipality_file = root / 'datos_preparados/municipios.csv'
        actual_entities = sum((1 for _ in municipality_file.open(encoding='utf-8-sig'))) - 1
        if coverage['entities'] != actual_entities:
            raise ContractViolation('capability:false_coverage')
    if coverage['territory'] == 'source_catalog' and coverage['entities'] != len(catalog):
        raise ContractViolation('capability:false_catalog_coverage')
    _strings(item['source_ids'], 'capability.source_ids', nonempty=item['enabled'])
    if any((source not in catalog for source in item['source_ids'])):
        raise ContractViolation('capability:false_source')
    expected_periods = list(dict.fromkeys((str(catalog[source]['reference_period']) for source in item['source_ids']))) if item['id'] != 'consultar_capacidades' else []
    if item['enabled'] and coverage['periods'] != expected_periods:
        raise ContractViolation('capability:false_period_coverage')
    _strings(item['precondition_checks'], 'capability.precondition_checks', nonempty=item['enabled'])
    if item['enabled'] and set(item['precondition_checks']) != {'required_data_sha256', 'handler_signature', 'source_catalog', 'coverage_count'}:
        raise ContractViolation('capability:unexecuted_precondition')
    if type(item['validation_evidence']) is not list or (item['enabled'] and (not item['validation_evidence'])):
        raise ContractViolation('capability:validation_evidence')
    for proof in item['validation_evidence']:
        _keys(proof, {'test_file', 'test_name', 'sha256'}, 'capability.validation_evidence')
        _text(proof['test_file'], 'capability.validation_evidence.test_file')
        _text(proof['test_name'], 'capability.validation_evidence.test_name')
        _hex(proof['sha256'], 'capability.validation_evidence.sha256')
        path = (root / proof['test_file']).resolve()
        bundled = _BUNDLED_VALIDATION_INDEX.get(proof['test_file'])
        file_valid = path.is_file() and digest(path.read_bytes()) == proof['sha256'] and (f"def {proof['test_name']}(" in path.read_text(encoding='utf-8'))
        bundled_valid = not path.exists() and type(bundled) is dict and (bundled['sha256'] == proof['sha256']) and (proof['test_name'] in bundled['test_names'])
        if root not in path.parents or not (file_valid or bundled_valid):
            raise ContractViolation('capability:stale_validation_evidence')
    for key in ('allowed_transformations', 'preconditions', 'restrictions', 'semantic_limits'):
        _strings(item[key], f'capability.{key}', nonempty=key == 'semantic_limits')

def _validate_arguments(args: Any, capability: dict[str, Any]) -> dict[str, Any]:
    if type(args) is not dict:
        raise ContractViolation('arguments:expected_object')
    fields = {item['name']: item for item in capability['input_fields']}
    missing = {name for name, item in fields.items() if item['required'] and name not in args}
    unexpected = set(args) - set(fields)
    if missing or unexpected:
        raise ContractViolation(f'arguments:missing={sorted(missing)}:unexpected={sorted(unexpected)}')
    for name, value in args.items():
        field = fields[name]
        if value is None and (not field['required']) and (name in {'periodo', 'categoria_servicio', 'municipios', 'latitud', 'longitud', 'service_id', 'nuevo_umbral_km', 'source_id', 'pregunta_o_dimension'}):
            continue
        kind = field['type']
        valid = {'string': lambda v: type(v) is str and bool(v.strip()), 'number': lambda v: type(v) in (int, float) and math.isfinite(v), 'integer': lambda v: type(v) is int, 'boolean': lambda v: type(v) is bool, 'string_array': lambda v: type(v) is list and bool(v) and all((type(x) is str and bool(x.strip()) for x in v)), 'object_or_array': lambda v: type(v) is dict or (type(v) is list and 2 <= len(v) <= 4 and all((type(x) is dict for x in v)))}[kind](value)
        if not valid or (field['allowed_values'] and value not in field['allowed_values']):
            raise ContractViolation(f'arguments:{name}:invalid_value')
        if name in {'umbral_km', 'nuevo_umbral_km'} and (not 0 < value <= 100):
            raise ContractViolation(f'arguments:{name}:out_of_range:(0,100]')
        if name == 'top_n' and (not 1 <= value <= 100):
            raise ContractViolation('arguments:top_n:out_of_range:[1,100]')
        if name == 'cuantil' and (not 0.5 <= value <= 0.95):
            raise ContractViolation('arguments:cuantil:out_of_range:[0.5,0.95]')
    if capability['id'] in {'analizar_acceso_servicios', 'simular_escenario'}:
        period = args.get('periodo')
        if period is not None and period not in capability['coverage']['periods']:
            raise ContractViolation(f"arguments:periodo:unsupported_period:available={capability['coverage']['periods']}")
    if capability['id'] == 'simular_escenario':
        required, optional = {'add_service': ({'latitud', 'longitud'}, {'service_id'}), 'remove_service': ({'service_id'}, set()), 'change_threshold': ({'nuevo_umbral_km'}, set())}[args['accion']]
        explicit = {name for name in ('latitud', 'longitud', 'service_id', 'nuevo_umbral_km') if args.get(name) is not None}
        missing = required - explicit
        unused = explicit - required - optional
        if missing or unused:
            raise ContractViolation(f'arguments:accion:missing={sorted(missing)}:not_applicable={sorted(unused)}')
    return dict(args)

def _repair_once(args: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Use the core's own equivalent aliases once; never guess a new intent."""
    repaired = dict(args)
    notes = []
    normalizers = {'categoria_servicio': territorial.normalize_service_category, 'grupo_edad': territorial.normalize_age_group, 'accion': territorial.normalize_scenario_action}
    for name, normalizer in normalizers.items():
        original = repaired.get(name)
        if original is None or type(original) is not str:
            continue
        try:
            canonical_value = normalizer(original)
        except ValueError:
            continue
        if canonical_value != original:
            repaired[name] = canonical_value
            notes.append(f'Alias del motor normalizado: {name}={original} → {canonical_value}.')
    if 'medida' in repaired and repaired['medida'] is not None:
        original = repaired['medida']
        try:
            metric, _ = territorial.TerritorialAnalysis._age_fields(repaired.get('grupo_edad', '65'), original)
            canonical_value = 'percentage' if metric.startswith('pct_') else 'count'
        except ValueError:
            canonical_value = original
        if canonical_value != original:
            repaired['medida'] = canonical_value
            notes.append(f'Alias del motor normalizado: medida={original} → {canonical_value}.')
    return (repaired, notes)

def _validate_result(raw: Any, catalog: dict[str, Any]) -> dict[str, Any]:
    if type(raw) is not dict:
        raise ContractViolation('tool_result:expected_object')
    if raw.get('status') == 'error':
        _keys(raw, {'status', 'error_code', 'message', 'available_options'}, 'tool_error')
        _text(raw['error_code'], 'tool_error.code')
        _text(raw['message'], 'tool_error.message')
        _strings(raw['available_options'], 'tool_error.options')
        return raw
    _keys(raw, {'status', 'question', 'filters', 'period', 'metric', 'unit', 'rows_used', 'data', 'method', 'sources', 'warnings', 'limitations'}, 'tool_result', optional=RESULT_KEYS)
    if raw['status'] != 'ok' or type(raw['filters']) is not dict or type(raw['rows_used']) is not int or (raw['rows_used'] < 0) or (type(raw['data']) is not list):
        raise ContractViolation('tool_result:shape')
    for key in ('question', 'method'):
        _text(raw[key], f'tool_result.{key}')
    for key in ('metric', 'unit'):
        _text(raw[key], f'tool_result.{key}', nullable=True)
    _text(raw['period'], 'tool_result.period', nullable=True)
    _strings(raw['warnings'], 'tool_result.warnings')
    _strings(raw['limitations'], 'tool_result.limitations')
    if type(raw['sources']) is not list:
        raise ContractViolation('tool_result:sources')
    for source in raw['sources']:
        if type(source) is not dict or source.get('source_id') not in catalog:
            raise ContractViolation('tool_result:false_source')
    _finite(raw)
    return raw

def _effective_request(handler: Callable[..., Any], arguments: dict[str, Any], root: Path) -> dict[str, Any]:
    """Resolve defaults and municipal identity before accepting tool observations."""
    bound = inspect.signature(handler).bind_partial(**arguments)
    bound.apply_defaults()
    parameters = {key: value for key, value in bound.arguments.items() if key not in {'detalle', 'root'}}
    operation = handler.__name__
    codes: list[str] = []
    labels: list[str] = []
    if 'municipio' in parameters or parameters.get('municipios') is not None:
        repo = territorial.DataRepository(root / 'datos_preparados')
        names = [parameters['municipio']] if 'municipio' in parameters else parameters['municipios']
        resolved = [repo.municipality_lookup(name) for name in names]
        codes = [item['municipality_code'] for item in resolved]
        labels = [item['municipality_name'] for item in resolved]
        if len(codes) != len(set(codes)):
            raise ContractViolation('request:duplicate_municipality')
    period = parameters.get('periodo')
    if operation in {'obtener_resumen_territorial', 'comparar_municipios', 'analizar_envejecimiento', 'analizar_coincidencia'}:
        try:
            period = territorial.DataRepository(root / 'datos_preparados').choose_period(period)
        except ValueError as exc:
            if getattr(exc, 'code', None) not in {'period_not_found', 'period_required'}:
                raise
            raise ContractViolation(f'arguments:periodo:{exc.code}:available={exc.available_options}') from exc
    return {'operation': operation, 'municipality_codes': codes, 'municipality_labels': labels, 'effective_period': period, 'parameters': parameters, 'defaults_applied': sorted(set(parameters) - set(arguments)), 'snapshot_id': None, 'contracts': {'evidence': VERSION, 'capability': CAPABILITY_VERSION}}

def _same(observed: Any, expected: Any, field: str) -> None:
    if type(observed) in (int, float) and type(expected) in (int, float):
        match = float(observed) == float(expected)
    else:
        match = observed == expected
    if not match:
        raise ContractViolation(f'tool_result:request_mismatch:{field}')

def _bind_result_to_arguments(raw: dict[str, Any], effective: dict[str, Any], root: Path) -> None:
    """Every effective parameter must be witnessed, including defaults and entities."""
    if raw['status'] != 'ok':
        return
    operation, args, filters = (effective['operation'], effective['parameters'], raw['filters'])
    mapping = {'grupo_edad': 'age_group', 'categoria_servicio': 'service_category', 'umbral_km': 'threshold_km', 'cuantil': 'quantile_threshold', 'top_n': 'top_n', 'medida': 'measure', 'source_id': 'source_id', 'pregunta_o_dimension': 'pregunta_o_dimension'}
    for argument, filter_name in mapping.items():
        if argument not in args or (operation == 'simular_escenario' and argument == 'umbral_km'):
            continue
        if filter_name not in filters:
            raise ContractViolation(f'tool_result:missing_filter:{filter_name}')
        expected = None if operation == 'comparar_municipios' and argument == 'umbral_km' and (args['categoria_servicio'] is None) else args[argument]
        _same(filters[filter_name], expected, argument)
    if operation in {'obtener_resumen_territorial', 'analizar_envejecimiento', 'analizar_coincidencia'}:
        if 'period' not in filters:
            raise ContractViolation('tool_result:missing_filter:period')
        _same(filters['period'], effective['effective_period'], 'periodo')
        _same(raw['period'], effective['effective_period'], 'result_period')
    elif operation == 'analizar_acceso_servicios':
        if 'period_requested' not in filters:
            raise ContractViolation('tool_result:missing_filter:period_requested')
        _same(filters['period_requested'], args['periodo'], 'periodo')
    elif operation == 'simular_escenario':
        if 'period' not in filters:
            raise ContractViolation('tool_result:missing_filter:period')
        _same(filters['period'], args['periodo'], 'periodo')
    elif operation == 'comparar_municipios':
        _same(raw['period'], effective['effective_period'], 'result_period')
    expected_codes = set(effective['municipality_codes'])
    if operation == 'obtener_resumen_territorial':
        if 'municipality_code' not in filters:
            raise ContractViolation('tool_result:missing_filter:municipality_code')
        _same(filters['municipality_code'], effective['municipality_codes'][0], 'municipio')
    if operation == 'comparar_municipios':
        if 'municipalities' not in filters or type(filters['municipalities']) is not list:
            raise ContractViolation('tool_result:missing_filter:municipalities')
        repo = territorial.DataRepository(root / 'datos_preparados')
        observed_codes = [repo.municipality_lookup(name)['municipality_code'] for name in filters['municipalities']]
        if len(observed_codes) != len(expected_codes) or set(observed_codes) != expected_codes:
            raise ContractViolation('tool_result:request_mismatch:municipios')
    if operation == 'analizar_acceso_servicios' and (not expected_codes):
        expected_codes = {row['municipality_code'] for row in territorial.DataRepository(root / 'datos_preparados').municipalities()}
    if operation in {'obtener_resumen_territorial', 'comparar_municipios', 'analizar_acceso_servicios'}:
        observed_rows = raw['data']
        observed_codes = [item.get('municipality_code') for item in observed_rows if type(item) is dict]
        if len(observed_rows) != len(expected_codes) or len(observed_codes) != len(expected_codes) or set(observed_codes) != expected_codes:
            raise ContractViolation('tool_result:request_mismatch:municipality_rows')
        repo = territorial.DataRepository(root / 'datos_preparados')
        if any((item.get('municipality_name') != repo.municipality_lookup(item['municipality_code'])['municipality_name'] for item in observed_rows)):
            raise ContractViolation('tool_result:request_mismatch:municipality_labels')
    if operation == 'simular_escenario':
        scenario = raw.get('scenario')
        if type(scenario) is not dict or type(scenario.get('changed_parameters')) is not dict:
            raise ContractViolation('tool_result:missing_scenario')
        changed = scenario['changed_parameters']
        action = args['accion']
        expected = {'action': action}
        if action == 'add_service':
            expected.update(service_id=args['service_id'] or 'HYPOTHETICAL_SERVICE', latitude=float(args['latitud']), longitude=float(args['longitud']))
        elif action == 'remove_service':
            expected['service_id'] = args['service_id']
        elif action == 'change_threshold':
            expected.update(threshold_km=float(args['umbral_km']), new_threshold_km=float(args['nuevo_umbral_km']))
        if set(changed) != set(expected):
            raise ContractViolation('tool_result:request_mismatch:scenario_fields')
        for key, value in expected.items():
            _same(changed[key], value, key)
        _same(scenario['baseline']['threshold_km'], args['umbral_km'], 'baseline_threshold')
        _same(scenario['scenario']['threshold_km'], args['nuevo_umbral_km'] if action == 'change_threshold' else args['umbral_km'], 'scenario_threshold')

def _pointer(raw: Any, pointer: str) -> Any:
    current = raw
    for part in pointer.lstrip('/').split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        current = current[int(part)] if type(current) is list else current[part]
    return current

def _claim_sources(field: str, available: set[str]) -> list[str]:
    demo = 'EUSTAT_EMH_2025'
    service = 'ODE_HEALTH_CENTRES_2026'
    geo = 'GEOEUSKADI_MUNICIPIOS_2025'
    if 'per_10000' in field:
        wanted = [demo, service]
    elif field.startswith(('population', 'pct_', 'age_')) or field in {'value', 'age_cut_percent'}:
        wanted = [demo]
    elif field.startswith(('distance', 'nearest_distance', 'baseline_distance', 'scenario_distance')) or field.endswith('_m'):
        wanted = [service, geo]
    elif field.startswith(('service', 'registered_service')):
        wanted = [service]
    else:
        wanted = sorted(available)
    return wanted if set(wanted) <= available else []

def _claim_period(field: str, source_ids: list[str], catalog: dict[str, Any]) -> str:
    periods = [str(catalog[source]['reference_period']) for source in source_ids]
    return ';'.join(dict.fromkeys(periods))

def _claim_unit(field: str, raw: dict[str, Any]) -> str:
    if field.endswith('_s'):
        return 's'
    if field in {'highlighted_count', 'joined_rows'}:
        return 'municipios'
    if 'per_10000' in field:
        return 'registros/10000 personas'
    if field.startswith('pct_') or field.endswith('_percent'):
        return '%'
    if field.endswith('_m') or 'distance' in field:
        return 'm'
    if field.startswith('population'):
        return 'personas'
    if field.endswith('_count') or field.startswith('services_'):
        return 'registros'
    if field == 'value':
        return str(raw.get('unit') or 'unidad declarada')
    return 'conteo'

def _source_roles(field: str, sources: list[str]) -> list[dict[str, str]]:
    roles = {'EUSTAT_EMH_2025': 'denominator' if 'per_10000' in field else 'demographic_observation', 'ODE_HEALTH_CENTRES_2026': 'numerator' if 'per_10000' in field else 'service_location', 'GEOEUSKADI_MUNICIPIOS_2025': 'municipal_reference_point', 'GTFS': 'official_schedule', 'HEALTH_REGISTRY': 'official_health_registry', 'HEALTH_PAGE': 'official_health_page', 'PADI_2026': 'official_health_page', 'OSM': 'open_network', 'MODEL': 'model_parameter', 'USER': 'agent_or_user_parameter', 'MODEL_DEFAULTS': 'model_parameter', 'DERIVED': 'derived_metric'}

    def role(source: str) -> str:
        for prefix, label in (('W1_GTFS@', 'official_schedule'), ('W2_USER@', 'user_parameter'), ('W1_MODEL@', 'modelling_assumption'), ('W1_DERIVED@', 'derived_network')):
            if source.startswith(prefix):
                return label
        return roles.get(source, 'observed_input')
    return [{'source_id': source, 'role': role(source)} for source in sources]

def _claim_entity(raw: dict[str, Any], pointer: str) -> tuple[str, str, str]:
    if raw.get('schema_version') in {'0.2.0', '0.3.1'}:
        if pointer.startswith('/differences_s/'):
            part = raw['differences_s'][int(pointer.split('/')[2])]
            left, right = (part['left_index'], part['right_index'])
            return ('comparison', f'{left}->{right}', f'Comparación de escenarios {left} y {right}')
        if pointer.startswith('/comparisons/'):
            part = raw['comparisons'][int(pointer.split('/')[2])]
            left, right = (part['left_index'], part['right_index'])
            return ('comparison', f'{left}->{right}', f'Comparación de escenarios {left} y {right}')
        result = raw['results'][int(pointer.split('/')[2])] if pointer.startswith('/results/') else raw
        request = result.get('normalized_request') or {}
        index_label = f"#{pointer.split('/')[2]}" if pointer.startswith('/results/') else ''
        identity = f"{request.get('origin_id', '?')}->{request.get('destination_id', '?')}@{request.get('date', '?')}T{request.get('appointment_time', '?')}{index_label}"
        return ('journey', identity, f'Viaje programado {identity}')
    if pointer.startswith('/summary/'):
        return ('municipality_set', 'GIPUZKOA_FILTERED', 'Municipios incluidos en el cruce')
    if pointer.startswith('/data/'):
        index = int(pointer.split('/')[2])
        row = raw['data'][index]
        if type(row) is dict and type(row.get('municipality_code')) is str and (type(row.get('municipality_name')) is str):
            return ('municipality', row['municipality_code'], row['municipality_name'])
    return ('result', 'RESULT_SCOPE', raw.get('question', 'Resultado sintético'))

def _make_claims(raw: dict[str, Any], catalog: dict[str, Any], root: Path) -> tuple[list[dict[str, Any]], int]:
    available = {item['source_id'] for item in raw['sources']}
    selected: list[tuple[str, str, Any]] = []
    summary = raw.get('summary')
    if type(summary) is dict:
        for key, value in summary.items():
            if type(value) in (int, float) and math.isfinite(value):
                selected.append((f'/summary/{key}', key, value))
    for index, row in enumerate(raw.get('data', [])):
        if type(row) is not dict:
            raise ContractViolation('tool_result:data_row')
        if 'highlighted' in row and (not row['highlighted']):
            continue
        for key, value in row.items():
            if key in {'rank', 'age_percentile_rank', 'distance_percentile_rank'}:
                continue
            if type(value) in (int, float) and math.isfinite(value):
                selected.append((f'/data/{index}/{key}', key, value))
            elif type(value) is dict and key == 'service_indicators':
                for category, indicators in value.items():
                    if type(indicators) is dict:
                        for metric, number in indicators.items():
                            if type(number) in (int, float) and math.isfinite(number):
                                selected.append((f'/data/{index}/service_indicators/{category}/{metric}', metric, number))
    claims = []
    unattributed = 0
    demographic_rows = {(row['municipality_code'], row['reference_period']): row for row in territorial.DataRepository(root / 'datos_preparados').demography()}
    demographic_sha = digest((root / 'datos_preparados/demografia.csv').read_bytes())
    for pointer, field, value in selected:
        sources = _claim_sources(field, available)
        if not sources:
            unattributed += 1
            continue
        denominator = None
        numerator = None
        if 'per_10000' in field:
            age = '75' if '75' in field else '65' if '65' in field else None
            if age is None:
                continue
            index = int(pointer.split('/')[2]) if pointer.startswith('/data/') else None
            row = raw['data'][index] if index is not None else {}
            population = row.get(f'population_{age}_plus') if type(row) is dict else None
            parts = pointer.split('/')
            category = parts[4] if len(parts) > 5 and parts[3] == 'service_indicators' else None
            count = row.get('service_indicators', {}).get(category, {}).get('registered_service_count') if category else None
            if type(population) not in (int, float) or population <= 0 or type(count) is not int or (abs(value - round(count / population * 10000, 3)) > 0.0005):
                unattributed += 1
                continue
            denominator = {'value': population, 'unit': 'personas', 'period': str(catalog['EUSTAT_EMH_2025']['reference_period']), 'source_id': 'EUSTAT_EMH_2025', 'evidence_path': f'/data/{index}/population_{age}_plus', 'data_ref': None}
            numerator = {'value': count, 'unit': 'registros', 'period': str(catalog['ODE_HEALTH_CENTRES_2026']['reference_period']), 'source_id': 'ODE_HEALTH_CENTRES_2026', 'evidence_path': f'/data/{index}/service_indicators/{category}/registered_service_count', 'data_ref': None}
        is_percentage = field.startswith('pct_') or (field == 'value' and str(raw.get('unit', '')).startswith('%'))
        if is_percentage:
            age = '75' if '75' in field else '65' if '65' in field else raw.get('filters', {}).get('age_group')
            index = int(pointer.split('/')[2]) if pointer.startswith('/data/') else None
            row = raw['data'][index] if index is not None else None
            code = row.get('municipality_code') if type(row) is dict else None
            period = str(catalog['EUSTAT_EMH_2025']['reference_period'])
            source_row = demographic_rows.get((code, period))
            age_count = source_row.get(f'population_{age}_plus') if source_row else None
            total = source_row.get('population_total') if source_row else None
            if age not in {'65', '75'} or type(age_count) not in (int, float) or type(total) not in (int, float) or (total <= 0) or (abs(value - round(age_count / total * 100, 3)) > 0.0005):
                unattributed += 1
                continue

            def data_ref(metric: str) -> dict[str, Any]:
                return {'path': 'datos_preparados/demografia.csv', 'sha256': demographic_sha, 'municipality_code': code, 'reference_period': period, 'field': metric}
            numerator = {'value': age_count, 'unit': 'personas', 'period': period, 'source_id': 'EUSTAT_EMH_2025', 'evidence_path': None, 'data_ref': data_ref(f'population_{age}_plus')}
            denominator = {'value': total, 'unit': 'personas', 'period': period, 'source_id': 'EUSTAT_EMH_2025', 'evidence_path': None, 'data_ref': data_ref('population_total')}
        entity_type, entity_id, entity_label = _claim_entity(raw, pointer)
        claims.append({'id': f'claim-{len(claims) + 1}', 'label': field, 'value': value, 'unit': _claim_unit(field, raw), 'period': _claim_period(field, sources, catalog), 'numerator': numerator, 'denominator': denominator, 'source_ids': sources, 'evidence_path': pointer, 'entity_type': entity_type, 'entity_id': entity_id, 'entity_label': entity_label, 'metric_id': field, 'reference_periods': [{'source_id': source, 'period': str(catalog[source]['reference_period'])} for source in sources], 'source_refs': _source_roles(field, sources), 'derivation': 'derived_exact' if numerator is not None or field in {'highlighted_count', 'joined_rows', 'age_cut_percent', 'distance_cut_m'} else 'direct', 'assumptions': ['75+ derivado del año de nacimiento en la fuente demográfica.'] if is_percentage and age == '75' else []})
    return (claims, unattributed)

def validate_evidence(evidence: Any, catalog: dict[str, Any], root: Path | None=None) -> None:
    root = _workspace_root(root)
    _keys(evidence, EVIDENCE_KEYS, 'evidence')
    if evidence['schema_version'] != VERSION or evidence['status'] not in {'valid', 'no_data', 'unsupported', 'error'}:
        raise ContractViolation('evidence:version_or_status')
    for key in ('request_id', 'capability_id'):
        _text(evidence[key], f'evidence.{key}')
    inp = _keys(evidence['normalized_input'], {'tool', 'arguments'}, 'evidence.input')
    execution = _keys(evidence['execution'], {'request_id', 'tool', 'arguments_sha256', 'snapshot_id', 'state'}, 'evidence.execution')
    if type(inp['arguments']) is not dict or execution['request_id'] != evidence['request_id'] or execution['tool'] != inp['tool'] or (evidence['capability_id'] != inp['tool']):
        raise ContractViolation('evidence:request_binding')
    _hex(execution['arguments_sha256'], 'evidence.execution.arguments_sha256')
    if execution['arguments_sha256'] != digest(canonical(inp['arguments'])):
        raise ContractViolation('evidence:arguments_hash')
    if execution['snapshot_id'] is not None:
        _text(execution['snapshot_id'], 'evidence.execution.snapshot_id')
    if execution['state'] not in {'not_started', 'completed', 'failed'}:
        raise ContractViolation('evidence:execution_state')
    if type(evidence['outcomes']) is not list:
        raise ContractViolation('evidence:outcomes')
    for outcome in evidence['outcomes']:
        _keys(outcome, {'index', 'status', 'error'}, 'evidence.outcome')
        if type(outcome['index']) is not int or outcome['index'] < 0 or outcome['status'] not in {'ok', 'no_feasible_journey', 'unsupported', 'unknown', 'error'} or (outcome['error'] is not None and type(outcome['error']) is not dict):
            raise ContractViolation('evidence:outcome_shape')
    effective = evidence['effective_request']
    if effective is not None:
        _keys(effective, {'operation', 'municipality_codes', 'municipality_labels', 'effective_period', 'parameters', 'defaults_applied', 'snapshot_id', 'contracts'}, 'evidence.effective_request')
        if effective['operation'] != inp['tool'] or effective['snapshot_id'] != execution['snapshot_id'] or type(effective['parameters']) is not dict or (type(effective['municipality_codes']) is not list) or (type(effective['municipality_labels']) is not list) or (len(effective['municipality_codes']) != len(effective['municipality_labels'])):
            raise ContractViolation('evidence:effective_request_binding')
        for key, value in inp['arguments'].items():
            observed = effective['parameters'].get(key)
            clock_equivalent = evidence['capability_id'] == 'plan_visit' and key in {'appointment_time', 'return_deadline'} and (type(value) is str) and (len(value) == 5) and (observed == value + ':00')
            if key not in effective['parameters'] or (observed != value and (not clock_equivalent)):
                raise ContractViolation('evidence:effective_parameter_mismatch')
        if effective['defaults_applied'] != sorted(set(effective['parameters']) - set(inp['arguments'])):
            raise ContractViolation('evidence:effective_defaults')
        _keys(effective['contracts'], {'evidence', 'capability'}, 'evidence.effective_contracts', optional={'mobility'})
    elif evidence['status'] == 'valid':
        raise ContractViolation('evidence:missing_effective_request')
    versions = _keys(evidence['versions'], {'data_sha256', 'code_sha256', 'contract_sha256'}, 'evidence.versions')
    for key, value in versions.items():
        _hex(value, f'evidence.versions.{key}')
    for key in ('assumptions', 'limitations'):
        _strings(evidence[key], f'evidence.{key}')
    if type(evidence['method']) is not str or type(evidence['claims']) is not list:
        raise ContractViolation('evidence:method_or_claims')
    raw_json = evidence['raw_result_json']
    raw = None
    if raw_json is not None:
        if type(raw_json) is not str:
            raise ContractViolation('evidence:raw_type')
        _hex(evidence['raw_result_sha256'], 'evidence.raw_result_sha256')
        if digest(raw_json) != evidence['raw_result_sha256']:
            raise ContractViolation('evidence:raw_hash')
        raw = strict_loads(raw_json)
    elif evidence['raw_result_sha256'] is not None:
        raise ContractViolation('evidence:raw_hash_without_result')
    if evidence['status'] == 'valid':
        if raw is None or evidence['error'] is not None:
            raise ContractViolation('evidence:valid_without_result')
    else:
        if evidence['claims'] or type(evidence['error']) is not dict:
            raise ContractViolation('evidence:error_with_claims')
        error = _keys(evidence['error'], {'origin', 'code', 'message', 'available_options', 'safe_next_action'}, 'evidence.error')
        if error['origin'] not in {'domain', 'data', 'execution', 'transport', 'unknown'}:
            raise ContractViolation('evidence:error_origin')
        for key in ('code', 'message', 'safe_next_action'):
            _text(error[key], f'evidence.error.{key}')
        _strings(error['available_options'], 'evidence.error.available_options')
    for claim in evidence['claims']:
        item = _keys(claim, {'id', 'label', 'value', 'unit', 'period', 'numerator', 'denominator', 'source_ids', 'evidence_path', 'entity_type', 'entity_id', 'entity_label', 'metric_id', 'reference_periods', 'source_refs', 'derivation', 'assumptions'}, 'claim')
        for key in ('id', 'label', 'unit', 'period', 'evidence_path', 'entity_type', 'entity_id', 'entity_label', 'metric_id'):
            _text(item[key], f'claim.{key}')
        if item['entity_type'] not in {'municipality', 'municipality_set', 'result', 'journey', 'comparison'} or item['derivation'] not in {'direct', 'derived_exact', 'estimated_with_assumptions'}:
            raise ContractViolation('claim:semantics')
        _strings(item['assumptions'], 'claim.assumptions')
        if not item['evidence_path'].startswith('/') or raw is None or type(item['value']) not in (int, float, str, bool, type(None)):
            raise ContractViolation('claim:shape')
        if type(item['value']) is float and (not math.isfinite(item['value'])):
            raise ContractViolation('claim:non_finite')
        try:
            observed = _pointer(raw, item['evidence_path'])
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ContractViolation('claim:bad_pointer') from exc
        if type(observed) is not type(item['value']) or observed != item['value']:
            raise ContractViolation('claim:unobserved_value')
        _strings(item['source_ids'], 'claim.source_ids', nonempty=True)
        if any((source not in catalog for source in item['source_ids'])):
            raise ContractViolation('claim:false_source')
        if evidence['capability_id'] != 'plan_visit' and type(raw) is dict and (type(raw.get('sources')) is list):
            used_sources = {source.get('source_id') for source in raw['sources'] if type(source) is dict}
            if not set(item['source_ids']) <= used_sources:
                raise ContractViolation('claim:unused_source')
        if type(item['reference_periods']) is not list or type(item['source_refs']) is not list:
            raise ContractViolation('claim:source_roles')
        expected_periods = [{'source_id': source, 'period': str(catalog[source].get('reference_period'))} for source in item['source_ids']]
        if item['reference_periods'] != expected_periods or {entry.get('source_id') for entry in item['source_refs'] if type(entry) is dict} != set(item['source_ids']):
            raise ContractViolation('claim:source_roles')
        for entry in item['source_refs']:
            _keys(entry, {'source_id', 'role'}, 'claim.source_ref')
            _text(entry['role'], 'claim.source_ref.role')
        if item['source_refs'] != _source_roles(item['metric_id'], item['source_ids']):
            raise ContractViolation('claim:source_role_mismatch')
        for source in item['source_ids']:
            source_period = catalog[source].get('reference_period')
            if type(source_period) is not str or source_period not in item['period']:
                raise ContractViolation('claim:period_mismatch')
        field_name = item['evidence_path'].split('/')[-1]
        if item['metric_id'] != field_name:
            raise ContractViolation('claim:metric_mismatch')
        entity_type, entity_id, entity_label = _claim_entity(raw, item['evidence_path'])
        if (item['entity_type'], item['entity_id'], item['entity_label']) != (entity_type, entity_id, entity_label):
            raise ContractViolation('claim:entity_mismatch')
        if (field_name.endswith(('_m', '_s')) or 'distance' in field_name or field_name.startswith('pct_') or field_name.endswith('_percent') or field_name.startswith('population') or ('per_10000' in field_name) or (field_name in {'highlighted_count', 'joined_rows'}) or (field_name == 'value' and str(raw.get('unit', '')).startswith('%'))) and item['unit'] != _claim_unit(field_name, raw):
            raise ContractViolation('claim:unit_mismatch')
        for part_name in ('numerator', 'denominator'):
            part = item[part_name]
            if part is None:
                continue
            _keys(part, {'value', 'unit', 'period', 'source_id', 'evidence_path', 'data_ref'}, f'claim.{part_name}')
            if type(part['value']) not in (int, float) or not math.isfinite(part['value']) or part['source_id'] not in item['source_ids']:
                raise ContractViolation(f'claim:{part_name}')
            if part['period'] != catalog[part['source_id']].get('reference_period'):
                raise ContractViolation(f'claim:{part_name}_provenance')
            if part['evidence_path'] is not None and part['data_ref'] is None:
                if not str(part['evidence_path']).startswith('/') or _pointer(raw, part['evidence_path']) != part['value']:
                    raise ContractViolation(f'claim:{part_name}_pointer')
            elif part['data_ref'] is not None and part['evidence_path'] is None:
                ref = _keys(part['data_ref'], {'path', 'sha256', 'municipality_code', 'reference_period', 'field'}, f'claim.{part_name}.data_ref')
                path = (root / ref['path']).resolve()
                if ref['path'] != 'datos_preparados/demografia.csv' or root not in path.parents or (not path.is_file()) or (digest(path.read_bytes()) != ref['sha256']) or (ref['municipality_code'] != item['entity_id']) or (ref['reference_period'] != part['period']):
                    raise ContractViolation(f'claim:{part_name}_data_ref')
                rows = territorial.DataRepository(root / 'datos_preparados').demography()
                matching = [row for row in rows if row['municipality_code'] == ref['municipality_code'] and row['reference_period'] == ref['reference_period']]
                if len(matching) != 1 or matching[0].get(ref['field']) != part['value']:
                    raise ContractViolation(f'claim:{part_name}_data_value')
            else:
                raise ContractViolation(f'claim:{part_name}_ambiguous_provenance')
        if 'per_10000' in field_name:
            numerator, denominator = (item['numerator'], item['denominator'])
            parts = item['evidence_path'].split('/')
            age = '75' if '75' in field_name else '65'
            expected_numerator = '/'.join(parts[:-1]) + '/registered_service_count'
            expected_denominator = f'/data/{parts[2]}/population_{age}_plus'
            if numerator is None or denominator is None or numerator['unit'] != 'registros' or (denominator['unit'] != 'personas') or (numerator['source_id'] != 'ODE_HEALTH_CENTRES_2026') or (denominator['source_id'] != 'EUSTAT_EMH_2025') or (numerator['evidence_path'] != expected_numerator) or (denominator['evidence_path'] != expected_denominator) or (denominator['value'] <= 0) or (abs(item['value'] - round(numerator['value'] / denominator['value'] * 10000, 3)) > 0.0005):
                raise ContractViolation('claim:rate_lineage')
        if field_name.startswith('pct_') or (field_name == 'value' and str(raw.get('unit', '')).startswith('%')):
            numerator, denominator = (item['numerator'], item['denominator'])
            age = '75' if '75' in field_name else '65' if '65' in field_name else raw.get('filters', {}).get('age_group')
            if numerator is None or denominator is None or numerator['unit'] != 'personas' or (denominator['unit'] != 'personas') or (numerator['source_id'] != denominator['source_id']) or (numerator['source_id'] != 'EUSTAT_EMH_2025') or (numerator['data_ref']['field'] != f'population_{age}_plus') or (denominator['data_ref']['field'] != 'population_total') or (denominator['value'] <= 0) or (abs(item['value'] - round(numerator['value'] / denominator['value'] * 100, 3)) > 0.0005):
                raise ContractViolation('claim:percentage_lineage')

def _error(request_id: str, capability_id: str, args: dict[str, Any], origin: str, code: str, message: str, *, options: list[str] | None=None, snapshot_id: str | None=None, raw_json: str | None=None, versions: dict[str, str] | None=None) -> dict[str, Any]:
    try:
        args_hash = digest(canonical(args))
        safe_args = args
    except (ContractViolation, TypeError, ValueError):
        safe_args = {}
        args_hash = digest(canonical(safe_args))
    return {'schema_version': VERSION, 'request_id': request_id, 'capability_id': capability_id, 'normalized_input': {'tool': capability_id, 'arguments': safe_args}, 'effective_request': None, 'execution': {'request_id': request_id, 'tool': capability_id, 'arguments_sha256': args_hash, 'snapshot_id': snapshot_id, 'state': 'not_started' if code == 'capability_unavailable' else 'completed' if raw_json is not None else 'failed'}, 'status': 'unsupported' if code in {'capability_unavailable', 'unsupported_age', 'unsupported_category'} else 'error', 'outcomes': [], 'claims': [], 'method': '', 'assumptions': [], 'limitations': [], 'error': {'origin': origin, 'code': code, 'message': message, 'available_options': options or [], 'safe_next_action': 'Revisar los valores disponibles; si el fallo persiste, no usar el resultado.'}, 'versions': versions or {key: '0' * 64 for key in ('data_sha256', 'code_sha256', 'contract_sha256')}, 'raw_result_json': raw_json, 'raw_result_sha256': digest(raw_json) if raw_json is not None else None}

def _versions(root: Path, cap: dict[str, Any]) -> dict[str, str]:
    data = ''.join((item['sha256'] for item in cap['required_data']))
    code_path = Path(__file__)
    contract_path = root / 'contracts/vnext/evidence-v1.1.schema.json'
    return {'data_sha256': digest(data), 'code_sha256': digest(code_path.read_bytes()), 'contract_sha256': digest(contract_path.read_bytes())}

def consultar_capacidades(pregunta_o_dimension: str | None=None, *, root: Path | None=None, detalle: bool=True) -> str:
    """Inspect validated capabilities; disabled entries stay visibly disabled."""
    root = _workspace_root(root)
    entries = _registry(root)
    selected = [item for item in entries if not pregunta_o_dimension or pregunta_o_dimension.lower() in (item['id'] + ' ' + item['description']).lower()]
    if not selected:
        selected = entries
    catalog = _catalog(root)
    return canonical({'status': 'ok', 'question': 'Capacidades verificadas de GIPUZKOA 360', 'filters': {'pregunta_o_dimension': pregunta_o_dimension}, 'period': None, 'metric': 'capability_registry', 'unit': 'no aplica', 'rows_used': len(selected), 'data': selected, 'method': 'Lectura del registro validado contra handlers, fuentes y hashes de datos.', 'sources': list(catalog.values()), 'warnings': [], 'limitations': ['Una capacidad deshabilitada no se puede ejecutar.', 'El registro no sustituye una prueba conversacional en portal.']})

def consultar_fuente(source_id: str | None=None, *, root: Path | None=None, detalle: bool=True) -> str:
    """Resolve W1 references through the W2 catalog; retain v4 source handling."""
    root = _workspace_root(root)
    additional = strict_loads((root / 'datos_preparados/vnext/mobility_sources.json').read_text(encoding='utf-8'))
    selected = [item for item in additional if item['source_id'] == source_id]
    if not selected:
        return _territorial_handler('consultar_fuente', root)(source_id=source_id, detalle=detalle)
    return canonical({'status': 'ok', 'question': 'Consulta de procedencia', 'filters': {'source_id': source_id}, 'period': None, 'metric': 'source_metadata', 'unit': 'no aplica', 'rows_used': 1, 'data': selected, 'method': 'Ficha W2 cotejada con referencias y hashes W1 publicados.', 'sources': [{'source_id': source_id}], 'warnings': [], 'limitations': ['La ficha describe procedencia; no convierte parámetros o modelos en observaciones oficiales.'], 'summary': {'total_result_rows': 1}, 'detail_level': 'compact'})

def _ensure_w1_runtime(root: Path) -> None:
    """The generated two-editor bundle replaces this with a pinned ZIP loader."""

def _execute_mobility(request: Any, request_id: str, root: Path) -> dict[str, Any]:
    try:
        _ensure_w1_runtime(root)
        from prototypes.ir_y_volver import provider_r6
        try:
            from . import mobility_adapter, health_adapter
        except ImportError:
            import mobility_adapter
            import health_adapter
        if type(request) is list:
            only_legacy = all((type(item) is dict and item.get('snapshot_id') == mobility_adapter.SNAPSHOT_ID for item in request))
            result = mobility_adapter.consume_compare_visits(provider_r6.r4, request, request_id, root=root) if only_legacy else health_adapter.consume_compare(provider_r6, request, request_id, root)
        elif type(request) is dict and request.get('snapshot_id') == mobility_adapter.SNAPSHOT_ID:
            result = mobility_adapter.consume_plan_visit(provider_r6.r4, request, request_id, root=root)
        else:
            result = health_adapter.consume_health(provider_r6, request, request_id, root)
        return result
    except ContractViolation as exc:
        result = _error(request_id, 'plan_visit', {'request': request}, 'domain' if str(exc).startswith('mobility:invalid') else 'execution', 'contract_violation', str(exc))
    except Exception:
        result = _error(request_id, 'plan_visit', {'request': request}, 'unknown', 'unverified_result', 'No se ha podido verificar el proveedor de movilidad.')
    validate_evidence(result, _catalog(root), root=root)
    return result

def plan_visit(request: Any) -> dict[str, Any]:
    """Execute one pinned W1 stop-only scenario or a bounded comparison."""
    return _execute_mobility(request, uuid4().hex, _workspace_root())

def execute(capability_id: str, arguments: dict[str, Any], request_id: str, *, root: Path | None=None, transport: Callable[[Callable[..., str], dict[str, Any]], str] | None=None) -> dict[str, Any]:
    """Execute one deterministic tool, bind and validate its evidence, fail closed."""
    _text(request_id, 'request_id')
    _text(capability_id, 'capability_id')
    if type(arguments) is not dict:
        raise ContractViolation('arguments:expected_object')
    catalog: dict[str, Any] = {}
    versions = None
    try:
        root = _workspace_root(root)
        catalog = _catalog(root)
        registry = _registry(root)
        cap = next((item for item in registry if item['id'] == capability_id), None)
        if cap is None or not cap['enabled']:
            return _error(request_id, capability_id, arguments, 'domain', 'capability_unavailable', 'La capacidad no está habilitada ni validada.', options=[item['id'] for item in registry if item['enabled']])
        versions = _versions(root, cap)
        repaired, repair_notes = _repair_once(arguments)
        normalized = _validate_arguments(repaired, cap)
        if capability_id == 'plan_visit':
            return _execute_mobility(normalized['request'], request_id, root)
        handler = consultar_capacidades if cap['handler'] == 'consultar_capacidades' else consultar_fuente if cap['handler'] == 'consultar_fuente' else _territorial_handler(cap['handler'], root)
        call_args = {**normalized, 'detalle': True}
        if handler in {consultar_capacidades, consultar_fuente}:
            call_args['root'] = root
        effective = _effective_request(handler, normalized, root)
        raw_text = transport(handler, call_args) if transport else handler(**call_args)
        if type(raw_text) is not str:
            raise ContractViolation('tool_result:expected_json_string')
        raw = _validate_result(strict_loads(raw_text), catalog)
        _bind_result_to_arguments(raw, effective, root)
        raw_json = canonical(raw)
        if len(raw_json.encode('utf-8')) > MAX_EVIDENCE_BYTES:
            return _error(request_id, capability_id, normalized, 'execution', 'payload_too_large', 'El resultado completo supera el límite seguro; acote la consulta.', options=['Acotar municipios o parámetros'], raw_json=None, versions=versions)
        if raw['status'] == 'error':
            code = raw['error_code']
            origin = 'domain' if code.startswith(('invalid', 'unknown', 'unsupported', 'source_not_found', 'municipality_not_found')) else 'data' if code.startswith(('missing', 'corrupt', 'no_')) else 'unknown'
            result = _error(request_id, capability_id, normalized, origin, code, raw['message'], options=raw['available_options'], raw_json=raw_json, versions=versions)
        else:
            claims, unattributed = _make_claims(raw, catalog, root)
            result = {'schema_version': VERSION, 'request_id': request_id, 'capability_id': capability_id, 'normalized_input': {'tool': capability_id, 'arguments': normalized}, 'effective_request': effective, 'execution': {'request_id': request_id, 'tool': capability_id, 'arguments_sha256': digest(canonical(normalized)), 'snapshot_id': None, 'state': 'completed'}, 'status': 'valid', 'outcomes': [], 'claims': claims, 'method': raw['method'], 'assumptions': repair_notes, 'limitations': raw['limitations'] + ([f'{unattributed} cifras del resultado carecen de atribución por fuente en la salida y no se ofrecen como afirmaciones verificadas.'] if unattributed else []), 'error': None, 'versions': versions, 'raw_result_json': raw_json, 'raw_result_sha256': digest(raw_json)}
        validate_evidence(result, catalog, root=root)
        return result
    except ObservedTransportError as exc:
        result = _error(request_id, capability_id, arguments, 'transport', 'observed_transport_failure', str(exc) or 'Fallo de transporte observado.', versions=versions)
    except ContractViolation as exc:
        if str(exc).startswith('workspace:'):
            return _error(request_id, capability_id, arguments, 'data', 'invalid_workspace_root', 'La raíz declarada no contiene el candidato completo; no se ha usado otra raíz.')
        user_argument_error = str(exc).startswith('arguments:')
        result = _error(request_id, capability_id, arguments, 'domain' if user_argument_error else 'execution', 'invalid_arguments' if user_argument_error else 'contract_violation', str(exc), versions=versions)
    except (OSError, json.JSONDecodeError) as exc:
        result = _error(request_id, capability_id, arguments, 'data', 'data_unavailable', str(exc), versions=versions)
    except Exception:
        result = _error(request_id, capability_id, arguments, 'unknown', 'unverified_result', 'No se ha podido verificar el resultado.', versions=versions)
    validate_evidence(result, catalog, root=root)
    return result

def _r15_mobility_catalog_view(root: Path) -> dict[str, Any] | None:
    catalog_path = root / 'datos_preparados/vnext/operational_catalog_r6.json'
    labels_path = root / 'datos_preparados/vnext/consumer_labels_r7.json'
    if not catalog_path.is_file() or not labels_path.is_file():
        return None
    if digest(catalog_path.read_bytes()) != 'c7bd3cc8ffe50956ce839bec0ef90a13578160a4d5b4053b09673d2dc4c4ec17' or digest(labels_path.read_bytes()) != 'f0804b646d0473531e4f9ad12e31dc1ee7ee50cab69576bc95a0485b8da62799':
        raise ContractViolation('mobility:catalog_or_labels_changed')
    catalog = strict_loads(catalog_path.read_text(encoding='utf-8'))
    labels = strict_loads(labels_path.read_text(encoding='utf-8'))
    return {'contract_scope': 'PUBLIC_AGENT_CONTRACT', 'public_contract_version': 'R15', 'scenario_kind': 'health_visit', 'contract_version': '0.3.1', 'origin_options': [{'origin_id': item['origin_id'], 'municipality_name': item['municipality_name'], 'name': item['name']} for item in catalog['origins']], 'destination': catalog['destination'], 'validated_date': catalog['validated_date'], 'walking_profile': labels['walking_profile'], 'provider_defaults': catalog['defaults'], 'defaults_policy': 'Informational producer defaults, not public arguments or evidence of human choice. Do not copy them into the tool call.', 'ranges': {'duration_minutes': catalog['ranges']['duration_minutes']}, 'restrictions': catalog['restrictions'], 'request_fields': ['origin_id', 'destination_id', 'date', 'appointment_time', 'duration_minutes'], 'required_fields': ['origin_id', 'destination_id', 'date', 'appointment_time', 'duration_minutes'], 'comparison': {'mode': 'individual_calls', 'batch_supported': False, 'cross_origin_comparison': catalog['cross_origin_comparison'], 'procedure': 'Execute one plan_visit per scenario, observe every output, then compare only valid compatible results. Differences are conditional, not observed savings or recommendations.'}, 'engine_contract': {'scope': 'internal_only', 'legacy_stop_only': 'preserved, not exposed by the public tool', 'optional_parameters': 'producer defaults; not public caller decisions'}}

def _r15_mobility_view(raw: dict[str, Any], root: Path, arguments: dict[str, Any]) -> dict[str, Any]:
    labels_path = root / 'datos_preparados/vnext/consumer_labels_r7.json'
    if not labels_path.is_file() or digest(labels_path.read_bytes()) != 'f0804b646d0473531e4f9ad12e31dc1ee7ee50cab69576bc95a0485b8da62799':
        raise ContractViolation('mobility:labels_changed_before_model_view')
    labels = strict_loads(labels_path.read_text(encoding='utf-8'))
    stop_labels = {item['stop_id']: item['name'] for item in labels['stops']}
    scenarios = raw['results'] if 'results' in raw else [raw]
    if any((item['schema_version'] == '0.2.0' for item in scenarios)):
        package = root / 'datos_preparados/vnext/w1_r6_runtime.zip'
        if digest(package.read_bytes()) != 'c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910':
            raise ContractViolation('mobility:legacy_labels_package_changed')
        with zipfile.ZipFile(package) as archive:
            snapshot_bytes = archive.read('prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-r4-20260929.json')
        if digest(snapshot_bytes) != '62e00c04edb96ccde0a5ce4fe81574452ddcacdb4c173b030ca49b000f5a084b':
            raise ContractViolation('mobility:legacy_labels_snapshot_changed')
        snapshot = strict_loads(snapshot_bytes.decode('utf-8'))
        for stop_id, row in snapshot['stops'].items():
            if stop_id in stop_labels and stop_labels[stop_id] != row['name']:
                raise ContractViolation('mobility:conflicting_stop_labels')
            stop_labels[stop_id] = row['name']
    route_labels = {item['route_id']: item['short_name'] for item in labels['routes']}
    origin_labels = {item['origin_id']: item['name'] for item in labels['origins']}
    catalog = _catalog(root)
    originals = arguments.get('requests', arguments.get('request', arguments))
    originals = originals if type(originals) is list else [originals]

    def label(table: dict[str, str], key: str) -> str:
        value = table.get(key)
        if not value or value == key:
            raise ContractViolation('mobility:missing_human_label')
        return value

    def scenario(result: dict[str, Any], index: int) -> dict[str, Any]:
        request = result.get('normalized_request') or {}
        supplied = {row['field']: row for row in result.get('parameter_provenance', [])}
        original = originals[index]
        attribution = [{'field': key, 'value': value, 'provider_origin': supplied[key]['origin'] if key in supplied else 'not_provided_by_legacy_contract', 'w2_attribution': 'provider_default' if key in supplied and supplied[key]['origin'] == 'model_default' else 'tool_argument_origin_unverified' if key in original else 'legacy_provider_default'} for key, value in request.items()]
        sources = []
        for item in result['sources']:
            if result['schema_version'] == '0.3.1':
                source = {key: item[key] for key in ('source_id', 'source_role', 'publisher', 'url', 'reference_period', 'transformation')}
                metadata = catalog[item['source_id']]
            elif result['schema_version'] == '0.2.0':
                source = dict(item)
                metadata = catalog['W1_GTFS@' + request['date']]
            else:
                raise ContractViolation('mobility:unsupported_projection_version')
            source.update(title=metadata['title'], institution=metadata['institution'], contract_version=result['schema_version'], catalog_source_id=metadata['source_id'])
            sources.append(source)
        view: dict[str, Any] = {'index': index, 'status': result['status'], 'error': result['error'], 'scenario_kind': result['scenario_kind'], 'scope': result['scope'], 'time_basis': result['time_basis'], 'snapshot_id': result['snapshot_id'], 'effective_parameters': request, 'parameter_attribution': attribution, 'origin_label': label(origin_labels, request['origin_id']) if result['status'] == 'ok' else origin_labels.get(request.get('origin_id')), 'destination_label': labels['destination'].get('name') if result['scenario_kind'] == 'health_visit' else 'Paradas de Beasain (sin acceso sanitario)', 'sources': sources, 'assumptions': result['assumptions'], 'limitations': result['limitations']}
        if result['status'] != 'ok':
            return view
        itinerary = result['itinerary']

        def leg(value: dict[str, Any]) -> dict[str, Any]:
            return {**value, 'route_label': label(route_labels, value['route_id']), 'from_stop_label': label(stop_labels, value['from_stop_id']), 'to_stop_label': label(stop_labels, value['to_stop_id'])}
        view['itinerary'] = {'outbound': leg(itinerary['outbound']), 'return': leg(itinerary['return']), 'origin_stop_id': itinerary['origin_stop_id'], 'return_stop_id': itinerary['return_stop_id'], 'total_s': itinerary['total_s'], 'return_slack_s': itinerary['return_slack_s']}
        view['components_s'] = result['components_s']
        if result['scenario_kind'] == 'health_visit':
            view['walking'] = {direction: {'total_metres': link['total_metres'], 'seconds': link['seconds'], 'modelled_access': link['modelled_access'], 'entrance_verified': link['entrance_verified'], 'source_refs': link['source_refs']} for direction, link in result['walking'].items()}
            destination = result['health_destination']
            view['health_destination'] = {key: destination[key] for key in ('centre_id', 'name', 'centre_anchor', 'address', 'address_conflict', 'human_review_required', 'entrance_verification', 'entrance_verified', 'modelled_access', 'wording', 'source_refs')}
        return view
    if 'results' in raw:
        return {'scenarios': [scenario(item, index) for index, item in enumerate(raw['results'])], 'comparisons': raw['comparisons'], 'differences_s': raw.get('differences_s', [])}
    return {'scenarios': [scenario(raw, 0)], 'comparisons': []}

def public_result(evidence: dict[str, Any], *, root: Path | None=None) -> str:
    """Validate at the projection boundary and never expose partial evidence."""
    try:
        root = _workspace_root(root)
        validate_evidence(evidence, _catalog(root), root=root)
        if evidence['raw_result_json'] is not None:
            if evidence['versions']['contract_sha256'] != digest((root / 'contracts/vnext/evidence-v1.1.schema.json').read_bytes()):
                raise ContractViolation('projection:contract_root_mismatch')
            if evidence['capability_id'] == 'plan_visit':
                if globals().get('_W1_BOUND_ROOT', root) != root:
                    raise ContractViolation('projection:provider_root_mismatch')
            elif evidence['status'] == 'valid':
                cap = next((item for item in _registry(root) if item['id'] == evidence['capability_id']))
                if evidence['versions'] != _versions(root, cap):
                    raise ContractViolation('projection:data_root_mismatch')
        return _public_result(evidence, root)
    except Exception as exc:
        code = 'invalid_workspace_root' if isinstance(exc, ContractViolation) and str(exc).startswith('workspace:') else 'public_projection_unverified'
        failure = _error(evidence.get('request_id', 'projection'), evidence.get('capability_id', 'unknown'), {}, 'data', code, 'No se ha podido verificar la vista con la raíz declarada; no se ofrecen cifras parciales.')
        return canonical({'schema_version': VERSION, 'request_id': failure['request_id'], 'capability_id': failure['capability_id'], 'status': 'error', 'claims': [], 'error': failure['error']})

def _r15_public_result(evidence: dict[str, Any], root: Path) -> str:
    """Return a bounded, attributed model view; keep raw evidence out of the prompt."""
    claims = evidence['claims']
    args = evidence['normalized_input']['arguments']
    explicit_entities = bool(args.get('municipio') or args.get('municipios'))
    raw = strict_loads(evidence['raw_result_json']) if evidence['raw_result_json'] is not None else {}
    municipality_ids = list(dict.fromkeys((row['municipality_code'] for row in raw.get('data', []) if type(row) is dict and type(row.get('municipality_code')) is str)))
    selected_ids = municipality_ids if explicit_entities else municipality_ids[:DEFAULT_PUBLIC_ENTITIES]
    selected = [claim for claim in claims if claim['entity_type'] != 'municipality' or claim['entity_id'] in selected_ids]
    claim_entities = {claim['entity_id'] for claim in selected if claim['entity_type'] == 'municipality'}
    selection = {'total_entities': len(municipality_ids), 'returned_entities': len(claim_entities), 'omitted_entities': len(municipality_ids) - len(claim_entities), 'criterion': 'Todas las entidades solicitadas explícitamente' if explicit_entities else 'Primeras entidades en el orden validado de la herramienta', 'detail_mechanism': 'Nueva consulta acotada con municipio(s) explícitos mediante las herramientas territoriales existentes; no hay lectura de rutas ni descarga de evidencia en el portal.'}
    view = {'schema_version': evidence['schema_version'], 'request_id': evidence['request_id'], 'capability_id': evidence['capability_id'], 'normalized_input': evidence['normalized_input'], 'effective_request': evidence['effective_request'], 'execution': evidence['execution'], 'status': evidence['status'], 'outcomes': evidence['outcomes'], 'claims': selected, 'selection': selection, 'method': evidence['method'], 'assumptions': evidence['assumptions'], 'limitations': evidence['limitations'], 'error': evidence['error'], 'versions': evidence['versions'], 'raw_result_sha256': evidence['raw_result_sha256']}
    if evidence['capability_id'] == 'consultar_capacidades' and type(raw.get('data')) is list:
        view['capabilities'] = [{key: item[key] for key in ('id', 'description', 'enabled', 'validation_status', 'derivation', 'coverage', 'semantic_limits', 'input_fields') if key in item} for item in raw['data'] if type(item) is dict]
        for item in view['capabilities']:
            item['input_fields'] = [dict(field) for field in item.get('input_fields', [])]
            period_field = next((field for field in item['input_fields'] if field['name'] == 'periodo'), None)
            if period_field is not None:
                demographic = item['id'] in {'obtener_resumen_territorial', 'comparar_municipios', 'analizar_envejecimiento', 'analizar_coincidencia'}
                allowed_periods = territorial.DataRepository(root / 'datos_preparados').available_periods() if demographic else item['coverage']['periods']
                period_field['allowed_values'] = list(allowed_periods)
                period_field['nullable'] = True
                item['period_policy'] = {'allowed_values': list(allowed_periods), 'meaning': 'demographic_selector' if demographic else 'source_reference_only_not_historical_filter', 'omitted_or_null': 'single_available_period_else_request_period' if demographic else 'current_sources_with_their_distinct_periods', 'explicit_invalid': 'reject_without_numeric_claims'}
            if item['id'] == 'plan_visit':
                item['description'] = 'Una visita sanitaria programada/modelada por llamada; comparar mediante llamadas individuales y sus resultados válidos. Sin batch público.'
                item['coverage'] = {**item['coverage'], 'scope': 'health_visit modelled; validated date only; origin_stop_presence_to_return_stop_arrival; public single visit'}
                item['contract_scope'] = 'PUBLIC_AGENT_CONTRACT'
                item['input_fields'] = [{'name': name, 'type': 'integer' if name == 'duration_minutes' else 'string', 'required': True, 'allowed_values': []} for name in ('origin_id', 'destination_id', 'date', 'appointment_time', 'duration_minutes')]
        mobility_catalog = _mobility_catalog_view(root)
        if mobility_catalog is not None:
            view['mobility_catalog'] = mobility_catalog
    if evidence['capability_id'] == 'consultar_fuente' and type(raw.get('data')) is list:
        view['source_metadata'] = [{key: item[key] for key in ('source_id', 'title', 'institution', 'reference_period', 'unit', 'url', 'limitations', 'method') if key in item} for item in raw['data'] if type(item) is dict]
    if evidence['capability_id'] == 'plan_visit' and raw:
        view['mobility'] = _mobility_view(raw, root, args)
    if explicit_entities and len(claim_entities) != len(municipality_ids):
        failure = _error(evidence['request_id'], evidence['capability_id'], args, 'data', 'missing_attributed_entity', 'Una entidad solicitada carece de cifra atribuida en la salida; no se ofrece una comparación parcial.')
        view.update(status='error', claims=[], error=failure['error'])
    rendered = canonical(view)
    if len(rendered.encode('utf-8')) > MAX_PUBLIC_BYTES:
        failure = _error(evidence['request_id'], evidence['capability_id'], args, 'execution', 'public_payload_too_large', 'La vista validada supera el límite local; acote los municipios o parámetros.')
        failure['error']['safe_next_action'] = 'Solicite municipios concretos; no se ha publicado ninguna cifra parcial.'
        view.update(status='error', claims=[], selection={**selection, 'returned_entities': 0, 'omitted_entities': selection['total_entities']}, error=failure['error'])
        for key in ('mobility', 'mobility_catalog', 'capabilities', 'source_metadata'):
            view.pop(key, None)
        rendered = canonical(view)
        if len(rendered.encode('utf-8')) > MAX_PUBLIC_BYTES:
            rendered = canonical({'status': 'error', 'code': 'public_payload_too_large', 'claims': []})
    return rendered
_BUNDLED_VALIDATION_INDEX = {'tests/vnext_agent/test_contracts.py': {'sha256': '8182f101056b37a9d9356bb05b81cb0b209571e0b5a4f57c7551a1760f0c76f0', 'test_names': ['test_canonical_coincidence_recomputes_7_4_2', 'test_corrupt_capability_rejected', 'test_domain_transport_and_unknown_failures_remain_distinct', 'test_every_enabled_handler_executes', 'test_evidence_tampering_rejected', 'test_invalid_nonfinite_input_is_controlled', 'test_only_explicit_equivalent_alias_is_repaired_once_and_disclosed', 'test_payload_over_limit_is_explicit_and_untruncated', 'test_registry_is_valid_and_does_not_enable_mobility_without_binding', 'test_result_cannot_cite_catalog_only_source', 'test_result_from_other_request_is_rejected', 'test_result_source_and_period_contract_failure_blocks_all_claims', 'test_sessions_are_isolated', 'test_strict_json_rejects_duplicates_and_nonfinite', 'test_synthetic_evidence_and_capability_contracts', 'test_unknown_category_and_source_have_no_numbers', 'test_unsupported_age_has_no_claims']}, 'tests/vnext_agent/test_mobility_binding.py': {'sha256': 'c1dfaccca55db59815c87b385a66cc51a9611cc820f49bef6c2f1d649f252311', 'test_names': ['test_comparison_is_common_evidence_and_keeps_every_outcome', 'test_effective_parameters_cannot_change_silently', 'test_explicit_margin_is_user_parameter', 'test_false_comparable_difference_is_rejected', 'test_incompatible_provider_version_is_rejected', 'test_nonviable_and_unknown_remain_distinct', 'test_published_w1_020_is_pinned_and_role_attributed', 'test_requested_unverified_snapshot_and_changed_blob_are_rejected']}, 'tests/vnext_agent/test_health_r10.py': {'sha256': '6c9c44e65355af5afe7e6c365502eca1b7a3208ad0f1aec743886c1b702ca216', 'test_names': ['test_health_provider_and_model_view', 'test_health_rejects_tampered_identity_sources_times_and_entrance', 'test_mobility_source_references_are_legible', 'test_parameter_authorship_comparison_limit_and_unknown_date', 'test_published_w1_fourteen_cases_through_w2_boundary']}, 'tests/vnext_agent/test_r12_generated.py': {'sha256': '2da6d2107d81665c32d5ecf061dd2dd16e80a8189d6417b0ed8c55f5d3e8ab23', 'test_names': ['test_generated_r12_end_to_end', 'test_r12_double_build_identical']}}

import sys as _w1_sys
import tempfile as _w1_tempfile
import types as _w1_types
import zipfile as _w1_zipfile
from pathlib import PurePosixPath as _W1PurePath

_W1_PACKAGE_SHA256 = 'c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910'
_W1_HELPERS = {'mobility_adapter': '"""Pinned, read-only consumer of W1 0.2.0 stop-only provider.\n\nThe approved W1 blobs are assembled at build time, never fetched at runtime.\nNo health-centre visit or realtime journey is exposed by this adapter.\n"""\n\nfrom __future__ import annotations\n\nimport re\nfrom datetime import date\nfrom pathlib import Path\nfrom typing import Any\n\ntry:\n    from . import tools\nexcept ImportError:  # Generated standalone Studio module.\n    import tools\n\n\nW1_PIN = "725a7b73ae0381092cd80edc41b8a25432d75fcd"\nW1_VERSION = "0.2.0"\nSNAPSHOT_ID = "official-goierrialdea-go01-r4-20260929"\nPROVIDER_SHA256 = "c97842617f3077c2eec1892653361b4471a18e1c64f8127b808b9968401cb834"\nVALIDATOR_SHA256 = "0773a1a612b366f59ea01f80ea1dc4fc0a4650ebbd339f6b99869c4061a16d42"\nALLOWLIST_SHA256 = "80d67a0a10da8f4aa6f7d3a30629a35dd861da9e419ede2e7fd5c907b8217cff"\nSNAPSHOT_SHA256 = "62e00c04edb96ccde0a5ce4fe81574452ddcacdb4c173b030ca49b000f5a084b"\nGTFS_SHA256 = "3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4"\nREQUEST_FIELDS = {"origin_id", "destination_id", "date", "appointment_time", "duration_minutes", "arrival_margin_minutes", "boarding_margin_minutes", "walking_profile_id", "snapshot_id", "return_deadline"}\nREQUIRED = {"origin_id", "destination_id", "date", "appointment_time", "duration_minutes"}\nRESULT_FIELDS = {"schema_version", "normalized_request", "status", "scenario_kind", "time_basis", "scope", "snapshot_id", "itinerary", "components_s", "components", "sources", "assumptions", "limitations", "error"}\nCOMPONENTS = ("initial_wait_s", "outbound_vehicle_s", "destination_walk_outbound_s", "pre_appointment_wait_s", "appointment_s", "destination_walk_return_s", "return_wait_s", "return_vehicle_s")\nSCOPE = "origin_stop_presence_to_return_stop_arrival"\n\n\ndef _clock(value: str) -> str:\n    if type(value) is not str or not re.fullmatch(r"(?:[01]\\d|2[0-3]):[0-5]\\d(?::[0-5]\\d)?", value):\n        raise tools.ContractViolation("mobility:invalid_clock")\n    return value if len(value) == 8 else value + ":00"\n\n\ndef _request(request: Any) -> dict[str, Any]:\n    if type(request) is not dict or REQUIRED - set(request) or set(request) - REQUEST_FIELDS:\n        raise tools.ContractViolation("mobility:invalid_request_fields")\n    for field in ("origin_id", "destination_id", "date", "appointment_time"):\n        tools._text(request[field], f"mobility.{field}")\n    try:\n        if date.fromisoformat(request["date"]).isoformat() != request["date"]:\n            raise ValueError("noncanonical date")\n    except ValueError as exc:\n        raise tools.ContractViolation("mobility:invalid_date") from exc\n    _clock(request["appointment_time"])\n    for field in ("duration_minutes", "arrival_margin_minutes", "boarding_margin_minutes"):\n        if field in request and type(request[field]) is not int:\n            raise tools.ContractViolation(f"mobility:{field}:expected_integer")\n    for field in ("walking_profile_id", "snapshot_id"):\n        if field in request:\n            tools._text(request[field], f"mobility.{field}")\n    if request.get("return_deadline") is not None:\n        _clock(request["return_deadline"])\n    if request.get("snapshot_id", SNAPSHOT_ID) != SNAPSHOT_ID:\n        raise tools.ContractViolation("mobility:unverified_requested_snapshot")\n    tools._finite(request)\n    return dict(request)\n\n\ndef _pinned_blobs(provider: Any) -> None:\n    source = Path(provider.__file__).resolve()\n    expected = {\n        source: PROVIDER_SHA256,\n        source.with_name("snapshot_validation.py"): VALIDATOR_SHA256,\n        source.with_name("snapshots") / "allowlist.json": ALLOWLIST_SHA256,\n        source.with_name("snapshots") / f"{SNAPSHOT_ID}.json": SNAPSHOT_SHA256,\n    }\n    for path, sha in expected.items():\n        if not path.is_file() or tools.digest(path.read_bytes()) != sha:\n            raise tools.ContractViolation(f"mobility:unverified_pinned_blob:{path.name}")\n\n\ndef _capabilities(provider: Any) -> dict[str, Any]:\n    _pinned_blobs(provider)\n    capability = provider.get_capabilities()\n    if type(capability) is not dict or capability.get("schema_version") != W1_VERSION or capability.get("provider_id") != "ir_y_volver" or capability.get("time_basis") != "scheduled" or capability.get("scope") != SCOPE:\n        raise tools.ContractViolation("mobility:provider_capability_not_verified")\n    snapshots = capability.get("snapshots")\n    if type(snapshots) is not list:\n        raise tools.ContractViolation("mobility:provider_snapshot_list")\n    matching = [item for item in snapshots if type(item) is dict and item.get("snapshot_id") == SNAPSHOT_ID and item.get("scenario_kind") == "stop_only" and item.get("fixture_kind") != "SYNTHETIC_TEST_ONLY"]\n    if len(matching) != 1 or type(matching[0].get("defaults")) is not dict or type(matching[0].get("walking_profiles")) is not dict:\n        raise tools.ContractViolation("mobility:provider_snapshot_not_verified")\n    return matching[0]\n\n\ndef _expected_normalized(request: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:\n    defaults = snapshot["defaults"]\n    return {\n        "origin_id": request["origin_id"], "destination_id": request["destination_id"], "date": request["date"],\n        "appointment_time": _clock(request["appointment_time"]), "duration_minutes": request["duration_minutes"],\n        "arrival_margin_minutes": request.get("arrival_margin_minutes", defaults["arrival_margin_minutes"]),\n        "boarding_margin_minutes": request.get("boarding_margin_minutes", defaults["boarding_margin_minutes"]),\n        "walking_profile_id": request.get("walking_profile_id", defaults["walking_profile_id"]),\n        "snapshot_id": SNAPSHOT_ID, "timezone": "Europe/Madrid",\n        "return_deadline": _clock(request["return_deadline"]) if request.get("return_deadline") is not None else None,\n    }\n\n\ndef _validate_result(raw: Any, request: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:\n    tools._keys(raw, RESULT_FIELDS, "mobility_result")\n    if raw["schema_version"] != W1_VERSION or raw["status"] not in {"ok", "no_feasible_journey", "unsupported", "unknown", "error"}:\n        raise tools.ContractViolation("mobility:version_or_status")\n    if raw["time_basis"] != "scheduled" or raw["scope"] != SCOPE or raw["scenario_kind"] != "stop_only" or raw["snapshot_id"] != SNAPSHOT_ID:\n        raise tools.ContractViolation("mobility:false_scope_or_snapshot")\n    normalized = raw["normalized_request"]\n    if normalized is not None and normalized != _expected_normalized(request, snapshot):\n        raise tools.ContractViolation("mobility:request_mismatch")\n    if raw["status"] == "ok" and normalized is None:\n        raise tools.ContractViolation("mobility:missing_normalized_request")\n    if type(raw["sources"]) is not list or not any(type(source) is dict and source.get("source_sha256") == GTFS_SHA256 for source in raw["sources"]):\n        raise tools.ContractViolation("mobility:official_schedule_source_missing")\n    tools._strings(raw["assumptions"], "mobility.assumptions")\n    tools._strings(raw["limitations"], "mobility.limitations")\n    if raw["status"] == "ok":\n        itinerary, components = raw["itinerary"], raw["components_s"]\n        if type(itinerary) is not dict or type(components) is not dict or set(components) != set(COMPONENTS) or type(raw["components"]) is not list or len(raw["components"]) != len(COMPONENTS) or raw["error"] is not None:\n            raise tools.ContractViolation("mobility:success_shape")\n        if any(type(components[key]) is not int or components[key] < 0 for key in COMPONENTS) or type(itinerary.get("total_s")) is not int or sum(components.values()) != itinerary["total_s"]:\n            raise tools.ContractViolation("mobility:component_total")\n        if type(itinerary.get("start_s")) is not int or type(itinerary.get("end_s")) is not int or itinerary["end_s"] - itinerary["start_s"] != itinerary["total_s"]:\n            raise tools.ContractViolation("mobility:interval_total")\n        cursor = itinerary["start_s"]\n        for name, item in zip(COMPONENTS, raw["components"]):\n            tools._keys(item, {"kind", "start_s", "end_s", "seconds", "basis", "derivation"}, "mobility.component")\n            if item["kind"] != name.removesuffix("_s") or item["start_s"] != cursor or item["end_s"] - item["start_s"] != item["seconds"] or item["seconds"] != components[name]:\n                raise tools.ContractViolation("mobility:component_interval")\n            cursor = item["end_s"]\n        if cursor != itinerary["end_s"] or components["appointment_s"] != normalized["duration_minutes"] * 60 or components["initial_wait_s"] != normalized["boarding_margin_minutes"] * 60 or components["destination_walk_outbound_s"] != 0 or components["destination_walk_return_s"] != 0:\n            raise tools.ContractViolation("mobility:parameter_or_stop_only_mismatch")\n    elif raw["itinerary"] is not None or raw["components_s"] is not None or raw["components"] is not None or type(raw["error"]) is not dict:\n        raise tools.ContractViolation("mobility:error_shape")\n    tools._finite(raw)\n    return raw\n\n\ndef _catalog(date_text: str) -> dict[str, dict[str, str]]:\n    return {f"{prefix}@{date_text}": {"reference_period": date_text} for prefix in ("W1_GTFS", "W2_USER", "W1_MODEL", "W1_DERIVED")}\n\n\ndef _ids(date_text: str, component: str) -> list[str]:\n    roles = {\n        "outbound_vehicle_s": ("W1_GTFS",), "return_vehicle_s": ("W1_GTFS",),\n        "appointment_s": ("W2_USER",),\n        "initial_wait_s": ("W2_USER", "W1_MODEL"),\n        "destination_walk_outbound_s": ("W1_MODEL",), "destination_walk_return_s": ("W1_MODEL",),\n    }\n    return [f"{prefix}@{date_text}" for prefix in roles.get(component, ("W1_GTFS", "W2_USER", "W1_MODEL", "W1_DERIVED"))]\n\n\ndef _claim(raw: dict[str, Any], pointer: str, value: int, date_text: str, claims: list[dict[str, Any]], component: str, *, explicit_boarding_margin: bool = False) -> None:\n    sources = [f"W2_USER@{date_text}"] if component == "initial_wait_s" and explicit_boarding_margin else [f"W1_MODEL@{date_text}"] if component == "initial_wait_s" else _ids(date_text, component)\n    entity_type, entity_id, entity_label = tools._claim_entity(raw, pointer)\n    claims.append({\n        "id": f"claim-{len(claims) + 1}", "label": component, "metric_id": component,\n        "value": value, "unit": "s", "period": date_text, "numerator": None, "denominator": None,\n        "source_ids": sources, "source_refs": tools._source_roles(component, sources),\n        "reference_periods": [{"source_id": source, "period": date_text} for source in sources],\n        "evidence_path": pointer, "entity_type": entity_type, "entity_id": entity_id,\n        "entity_label": entity_label, "derivation": "estimated_with_assumptions", "assumptions": ["Horario programado y alcance stop_only; no duración real observada."],\n    })\n\n\ndef _envelope(raw: dict[str, Any], original_args: dict[str, Any], effective_parameters: dict[str, Any], defaults_applied: list[str], request_id: str, claims: list[dict[str, Any]], outcomes: list[dict[str, Any]], status: str, error: dict[str, Any] | None, catalog: dict[str, Any], root: Path | None = None) -> dict[str, Any]:\n    root = tools._workspace_root(root)\n    raw_json = tools.canonical(raw)\n    if len(raw_json.encode("utf-8")) > tools.MAX_EVIDENCE_BYTES:\n        raise tools.ContractViolation("mobility:payload_too_large")\n    date_text = effective_parameters.get("date") if type(effective_parameters.get("date")) is str else None\n    result = {\n        "schema_version": tools.VERSION, "request_id": request_id, "capability_id": "plan_visit",\n        "normalized_input": {"tool": "plan_visit", "arguments": original_args},\n        "effective_request": {"operation": "plan_visit", "municipality_codes": [], "municipality_labels": [], "effective_period": date_text, "parameters": effective_parameters, "defaults_applied": defaults_applied, "snapshot_id": SNAPSHOT_ID, "contracts": {"evidence": tools.VERSION, "capability": tools.CAPABILITY_VERSION, "mobility": W1_VERSION}},\n        "execution": {"request_id": request_id, "tool": "plan_visit", "arguments_sha256": tools.digest(tools.canonical(original_args)), "snapshot_id": SNAPSHOT_ID, "state": "completed"},\n        "status": status, "outcomes": outcomes, "claims": claims,\n        "method": "W1 0.2.0: búsqueda completa de pares directos programados entre paradas; tiempos modelados y parámetros aplicados diferenciados, sin acreditar autoría humana.",\n        "assumptions": ["Horario programado, no observado en tiempo real.", "El destino es una parada; no acredita entrada ni visita a centro sanitario."],\n        "limitations": ["Solo fecha GO01 validada y scope stop_only; no puerta a puerta, transbordos ni acceso sanitario acreditado."],\n        "error": error,\n        "versions": {"data_sha256": SNAPSHOT_SHA256, "code_sha256": PROVIDER_SHA256, "contract_sha256": tools.digest((root / "contracts/vnext/evidence-v1.1.schema.json").read_bytes())},\n        "raw_result_json": raw_json, "raw_result_sha256": tools.digest(raw_json),\n    }\n    tools.validate_evidence(result, catalog, root=root)\n    return result\n\n\ndef _outcome(index: int, raw: dict[str, Any]) -> dict[str, Any]:\n    return {"index": index, "status": raw["status"], "error": raw["error"]}\n\n\ndef consume_plan_visit(provider: Any, request: dict[str, Any], request_id: str, *, root: Path | None = None) -> dict[str, Any]:\n    normalized_input = _request(request)\n    snapshot = _capabilities(provider)\n    raw = _validate_result(provider.plan_visit(normalized_input), normalized_input, snapshot)\n    expected = _expected_normalized(normalized_input, snapshot)\n    claims: list[dict[str, Any]] = []\n    status = {"ok": "valid", "no_feasible_journey": "no_data", "unsupported": "unsupported", "unknown": "error", "error": "error"}[raw["status"]]\n    if status == "valid":\n        _claim(raw, "/itinerary/total_s", raw["itinerary"]["total_s"], expected["date"], claims, "total_s")\n        for component in COMPONENTS:\n            _claim(raw, f"/components_s/{component}", raw["components_s"][component], expected["date"], claims, component, explicit_boarding_margin="boarding_margin_minutes" in normalized_input)\n    error = None if status == "valid" else {\n        "origin": "data" if raw["status"] == "unknown" else "domain",\n        "code": raw["error"]["code"], "message": raw["error"]["message"],\n        "available_options": [], "safe_next_action": "Revise el catálogo y la fecha validada; unknown no demuestra ausencia de transporte.",\n    }\n    return _envelope(raw, normalized_input, expected if raw["normalized_request"] is not None else normalized_input, sorted(set(expected if raw["normalized_request"] is not None else normalized_input) - set(normalized_input)), request_id, claims, [_outcome(0, raw)], status, error, _catalog(expected["date"]), root)\n\n\ndef consume_compare_visits(provider: Any, requests: list[dict[str, Any]], request_id: str, *, root: Path | None = None) -> dict[str, Any]:\n    if type(requests) is not list or not 2 <= len(requests) <= 32:\n        raise tools.ContractViolation("mobility:comparison_requires_2_to_32")\n    normalized = [_request(request) for request in requests]\n    snapshot = _capabilities(provider)\n    raw = provider.compare_visits(normalized)\n    tools._keys(raw, {"schema_version", "status", "results", "comparisons", "differences_s", "error"}, "mobility_comparison")\n    if raw["schema_version"] != W1_VERSION or raw["status"] != "ok" or type(raw["results"]) is not list or len(raw["results"]) != len(normalized) or type(raw["comparisons"]) is not list or type(raw["differences_s"]) is not list or raw["error"] is not None:\n        raise tools.ContractViolation("mobility:comparison_result")\n    for item, request in zip(raw["results"], normalized):\n        _validate_result(item, request, snapshot)\n    expected_pairs = {(left, right) for left in range(len(normalized)) for right in range(left + 1, len(normalized))}\n    seen_pairs = set()\n    comparable_pairs = set()\n    for comparison in raw["comparisons"]:\n        tools._keys(comparison, {"left_index", "right_index", "requested_changes", "held_constant", "comparability", "limitations"}, "mobility.comparison")\n        left, right = comparison["left_index"], comparison["right_index"]\n        if type(left) is not int or type(right) is not int or (left, right) not in expected_pairs or (left, right) in seen_pairs:\n            raise tools.ContractViolation("mobility:comparison_index")\n        seen_pairs.add((left, right))\n        a, b = raw["results"][left], raw["results"][right]\n        na, nb = a["normalized_request"], b["normalized_request"]\n        changes, held = {}, {}\n        if na is not None and nb is not None:\n            for key in sorted(na.keys() | nb.keys()):\n                if na.get(key) == nb.get(key):\n                    held[key] = na.get(key)\n                else:\n                    changes[key] = {"left": na.get(key), "right": nb.get(key)}\n        comparable = a["status"] == b["status"] == "ok" and all(na.get(key) == nb.get(key) for key in ("snapshot_id", "date", "timezone", "origin_id", "destination_id", "walking_profile_id"))\n        if comparison["requested_changes"] != changes or comparison["held_constant"] != held or comparison["comparability"] != ("comparable" if comparable else "not_comparable"):\n            raise tools.ContractViolation("mobility:comparison_semantics")\n        if comparable:\n            comparable_pairs.add((left, right))\n    if seen_pairs != expected_pairs:\n        raise tools.ContractViolation("mobility:missing_comparisons")\n    seen_differences = set()\n    for difference in raw["differences_s"]:\n        tools._keys(difference, {"left_index", "right_index", "total_difference_s"}, "mobility.difference")\n        pair = (difference["left_index"], difference["right_index"])\n        if pair not in comparable_pairs or pair in seen_differences or type(difference["total_difference_s"]) is not int:\n            raise tools.ContractViolation("mobility:invalid_difference")\n        seen_differences.add(pair)\n        left, right = pair\n        if difference["total_difference_s"] != raw["results"][right]["itinerary"]["total_s"] - raw["results"][left]["itinerary"]["total_s"]:\n            raise tools.ContractViolation("mobility:wrong_difference")\n    if seen_differences != comparable_pairs:\n        raise tools.ContractViolation("mobility:missing_difference")\n    tools._finite(raw)\n    claims: list[dict[str, Any]] = []\n    catalog: dict[str, Any] = {}\n    for index, item in enumerate(raw["results"]):\n        date_text = normalized[index]["date"]\n        catalog.update(_catalog(date_text))\n        if item["status"] == "ok":\n            _claim(raw, f"/results/{index}/itinerary/total_s", item["itinerary"]["total_s"], date_text, claims, "total_s")\n    for index, difference in enumerate(raw["differences_s"]):\n        date_text = normalized[difference["left_index"]]["date"]\n        _claim(raw, f"/differences_s/{index}/total_difference_s", difference["total_difference_s"], date_text, claims, "total_difference_s")\n    args = {"requests": normalized}\n    outcomes = [_outcome(index, item) for index, item in enumerate(raw["results"])]\n    return _envelope(raw, args, args, [], request_id, claims, outcomes, "valid", None, catalog, root)\n', 'health_adapter': '"""W2 boundary for the pinned W1 0.3.1 health-visit provider.\n\nThe provider\'s ``human_explicit`` means present in its input dictionary. W2 does\nnot promote that to a claim that a person selected the parameter.\n"""\n\nfrom __future__ import annotations\n\nimport json\nfrom pathlib import Path\nfrom typing import Any\n\ntry:\n    from . import tools\nexcept ImportError:  # Generated standalone Studio bundle.\n    import tools\n\ntry:\n    from . import mobility_adapter\nexcept ImportError:  # Generated standalone Studio bundle.\n    import mobility_adapter\n\n\nVERSION = "0.3.1"\nSNAPSHOT_ID = "official-goierrialdea-go01-health-r5-20260929"\nSNAPSHOT_SHA256 = "59fcded9e4236ee094eeb0881c4eb94f521b96fb6c8c89c881c3e9f6d5140901"\nR4_SNAPSHOT_ID = "official-goierrialdea-go01-r4-20260929"\nPROVIDER_SHA256 = "c9fe7e4c8078ba7f9bf2eb2a51e050b729d9f01e6021dbcc6909f951d2e936e8"\nCATALOG_SHA256 = "c7bd3cc8ffe50956ce839bec0ef90a13578160a4d5b4053b09673d2dc4c4ec17"\nRESULT_SCHEMA_SHA256 = "5408f0869cc243f901ce5d142865af968bac00b02113cfa0e793ed2b1a96226a"\nSCOPE = "origin_stop_presence_to_return_stop_arrival"\nCOMPONENTS = (\n    "initial_wait_s", "outbound_vehicle_s", "destination_walk_outbound_s",\n    "pre_appointment_wait_s", "appointment_s", "destination_walk_return_s",\n    "return_wait_s", "return_vehicle_s",\n)\nREQUEST_FIELDS = {\n    "origin_id", "destination_id", "date", "appointment_time", "duration_minutes",\n    "arrival_margin_minutes", "boarding_margin_minutes", "walking_profile_id",\n    "snapshot_id", "return_deadline",\n}\nREQUIRED = {"origin_id", "destination_id", "date", "appointment_time", "duration_minutes"}\nOFFICIAL_IDS = {"GTFS", "HEALTH_REGISTRY", "HEALTH_PAGE", "PADI_2026", "OSM"}\n\n\ndef _pinned(provider: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:\n    base = Path(provider.__file__).resolve().parent\n    root = base.parents[1]\n    expected = {\n        base / "provider_r6.py": PROVIDER_SHA256,\n        base / "contracts/v0.3.1/result.schema.json": RESULT_SCHEMA_SHA256,\n        base / "snapshots" / f"{SNAPSHOT_ID}.json": SNAPSHOT_SHA256,\n        root / "datos_preparados/movilidad/operational_catalog_r6.json": CATALOG_SHA256,\n    }\n    for path, digest in expected.items():\n        if not path.is_file() or tools.digest(path.read_bytes()) != digest:\n            raise tools.ContractViolation(f"health:unverified_pinned_blob:{path.name}")\n    catalog = tools.strict_loads((root / "datos_preparados/movilidad/operational_catalog_r6.json").read_text(encoding="utf-8"))\n    health = tools.strict_loads((base / "snapshots" / f"{SNAPSHOT_ID}.json").read_text(encoding="utf-8"))\n    r4 = tools.strict_loads((base / "snapshots" / f"{R4_SNAPSHOT_ID}.json").read_text(encoding="utf-8"))\n    if catalog["snapshot_id"] != SNAPSHOT_ID or catalog["snapshot_sha256"] != SNAPSHOT_SHA256 or catalog["contract_version"] != VERSION:\n        raise tools.ContractViolation("health:catalog_contract")\n    capability = provider.get_capabilities()\n    snapshots = capability.get("snapshots", [])\n    matched = [item for item in snapshots if item.get("snapshot_id") == SNAPSHOT_ID]\n    if capability.get("schema_version") != VERSION or capability.get("provider_id") != "ir_y_volver_r6" or capability.get("error") is not None or len(matched) != 1 or matched[0].get("scenario_kind") != "health_visit" or matched[0].get("entrance_verified") is not False:\n        raise tools.ContractViolation("health:capability_contract")\n    return catalog, health, r4\n\n\ndef _request(value: Any, catalog: dict[str, Any]) -> dict[str, Any]:\n    if type(value) is not dict or REQUIRED - set(value) or set(value) - REQUEST_FIELDS:\n        raise tools.ContractViolation("health:invalid_request_fields")\n    for field in ("origin_id", "destination_id", "date", "appointment_time"):\n        tools._text(value[field], f"health.{field}")\n    if type(value["duration_minutes"]) is not int:\n        raise tools.ContractViolation("health:invalid_duration")\n    for field in ("arrival_margin_minutes", "boarding_margin_minutes"):\n        if field in value and type(value[field]) is not int:\n            raise tools.ContractViolation(f"health:invalid_{field}")\n    if value.get("snapshot_id", SNAPSHOT_ID) not in {SNAPSHOT_ID, R4_SNAPSHOT_ID}:\n        raise tools.ContractViolation("health:unverified_requested_snapshot")\n    for field in ("appointment_time", "return_deadline"):\n        if value.get(field) is not None:\n            mobility_adapter._clock(value[field])\n    tools._finite(value)\n    return dict(value)\n\n\ndef _expected(request: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:\n    defaults = catalog["defaults"]\n    return {\n        "origin_id": request["origin_id"], "destination_id": request["destination_id"],\n        "date": request["date"], "appointment_time": mobility_adapter._clock(request["appointment_time"]),\n        "duration_minutes": request["duration_minutes"],\n        "arrival_margin_minutes": request.get("arrival_margin_minutes", defaults["arrival_margin_minutes"]),\n        "boarding_margin_minutes": request.get("boarding_margin_minutes", defaults["boarding_margin_minutes"]),\n        "walking_profile_id": request.get("walking_profile_id", defaults["walking_profile_id"]),\n        "snapshot_id": SNAPSHOT_ID, "timezone": defaults["timezone"],\n        "return_deadline": mobility_adapter._clock(request["return_deadline"]) if request.get("return_deadline") else None,\n    }\n\n\ndef _seconds(clock: str) -> int:\n    hour, minute, second = map(int, clock.split(":"))\n    return hour * 3600 + minute * 60 + second\n\n\ndef _leg_identity(leg: Any, snapshot: dict[str, Any]) -> None:\n    if type(leg) is not dict:\n        raise tools.ContractViolation("health:missing_leg")\n    matches = [trip for trip in snapshot["trips"] if trip["trip_id"] == leg.get("trip_id")]\n    if len(matches) != 1:\n        raise tools.ContractViolation("health:trip_id_mismatch")\n    trip = matches[0]\n    stops = trip["stops"]\n    starts = [stop for stop in stops if stop["sequence"] == leg.get("from_stop_sequence")]\n    ends = [stop for stop in stops if stop["sequence"] == leg.get("to_stop_sequence")]\n    if len(starts) != 1 or len(ends) != 1 or starts[0]["sequence"] >= ends[0]["sequence"]:\n        raise tools.ContractViolation("health:stop_sequence_mismatch")\n    start, end = starts[0], ends[0]\n    expected = {\n        "route_id": trip["route_id"], "service_id": trip["service_id"],\n        "from_stop_id": start["stop_id"], "to_stop_id": end["stop_id"],\n        "departure_time": start["departure"], "arrival_time": end["arrival"],\n        "pickup_type": start["pickup_type"], "drop_off_type": end["drop_off_type"],\n        "from_timepoint": start["timepoint"], "to_timepoint": end["timepoint"],\n    }\n    if any(leg.get(key) != value for key, value in expected.items()):\n        raise tools.ContractViolation("health:leg_identity_mismatch")\n\n\ndef _validate_health(raw: Any, request: dict[str, Any], catalog: dict[str, Any], health: dict[str, Any], r4: dict[str, Any], provider: Any, root: Path) -> dict[str, Any]:\n    schema_path = Path(provider.__file__).resolve().parent / "contracts/v0.3.1/result.schema.json"\n    schema = tools.strict_loads(schema_path.read_text(encoding="utf-8"))\n    try:\n        provider.r5.schema_validate(raw, schema)\n    except (ValueError, KeyError, TypeError) as exc:\n        raise tools.ContractViolation("health:result_schema") from exc\n    if raw["schema_version"] != VERSION or raw["scenario_kind"] != "health_visit" or raw["snapshot_id"] != SNAPSHOT_ID or raw["scope"] != SCOPE or raw["time_basis"] != "scheduled":\n        raise tools.ContractViolation("health:identity_or_scope")\n    normalized = raw["normalized_request"]\n    if normalized is not None and normalized != _expected(request, catalog):\n        raise tools.ContractViolation("health:request_mismatch")\n    if raw["status"] == "ok" and normalized is None:\n        raise tools.ContractViolation("health:missing_normalized_request")\n    rows = raw["parameter_provenance"]\n    if normalized is None:\n        if rows:\n            raise tools.ContractViolation("health:false_parameter_provenance")\n    else:\n        if type(rows) is not list or len(rows) != len(normalized) or {row.get("field") for row in rows} != set(normalized):\n            raise tools.ContractViolation("health:parameter_provenance_shape")\n        for row in rows:\n            field = row["field"]\n            explicit = field in request\n            if row["value"] != normalized[field] or row["origin"] != ("human_explicit" if explicit else "model_default") or row["source_ref"] != ("USER" if explicit else "MODEL_DEFAULTS"):\n                raise tools.ContractViolation("health:parameter_provenance_binding")\n    metadata = tools._catalog(root)\n    source_ids = set()\n    for source in raw["sources"]:\n        sid = source["source_id"]\n        if sid in source_ids or sid not in metadata:\n            raise tools.ContractViolation("health:source_identity")\n        source_ids.add(sid)\n        known = metadata[sid]\n        producer_role = "user_input" if sid == "USER" else known["role"]\n        expected_period = normalized["date"] if sid in {"USER", "MODEL_DEFAULTS", "DERIVED"} and normalized is not None else known["reference_period"]\n        if source["source_role"] != producer_role or source["reference_period"] != expected_period:\n            raise tools.ContractViolation("health:source_role_or_period")\n        if sid in OFFICIAL_IDS and (source["source_sha256"] != known["source_sha256"] or source["url"] != known["url"]):\n            raise tools.ContractViolation("health:external_source_mutation")\n        if sid not in OFFICIAL_IDS and source["url"] is not None:\n            raise tools.ContractViolation("health:internal_source_as_official")\n    if raw["status"] == "ok":\n        if raw["health_destination"] != health["health_destination"] or raw["health_destination"]["entrance_verified"] is not False or raw["health_destination"]["human_review_required"] is not True:\n            raise tools.ContractViolation("health:destination_misrepresentation")\n        itinerary = raw["itinerary"]\n        _leg_identity(itinerary["outbound"], r4)\n        _leg_identity(itinerary["return"], r4)\n        if itinerary["origin_stop_id"] != itinerary["outbound"]["from_stop_id"] or itinerary["return_stop_id"] != itinerary["return"]["to_stop_id"]:\n            raise tools.ContractViolation("health:stop_identity")\n        walking = raw["walking"]\n        if walking["outbound"] != health["walking_links"][itinerary["outbound"]["to_stop_id"]]["outbound"] or walking["return"] != health["walking_links"][itinerary["return"]["from_stop_id"]]["return"]:\n            raise tools.ContractViolation("health:walking_identity")\n        components = raw["components_s"]\n        if type(components) is not dict or set(components) != set(COMPONENTS) or type(raw["components"]) is not list or len(raw["components"]) != 8:\n            raise tools.ContractViolation("health:components_shape")\n        if any(type(components[key]) is not int or components[key] < 0 for key in COMPONENTS) or sum(components.values()) != itinerary["total_s"] or itinerary["end_s"] - itinerary["start_s"] != itinerary["total_s"]:\n            raise tools.ContractViolation("health:component_total")\n        cursor = itinerary["start_s"]\n        for field, item in zip(COMPONENTS, raw["components"]):\n            if item["kind"] != field.removesuffix("_s") or item["start_s"] != cursor or item["end_s"] - item["start_s"] != item["seconds"] or item["seconds"] != components[field] or not set(item["source_refs"]) <= source_ids:\n                raise tools.ContractViolation("health:component_interval_or_source")\n            cursor = item["end_s"]\n        if cursor != itinerary["end_s"] or components["initial_wait_s"] != normalized["boarding_margin_minutes"] * 60 or components["appointment_s"] != normalized["duration_minutes"] * 60 or components["destination_walk_outbound_s"] != walking["outbound"]["seconds"] or components["destination_walk_return_s"] != walking["return"]["seconds"]:\n            raise tools.ContractViolation("health:parameter_or_walking_mismatch")\n        if components["outbound_vehicle_s"] != _seconds(itinerary["outbound"]["arrival_time"]) - _seconds(itinerary["outbound"]["departure_time"]) or components["return_vehicle_s"] != _seconds(itinerary["return"]["arrival_time"]) - _seconds(itinerary["return"]["departure_time"]):\n            raise tools.ContractViolation("health:schedule_component_mismatch")\n        if itinerary["return_slack_s"] != _seconds(itinerary["return"]["departure_time"]) - _seconds(normalized["appointment_time"]) - normalized["duration_minutes"] * 60 - walking["return"]["seconds"] - normalized["boarding_margin_minutes"] * 60:\n            raise tools.ContractViolation("health:return_slack_mismatch")\n        if components["pre_appointment_wait_s"] != _seconds(normalized["appointment_time"]) - _seconds(itinerary["outbound"]["arrival_time"]) - walking["outbound"]["seconds"]:\n            raise tools.ContractViolation("health:appointment_wait_mismatch")\n    else:\n        if raw["itinerary"] is not None or raw["components_s"] is not None or raw["walking"] is not None or type(raw["error"]) is not dict:\n            raise tools.ContractViolation("health:error_shape")\n    tools._finite(raw)\n    return raw\n\n\ndef _claim(raw: dict[str, Any], pointer: str, unit: str, sources: list[str], catalog: dict[str, Any], claims: list[dict[str, Any]]) -> None:\n    value = tools._pointer(raw, pointer)\n    entity_type, entity_id, entity_label = tools._claim_entity(raw, pointer)\n    metric = pointer.split("/")[-1]\n    claims.append({\n        "id": f"claim-{len(claims) + 1}", "label": metric, "value": value, "unit": unit,\n        "period": ";".join(dict.fromkeys(catalog[source]["reference_period"] for source in sources)),\n        "numerator": None, "denominator": None, "source_ids": sources,\n        "evidence_path": pointer, "entity_type": entity_type, "entity_id": entity_id,\n        "entity_label": entity_label, "metric_id": metric,\n        "reference_periods": [{"source_id": source, "period": catalog[source]["reference_period"]} for source in sources],\n        "source_refs": tools._source_roles(metric, sources), "derivation": "estimated_with_assumptions",\n        "assumptions": ["Horario GTFS estático y paseo modelado; no duración real observada."],\n    })\n\n\ndef _claims(raw: dict[str, Any], prefix: str, catalog: dict[str, Any], claims: list[dict[str, Any]]) -> None:\n    sources = ["GTFS", "HEALTH_REGISTRY", "OSM", "MODEL", "USER", "MODEL_DEFAULTS", "DERIVED"]\n    _claim(raw, prefix + "/itinerary/total_s", "s", sources, catalog, claims)\n    for field in COMPONENTS:\n        scenario = tools._pointer(raw, prefix) if prefix else raw\n        provenance = {row["field"]: row["source_ref"] for row in scenario["parameter_provenance"]}\n        related = ["GTFS"] if field.endswith("vehicle_s") else [provenance["duration_minutes" if field == "appointment_s" else "boarding_margin_minutes"]] if field in {"appointment_s", "initial_wait_s"} else sources\n        _claim(raw, prefix + "/components_s/" + field, "s", related, catalog, claims)\n    for direction in ("outbound", "return"):\n        _claim(raw, prefix + f"/walking/{direction}/total_metres", "m", ["GTFS", "HEALTH_REGISTRY", "OSM", "MODEL"], catalog, claims)\n\n\ndef _error(raw: dict[str, Any]) -> dict[str, Any]:\n    code = raw["error"]["code"]\n    origin = "data" if code in {"invalid_health_snapshot", "date_not_validated"} else "domain"\n    return {"origin": origin, "code": code, "message": raw["error"]["message"],\n            "available_options": [], "safe_next_action": "Revise el catálogo, parámetros y fecha validada; este estado no prueba ausencia de transporte."}\n\n\ndef _envelope(raw: dict[str, Any], arguments: dict[str, Any], effective: dict[str, Any] | None, request_id: str, claims: list[dict[str, Any]], outcomes: list[dict[str, Any]], status: str, error: dict[str, Any] | None, root: Path) -> dict[str, Any]:\n    raw_json = tools.canonical(raw)\n    if len(raw_json.encode("utf-8")) > tools.MAX_EVIDENCE_BYTES:\n        raise tools.ContractViolation("health:evidence_payload_too_large")\n    snapshot = effective.get("snapshot_id") if effective else SNAPSHOT_ID\n    result = {\n        "schema_version": tools.VERSION, "request_id": request_id, "capability_id": "plan_visit",\n        "normalized_input": {"tool": "plan_visit", "arguments": arguments},\n        "effective_request": None if effective is None else {\n            "operation": "plan_visit", "municipality_codes": [], "municipality_labels": [],\n            "effective_period": effective.get("date"), "parameters": effective,\n            "defaults_applied": sorted(set(effective) - set(arguments)), "snapshot_id": snapshot,\n            "contracts": {"evidence": tools.VERSION, "capability": tools.CAPABILITY_VERSION, "mobility": VERSION},\n        },\n        "execution": {"request_id": request_id, "tool": "plan_visit", "arguments_sha256": tools.digest(tools.canonical(arguments)), "snapshot_id": snapshot, "state": "completed"},\n        "status": status, "outcomes": outcomes, "claims": claims,\n        "method": "W1 0.3.1: pares GO01 programados y paseo modelado hasta punto oficial del centro; validación W2 de identidad, parámetros y componentes.",\n        "assumptions": ["Los argumentos del agente no acreditan autoría humana aunque W1 los marque human_explicit.", "Paseo de referencia 50 m/min + 120 s por enlace completo y sentido."],\n        "limitations": ["Entrada física NOT_VERIFIED; conflicto Bernedo Enea 1 / Zaldizurreta 2 pendiente de revisión humana.", "GTFS estático y tiempos timepoint=0 aproximados; no realtime, domicilio, cita ni accesibilidad garantizada."],\n        "error": error,\n        "versions": {"data_sha256": SNAPSHOT_SHA256, "code_sha256": PROVIDER_SHA256,\n                     "contract_sha256": tools.digest((root / "contracts/vnext/evidence-v1.1.schema.json").read_bytes())},\n        "raw_result_json": raw_json, "raw_result_sha256": tools.digest(raw_json),\n    }\n    tools.validate_evidence(result, tools._catalog(root), root)\n    return result\n\n\ndef consume_health(provider: Any, request: dict[str, Any], request_id: str, root: Path) -> dict[str, Any]:\n    catalog, health, r4 = _pinned(provider)\n    request = _request(request, catalog)\n    if request.get("snapshot_id", SNAPSHOT_ID) != SNAPSHOT_ID:\n        raise tools.ContractViolation("health:wrong_consumer_for_stop_only")\n    raw = _validate_health(provider.plan_visit(request), request, catalog, health, r4, provider, root)\n    normalized = raw["normalized_request"]\n    status = {"ok": "valid", "no_feasible_journey": "no_data", "unknown": "error", "unsupported": "unsupported", "error": "error"}[raw["status"]]\n    claims: list[dict[str, Any]] = []\n    if status == "valid":\n        _claims(raw, "", tools._catalog(root), claims)\n    return _envelope(raw, request, normalized, request_id, claims, [{"index": 0, "status": raw["status"], "error": raw["error"]}], status, None if status == "valid" else _error(raw), root)\n\n\ndef consume_compare(provider: Any, requests: list[dict[str, Any]], request_id: str, root: Path) -> dict[str, Any]:\n    if type(requests) is not list or not 2 <= len(requests) <= 4:\n        raise tools.ContractViolation("health:comparison_requires_2_to_4")\n    catalog, health, r4 = _pinned(provider)\n    normalized = [_request(request, catalog) for request in requests]\n    raw = provider.compare_visits(normalized)\n    if raw.get("schema_version") != VERSION or raw.get("status") != "ok" or type(raw.get("results")) is not list or len(raw["results"]) != len(normalized) or type(raw.get("comparisons")) is not list or len(raw["comparisons"]) != len(normalized) * (len(normalized) - 1) // 2 or raw.get("error") is not None:\n        raise tools.ContractViolation("health:comparison_shape")\n    r4_snapshot = mobility_adapter._capabilities(provider.r4)\n    for item, request in zip(raw["results"], normalized):\n        if request.get("snapshot_id", SNAPSHOT_ID) == R4_SNAPSHOT_ID:\n            mobility_adapter._validate_result(item, request, r4_snapshot)\n        else:\n            _validate_health(item, request, catalog, health, r4, provider, root)\n    pairs = {(i, j) for i in range(len(normalized)) for j in range(i + 1, len(normalized))}\n    seen = set()\n    for comparison in raw["comparisons"]:\n        left, right = comparison["left_index"], comparison["right_index"]\n        if type(left) is not int or type(right) is not int or (left, right) not in pairs or (left, right) in seen:\n            raise tools.ContractViolation("health:comparison_index")\n        seen.add((left, right))\n        a, b = raw["results"][left], raw["results"][right]\n        na, nb = a["normalized_request"], b["normalized_request"]\n        comparable = a["status"] == b["status"] == "ok" and all(na[key] == nb[key] for key in ("origin_id", "destination_id", "date", "snapshot_id", "walking_profile_id", "timezone"))\n        if comparison["comparability"] != ("comparable" if comparable else "not_comparable") or comparison["total_difference_s"] != (b["itinerary"]["total_s"] - a["itinerary"]["total_s"] if comparable else None):\n            raise tools.ContractViolation("health:comparison_delta")\n        if na is not None and nb is not None:\n            changes = [{"field": key, "left": na[key], "right": nb[key]} for key in sorted(na) if na[key] != nb[key]]\n            held = [key for key in sorted(na) if na[key] == nb[key]]\n            if comparison["requested_changes"] != changes or comparison["held_constant"] != held:\n                raise tools.ContractViolation("health:comparison_parameters")\n    if seen != pairs:\n        raise tools.ContractViolation("health:missing_comparison")\n    tools._finite(raw)\n    claims: list[dict[str, Any]] = []\n    source_catalog = tools._catalog(root)\n    for index, item in enumerate(raw["results"]):\n        if item["status"] == "ok" and item["schema_version"] == VERSION:\n            _claims(raw, f"/results/{index}", source_catalog, claims)\n        elif item["status"] == "ok":\n            mobility_adapter._claim(raw, f"/results/{index}/itinerary/total_s", item["itinerary"]["total_s"], item["normalized_request"]["date"], claims, "total_s")\n    for index, comparison in enumerate(raw["comparisons"]):\n        if comparison["comparability"] == "comparable":\n            _claim(raw, f"/comparisons/{index}/total_difference_s", "s", ["GTFS", "HEALTH_REGISTRY", "OSM", "MODEL", "USER", "MODEL_DEFAULTS", "DERIVED"], source_catalog, claims)\n    args = {"requests": normalized}\n    outcomes = [{"index": index, "status": item["status"], "error": item["error"]} for index, item in enumerate(raw["results"])]\n    return _envelope(raw, args, args, request_id, claims, outcomes, "valid", None, root)\n'}
_W1_TEMPDIR = None
_W1_BOUND_ROOT = None

def _ensure_w1_runtime(root):
    global _W1_TEMPDIR, _W1_BOUND_ROOT
    archive_path = root / 'datos_preparados/vnext/w1_r6_runtime.zip'
    if not archive_path.is_file():
        raise ContractViolation("mobility:pinned_package_missing")
    raw = archive_path.read_bytes()
    if digest(raw) != _W1_PACKAGE_SHA256:
        raise ContractViolation("mobility:pinned_package_sha_mismatch")
    if _W1_TEMPDIR is not None:
        if root != _W1_BOUND_ROOT:
            raise ContractViolation("mobility:runtime_root_changed")
        return
    existing = _w1_sys.modules.get("prototypes")
    if existing is not None:
        raise ContractViolation("mobility:unverified_preloaded_provider")
    temp = _w1_tempfile.TemporaryDirectory(prefix="g360-w1-r6-")
    with _w1_zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if sum(item.file_size for item in members) > 2_000_000:
            raise ContractViolation("mobility:archive_too_large")
        for item in members:
            part = _W1PurePath(item.filename)
            if part.is_absolute() or ".." in part.parts or "\\" in item.filename:
                raise ContractViolation("mobility:unsafe_archive_path")
        archive.extractall(temp.name)
    _w1_sys.path.insert(0, temp.name)
    for name, source in _W1_HELPERS.items():
        module = _w1_types.ModuleType(name)
        module.__file__ = "<verified W2 bundled " + name + ">"
        _w1_sys.modules[name] = module
        exec(compile(source, module.__file__, "exec"), module.__dict__)
    _W1_TEMPDIR = temp
    _W1_BOUND_ROOT = root


"""R16 public presentation delta; appended to the immutable R15 tools module.

No provider execution, data, argument validation or arithmetic is replaced.
Names supplied by that module are intentionally resolved only in the bundle.
"""


def _duration_hms(seconds):
    if type(seconds) is not int or not 0 <= seconds < 86400:
        raise ContractViolation("presentation:invalid_duration")
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours} h {minutes} min {seconds} s"


def _civil_clock(seconds):
    if type(seconds) is not int or not 0 <= seconds < 86400:
        raise ContractViolation("presentation:invalid_civil_clock")
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _time_summary(result):
    itinerary = result["itinerary"]
    start, end, total = (itinerary[key] for key in ("start_s", "end_s", "total_s"))
    components = result["components_s"]
    if any(type(value) is not int for value in (start, end, total)):
        raise ContractViolation("presentation:non_integer_scope")
    if type(components) is not dict or not components or any(
        type(value) is not int or value < 0 for value in components.values()
    ):
        raise ContractViolation("presentation:invalid_components")
    if end - start != total or sum(components.values()) != total:
        raise ContractViolation("presentation:inconsistent_total")
    initial = components.get("initial_wait_s")
    if type(initial) is not int or initial < 0:
        raise ContractViolation("presentation:invalid_initial_wait")
    # The provider's departure string is retained, never used to derive scope.
    departure = itinerary["outbound"]["departure_time"]
    if _civil_clock(start + initial) != departure:
        raise ContractViolation("presentation:initial_wait_scope_mismatch")
    return {
        "scope": result["scope"], "scope_start_s": start, "scope_end_s": end,
        "scope_start_clock": _civil_clock(start), "scope_end_clock": _civil_clock(end),
        "total_s": total, "total_hms": _duration_hms(total), "initial_wait_s": initial,
    }


def _mobility_view(raw, root, arguments):
    view = _r15_mobility_view(raw, root, arguments)
    scenarios = raw["results"] if "results" in raw else [raw]
    for result, projected in zip(scenarios, view["scenarios"], strict=True):
        if result["status"] == "ok":
            projected["time_summary"] = _time_summary(result)
    return view


def _mobility_catalog_view(root):
    view = _r15_mobility_catalog_view(root)
    if view is None:
        return None
    defaults = view.pop("provider_defaults")
    for key in ("contract_scope", "public_contract_version", "contract_version", "engine_contract", "defaults_policy"):
        view.pop(key, None)
    view["modelling_assumptions"] = {
        "arrival_margin_minutes": defaults["arrival_margin_minutes"],
        "boarding_margin_minutes": defaults["boarding_margin_minutes"],
        "walking_profile": view["walking_profile"]["label"],
        "meaning": "Supuestos de cálculo; no son decisiones observadas del usuario ni argumentos públicos.",
    }
    return view


def _human_metadata(value):
    """Hide internal identities, not source IDs, real periods or numeric claims.

The original envelope/raw and manifest retain all technical lineage. A model
version label is not an observed source period; label it honestly as such.
"""
    if type(value) is dict:
        hidden = {"versions", "snapshot_id", "contracts", "contract_version", "engine_contract", "contract_scope", "public_contract_version"}
        return {key: _human_metadata(child) for key, child in value.items()
                if key not in hidden and "sha256" not in key}
    if type(value) is list:
        return [_human_metadata(child) for child in value
                if not (type(child) is dict and child.get("field") == "snapshot_id")]
    if type(value) is str:
        for old, new in (
            ("R5.1", "supuesto del modelo de paseo, no periodo observado"),
            ("Defaults applied by provider_r6; not observed human choices.", "Márgenes y perfil aplicados como supuestos del cálculo, no elecciones humanas observadas."),
            ("Only fields explicitly supplied by the caller; no provider defaults.", "Campos recibidos en la consulta; no incluye los supuestos aplicados por el cálculo."),
        ):
            value = value.replace(old, new)
    return value


def _public_result(evidence, root):
    return canonical(_human_metadata(strict_loads(_r15_public_result(evidence, root))))
