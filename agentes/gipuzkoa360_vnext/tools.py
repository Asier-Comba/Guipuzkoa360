"""Strict evidence adapter around the unchanged territorial runtime.

The package builder replaces the import below with the same core source in a
portal-only generated bundle. No territorial calculations are implemented here.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
import os
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

try:
    from agentes.gipuzkoa360 import tools as territorial
except ImportError:  # Generated Studio bundle supplies this name.
    territorial = None  # type: ignore[assignment]


VERSION = "1.1.0"
CAPABILITY_VERSION = "1.1.0"
MAX_EVIDENCE_BYTES = 120_000
MAX_PUBLIC_BYTES = 120_000
DEFAULT_PUBLIC_ENTITIES = 10
SHA256_KEYS = {"data_sha256", "code_sha256", "contract_sha256", "arguments_sha256", "raw_result_sha256"}
EVIDENCE_KEYS = {
    "schema_version", "request_id", "capability_id", "normalized_input", "effective_request", "execution",
    "status", "outcomes", "claims", "method", "assumptions", "limitations", "error", "versions",
    "raw_result_json", "raw_result_sha256",
}
CAPABILITY_KEYS = {
    "schema_version", "id", "description", "derivation", "enabled", "validation_status",
    "handler", "input_fields", "required_data", "coverage", "source_ids",
    "allowed_transformations", "preconditions", "precondition_checks", "validation_evidence", "restrictions", "semantic_limits",
}
RESULT_KEYS = {
    "status", "question", "filters", "period", "metric", "unit", "rows_used", "data",
    "method", "sources", "warnings", "limitations", "summary", "scenario", "detail_level",
}
TERRITORIAL_HANDLERS = {
    "obtener_resumen_territorial", "comparar_municipios", "analizar_envejecimiento",
    "analizar_acceso_servicios", "analizar_coincidencia", "simular_escenario", "consultar_fuente",
}
LOCAL_HANDLERS = {"consultar_capacidades"}
MOBILITY_HANDLERS = {"plan_visit"}


class ContractViolation(ValueError):
    pass


class ObservedTransportError(RuntimeError):
    """Only an explicitly observed transport failure may use this origin."""


def _reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractViolation(f"duplicate_key:{key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ContractViolation(f"non_finite:{value}")


def strict_loads(raw: str) -> Any:
    value = json.loads(raw, object_pairs_hook=_reject_duplicate, parse_constant=_reject_constant)
    _finite(value)
    return value


def _finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ContractViolation("non_finite")
    if isinstance(value, dict):
        for child in value.values():
            _finite(child)
    elif isinstance(value, list):
        for child in value:
            _finite(child)


def canonical(value: Any) -> str:
    _finite(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _keys(value: Any, required: set[str], where: str, *, optional: set[str] | None = None) -> dict[str, Any]:
    if type(value) is not dict:
        raise ContractViolation(f"{where}:expected_object")
    missing = required - set(value)
    unexpected = set(value) - required - (optional or set())
    if missing or unexpected:
        raise ContractViolation(f"{where}:missing={sorted(missing)}:unexpected={sorted(unexpected)}")
    return value


def _text(value: Any, where: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if type(value) is not str or not value:
        raise ContractViolation(f"{where}:expected_nonempty_string")


def _strings(value: Any, where: str, *, nonempty: bool = False) -> None:
    if type(value) is not list or (nonempty and not value) or any(type(item) is not str or not item for item in value):
        raise ContractViolation(f"{where}:expected_string_array")


def _hex(value: Any, where: str) -> None:
    if type(value) is not str or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ContractViolation(f"{where}:expected_sha256")


def _workspace_root() -> Path:
    configured = os.environ.get("GIPUZKOA360_VNEXT_ROOT")
    if configured:
        return Path(configured).resolve()
    candidate = Path.cwd().resolve()
    if (candidate / "datos_preparados").is_dir():
        return candidate
    return Path(__file__).resolve().parents[2]


def _catalog(root: Path) -> dict[str, dict[str, Any]]:
    payload = strict_loads((root / "datos_preparados/metadata_sources.json").read_text(encoding="utf-8"))
    if type(payload) is not list:
        raise ContractViolation("source_catalog:expected_array")
    extra = root / "datos_preparados/vnext/mobility_sources.json"
    if extra.is_file():
        additional = strict_loads(extra.read_text(encoding="utf-8"))
        if type(additional) is not list:
            raise ContractViolation("source_catalog:invalid_additional_sources")
        payload += additional
    result = {}
    for item in payload:
        if type(item) is not dict or type(item.get("source_id")) is not str:
            raise ContractViolation("source_catalog:invalid_source")
        if item["source_id"] in result:
            raise ContractViolation("source_catalog:duplicate_source")
        result[item["source_id"]] = item
    return result


def _registry(root: Path) -> list[dict[str, Any]]:
    path = root / "datos_preparados/vnext/capabilities.json"
    payload = strict_loads(path.read_text(encoding="utf-8"))
    _keys(payload, {"schema_version", "capabilities"}, "registry")
    if payload["schema_version"] != CAPABILITY_VERSION or type(payload["capabilities"]) is not list:
        raise ContractViolation("registry:version_or_type")
    catalog = _catalog(root)
    for item in payload["capabilities"]:
        validate_capability(item, root, catalog)
    ids = [item["id"] for item in payload["capabilities"]]
    if len(ids) != len(set(ids)):
        raise ContractViolation("registry:duplicate_capability")
    return payload["capabilities"]


def validate_capability(item: Any, root: Path, catalog: dict[str, Any]) -> None:
    _keys(item, CAPABILITY_KEYS, "capability")
    if item["schema_version"] != CAPABILITY_VERSION:
        raise ContractViolation("capability:version")
    for field in ("id", "description"):
        _text(item[field], f"capability.{field}")
    if item["derivation"] not in {"direct", "derived_exact", "estimated_with_assumptions", "unavailable"}:
        raise ContractViolation("capability:derivation")
    if type(item["enabled"]) is not bool or item["validation_status"] not in {"tested", "pending", "failed"}:
        raise ContractViolation("capability:state")
    if item["enabled"]:
        if item["validation_status"] != "tested" or item["derivation"] == "unavailable":
            raise ContractViolation("capability:unverified_enabled")
        if item["handler"] not in TERRITORIAL_HANDLERS | LOCAL_HANDLERS | MOBILITY_HANDLERS:
            raise ContractViolation("capability:missing_handler")
        if item["handler"] in TERRITORIAL_HANDLERS and not callable(getattr(territorial, item["handler"], None)):
            raise ContractViolation("capability:missing_handler")
        handler = consultar_capacidades if item["handler"] in LOCAL_HANDLERS else plan_visit if item["handler"] in MOBILITY_HANDLERS else getattr(territorial, item["handler"])
        signature = inspect.signature(handler)
        provided = {field["name"] for field in item["input_fields"]}
        expected = set(signature.parameters) - {"detalle", "root"}
        if provided != expected:
            raise ContractViolation("capability:handler_schema_mismatch")
    elif item["handler"] is not None and type(item["handler"]) is not str:
        raise ContractViolation("capability:handler_type")
    if type(item["input_fields"]) is not list:
        raise ContractViolation("capability:input_fields")
    names = set()
    for field in item["input_fields"]:
        _keys(field, {"name", "type", "required", "allowed_values"}, "capability.input_field")
        _text(field["name"], "capability.input_field.name")
        if field["name"] in names or field["type"] not in {"string", "number", "integer", "boolean", "string_array", "object_or_array"} or type(field["required"]) is not bool or type(field["allowed_values"]) is not list:
            raise ContractViolation("capability:bad_input_field")
        names.add(field["name"])
    if type(item["required_data"]) is not list or (item["enabled"] and not item["required_data"]):
        raise ContractViolation("capability:required_data")
    for data in item["required_data"]:
        _keys(data, {"path", "sha256"}, "capability.data")
        _text(data["path"], "capability.data.path")
        _hex(data["sha256"], "capability.data.sha256")
        path = (root / data["path"]).resolve()
        if root not in path.parents or not path.is_file() or digest(path.read_bytes()) != data["sha256"]:
            raise ContractViolation(f"capability:stale_data:{data['path']}")
    coverage = _keys(item["coverage"], {"territory", "periods", "entities", "scope"}, "capability.coverage")
    _text(coverage["territory"], "capability.coverage.territory")
    _text(coverage["scope"], "capability.coverage.scope")
    _strings(coverage["periods"], "capability.coverage.periods")
    if type(coverage["entities"]) is not int or coverage["entities"] < 0:
        raise ContractViolation("capability.coverage.entities")
    if item["enabled"] and coverage["territory"] == "Gipuzkoa":
        municipality_file = root / "datos_preparados/municipios.csv"
        actual_entities = sum(1 for _ in municipality_file.open(encoding="utf-8-sig")) - 1
        if coverage["entities"] != actual_entities:
            raise ContractViolation("capability:false_coverage")
    if coverage["territory"] == "source_catalog" and coverage["entities"] != len([source for source in catalog if not source.startswith(("W1_", "W2_"))]):
        raise ContractViolation("capability:false_catalog_coverage")
    _strings(item["source_ids"], "capability.source_ids", nonempty=item["enabled"])
    if any(source not in catalog for source in item["source_ids"]):
        raise ContractViolation("capability:false_source")
    expected_periods = list(dict.fromkeys(str(catalog[source]["reference_period"]) for source in item["source_ids"])) if item["id"] != "consultar_capacidades" else []
    if item["enabled"] and coverage["periods"] != expected_periods:
        raise ContractViolation("capability:false_period_coverage")
    _strings(item["precondition_checks"], "capability.precondition_checks", nonempty=item["enabled"])
    if item["enabled"] and set(item["precondition_checks"]) != {"required_data_sha256", "handler_signature", "source_catalog", "coverage_count"}:
        raise ContractViolation("capability:unexecuted_precondition")
    if type(item["validation_evidence"]) is not list or (item["enabled"] and not item["validation_evidence"]):
        raise ContractViolation("capability:validation_evidence")
    for proof in item["validation_evidence"]:
        _keys(proof, {"test_file", "test_name", "sha256"}, "capability.validation_evidence")
        _text(proof["test_file"], "capability.validation_evidence.test_file")
        _text(proof["test_name"], "capability.validation_evidence.test_name")
        _hex(proof["sha256"], "capability.validation_evidence.sha256")
        path = (root / proof["test_file"]).resolve()
        if root not in path.parents or not path.is_file() or digest(path.read_bytes()) != proof["sha256"] or f"def {proof['test_name']}(" not in path.read_text(encoding="utf-8"):
            raise ContractViolation("capability:stale_validation_evidence")
    for key in ("allowed_transformations", "preconditions", "restrictions", "semantic_limits"):
        _strings(item[key], f"capability.{key}", nonempty=key == "semantic_limits")


def _validate_arguments(args: Any, capability: dict[str, Any]) -> dict[str, Any]:
    if type(args) is not dict:
        raise ContractViolation("arguments:expected_object")
    fields = {item["name"]: item for item in capability["input_fields"]}
    missing = {name for name, item in fields.items() if item["required"] and name not in args}
    unexpected = set(args) - set(fields)
    if missing or unexpected:
        raise ContractViolation(f"arguments:missing={sorted(missing)}:unexpected={sorted(unexpected)}")
    for name, value in args.items():
        field = fields[name]
        if value is None and not field["required"]:
            continue
        kind = field["type"]
        valid = {
            "string": lambda v: type(v) is str and bool(v),
            "number": lambda v: type(v) in (int, float) and math.isfinite(v),
            "integer": lambda v: type(v) is int,
            "boolean": lambda v: type(v) is bool,
            "string_array": lambda v: type(v) is list and bool(v) and all(type(x) is str and bool(x) for x in v),
            "object_or_array": lambda v: type(v) is dict or type(v) is list and 2 <= len(v) <= 32 and all(type(x) is dict for x in v),
        }[kind](value)
        if not valid or (field["allowed_values"] and value not in field["allowed_values"]):
            raise ContractViolation(f"arguments:{name}:invalid_value")
    return dict(args)


def _repair_once(args: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Use the core's own equivalent aliases once; never guess a new intent."""
    repaired = dict(args)
    notes = []
    normalizers = {
        "categoria_servicio": territorial.normalize_service_category,
        "grupo_edad": territorial.normalize_age_group,
        "accion": territorial.normalize_scenario_action,
    }
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
            notes.append(f"Alias del motor normalizado: {name}={original} → {canonical_value}.")
    if "medida" in repaired and repaired["medida"] is not None:
        original = repaired["medida"]
        try:
            metric, _ = territorial.TerritorialAnalysis._age_fields(repaired.get("grupo_edad", "65"), original)
            canonical_value = "percentage" if metric.startswith("pct_") else "count"
        except ValueError:
            canonical_value = original
        if canonical_value != original:
            repaired["medida"] = canonical_value
            notes.append(f"Alias del motor normalizado: medida={original} → {canonical_value}.")
    return repaired, notes


