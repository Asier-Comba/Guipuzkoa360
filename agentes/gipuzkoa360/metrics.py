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
