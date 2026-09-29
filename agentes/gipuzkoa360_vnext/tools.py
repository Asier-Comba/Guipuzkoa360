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

try:
    from agentes.gipuzkoa360 import tools as territorial
except ImportError:  # Generated Studio bundle supplies this name.
    territorial = None  # type: ignore[assignment]


VERSION = "1.0.0"
MAX_EVIDENCE_BYTES = 120_000
SHA256_KEYS = {"data_sha256", "code_sha256", "contract_sha256", "arguments_sha256", "raw_result_sha256"}
EVIDENCE_KEYS = {
    "schema_version", "request_id", "capability_id", "normalized_input", "execution",
    "status", "claims", "method", "assumptions", "limitations", "error", "versions",
    "raw_result_json", "raw_result_sha256",
}
CAPABILITY_KEYS = {
    "schema_version", "id", "description", "derivation", "enabled", "validation_status",
    "handler", "input_fields", "required_data", "coverage", "source_ids",
    "allowed_transformations", "preconditions", "restrictions", "semantic_limits",
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
    result = {}
    for item in payload:
        if type(item) is not dict or type(item.get("source_id")) is not str:
            raise ContractViolation("source_catalog:invalid_source")
        result[item["source_id"]] = item
    return result


def _registry(root: Path) -> list[dict[str, Any]]:
    path = root / "datos_preparados/vnext/capabilities.json"
    payload = strict_loads(path.read_text(encoding="utf-8"))
    _keys(payload, {"schema_version", "capabilities"}, "registry")
    if payload["schema_version"] != VERSION or type(payload["capabilities"]) is not list:
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
    if item["schema_version"] != VERSION:
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
        if item["handler"] not in TERRITORIAL_HANDLERS | LOCAL_HANDLERS:
            raise ContractViolation("capability:missing_handler")
        if item["handler"] in TERRITORIAL_HANDLERS and not callable(getattr(territorial, item["handler"], None)):
            raise ContractViolation("capability:missing_handler")
        handler = consultar_capacidades if item["handler"] in LOCAL_HANDLERS else getattr(territorial, item["handler"])
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
        if field["name"] in names or field["type"] not in {"string", "number", "integer", "boolean", "string_array"} or type(field["required"]) is not bool or type(field["allowed_values"]) is not list:
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
    _strings(item["source_ids"], "capability.source_ids", nonempty=item["enabled"])
    if any(source not in catalog for source in item["source_ids"]):
        raise ContractViolation("capability:false_source")
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
        }[kind](value)
        if not valid or (field["allowed_values"] and value not in field["allowed_values"]):
            raise ContractViolation(f"arguments:{name}:invalid_value")
    return dict(args)