def _validate_result(raw: Any, catalog: dict[str, Any]) -> dict[str, Any]:
    if type(raw) is not dict:
        raise ContractViolation("tool_result:expected_object")
    if raw.get("status") == "error":
        _keys(raw, {"status", "error_code", "message", "available_options"}, "tool_error")
        _text(raw["error_code"], "tool_error.code")
        _text(raw["message"], "tool_error.message")
        _strings(raw["available_options"], "tool_error.options")
        return raw
    _keys(raw, {"status", "question", "filters", "period", "metric", "unit", "rows_used", "data", "method", "sources", "warnings", "limitations"}, "tool_result", optional=RESULT_KEYS)
    if raw["status"] != "ok" or type(raw["filters"]) is not dict or type(raw["rows_used"]) is not int or raw["rows_used"] < 0 or type(raw["data"]) is not list:
        raise ContractViolation("tool_result:shape")
    for key in ("question", "method"):
        _text(raw[key], f"tool_result.{key}")
    for key in ("metric", "unit"):
        _text(raw[key], f"tool_result.{key}", nullable=True)
    _text(raw["period"], "tool_result.period", nullable=True)
    _strings(raw["warnings"], "tool_result.warnings")
    _strings(raw["limitations"], "tool_result.limitations")
    if type(raw["sources"]) is not list:
        raise ContractViolation("tool_result:sources")
    for source in raw["sources"]:
        if type(source) is not dict or source.get("source_id") not in catalog:
            raise ContractViolation("tool_result:false_source")
    _finite(raw)
    return raw


