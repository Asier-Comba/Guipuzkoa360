"""Bundle autocontenido generado; editar los módulos fuente, no este archivo."""

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
        raise DataContractError('missing_columns', f'{filename} no contiene columnas requeridas: {', '.join(missing)}.', sorted(mapping))

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
                        raise DataContractError('invalid_population', f'{population_field} no puede ser negativo en la fila {row['_row_number']}.')
                for age in ('65', '75'):
                    count_key, pct_key = (f'population_{age}_plus', f'pct_{age}_plus')
                    count, pct = (row.get(count_key), row.get(pct_key))
                    if pct is not None and (not 0 <= pct <= 100):
                        raise DataContractError('invalid_percentage', f'{pct_key} debe estar entre 0 y 100 en la fila {row['_row_number']}.')
                    if count is not None and total is not None and (count > total):
                        raise DataContractError('invalid_population', f'{count_key} supera population_total en la fila {row['_row_number']}.')
                    if pct is None and count is not None and (total not in (None, 0)):
                        row[pct_key] = 100.0 * count / total
                        self.warnings.append(f'{pct_key} calculado a partir de recuento y población total.')
                    if count is None and pct is None:
                        self.warnings.append(f'Sin métrica >= {age} para {row.get('municipality_name')} ({row.get('reference_period')}).')
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
                    raise DataContractError('invalid_coordinates', f'Coordenadas inválidas para {row.get('service_id')}.')
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
    aliases = {'65': {'65', '65+', '>=65'}, '75': {'75', '75+', '>=75'}}
    for canonical, choices in aliases.items():
        if compact in choices:
            return canonical
    raise DataContractError('invalid_age_group', f'Grupo de edad no reconocido: {value!r}.', ['65', '65+', '≥65', '>=65', '75', '75+', '≥75', '>=75'])

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
        if measure not in {'percentage', 'count'}:
            raise DataContractError('invalid_measure', 'La medida debe ser percentage o count.', ['percentage', 'count'])
        return (f'pct_{age}_plus' if measure == 'percentage' else f'population_{age}_plus', age)

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
            raise DataContractError('missing_demography', f'No hay demografía para {municipality_row['municipality_name']} en {selected}.')
        demo = matches[0]
        service_rows = [row for row in self.repo.services() if row.get('municipality_code') == code]
        categories: dict[str, int] = {}
        for row in service_rows:
            category = row['service_category']
            categories[category] = categories.get(category, 0) + 1
        data = {'municipality_code': code, 'municipality_name': municipality_row['municipality_name'], 'population_total': demo.get('population_total'), 'population_65_plus': demo.get('population_65_plus'), 'population_75_plus': demo.get('population_75_plus'), 'pct_65_plus': demo.get('pct_65_plus'), 'pct_75_plus': demo.get('pct_75_plus'), 'services_in_municipality': categories, 'service_indicators': {category: {'registered_service_count': municipality_row.get(f'services_{category}'), 'rate_per_10000_65_plus': municipality_row.get(f'{category}_per_10000_65_plus'), 'rate_per_10000_75_plus': municipality_row.get(f'{category}_per_10000_75_plus'), 'nearest_distance_m': municipality_row.get(f'distance_to_nearest_{category}_m')} for category in ('primary_care', 'hospital', 'mental_health', 'other_health')}, 'metrics_reference_period': municipality_row.get('metrics_reference_period')}
        used = [demo] + service_rows
        return ResultEnvelope(question=f'Resumen territorial de {municipality_row['municipality_name']}', filters={'municipality_code': code, 'period': selected}, period=selected, metric='territorial_summary', unit='varias; ver cada campo', rows_used=len(used), data=[data], method='Selección por código municipal; recuento de registros por categoría; tasas por 10.000 personas del grupo de edad y mínima distancia euclídea EPSG:25830 desde el punto representativo municipal.', sources=self._sources(used), warnings=list(dict.fromkeys(self.repo.warnings)), limitations=['La presencia de un servicio no acredita capacidad, horario, calidad ni acceso real.', 'Los periodos de demografía y servicios pueden ser distintos; se muestran en las fuentes.']).to_dict()

    def envejecimiento(self, age_group: str='65', measure: str='percentage', period: str | None=None, top_n: int=10) -> dict[str, Any]:
        metric, age = self._age_fields(age_group, measure)
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
        return ResultEnvelope(question=f'Envejecimiento de población >= {age}', filters={'age_group': age, 'measure': measure, 'period': selected, 'top_n': int(top_n)}, period=selected, metric=metric, unit='% de población' if measure == 'percentage' else 'personas', rows_used=len(available), data=data, method=f'Orden descendente de {metric}; empates por nombre municipal.', sources=self._sources(available), warnings=warnings, limitations=['El indicador describe estructura demográfica; no explica sus causas.']).to_dict()

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
