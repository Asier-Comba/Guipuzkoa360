"""Cálculos deterministas del proyecto."""

from __future__ import annotations

import math
from typing import Any, Iterable


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def percentile_rank(values: Iterable[float], value: float) -> float:
    ordered = sorted(values)
    if len(ordered) <= 1:
        return 1.0
    below = sum(item < value for item in ordered)
    equal = sum(item == value for item in ordered)
    return (below + (equal - 1) / 2) / (len(ordered) - 1)


def quantile(values: Iterable[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("No hay valores para calcular el cuantil.")
    position = (len(ordered) - 1) * q
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def nearest_service(
    latitude: float,
    longitude: float,
    services: list[dict[str, Any]],
) -> tuple[float | None, dict[str, Any] | None]:
    if not services:
        return None, None
    pairs = [
        (haversine_km(latitude, longitude, item["latitude"], item["longitude"]), item)
        for item in services
    ]
    return min(pairs, key=lambda pair: pair[0])


def nearest_service_projected(
    easting_m: float,
    northing_m: float,
    services: list[dict[str, Any]],
) -> tuple[float | None, dict[str, Any] | None]:
    """Distancia euclídea en EPSG:25830, en metros."""
    projected = [
        item for item in services
        if item.get("easting_m") is not None and item.get("northing_m") is not None
    ]
    if not projected:
        return None, None
    pairs = [
        (math.hypot(item["easting_m"] - easting_m, item["northing_m"] - northing_m), item)
        for item in projected
    ]
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
    m = a * (
        (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * phi
        - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * math.sin(2 * phi)
        + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * math.sin(4 * phi)
        - (35 * e2**3 / 3072) * math.sin(6 * phi)
    )
    easting = 500000 + k0 * n * (
        aa + (1 - t + c) * aa**3 / 6 + (5 - 18 * t + t**2 + 72 * c - 58 * ep2) * aa**5 / 120
    )
    northing = k0 * (
        m + n * math.tan(phi) * (
            aa**2 / 2
            + (5 - t + 9 * c + 4 * c**2) * aa**4 / 24
            + (61 - 58 * t + t**2 + 600 * c - 330 * ep2) * aa**6 / 720
        )
    )
    return easting, northing