def _effective_request(handler: Callable[..., Any], arguments: dict[str, Any], root: Path) -> dict[str, Any]:
    """Resolve defaults and municipal identity before accepting tool observations."""
    bound = inspect.signature(handler).bind_partial(**arguments)
    bound.apply_defaults()
    parameters = {key: value for key, value in bound.arguments.items() if key not in {"detalle", "root"}}
    operation = handler.__name__
    codes: list[str] = []
    labels: list[str] = []
    if "municipio" in parameters or parameters.get("municipios") is not None:
        repo = territorial.DataRepository(root / "datos_preparados")
        names = [parameters["municipio"]] if "municipio" in parameters else parameters["municipios"]
        resolved = [repo.municipality_lookup(name) for name in names]
        codes = [item["municipality_code"] for item in resolved]
        labels = [item["municipality_name"] for item in resolved]
        if len(codes) != len(set(codes)):
            raise ContractViolation("request:duplicate_municipality")
    period = parameters.get("periodo")
    if operation in {"obtener_resumen_territorial", "comparar_municipios", "analizar_envejecimiento", "analizar_coincidencia"}:
        period = territorial.DataRepository(root / "datos_preparados").choose_period(period)
    return {"operation": operation, "municipality_codes": codes, "municipality_labels": labels, "effective_period": period, "parameters": parameters, "defaults_applied": sorted(set(parameters) - set(arguments)), "snapshot_id": None, "contracts": {"evidence": VERSION, "capability": CAPABILITY_VERSION}}


def _same(observed: Any, expected: Any, field: str) -> None:
    if type(observed) in (int, float) and type(expected) in (int, float):
        match = float(observed) == float(expected)
    else:
        match = observed == expected
    if not match:
        raise ContractViolation(f"tool_result:request_mismatch:{field}")


def _bind_result_to_arguments(raw: dict[str, Any], effective: dict[str, Any], root: Path) -> None:
    """Every effective parameter must be witnessed, including defaults and entities."""
    if raw["status"] != "ok":
        return
    operation, args, filters = effective["operation"], effective["parameters"], raw["filters"]
    mapping = {
        "grupo_edad": "age_group", "categoria_servicio": "service_category",
        "umbral_km": "threshold_km", "cuantil": "quantile_threshold",
        "top_n": "top_n", "medida": "measure", "source_id": "source_id",
        "pregunta_o_dimension": "pregunta_o_dimension",
    }
    for argument, filter_name in mapping.items():
        if argument not in args or (operation == "simular_escenario" and argument == "umbral_km"):
            continue
        if filter_name not in filters:
            raise ContractViolation(f"tool_result:missing_filter:{filter_name}")
        expected = None if operation == "comparar_municipios" and argument == "umbral_km" and args["categoria_servicio"] is None else args[argument]
        _same(filters[filter_name], expected, argument)
    if operation in {"obtener_resumen_territorial", "analizar_envejecimiento", "analizar_coincidencia"}:
        if "period" not in filters:
            raise ContractViolation("tool_result:missing_filter:period")
        _same(filters["period"], effective["effective_period"], "periodo")
        _same(raw["period"], effective["effective_period"], "result_period")
    elif operation == "analizar_acceso_servicios":
        if "period_requested" not in filters:
            raise ContractViolation("tool_result:missing_filter:period_requested")
        _same(filters["period_requested"], args["periodo"], "periodo")
    elif operation == "simular_escenario":
        if "period" not in filters:
            raise ContractViolation("tool_result:missing_filter:period")
        _same(filters["period"], args["periodo"], "periodo")
    elif operation == "comparar_municipios":
        _same(raw["period"], effective["effective_period"], "result_period")
    expected_codes = set(effective["municipality_codes"])
    if operation == "obtener_resumen_territorial":
        if "municipality_code" not in filters:
            raise ContractViolation("tool_result:missing_filter:municipality_code")
        _same(filters["municipality_code"], effective["municipality_codes"][0], "municipio")
    if operation == "comparar_municipios":
        if "municipalities" not in filters or type(filters["municipalities"]) is not list:
            raise ContractViolation("tool_result:missing_filter:municipalities")
        repo = territorial.DataRepository(root / "datos_preparados")
        observed_codes = [repo.municipality_lookup(name)["municipality_code"] for name in filters["municipalities"]]
        if len(observed_codes) != len(expected_codes) or set(observed_codes) != expected_codes:
            raise ContractViolation("tool_result:request_mismatch:municipios")
    if operation == "analizar_acceso_servicios" and not expected_codes:
        expected_codes = {row["municipality_code"] for row in territorial.DataRepository(root / "datos_preparados").municipalities()}
    if operation in {"obtener_resumen_territorial", "comparar_municipios", "analizar_acceso_servicios"}:
        observed_rows = raw["data"]
        observed_codes = [item.get("municipality_code") for item in observed_rows if type(item) is dict]
        if len(observed_rows) != len(expected_codes) or len(observed_codes) != len(expected_codes) or set(observed_codes) != expected_codes:
            raise ContractViolation("tool_result:request_mismatch:municipality_rows")
        repo = territorial.DataRepository(root / "datos_preparados")
        if any(item.get("municipality_name") != repo.municipality_lookup(item["municipality_code"])["municipality_name"] for item in observed_rows):
            raise ContractViolation("tool_result:request_mismatch:municipality_labels")
    if operation == "simular_escenario":
        scenario = raw.get("scenario")
        if type(scenario) is not dict or type(scenario.get("changed_parameters")) is not dict:
            raise ContractViolation("tool_result:missing_scenario")
        changed = scenario["changed_parameters"]
        action = args["accion"]
        expected = {"action": action}
        if action == "add_service":
            expected.update(service_id=args["service_id"] or "HYPOTHETICAL_SERVICE", latitude=float(args["latitud"]), longitude=float(args["longitud"]))
        elif action == "remove_service":
            expected["service_id"] = args["service_id"]
        elif action == "change_threshold":
            expected.update(threshold_km=float(args["umbral_km"]), new_threshold_km=float(args["nuevo_umbral_km"]))
        if set(changed) != set(expected):
            raise ContractViolation("tool_result:request_mismatch:scenario_fields")
        for key, value in expected.items():
            _same(changed[key], value, key)
        _same(scenario["baseline"]["threshold_km"], args["umbral_km"], "baseline_threshold")
        _same(scenario["scenario"]["threshold_km"], args["nuevo_umbral_km"] if action == "change_threshold" else args["umbral_km"], "scenario_threshold")


