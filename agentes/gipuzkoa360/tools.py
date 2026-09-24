"""Siete herramientas deterministas para el coordinador GIPUZKOA 360."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

try:
    from studio import tool
except ImportError:  # Permite pruebas locales sin el runtime del portal.
    def tool(function: Callable[..., Any]) -> Callable[..., Any]:
        return function

try:
    from .data_access import DataRepository
    from .metrics import nearest_service, percentile_rank, quantile
    from .schemas import DataContractError, ResultEnvelope
except ImportError:  # Studio ejecuta main.py y tools.py desde la carpeta del agente.
    from data_access import DataRepository
    from metrics import nearest_service, percentile_rank, quantile
    from schemas import DataContractError, ResultEnvelope


def _default_data_dir() -> Path:
    configured = os.environ.get("GIPUZKOA360_DATA_DIR")
    if configured:
        return Path(configured)
    workspace_path = Path("datos_preparados")
    if workspace_path.exists():
        return workspace_path
    return Path(__file__).resolve().parents[2] / "datos_preparados"


def _json(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, sort_keys=True)


def _safe(operation: Callable[[], dict[str, Any]]) -> str:
    try:
        return _json(operation())
    except DataContractError as exc:
        return _json(exc.as_result())
    except (ValueError, TypeError) as exc:
        return _json(
            {
                "status": "error",
                "error_code": "invalid_request",
                "message": str(exc),
                "available_options": [],
            }
        )


class TerritorialAnalysis:
    def __init__(self, repository: DataRepository) -> None:
        self.repo = repository

    @staticmethod
    def _age_fields(age_group: str, measure: str = "percentage") -> tuple[str, str]:
        age = str(age_group).replace("≥", "").replace("+", "").strip()
        if age not in {"65", "75"}:
            raise DataContractError("invalid_age_group", "El grupo de edad debe ser 65 o 75.", ["65", "75"])
        if measure not in {"percentage", "count"}:
            raise DataContractError(
                "invalid_measure", "La medida debe ser percentage o count.", ["percentage", "count"]
            )
        return (f"pct_{age}_plus" if measure == "percentage" else f"population_{age}_plus", age)

    def _demography_for_period(self, period: str | None) -> tuple[str, list[dict[str, Any]]]:
        selected = self.repo.choose_period(period)
        rows = [row for row in self.repo.demography() if str(row.get("reference_period")) == selected]
        return selected, rows

    def _sources(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return self.repo.source_details(row.get("source_id") for row in rows)

    def resumen(self, municipality: str, period: str | None = None) -> dict[str, Any]:
        selected, demo_rows = self._demography_for_period(period)
        municipality_row = self.repo.municipality_lookup(municipality)
        code = municipality_row["municipality_code"]
        matches = [row for row in demo_rows if row.get("municipality_code") == code]
        if not matches:
            raise DataContractError(
                "missing_demography", f"No hay demografía para {municipality_row['municipality_name']} en {selected}."
            )
        demo = matches[0]
        service_rows = [row for row in self.repo.services() if row.get("municipality_code") == code]
        categories: dict[str, int] = {}
        for row in service_rows:
            category = row["service_category"]
            categories[category] = categories.get(category, 0) + 1
        data = {
            "municipality_code": code,
            "municipality_name": municipality_row["municipality_name"],
            "population_total": demo.get("population_total"),
            "population_65_plus": demo.get("population_65_plus"),
            "population_75_plus": demo.get("population_75_plus"),
            "pct_65_plus": demo.get("pct_65_plus"),
            "pct_75_plus": demo.get("pct_75_plus"),
            "services_in_municipality": categories,
        }
        used = [demo] + service_rows
        return ResultEnvelope(
            question=f"Resumen territorial de {municipality_row['municipality_name']}",
            filters={"municipality_code": code, "period": selected},
            period=selected,
            metric="territorial_summary",
            unit="varias; ver cada campo",
            rows_used=len(used),
            data=[data],
            method="Selección por código municipal; recuento de servicios por categoría.",
            sources=self._sources(used),
            warnings=list(dict.fromkeys(self.repo.warnings)),
            limitations=[
                "La presencia de un servicio no acredita capacidad, horario, calidad ni acceso real.",
                "Los periodos de demografía y servicios pueden ser distintos; se muestran en las fuentes.",
            ],
        ).to_dict()

    def envejecimiento(
        self,
        age_group: str = "65",
        measure: str = "percentage",
        period: str | None = None,
        top_n: int = 10,
    ) -> dict[str, Any]:
        metric, age = self._age_fields(age_group, measure)
        if not 1 <= int(top_n) <= 100:
            raise DataContractError("invalid_top_n", "top_n debe estar entre 1 y 100.")
        selected, rows = self._demography_for_period(period)
        available = [row for row in rows if row.get(metric) is not None]
        omitted = len(rows) - len(available)
        if not available:
            raise DataContractError("missing_metric", f"No hay valores disponibles para {metric} en {selected}.")
        ordered = sorted(available, key=lambda row: (-row[metric], row["municipality_name"]))[: int(top_n)]
        data = [
            {
                "rank": rank,
                "municipality_code": row["municipality_code"],
                "municipality_name": row["municipality_name"],
                "value": round(row[metric], 4),
                "source_id": row.get("source_id"),
            }
            for rank, row in enumerate(ordered, start=1)
        ]
        warnings = list(dict.fromkeys(self.repo.warnings))
        if omitted:
            warnings.append(f"Se omitieron {omitted} filas sin {metric}; no se trataron como cero.")
        return ResultEnvelope(
            question=f"Envejecimiento de población >= {age}",
            filters={"age_group": age, "measure": measure, "period": selected, "top_n": int(top_n)},
            period=selected,
            metric=metric,
            unit="% de población" if measure == "percentage" else "personas",
            rows_used=len(available),
            data=data,
            method=f"Orden descendente de {metric}; empates por nombre municipal.",
            sources=self._sources(available),
            warnings=warnings,
            limitations=["El indicador describe estructura demográfica; no explica sus causas."],
        ).to_dict()

    def acceso(
        self,
        service_category: str,
        threshold_km: float = 1.0,
        period: str | None = None,
        municipality_names: list[str] | None = None,
        service_override: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if threshold_km <= 0 or threshold_km > 100:
            raise DataContractError("invalid_threshold", "threshold_km debe ser mayor que 0 y no superar 100.")
        municipalities = self.repo.municipalities()
        if municipality_names:
            selected_codes = {self.repo.municipality_lookup(name)["municipality_code"] for name in municipality_names}
            municipalities = [row for row in municipalities if row["municipality_code"] in selected_codes]
        missing_centroids = [row["municipality_name"] for row in municipalities if row.get("latitude") is None or row.get("longitude") is None]
        municipalities = [row for row in municipalities if row.get("latitude") is not None and row.get("longitude") is not None]
        if not municipalities:
            raise DataContractError(
                "missing_coordinates",
                "No hay coordenadas o centroides municipales para calcular distancia geométrica.",
            )
        all_services = service_override if service_override is not None else self.repo.services()
        services = [row for row in all_services if row.get("service_category", "").casefold() == service_category.casefold()]
        categories = sorted({row["service_category"] for row in all_services})
        if not services:
            raise DataContractError(
                "service_category_not_found", f"No hay servicios de categoría {service_category!r}.", categories
            )
        data: list[dict[str, Any]] = []
        for municipality in municipalities:
            distance, service = nearest_service(
                municipality["latitude"], municipality["longitude"], services
            )
            data.append(
                {
                    "municipality_code": municipality["municipality_code"],
                    "municipality_name": municipality["municipality_name"],
                    "nearest_service_id": service["service_id"] if service else None,
                    "nearest_distance_km": round(distance, 4) if distance is not None else None,
                    "within_threshold": bool(distance is not None and distance <= threshold_km),
                }
            )
        data.sort(key=lambda item: (-item["nearest_distance_km"], item["municipality_name"]))
        warnings = list(dict.fromkeys(self.repo.warnings))
        if missing_centroids:
            warnings.append("Municipios omitidos por falta de coordenadas: " + ", ".join(missing_centroids))
        service_periods = sorted({str(row.get("reference_period")) for row in services if row.get("reference_period")})
        return ResultEnvelope(
            question=f"Acceso geométrico a {service_category}",
            filters={"service_category": service_category, "threshold_km": threshold_km, "period_requested": period},
            period=", ".join(service_periods) or None,
            metric="nearest_straight_line_distance",
            unit="km",
            rows_used=len(municipalities) + len(services),
            data=data,
            method="Distancia Haversine desde el centroide/punto municipal al servicio más cercano de la categoría.",
            sources=self._sources(services),
            warnings=warnings,
            limitations=[
                "Es distancia geodésica entre puntos, no distancia de red, tiempo de viaje ni acceso peatonal real.",
                "El centroide municipal no representa dónde vive cada persona.",
                "La existencia registrada no acredita apertura, capacidad ni accesibilidad universal.",
            ],
        ).to_dict()

    def comparar(
        self,
        municipality_names: list[str],
        age_group: str = "65",
        service_category: str | None = None,
        threshold_km: float = 1.0,
        period: str | None = None,
    ) -> dict[str, Any]:
        if not 2 <= len(municipality_names) <= 20:
            raise DataContractError("invalid_municipality_count", "Indica entre 2 y 20 municipios.")
        metric, age = self._age_fields(age_group, "percentage")
        selected, demo_rows = self._demography_for_period(period)
        resolved = [self.repo.municipality_lookup(name) for name in municipality_names]
        codes = {row["municipality_code"] for row in resolved}
        by_code = {row["municipality_code"]: row for row in demo_rows if row["municipality_code"] in codes}
        missing = [row["municipality_name"] for row in resolved if row["municipality_code"] not in by_code]
        if missing:
            raise DataContractError("missing_demography", "Falta demografía para: " + ", ".join(missing))
        access_by_code: dict[str, dict[str, Any]] = {}
        access_result: dict[str, Any] | None = None
        if service_category:
            access_result = self.acceso(service_category, threshold_km, selected, municipality_names)
            access_by_code = {row["municipality_code"]: row for row in access_result["data"]}
        data = []
        for municipality in resolved:
            demo = by_code[municipality["municipality_code"]]
            item = {
                "municipality_code": municipality["municipality_code"],
                "municipality_name": municipality["municipality_name"],
                metric: demo.get(metric),
                "population_total": demo.get("population_total"),
                "source_id": demo.get("source_id"),
            }
            item.update(access_by_code.get(municipality["municipality_code"], {}))
            data.append(item)
        sources = self._sources([by_code[code] for code in codes])
        if access_result:
            sources = list({item.get("source_id", str(index)): item for index, item in enumerate(sources + access_result["sources"])}.values())
        return ResultEnvelope(
            question="Comparación municipal",
            filters={
                "municipalities": [row["municipality_name"] for row in resolved],
                "age_group": age,
                "service_category": service_category,
                "threshold_km": threshold_km if service_category else None,
            },
            period=selected,
            metric=metric + (" + nearest_straight_line_distance" if service_category else ""),
            unit="% y km" if service_category else "%",
            rows_used=len(data),
            data=data,
            method="Selección por código municipal y comparación campo a campo; sin agregación opaca.",
            sources=sources,
            warnings=list(dict.fromkeys(self.repo.warnings)),
            limitations=(access_result or {}).get("limitations", []) + ["La comparación no demuestra causalidad."],
        ).to_dict()

    def coincidencia(
        self,
        service_category: str,
        age_group: str = "65",
        threshold_km: float = 1.0,
        period: str | None = None,
        quantile_threshold: float = 0.75,
    ) -> dict[str, Any]:
        if not 0.5 <= quantile_threshold <= 0.95:
            raise DataContractError("invalid_quantile", "quantile_threshold debe estar entre 0.5 y 0.95.")
        metric, age = self._age_fields(age_group, "percentage")
        selected, demo_rows = self._demography_for_period(period)
        access = self.acceso(service_category, threshold_km, selected)
        by_code = {row["municipality_code"]: row for row in demo_rows if row.get(metric) is not None}
        joined = []
        for row in access["data"]:
            demo = by_code.get(row["municipality_code"])
            if demo:
                joined.append({**row, metric: demo[metric], "age_source_id": demo.get("source_id")})
        if not joined:
            raise DataContractError("no_joined_rows", "No hay municipios con ambas métricas disponibles.")
        age_values = [row[metric] for row in joined]
        distance_values = [row["nearest_distance_km"] for row in joined]
        age_cut = quantile(age_values, quantile_threshold)
        distance_cut = quantile(distance_values, quantile_threshold)
        for row in joined:
            row["age_percentile_rank"] = round(percentile_rank(age_values, row[metric]), 4)
            row["distance_percentile_rank"] = round(
                percentile_rank(distance_values, row["nearest_distance_km"]), 4
            )
            row["meets_age_criterion"] = row[metric] >= age_cut
            row["meets_access_criterion"] = row["nearest_distance_km"] >= distance_cut
            row["highlighted"] = row["meets_age_criterion"] and row["meets_access_criterion"]
        joined.sort(
            key=lambda row: (
                not row["highlighted"],
                -row[metric],
                -row["nearest_distance_km"],
                row["municipality_name"],
            )
        )
        used_demo = [by_code[row["municipality_code"]] for row in joined]
        sources = self._sources(used_demo) + access["sources"]
        deduped = {str(item.get("source_id", item)): item for item in sources}
        return ResultEnvelope(
            question=f"Coincidencia de envejecimiento >= {age} y peor acceso a {service_category}",
            filters={
                "age_group": age,
                "service_category": service_category,
                "threshold_km": threshold_km,
                "period": selected,
                "quantile_threshold": quantile_threshold,
            },
            period=selected,
            metric=f"{metric} + nearest_straight_line_distance",
            unit="% y km",
            rows_used=len(joined),
            data=joined,
            method=(
                f"Cruce por código municipal. Se destacan valores >= cuantil {quantile_threshold:.2f} "
                f"en ambas métricas (cortes: {age_cut:.4f}% y {distance_cut:.4f} km). "
                "Se muestran ambos componentes y no se usa una puntuación compuesta."
            ),
            sources=list(deduped.values()),
            warnings=list(dict.fromkeys(self.repo.warnings + access["warnings"])),
            limitations=access["limitations"]
            + [
                "La coincidencia estadística no demuestra causalidad ni identifica necesidades individuales.",
                "Los resultados dependen del cuantil, grupo de edad, categoría y periodo elegidos.",
            ],
        ).to_dict()

    def escenario(
        self,
        action: str,
        service_category: str,
        threshold_km: float = 1.0,
        period: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        service_id: str | None = None,
        new_threshold_km: float | None = None,
    ) -> dict[str, Any]:
        action = action.strip().casefold()
        services = list(self.repo.services())
        changed: dict[str, Any]
        scenario_services = list(services)
        scenario_threshold = threshold_km
        if action == "add_service":
            if latitude is None or longitude is None or not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                raise DataContractError("invalid_coordinates", "add_service requiere latitud y longitud válidas.")
            hypothetical_id = service_id or "HYPOTHETICAL_SERVICE"
            scenario_services.append(
                {
                    "service_id": hypothetical_id,
                    "service_name": "Servicio hipotético",
                    "service_category": service_category,
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "reference_period": "escenario",
                    "source_id": "SCENARIO_INPUT",
                }
            )
            changed = {"action": action, "service_id": hypothetical_id, "latitude": latitude, "longitude": longitude}
        elif action == "remove_service":
            if not service_id:
                raise DataContractError("service_id_required", "remove_service requiere service_id.")
            if not any(row["service_id"] == service_id for row in scenario_services):
                raise DataContractError(
                    "service_not_found", f"No existe el servicio {service_id}.", [row["service_id"] for row in services]
                )
            scenario_services = [row for row in scenario_services if row["service_id"] != service_id]
            changed = {"action": action, "service_id": service_id}
        elif action == "change_threshold":
            if new_threshold_km is None:
                raise DataContractError("threshold_required", "change_threshold requiere new_threshold_km.")
            scenario_threshold = float(new_threshold_km)
            changed = {"action": action, "threshold_km": threshold_km, "new_threshold_km": scenario_threshold}
        else:
            raise DataContractError(
                "invalid_scenario", "Escenario no compatible.", ["add_service", "remove_service", "change_threshold"]
            )
        baseline = self.acceso(service_category, threshold_km, period, service_override=services)
        scenario = self.acceso(
            service_category, scenario_threshold, period, service_override=scenario_services
        )
        baseline_by_code = {row["municipality_code"]: row for row in baseline["data"]}
        differences = []
        for item in scenario["data"]:
            original = baseline_by_code[item["municipality_code"]]
            before, after = original["nearest_distance_km"], item["nearest_distance_km"]
            absolute = after - before
            differences.append(
                {
                    "municipality_code": item["municipality_code"],
                    "municipality_name": item["municipality_name"],
                    "baseline_distance_km": before,
                    "scenario_distance_km": after,
                    "difference_absolute_km": round(absolute, 4),
                    "difference_relative_pct": round(100 * absolute / before, 4) if before else None,
                    "baseline_within_threshold": original["within_threshold"],
                    "scenario_within_threshold": item["within_threshold"],
                }
            )
        result = ResultEnvelope(
            question=f"Escenario {action} para {service_category}",
            filters={"period": period, "service_category": service_category},
            period=scenario.get("period"),
            metric="nearest_straight_line_distance",
            unit="km",
            rows_used=scenario["rows_used"],
            data=differences,
            method="Recalculo determinista del mismo indicador antes y después del cambio hipotético.",
            sources=baseline["sources"],
            warnings=list(dict.fromkeys(baseline["warnings"] + scenario["warnings"])),
            limitations=scenario["limitations"]
            + [
                "Es un contrafactual analítico, no una predicción de uso, conducta, coste o impacto social.",
                "No constituye una recomendación de ubicación ni una decisión administrativa.",
            ],
        ).to_dict()
        result["scenario"] = {
            "baseline": {"threshold_km": threshold_km, "service_count": len(services)},
            "scenario": {"threshold_km": scenario_threshold, "service_count": len(scenario_services)},
            "changed_parameters": changed,
            "affected_metric": "nearest_straight_line_distance / within_threshold",
            "assumptions": ["El resto de datos permanece constante.", "Las coordenadas representan puntos válidos."],
            "limitations": result["limitations"],
        }
        return result

    def fuente(self, source_id: str | None = None) -> dict[str, Any]:
        all_sources = self.repo.metadata().get("sources", [])
        if source_id:
            matches = [item for item in all_sources if str(item.get("source_id")) == str(source_id)]
            if not matches:
                available = [str(item.get("source_id")) for item in all_sources]
                raise DataContractError("source_not_found", f"No hay metadatos para {source_id}.", available)
            data = matches
        else:
            data = all_sources
        warnings = list(dict.fromkeys(self.repo.warnings))
        if not data:
            warnings.append("No hay metadatos de fuente disponibles; no se debe inventar procedencia.")
        return ResultEnvelope(
            question="Consulta de procedencia",
            filters={"source_id": source_id},
            metric="source_metadata",
            unit="no aplica",
            rows_used=len(data),
            data=data,
            method="Lectura directa de metadata_sources.json.",
            sources=data,
            warnings=warnings,
            limitations=["La ficha de fuente describe procedencia; no valida por sí sola la calidad del dato."],
        ).to_dict()


def _analysis() -> TerritorialAnalysis:
    return TerritorialAnalysis(DataRepository(_default_data_dir()))


@tool
def obtener_resumen_territorial(municipio: str, periodo: str | None = None) -> str:
    """Resume demografía y servicios de un municipio; no interpreta ausencia como cero."""
    return _safe(lambda: _analysis().resumen(municipio, periodo))


@tool
def comparar_municipios(
    municipios: list[str],
    grupo_edad: str = "65",
    categoria_servicio: str | None = None,
    umbral_km: float = 1.0,
    periodo: str | None = None,
) -> str:
    """Compara 2-20 municipios con porcentaje de edad y, opcionalmente, distancia a servicios."""
    return _safe(lambda: _analysis().comparar(municipios, grupo_edad, categoria_servicio, umbral_km, periodo))


@tool
def analizar_envejecimiento(
    grupo_edad: str = "65",
    medida: str = "percentage",
    periodo: str | None = None,
    top_n: int = 10,
) -> str:
    """Calcula ranking de población >=65 o >=75 por porcentaje o recuento."""
    return _safe(lambda: _analysis().envejecimiento(grupo_edad, medida, periodo, top_n))


@tool
def analizar_acceso_servicios(
    categoria_servicio: str,
    umbral_km: float = 1.0,
    periodo: str | None = None,
    municipios: list[str] | None = None,
) -> str:
    """Calcula distancia recta centroide-servicio; no devuelve tiempos de viaje ni acceso real."""
    return _safe(lambda: _analysis().acceso(categoria_servicio, umbral_km, periodo, municipios))


@tool
def analizar_coincidencia(
    categoria_servicio: str,
    grupo_edad: str = "65",
    umbral_km: float = 1.0,
    periodo: str | None = None,
    cuantil: float = 0.75,
) -> str:
    """Cruza envejecimiento y distancia mostrando ambos componentes y criterios de corte."""
    return _safe(lambda: _analysis().coincidencia(categoria_servicio, grupo_edad, umbral_km, periodo, cuantil))


@tool
def simular_escenario(
    accion: str,
    categoria_servicio: str,
    umbral_km: float = 1.0,
    periodo: str | None = None,
    latitud: float | None = None,
    longitud: float | None = None,
    service_id: str | None = None,
    nuevo_umbral_km: float | None = None,
) -> str:
    """Recalcula un contrafactual: add_service, remove_service o change_threshold."""
    return _safe(
        lambda: _analysis().escenario(
            accion,
            categoria_servicio,
            umbral_km,
            periodo,
            latitud,
            longitud,
            service_id,
            nuevo_umbral_km,
        )
    )


@tool
def consultar_fuente(source_id: str | None = None) -> str:
    """Devuelve procedencia, periodo, institución, unidad, licencia y limitaciones disponibles."""
    return _safe(lambda: _analysis().fuente(source_id))


TOOLS = [
    obtener_resumen_territorial,
    comparar_municipios,
    analizar_envejecimiento,
    analizar_acceso_servicios,
    analizar_coincidencia,
    simular_escenario,
    consultar_fuente,
]