def _repair_once(args: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Only an explicit equivalent category alias is safe to normalize."""
    if args.get("categoria_servicio") in {"atención primaria", "atencion primaria"}:
        original = args["categoria_servicio"]
        return {**args, "categoria_servicio": "primary_care"}, [f"Alias explícito normalizado una vez: {original} → primary_care."]
    return args, []


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


def _bind_result_to_arguments(raw: dict[str, Any], arguments: dict[str, Any]) -> None:
    """Reject a valid result substituted from another parameterized request."""
    if raw["status"] != "ok":
        return
    filters = raw["filters"]
    mapping = {
        "grupo_edad": "age_group", "categoria_servicio": "service_category",
        "umbral_km": "threshold_km", "cuantil": "quantile_threshold",
        "periodo": "period", "top_n": "top_n", "medida": "measure",
        "accion": "action", "source_id": "source_id",
    }
    for argument, filter_name in mapping.items():
        requested = arguments.get(argument)
        if requested is None or filter_name not in filters:
            continue
        observed = filters[filter_name]
        if type(requested) in (int, float) and type(observed) in (int, float):
            matched = float(requested) == float(observed)
        else:
            matched = requested == observed
        if not matched:
            raise ContractViolation(f"tool_result:request_mismatch:{argument}")


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
    return [source for source in wanted if source in available]


def _claim_period(field: str, source_ids: list[str], catalog: dict[str, Any]) -> str:
    if field.startswith(("population", "pct_", "age_")) or field in {"value", "age_cut_percent"}:
        return "2025-01-01"
    periods = [str(catalog[source]["reference_period"]) for source in source_ids]
    return ";".join(periods)


def _claim_unit(field: str, raw: dict[str, Any]) -> str:
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


def _make_claims(raw: dict[str, Any], catalog: dict[str, Any], *, max_claims: int = 64) -> tuple[list[dict[str, Any]], int]:
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
        if len(selected) >= max_claims:
            break
    claims = []
    unattributed = 0
    for pointer, field, value in selected[:max_claims]:
        sources = _claim_sources(field, available)
        if not sources:
            unattributed += 1
            continue
        denominator = None
        if "per_10000" in field:
            age = "75" if "75" in field else "65" if "65" in field else None
            if age is None:
                continue
            index = int(pointer.split("/")[2]) if pointer.startswith("/data/") else None
            row = raw["data"][index] if index is not None else {}
            population = row.get(f"population_{age}_plus") if type(row) is dict else None
            if type(population) not in (int, float) or population <= 0:
                continue
            denominator = {"value": population, "unit": "personas", "period": "2025-01-01", "source_id": "EUSTAT_EMH_2025"}
        claims.append({
            "id": f"claim-{len(claims) + 1}", "label": field, "value": value,
            "unit": _claim_unit(field, raw), "period": _claim_period(field, sources, catalog),
            "denominator": denominator, "source_ids": sources, "evidence_path": pointer,
        })
    return claims, unattributed


def validate_evidence(evidence: Any, catalog: dict[str, Any]) -> None:
    _keys(evidence, EVIDENCE_KEYS, "evidence")
    if evidence["schema_version"] != VERSION or evidence["status"] not in {"valid", "no_data", "unsupported", "error"}:
        raise ContractViolation("evidence:version_or_status")
    for key in ("request_id", "capability_id"):
        _text(evidence[key], f"evidence.{key}")
    inp = _keys(evidence["normalized_input"], {"tool", "arguments"}, "evidence.input")
    execution = _keys(evidence["execution"], {"request_id", "tool", "arguments_sha256", "snapshot_id"}, "evidence.execution")
    if type(inp["arguments"]) is not dict or execution["request_id"] != evidence["request_id"] or execution["tool"] != inp["tool"] or evidence["capability_id"] != inp["tool"]:
        raise ContractViolation("evidence:request_binding")
    _hex(execution["arguments_sha256"], "evidence.execution.arguments_sha256")
    if execution["arguments_sha256"] != digest(canonical(inp["arguments"])):
        raise ContractViolation("evidence:arguments_hash")
    if execution["snapshot_id"] is not None:
        _text(execution["snapshot_id"], "evidence.execution.snapshot_id")
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
        item = _keys(claim, {"id", "label", "value", "unit", "period", "denominator", "source_ids", "evidence_path"}, "claim")
        for key in ("id", "label", "unit", "period", "evidence_path"):
            _text(item[key], f"claim.{key}")
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
        for source in item["source_ids"]:
            source_period = catalog[source].get("reference_period")
            if type(source_period) is not str or source_period not in item["period"]:
                raise ContractViolation("claim:period_mismatch")
        field_name = item["evidence_path"].split("/")[-1]
        if (field_name.endswith("_m") or "distance" in field_name or field_name.startswith("pct_") or field_name.endswith("_percent") or field_name.startswith("population") or "per_10000" in field_name) and item["unit"] != _claim_unit(field_name, raw):
            raise ContractViolation("claim:unit_mismatch")
        if item["denominator"] is not None:
            denom = _keys(item["denominator"], {"value", "unit", "period", "source_id"}, "claim.denominator")
            if type(denom["value"]) not in (int, float) or not math.isfinite(denom["value"]) or denom["source_id"] not in catalog:
                raise ContractViolation("claim:denominator")
            if denom["unit"] != "personas" or denom["period"] != catalog[denom["source_id"]].get("reference_period"):
                raise ContractViolation("claim:denominator_provenance")
        elif "per_10000" in field_name:
            raise ContractViolation("claim:missing_denominator")


def _error(request_id: str, capability_id: str, args: dict[str, Any], origin: str, code: str, message: str, *, options: list[str] | None = None, snapshot_id: str | None = None, raw_json: str | None = None, versions: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        args_hash = digest(canonical(args))
        safe_args = args
    except (ContractViolation, TypeError, ValueError):
        safe_args = {}
        args_hash = digest(canonical(safe_args))
    return {
        "schema_version": VERSION, "request_id": request_id, "capability_id": capability_id,
        "normalized_input": {"tool": capability_id, "arguments": safe_args},
        "execution": {"request_id": request_id, "tool": capability_id, "arguments_sha256": args_hash, "snapshot_id": snapshot_id},
        "status": "unsupported" if code in {"capability_unavailable", "unsupported_age", "unsupported_category"} else "error",
        "claims": [], "method": "", "assumptions": [], "limitations": [],
        "error": {"origin": origin, "code": code, "message": message, "available_options": options or [], "safe_next_action": "Revisar los valores disponibles; si el fallo persiste, no usar el resultado."},
        "versions": versions or {key: "0" * 64 for key in ("data_sha256", "code_sha256", "contract_sha256")},
        "raw_result_json": raw_json, "raw_result_sha256": digest(raw_json) if raw_json is not None else None,
    }


def _versions(root: Path, cap: dict[str, Any]) -> dict[str, str]:
    data = "".join(item["sha256"] for item in cap["required_data"])
    code_path = Path(__file__)
    contract_path = root / "contracts/vnext/evidence-v1.schema.json"
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
        handler = consultar_capacidades if cap["handler"] == "consultar_capacidades" else getattr(territorial, cap["handler"])
        call_args = {**normalized, "detalle": True}
        if handler is consultar_capacidades:
            call_args["root"] = root
        raw_text = transport(handler, call_args) if transport else handler(**call_args)
        if type(raw_text) is not str:
            raise ContractViolation("tool_result:expected_json_string")
        raw = _validate_result(strict_loads(raw_text), catalog)
        _bind_result_to_arguments(raw, normalized)
        raw_json = canonical(raw)
        if len(raw_json.encode("utf-8")) > MAX_EVIDENCE_BYTES:
            return _error(request_id, capability_id, normalized, "execution", "payload_too_large", "El resultado completo supera el límite seguro; acote la consulta.", options=["Acotar municipios o parámetros"], raw_json=None, versions=versions)
        if raw["status"] == "error":
            code = raw["error_code"]
            origin = "domain" if code.startswith(("invalid", "unknown", "unsupported", "source_not_found", "municipality_not_found")) else "data" if code.startswith(("missing", "corrupt", "no_")) else "unknown"
            result = _error(request_id, capability_id, normalized, origin, code, raw["message"], options=raw["available_options"], raw_json=raw_json, versions=versions)
        else:
            claims, unattributed = _make_claims(raw, catalog)
            result = {
                "schema_version": VERSION, "request_id": request_id, "capability_id": capability_id,
                "normalized_input": {"tool": capability_id, "arguments": normalized},
                "execution": {"request_id": request_id, "tool": capability_id, "arguments_sha256": digest(canonical(normalized)), "snapshot_id": None},
                "status": "valid", "claims": claims, "method": raw["method"],
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
    """Expose the complete verified evidence; never silently drop result rows."""
    return canonical(evidence)