def _pointer(raw: Any, pointer: str) -> Any:
    current = raw
    for part in pointer.lstrip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        current = current[int(part)] if type(current) is list else current[part]
    return current


def _claim_sources(field: str, available: set[str]) -> list[str]:
    demo = "EUSTAT_EMH_2025"
    service = "ODE_HEALTH_CENTRES_2026"
    geo = "GEOEUSKADI_MUNICIPIOS_2025"
    if "per_10000" in field:
        wanted = [demo, service]
    elif field.startswith(("population", "pct_", "age_")) or field in {"value", "age_cut_percent"}:
        wanted = [demo]
    elif field.startswith(("distance", "nearest_distance", "baseline_distance", "scenario_distance")) or field.endswith("_m"):
        wanted = [service, geo]
    elif field.startswith(("service", "registered_service")):
        wanted = [service]
    else:
        wanted = sorted(available)
    return wanted if set(wanted) <= available else []


def _claim_period(field: str, source_ids: list[str], catalog: dict[str, Any]) -> str:
    periods = [str(catalog[source]["reference_period"]) for source in source_ids]
    return ";".join(dict.fromkeys(periods))


def _claim_unit(field: str, raw: dict[str, Any]) -> str:
    if field.endswith("_s"):
        return "s"
    if field in {"highlighted_count", "joined_rows"}:
        return "municipios"
    if "per_10000" in field:
        return "registros/10000 personas"
    if field.startswith("pct_") or field.endswith("_percent"):
        return "%"
    if field.endswith("_m") or "distance" in field:
        return "m"
    if field.startswith("population"):
        return "personas"
    if field.endswith("_count") or field.startswith("services_"):
        return "registros"
    if field == "value":
        return str(raw.get("unit") or "unidad declarada")
    return "conteo"


def _source_roles(field: str, sources: list[str]) -> list[dict[str, str]]:
    roles = {
        "EUSTAT_EMH_2025": "denominator" if "per_10000" in field else "demographic_observation",
        "ODE_HEALTH_CENTRES_2026": "numerator" if "per_10000" in field else "service_location",
        "GEOEUSKADI_MUNICIPIOS_2025": "municipal_reference_point",
    }
    def role(source: str) -> str:
        for prefix, label in (("W1_GTFS@", "official_schedule"), ("W2_USER@", "user_parameter"), ("W1_MODEL@", "modelling_assumption"), ("W1_DERIVED@", "derived_network")):
            if source.startswith(prefix):
                return label
        return roles.get(source, "observed_input")
    return [{"source_id": source, "role": role(source)} for source in sources]


def _claim_entity(raw: dict[str, Any], pointer: str) -> tuple[str, str, str]:
    if raw.get("schema_version") == "0.2.0":
        if pointer.startswith("/differences_s/"):
            part = raw["differences_s"][int(pointer.split("/")[2])]
            left, right = part["left_index"], part["right_index"]
            return "comparison", f"{left}->{right}", f"Comparación de escenarios {left} y {right}"
        result = raw["results"][int(pointer.split("/")[2])] if pointer.startswith("/results/") else raw
        request = result.get("normalized_request") or {}
        index_label = f"#{pointer.split('/')[2]}" if pointer.startswith("/results/") else ""
        identity = f"{request.get('origin_id', '?')}->{request.get('destination_id', '?')}@{request.get('date', '?')}T{request.get('appointment_time', '?')}{index_label}"
        return "journey", identity, f"Viaje programado {identity}"
    if pointer.startswith("/summary/"):
        return "municipality_set", "GIPUZKOA_FILTERED", "Municipios incluidos en el cruce"
    if pointer.startswith("/data/"):
        index = int(pointer.split("/")[2])
        row = raw["data"][index]
        if type(row) is dict and type(row.get("municipality_code")) is str and type(row.get("municipality_name")) is str:
            return "municipality", row["municipality_code"], row["municipality_name"]
    return "result", "RESULT_SCOPE", raw.get("question", "Resultado sintético")


def _make_claims(raw: dict[str, Any], catalog: dict[str, Any], root: Path) -> tuple[list[dict[str, Any]], int]:
    # A catalogued source is not evidence that this particular execution used it.
    available = {item["source_id"] for item in raw["sources"]}
    selected: list[tuple[str, str, Any]] = []
    summary = raw.get("summary")
    if type(summary) is dict:
        for key, value in summary.items():
            if type(value) in (int, float) and math.isfinite(value):
                selected.append((f"/summary/{key}", key, value))
    for index, row in enumerate(raw.get("data", [])):
        if type(row) is not dict:
            raise ContractViolation("tool_result:data_row")
        if "highlighted" in row and not row["highlighted"]:
            continue
        for key, value in row.items():
            if key in {"rank", "age_percentile_rank", "distance_percentile_rank"}:
                continue
            if type(value) in (int, float) and math.isfinite(value):
                selected.append((f"/data/{index}/{key}", key, value))
            elif type(value) is dict and key == "service_indicators":
                for category, indicators in value.items():
                    if type(indicators) is dict:
                        for metric, number in indicators.items():
                            if type(number) in (int, float) and math.isfinite(number):
                                selected.append((f"/data/{index}/service_indicators/{category}/{metric}", metric, number))
    claims = []
    unattributed = 0
    demographic_rows = {(row["municipality_code"], row["reference_period"]): row for row in territorial.DataRepository(root / "datos_preparados").demography()}
    demographic_sha = digest((root / "datos_preparados/demografia.csv").read_bytes())
    for pointer, field, value in selected:
        sources = _claim_sources(field, available)
        if not sources:
            unattributed += 1
            continue
        denominator = None
        numerator = None
        if "per_10000" in field:
            age = "75" if "75" in field else "65" if "65" in field else None
            if age is None:
                continue
            index = int(pointer.split("/")[2]) if pointer.startswith("/data/") else None
            row = raw["data"][index] if index is not None else {}
            population = row.get(f"population_{age}_plus") if type(row) is dict else None
            parts = pointer.split("/")
            category = parts[4] if len(parts) > 5 and parts[3] == "service_indicators" else None
            count = row.get("service_indicators", {}).get(category, {}).get("registered_service_count") if category else None
            if type(population) not in (int, float) or population <= 0 or type(count) is not int or abs(value - round(count / population * 10000, 3)) > 0.0005:
                unattributed += 1
                continue
            denominator = {"value": population, "unit": "personas", "period": str(catalog["EUSTAT_EMH_2025"]["reference_period"]), "source_id": "EUSTAT_EMH_2025", "evidence_path": f"/data/{index}/population_{age}_plus", "data_ref": None}
            numerator = {"value": count, "unit": "registros", "period": str(catalog["ODE_HEALTH_CENTRES_2026"]["reference_period"]), "source_id": "ODE_HEALTH_CENTRES_2026", "evidence_path": f"/data/{index}/service_indicators/{category}/registered_service_count", "data_ref": None}
        is_percentage = field.startswith("pct_") or field == "value" and str(raw.get("unit", "")).startswith("%")
        if is_percentage:
            age = "75" if "75" in field else "65" if "65" in field else raw.get("filters", {}).get("age_group")
            index = int(pointer.split("/")[2]) if pointer.startswith("/data/") else None
            row = raw["data"][index] if index is not None else None
            code = row.get("municipality_code") if type(row) is dict else None
            period = str(catalog["EUSTAT_EMH_2025"]["reference_period"])
            source_row = demographic_rows.get((code, period))
            age_count = source_row.get(f"population_{age}_plus") if source_row else None
            total = source_row.get("population_total") if source_row else None
            if age not in {"65", "75"} or type(age_count) not in (int, float) or type(total) not in (int, float) or total <= 0 or abs(value - round(age_count / total * 100, 3)) > 0.0005:
                unattributed += 1
                continue
            def data_ref(metric: str) -> dict[str, Any]:
                return {"path": "datos_preparados/demografia.csv", "sha256": demographic_sha, "municipality_code": code, "reference_period": period, "field": metric}
            numerator = {"value": age_count, "unit": "personas", "period": period, "source_id": "EUSTAT_EMH_2025", "evidence_path": None, "data_ref": data_ref(f"population_{age}_plus")}
            denominator = {"value": total, "unit": "personas", "period": period, "source_id": "EUSTAT_EMH_2025", "evidence_path": None, "data_ref": data_ref("population_total")}
        entity_type, entity_id, entity_label = _claim_entity(raw, pointer)
        claims.append({
            "id": f"claim-{len(claims) + 1}", "label": field, "value": value,
            "unit": _claim_unit(field, raw), "period": _claim_period(field, sources, catalog),
            "numerator": numerator, "denominator": denominator, "source_ids": sources, "evidence_path": pointer,
            "entity_type": entity_type, "entity_id": entity_id, "entity_label": entity_label,
            "metric_id": field, "reference_periods": [{"source_id": source, "period": str(catalog[source]["reference_period"])} for source in sources],
            "source_refs": _source_roles(field, sources),
            "derivation": "derived_exact" if numerator is not None or field in {"highlighted_count", "joined_rows", "age_cut_percent", "distance_cut_m"} else "direct",
            "assumptions": ["75+ derivado del año de nacimiento en la fuente demográfica."] if is_percentage and age == "75" else [],
        })
    return claims, unattributed


def validate_evidence(evidence: Any, catalog: dict[str, Any], root: Path | None = None) -> None:
    root = (root or _workspace_root()).resolve()
    _keys(evidence, EVIDENCE_KEYS, "evidence")
    if evidence["schema_version"] != VERSION or evidence["status"] not in {"valid", "no_data", "unsupported", "error"}:
        raise ContractViolation("evidence:version_or_status")
    for key in ("request_id", "capability_id"):
        _text(evidence[key], f"evidence.{key}")
    inp = _keys(evidence["normalized_input"], {"tool", "arguments"}, "evidence.input")
    execution = _keys(evidence["execution"], {"request_id", "tool", "arguments_sha256", "snapshot_id", "state"}, "evidence.execution")
    if type(inp["arguments"]) is not dict or execution["request_id"] != evidence["request_id"] or execution["tool"] != inp["tool"] or evidence["capability_id"] != inp["tool"]:
        raise ContractViolation("evidence:request_binding")
    _hex(execution["arguments_sha256"], "evidence.execution.arguments_sha256")
    if execution["arguments_sha256"] != digest(canonical(inp["arguments"])):
        raise ContractViolation("evidence:arguments_hash")
    if execution["snapshot_id"] is not None:
        _text(execution["snapshot_id"], "evidence.execution.snapshot_id")
    if execution["state"] not in {"not_started", "completed", "failed"}:
        raise ContractViolation("evidence:execution_state")
    if type(evidence["outcomes"]) is not list:
        raise ContractViolation("evidence:outcomes")
    for outcome in evidence["outcomes"]:
        _keys(outcome, {"index", "status", "error"}, "evidence.outcome")
        if type(outcome["index"]) is not int or outcome["index"] < 0 or outcome["status"] not in {"ok", "no_feasible_journey", "unsupported", "unknown", "error"} or outcome["error"] is not None and type(outcome["error"]) is not dict:
            raise ContractViolation("evidence:outcome_shape")
    effective = evidence["effective_request"]
    if effective is not None:
        _keys(effective, {"operation", "municipality_codes", "municipality_labels", "effective_period", "parameters", "defaults_applied", "snapshot_id", "contracts"}, "evidence.effective_request")
        if effective["operation"] != inp["tool"] or effective["snapshot_id"] != execution["snapshot_id"] or type(effective["parameters"]) is not dict or type(effective["municipality_codes"]) is not list or type(effective["municipality_labels"]) is not list or len(effective["municipality_codes"]) != len(effective["municipality_labels"]):
            raise ContractViolation("evidence:effective_request_binding")
        for key, value in inp["arguments"].items():
            observed = effective["parameters"].get(key)
            clock_equivalent = evidence["capability_id"] == "plan_visit" and key in {"appointment_time", "return_deadline"} and type(value) is str and len(value) == 5 and observed == value + ":00"
            if key not in effective["parameters"] or observed != value and not clock_equivalent:
                raise ContractViolation("evidence:effective_parameter_mismatch")
        if effective["defaults_applied"] != sorted(set(effective["parameters"]) - set(inp["arguments"])):
            raise ContractViolation("evidence:effective_defaults")
        _keys(effective["contracts"], {"evidence", "capability"}, "evidence.effective_contracts", optional={"mobility"})
    elif evidence["status"] == "valid":
        raise ContractViolation("evidence:missing_effective_request")
    versions = _keys(evidence["versions"], {"data_sha256", "code_sha256", "contract_sha256"}, "evidence.versions")
    for key, value in versions.items():
        _hex(value, f"evidence.versions.{key}")
    for key in ("assumptions", "limitations"):
        _strings(evidence[key], f"evidence.{key}")
    if type(evidence["method"]) is not str or type(evidence["claims"]) is not list:
        raise ContractViolation("evidence:method_or_claims")
    raw_json = evidence["raw_result_json"]
    raw = None
    if raw_json is not None:
        if type(raw_json) is not str:
            raise ContractViolation("evidence:raw_type")
        _hex(evidence["raw_result_sha256"], "evidence.raw_result_sha256")
        if digest(raw_json) != evidence["raw_result_sha256"]:
            raise ContractViolation("evidence:raw_hash")
        raw = strict_loads(raw_json)
    elif evidence["raw_result_sha256"] is not None:
        raise ContractViolation("evidence:raw_hash_without_result")
    if evidence["status"] == "valid":
        if raw is None or evidence["error"] is not None:
            raise ContractViolation("evidence:valid_without_result")
    else:
        if evidence["claims"] or type(evidence["error"]) is not dict:
            raise ContractViolation("evidence:error_with_claims")
        error = _keys(evidence["error"], {"origin", "code", "message", "available_options", "safe_next_action"}, "evidence.error")
        if error["origin"] not in {"domain", "data", "execution", "transport", "unknown"}:
            raise ContractViolation("evidence:error_origin")
        for key in ("code", "message", "safe_next_action"):
            _text(error[key], f"evidence.error.{key}")
        _strings(error["available_options"], "evidence.error.available_options")
    for claim in evidence["claims"]:
        item = _keys(claim, {"id", "label", "value", "unit", "period", "numerator", "denominator", "source_ids", "evidence_path", "entity_type", "entity_id", "entity_label", "metric_id", "reference_periods", "source_refs", "derivation", "assumptions"}, "claim")
        for key in ("id", "label", "unit", "period", "evidence_path", "entity_type", "entity_id", "entity_label", "metric_id"):
            _text(item[key], f"claim.{key}")
        if item["entity_type"] not in {"municipality", "municipality_set", "result", "journey", "comparison"} or item["derivation"] not in {"direct", "derived_exact", "estimated_with_assumptions"}:
            raise ContractViolation("claim:semantics")
        _strings(item["assumptions"], "claim.assumptions")
        if not item["evidence_path"].startswith("/") or raw is None or type(item["value"]) not in (int, float, str, bool, type(None)):
            raise ContractViolation("claim:shape")
        if type(item["value"]) is float and not math.isfinite(item["value"]):
            raise ContractViolation("claim:non_finite")
        try:
            observed = _pointer(raw, item["evidence_path"])
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ContractViolation("claim:bad_pointer") from exc
        if type(observed) is not type(item["value"]) or observed != item["value"]:
            raise ContractViolation("claim:unobserved_value")
        _strings(item["source_ids"], "claim.source_ids", nonempty=True)
        if any(source not in catalog for source in item["source_ids"]):
            raise ContractViolation("claim:false_source")
        if evidence["capability_id"] != "plan_visit" and type(raw) is dict and type(raw.get("sources")) is list:
            used_sources = {source.get("source_id") for source in raw["sources"] if type(source) is dict}
            if not set(item["source_ids"]) <= used_sources:
                raise ContractViolation("claim:unused_source")
        if type(item["reference_periods"]) is not list or type(item["source_refs"]) is not list:
            raise ContractViolation("claim:source_roles")
        expected_periods = [{"source_id": source, "period": str(catalog[source].get("reference_period"))} for source in item["source_ids"]]
        if item["reference_periods"] != expected_periods or {entry.get("source_id") for entry in item["source_refs"] if type(entry) is dict} != set(item["source_ids"]):
            raise ContractViolation("claim:source_roles")
        for entry in item["source_refs"]:
            _keys(entry, {"source_id", "role"}, "claim.source_ref")
            _text(entry["role"], "claim.source_ref.role")
        if item["source_refs"] != _source_roles(item["metric_id"], item["source_ids"]):
            raise ContractViolation("claim:source_role_mismatch")
        for source in item["source_ids"]:
            source_period = catalog[source].get("reference_period")
            if type(source_period) is not str or source_period not in item["period"]:
                raise ContractViolation("claim:period_mismatch")
        field_name = item["evidence_path"].split("/")[-1]
        if item["metric_id"] != field_name:
            raise ContractViolation("claim:metric_mismatch")
        entity_type, entity_id, entity_label = _claim_entity(raw, item["evidence_path"])
        if (item["entity_type"], item["entity_id"], item["entity_label"]) != (entity_type, entity_id, entity_label):
            raise ContractViolation("claim:entity_mismatch")
        if (field_name.endswith(("_m", "_s")) or "distance" in field_name or field_name.startswith("pct_") or field_name.endswith("_percent") or field_name.startswith("population") or "per_10000" in field_name or field_name in {"highlighted_count", "joined_rows"} or field_name == "value" and str(raw.get("unit", "")).startswith("%")) and item["unit"] != _claim_unit(field_name, raw):
            raise ContractViolation("claim:unit_mismatch")
        for part_name in ("numerator", "denominator"):
            part = item[part_name]
            if part is None:
                continue
            _keys(part, {"value", "unit", "period", "source_id", "evidence_path", "data_ref"}, f"claim.{part_name}")
            if type(part["value"]) not in (int, float) or not math.isfinite(part["value"]) or part["source_id"] not in item["source_ids"]:
                raise ContractViolation(f"claim:{part_name}")
            if part["period"] != catalog[part["source_id"]].get("reference_period"):
                raise ContractViolation(f"claim:{part_name}_provenance")
            if part["evidence_path"] is not None and part["data_ref"] is None:
                if not str(part["evidence_path"]).startswith("/") or _pointer(raw, part["evidence_path"]) != part["value"]:
                    raise ContractViolation(f"claim:{part_name}_pointer")
            elif part["data_ref"] is not None and part["evidence_path"] is None:
                ref = _keys(part["data_ref"], {"path", "sha256", "municipality_code", "reference_period", "field"}, f"claim.{part_name}.data_ref")
                path = (root / ref["path"]).resolve()
                if ref["path"] != "datos_preparados/demografia.csv" or root not in path.parents or not path.is_file() or digest(path.read_bytes()) != ref["sha256"] or ref["municipality_code"] != item["entity_id"] or ref["reference_period"] != part["period"]:
                    raise ContractViolation(f"claim:{part_name}_data_ref")
                rows = territorial.DataRepository(root / "datos_preparados").demography()
                matching = [row for row in rows if row["municipality_code"] == ref["municipality_code"] and row["reference_period"] == ref["reference_period"]]
                if len(matching) != 1 or matching[0].get(ref["field"]) != part["value"]:
                    raise ContractViolation(f"claim:{part_name}_data_value")
            else:
                raise ContractViolation(f"claim:{part_name}_ambiguous_provenance")
        if "per_10000" in field_name:
            numerator, denominator = item["numerator"], item["denominator"]
            parts = item["evidence_path"].split("/")
            age = "75" if "75" in field_name else "65"
            expected_numerator = "/".join(parts[:-1]) + "/registered_service_count"
            expected_denominator = f"/data/{parts[2]}/population_{age}_plus"
            if numerator is None or denominator is None or numerator["unit"] != "registros" or denominator["unit"] != "personas" or numerator["source_id"] != "ODE_HEALTH_CENTRES_2026" or denominator["source_id"] != "EUSTAT_EMH_2025" or numerator["evidence_path"] != expected_numerator or denominator["evidence_path"] != expected_denominator or denominator["value"] <= 0 or abs(item["value"] - round(numerator["value"] / denominator["value"] * 10000, 3)) > 0.0005:
                raise ContractViolation("claim:rate_lineage")
        if field_name.startswith("pct_") or field_name == "value" and str(raw.get("unit", "")).startswith("%"):
            numerator, denominator = item["numerator"], item["denominator"]
            age = "75" if "75" in field_name else "65" if "65" in field_name else raw.get("filters", {}).get("age_group")
            if numerator is None or denominator is None or numerator["unit"] != "personas" or denominator["unit"] != "personas" or numerator["source_id"] != denominator["source_id"] or numerator["source_id"] != "EUSTAT_EMH_2025" or numerator["data_ref"]["field"] != f"population_{age}_plus" or denominator["data_ref"]["field"] != "population_total" or denominator["value"] <= 0 or abs(item["value"] - round(numerator["value"] / denominator["value"] * 100, 3)) > 0.0005:
                raise ContractViolation("claim:percentage_lineage")


def _error(request_id: str, capability_id: str, args: dict[str, Any], origin: str, code: str, message: str, *, options: list[str] | None = None, snapshot_id: str | None = None, raw_json: str | None = None, versions: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        args_hash = digest(canonical(args))
        safe_args = args
    except (ContractViolation, TypeError, ValueError):
        safe_args = {}
        args_hash = digest(canonical(safe_args))
    return {
        "schema_version": VERSION, "request_id": request_id, "capability_id": capability_id,
        "normalized_input": {"tool": capability_id, "arguments": safe_args}, "effective_request": None,
        "execution": {"request_id": request_id, "tool": capability_id, "arguments_sha256": args_hash, "snapshot_id": snapshot_id, "state": "not_started" if code == "capability_unavailable" else "completed" if raw_json is not None else "failed"},
        "status": "unsupported" if code in {"capability_unavailable", "unsupported_age", "unsupported_category"} else "error", "outcomes": [],
        "claims": [], "method": "", "assumptions": [], "limitations": [],
        "error": {"origin": origin, "code": code, "message": message, "available_options": options or [], "safe_next_action": "Revisar los valores disponibles; si el fallo persiste, no usar el resultado."},
        "versions": versions or {key: "0" * 64 for key in ("data_sha256", "code_sha256", "contract_sha256")},
        "raw_result_json": raw_json, "raw_result_sha256": digest(raw_json) if raw_json is not None else None,
    }


def _versions(root: Path, cap: dict[str, Any]) -> dict[str, str]:
    data = "".join(item["sha256"] for item in cap["required_data"])
    code_path = Path(__file__)
    contract_path = root / "contracts/vnext/evidence-v1.1.schema.json"
    return {
        "data_sha256": digest(data),
        "code_sha256": digest(code_path.read_bytes()),
        "contract_sha256": digest(contract_path.read_bytes()),
    }


def consultar_capacidades(pregunta_o_dimension: str | None = None, *, root: Path | None = None, detalle: bool = True) -> str:
    """Inspect validated capabilities; disabled entries stay visibly disabled."""
    root = (root or _workspace_root()).resolve()
    entries = _registry(root)
    selected = [item for item in entries if not pregunta_o_dimension or pregunta_o_dimension.lower() in (item["id"] + " " + item["description"]).lower()]
    if not selected:
        selected = entries
    catalog = _catalog(root)
    return canonical({
        "status": "ok", "question": "Capacidades verificadas de GIPUZKOA 360",
        "filters": {"pregunta_o_dimension": pregunta_o_dimension}, "period": None,
        "metric": "capability_registry", "unit": "no aplica", "rows_used": len(selected),
        "data": selected, "method": "Lectura del registro validado contra handlers, fuentes y hashes de datos.",
        "sources": list(catalog.values()), "warnings": [],
        "limitations": ["Una capacidad deshabilitada no se puede ejecutar.", "El registro no sustituye una prueba conversacional en portal."],
    })


def _execute_mobility(request: Any, request_id: str, root: Path) -> dict[str, Any]:
    try:
        from prototypes.ir_y_volver import provider
        try:
            from . import mobility_adapter
        except ImportError:
            import mobility_adapter
        result = mobility_adapter.consume_compare_visits(provider, request, request_id) if type(request) is list else mobility_adapter.consume_plan_visit(provider, request, request_id)
        return result
    except ContractViolation as exc:
        result = _error(request_id, "plan_visit", {"request": request}, "domain" if str(exc).startswith("mobility:invalid") else "execution", "contract_violation", str(exc))
    except Exception:
        result = _error(request_id, "plan_visit", {"request": request}, "unknown", "unverified_result", "No se ha podido verificar el proveedor de movilidad.")
    validate_evidence(result, _catalog(root))
    return result


def plan_visit(request: Any) -> dict[str, Any]:
    """Execute one pinned W1 stop-only scenario or a bounded comparison."""
    return _execute_mobility(request, uuid4().hex, _workspace_root())


def execute(capability_id: str, arguments: dict[str, Any], request_id: str, *, root: Path | None = None, transport: Callable[[Callable[..., str], dict[str, Any]], str] | None = None) -> dict[str, Any]:
    """Execute one deterministic tool, bind and validate its evidence, fail closed."""
    root = (root or _workspace_root()).resolve()
    _text(request_id, "request_id")
    _text(capability_id, "capability_id")
    if type(arguments) is not dict:
        raise ContractViolation("arguments:expected_object")
    catalog: dict[str, Any] = {}
    versions = None
    try:
        catalog = _catalog(root)
        registry = _registry(root)
        cap = next((item for item in registry if item["id"] == capability_id), None)
        if cap is None or not cap["enabled"]:
            return _error(request_id, capability_id, arguments, "domain", "capability_unavailable", "La capacidad no está habilitada ni validada.", options=[item["id"] for item in registry if item["enabled"]])
        versions = _versions(root, cap)
        repaired, repair_notes = _repair_once(arguments)
        normalized = _validate_arguments(repaired, cap)
        if capability_id == "plan_visit":
            return _execute_mobility(normalized["request"], request_id, root)
        handler = consultar_capacidades if cap["handler"] == "consultar_capacidades" else getattr(territorial, cap["handler"])
        call_args = {**normalized, "detalle": True}
        if handler is consultar_capacidades:
            call_args["root"] = root
        effective = _effective_request(handler, normalized, root)
        raw_text = transport(handler, call_args) if transport else handler(**call_args)
        if type(raw_text) is not str:
            raise ContractViolation("tool_result:expected_json_string")
        raw = _validate_result(strict_loads(raw_text), catalog)
        _bind_result_to_arguments(raw, effective, root)
        raw_json = canonical(raw)
        if len(raw_json.encode("utf-8")) > MAX_EVIDENCE_BYTES:
            return _error(request_id, capability_id, normalized, "execution", "payload_too_large", "El resultado completo supera el límite seguro; acote la consulta.", options=["Acotar municipios o parámetros"], raw_json=None, versions=versions)
        if raw["status"] == "error":
            code = raw["error_code"]
            origin = "domain" if code.startswith(("invalid", "unknown", "unsupported", "source_not_found", "municipality_not_found")) else "data" if code.startswith(("missing", "corrupt", "no_")) else "unknown"
            result = _error(request_id, capability_id, normalized, origin, code, raw["message"], options=raw["available_options"], raw_json=raw_json, versions=versions)
        else:
            claims, unattributed = _make_claims(raw, catalog, root)
            result = {
                "schema_version": VERSION, "request_id": request_id, "capability_id": capability_id,
                "normalized_input": {"tool": capability_id, "arguments": normalized},
                "effective_request": effective,
                "execution": {"request_id": request_id, "tool": capability_id, "arguments_sha256": digest(canonical(normalized)), "snapshot_id": None, "state": "completed"},
                "status": "valid", "outcomes": [], "claims": claims, "method": raw["method"],
                "assumptions": repair_notes, "limitations": raw["limitations"] + ([f"{unattributed} cifras del resultado carecen de atribución por fuente en la salida y no se ofrecen como afirmaciones verificadas."] if unattributed else []), "error": None,
                "versions": versions, "raw_result_json": raw_json, "raw_result_sha256": digest(raw_json),
            }
        validate_evidence(result, catalog)
        return result
    except ObservedTransportError as exc:
        result = _error(request_id, capability_id, arguments, "transport", "observed_transport_failure", str(exc) or "Fallo de transporte observado.", versions=versions)
    except ContractViolation as exc:
        user_argument_error = str(exc).startswith("arguments:")
        result = _error(request_id, capability_id, arguments, "domain" if user_argument_error else "execution", "invalid_arguments" if user_argument_error else "contract_violation", str(exc), versions=versions)
    except (OSError, json.JSONDecodeError) as exc:
        result = _error(request_id, capability_id, arguments, "data", "data_unavailable", str(exc), versions=versions)
    except Exception:
        result = _error(request_id, capability_id, arguments, "unknown", "unverified_result", "No se ha podido verificar el resultado.", versions=versions)
    validate_evidence(result, catalog)
    return result


def public_result(evidence: dict[str, Any]) -> str:
    """Return a bounded, attributed model view; keep raw evidence out of the prompt."""
    claims = evidence["claims"]
    args = evidence["normalized_input"]["arguments"]
    explicit_entities = bool(args.get("municipio") or args.get("municipios"))
    raw = strict_loads(evidence["raw_result_json"]) if evidence["raw_result_json"] is not None else {}
    municipality_ids = list(dict.fromkeys(row["municipality_code"] for row in raw.get("data", []) if type(row) is dict and type(row.get("municipality_code")) is str))
    selected_ids = municipality_ids if explicit_entities else municipality_ids[:DEFAULT_PUBLIC_ENTITIES]
    selected = [claim for claim in claims if claim["entity_type"] != "municipality" or claim["entity_id"] in selected_ids]
    claim_entities = {claim["entity_id"] for claim in selected if claim["entity_type"] == "municipality"}
    selection = {
        "total_entities": len(municipality_ids), "returned_entities": len(claim_entities),
        "omitted_entities": len(municipality_ids) - len(claim_entities),
        "criterion": "Todas las entidades solicitadas explícitamente" if explicit_entities else "Primeras entidades en el orden validado de la herramienta",
        "detail_mechanism": "Nueva consulta acotada con municipio(s) explícitos mediante las herramientas territoriales existentes; no hay lectura de rutas ni descarga de evidencia en el portal.",
    }
    view = {
        "schema_version": evidence["schema_version"], "request_id": evidence["request_id"],
        "capability_id": evidence["capability_id"], "normalized_input": evidence["normalized_input"], "effective_request": evidence["effective_request"], "execution": evidence["execution"],
        "status": evidence["status"], "outcomes": evidence["outcomes"], "claims": selected, "selection": selection,
        "method": evidence["method"], "assumptions": evidence["assumptions"],
        "limitations": evidence["limitations"], "error": evidence["error"],
        "versions": evidence["versions"], "raw_result_sha256": evidence["raw_result_sha256"],
    }
    if evidence["capability_id"] == "consultar_capacidades" and type(raw.get("data")) is list:
        view["capabilities"] = [
            {key: item[key] for key in ("id", "description", "enabled", "validation_status", "derivation", "coverage", "semantic_limits") if key in item}
            for item in raw["data"] if type(item) is dict
        ]
    if evidence["capability_id"] == "consultar_fuente" and type(raw.get("data")) is list:
        view["source_metadata"] = [
            {key: item[key] for key in ("source_id", "title", "institution", "reference_period", "unit", "url", "limitations") if key in item}
            for item in raw["data"] if type(item) is dict
        ]
    if explicit_entities and len(claim_entities) != len(municipality_ids):
        failure = _error(evidence["request_id"], evidence["capability_id"], args, "data", "missing_attributed_entity", "Una entidad solicitada carece de cifra atribuida en la salida; no se ofrece una comparación parcial.")
        view.update(status="error", claims=[], error=failure["error"])
    rendered = canonical(view)
    if len(rendered.encode("utf-8")) > MAX_PUBLIC_BYTES:
        failure = _error(evidence["request_id"], evidence["capability_id"], args, "execution", "public_payload_too_large", "La vista validada supera el límite local; acote los municipios o parámetros.")
        failure["error"]["safe_next_action"] = "Solicite municipios concretos; no se ha publicado ninguna cifra parcial."
        view.update(status="error", claims=[], selection={**selection, "returned_entities": 0, "omitted_entities": selection["total_entities"]}, error=failure["error"])
        rendered = canonical(view)
        if len(rendered.encode("utf-8")) > MAX_PUBLIC_BYTES:
            rendered = canonical({"status": "error", "code": "public_payload_too_large", "claims": []})
    return rendered
