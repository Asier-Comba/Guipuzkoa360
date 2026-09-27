"""Bounded planner → allowlist → existing core → evidence critic → grounded renderer.

No model, networking, persistence, production writes or new territorial calculations.
The planner consumes an explicit intent and typed parameters, not arbitrary natural language.
"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_VERSION = "195b4980fa5998b096c308296a55e452380b0371"
CAPABILITY_VERSION = "next-registry-0.1"
PROMPT_VERSION = "none-deterministic-template-0.1"
BENCHMARK_VERSION = "next-evaluation-0.1"

def strict_loads(raw: str):
    def finite(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Non-finite JSON number")
        return number
    def constant(value):
        raise ValueError("Non-finite JSON constant: " + value)
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    return json.loads(raw, parse_constant=constant, parse_float=finite, object_pairs_hook=pairs)

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

@dataclass(frozen=True)
class Capability:
    id: str
    description: str
    status: str
    required_data: tuple[str, ...]
    tool: str | None
    parameters: tuple[str, ...]
    evidence_requirements: tuple[str, ...] = ("sources", "period", "unit", "rows_used", "method", "limitations")
    limitations: tuple[str, ...] = ("Territorial evidence only; no causal, travel-time, capacity or predictive claims.",)

TOOL_NAMES = {
    "summary": "obtener_resumen_territorial", "comparison": "comparar_municipios",
    "aging": "analizar_envejecimiento", "access": "analizar_acceso_servicios",
    "coincidence": "analizar_coincidencia", "scenario": "simular_escenario", "source": "consultar_fuente",
}
PARAMS = {
    "summary": ("municipio", "periodo"),
    "comparison": ("municipios", "grupo_edad", "categoria_servicio", "umbral_km", "periodo"),
    "aging": ("grupo_edad", "medida", "periodo", "top_n"),
    "access": ("categoria_servicio", "umbral_km", "periodo", "municipios"),
    "coincidence": ("categoria_servicio", "grupo_edad", "umbral_km", "periodo", "cuantil"),
    "scenario": ("accion", "categoria_servicio", "umbral_km", "periodo", "latitud", "longitud", "service_id", "nuevo_umbral_km"),
    "source": ("source_id",),
}
REQUIRED = {"summary": ("municipio",), "comparison": ("municipios",),
            "access": ("categoria_servicio",), "coincidence": ("categoria_servicio",),
            "scenario": ("accion", "categoria_servicio"), "aging": (), "source": ()}
ALIASES = {"resumen": "summary", "comparación": "comparison", "comparacion": "comparison",
           "envejecimiento": "aging", "acceso": "access", "coincidencia": "coincidence",
           "escenario": "scenario", "fuente": "source", **{v: k for k, v in TOOL_NAMES.items()}}

class CapabilityRegistry:
    def __init__(self):
        self._entries = {
            k: Capability(k, TOOL_NAMES[k], "ACTIVE",
                          ("metadata_sources.json",) if k == "source" else ("municipios.csv", "demografia.csv", "runtime_servicios.csv", "runtime_municipality_points.csv"),
                          tool, PARAMS[k]) for k, tool in TOOL_NAMES.items()
        }
        for name in ("mobility", "capacity", "demand", "housing", "environment"):
            self._entries[name] = Capability(name, "Requires independently verified data", "REQUIRES_DATA", (), None, ())

    def resolve(self, identifier):
        if not isinstance(identifier, str):
            return None
        return self._entries.get(ALIASES.get(identifier.casefold().strip(), identifier.casefold().strip()))

    def entries(self):
        return tuple(self._entries.values())

@dataclass(frozen=True)
class Plan:
    intent: str
    candidate_capability: str | None
    parameters: dict[str, Any]
    ambiguities: tuple[str, ...] = ()
    missing_inputs: tuple[str, ...] = ()
    out_of_scope: bool = False
    expected_evidence: tuple[str, ...] = ()
    followup: bool = False

class Planner:
    """Contract planner for explicit intent/parameters. No numerical result generation."""
    def __init__(self, registry=None):
        self.registry = registry or CapabilityRegistry()

    def plan(self, intent, parameters=None, previous=None):
        if not isinstance(intent, str) or (parameters is not None and not isinstance(parameters, dict)):
            return Plan(str(intent) if isinstance(intent, (int, float)) else "invalid", None, {}, ambiguities=("invalid_contract_type",))
        params = copy.deepcopy(parameters or {})
        followup = intent.casefold().strip() in {"follow-up", "seguimiento"}
        if followup and previous is None:
            return Plan(intent, None, params, missing_inputs=("previous_plan",))
        identifier = previous.candidate_capability if followup else intent
        cap = self.registry.resolve(identifier or "")
        if cap is None or cap.status != "ACTIVE":
            return Plan(intent, cap.id if cap else None, {}, out_of_scope=True)
        if followup:
            params = {**copy.deepcopy(previous.parameters), **params}
        if any(not isinstance(k, str) for k in params):
            return Plan(intent, cap.id, {}, ambiguities=("invalid_parameter_key",))
        unknown = tuple(sorted(set(params) - set(cap.parameters)))
        for key in ("cuantil", "umbral_km", "nuevo_umbral_km", "latitud", "longitud", "top_n"):
            if key in params and params[key] is not None and (type(params[key]) not in (int, float)):
                unknown += ("invalid_type:"+key,)
        missing = tuple(k for k in REQUIRED[cap.id] if params.get(k) in (None, "", []))
        try:
            canonical(params)
        except (TypeError, ValueError):
            unknown += ("non_json_or_non_finite_parameters",)
        return Plan(intent, cap.id, params, unknown, missing, False, cap.evidence_requirements, followup)

def load_core():
    """Unique module prevents experiments from replacing normal test imports."""
    name = "_g360_next_frozen_core"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT/"agentes/gipuzkoa360/portal/tools.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]

@dataclass(frozen=True)
class Execution:
    tool: str
    arguments_json: str
    output_json: str
    versions: dict[str, str]

class Executor:
    def __init__(self, data_dir=None):
        self.registry = CapabilityRegistry()
        self.core = load_core()
        self.data_dir = Path(data_dir or ROOT/"datos_preparados")
        self.analysis = self.core.TerritorialAnalysis(self.core.DataRepository(self.data_dir))
        self.call_count = 0
        self.versions = {"DATA_VERSION": hashlib.sha256((self.data_dir/"runtime_manifest.json").read_bytes()).hexdigest(),
                         "RUNTIME_VERSION": RUNTIME_VERSION, "CAPABILITY_VERSION": CAPABILITY_VERSION,
                         "PROMPT_VERSION": PROMPT_VERSION, "BENCHMARK_VERSION": BENCHMARK_VERSION}

    def execute(self, plan):
        cap = self.registry.resolve(plan.candidate_capability or "")
        if plan.out_of_scope or plan.missing_inputs or plan.ambiguities or not cap or cap.status != "ACTIVE":
            raise ValueError("Plan is not executable")
        if set(plan.parameters) - set(cap.parameters):
            raise ValueError("Unregistered parameter")
        checked = Planner(self.registry).plan(cap.id, plan.parameters)
        if checked.ambiguities or checked.missing_inputs:
            raise ValueError("Invalid plan parameters")
        p = copy.deepcopy(plan.parameters)
        canonical(p)
        operations = {
            "summary": lambda: self.analysis.resumen(p["municipio"], p.get("periodo")),
            "comparison": lambda: self.analysis.comparar(p["municipios"], p.get("grupo_edad", "65"), p.get("categoria_servicio"), p.get("umbral_km", 1), p.get("periodo")),
            "aging": lambda: self.analysis.envejecimiento(p.get("grupo_edad", "65"), p.get("medida", "percentage"), p.get("periodo"), p.get("top_n", 10)),
            "access": lambda: self.analysis.acceso(p["categoria_servicio"], p.get("umbral_km", 1), p.get("periodo"), p.get("municipios")),
            "coincidence": lambda: self.analysis.coincidencia(p["categoria_servicio"], p.get("grupo_edad", "65"), p.get("umbral_km", 1), p.get("periodo"), p.get("cuantil", .75)),
            "scenario": lambda: self.analysis.escenario(p["accion"], p["categoria_servicio"], p.get("umbral_km", 1), p.get("periodo"), p.get("latitud"), p.get("longitud"), p.get("service_id"), p.get("nuevo_umbral_km")),
            "source": lambda: self.analysis.fuente(p.get("source_id")),
        }
        self.call_count += 1
        raw = self.core._safe(operations[cap.id], result_kind=cap.id)
        strict_loads(raw)
        return Execution(cap.tool, canonical(p), raw, dict(self.versions))

def render(output):
    """Only verbatim evidence and fixed caveats; no free-text numerical inference."""
    prefix = "ESCENARIO HIPOTÉTICO. " if "scenario" in output else "Evidencia territorial. "
    return prefix + canonical({k: output.get(k) for k in ("data", "summary", "scenario", "unit", "period", "sources", "method", "rows_used", "warnings", "limitations")})

@dataclass(frozen=True)
class Review:
    status: str
    reasons: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    safe_next_action: str
    evidence_json: str = ""
    evidence_sha256: str = ""
    versions: dict[str, str] = field(default_factory=dict)

class EvidenceCritic:
    """Compare to an authoritative re-execution, not to an untrusted numerical claim."""
    def __init__(self, executor):
        self.executor = executor

    def review(self, plan, raw, draft=None):
        reasons, missing = [], []
        try:
            obj = strict_loads(raw)
            if not isinstance(obj, dict) or obj.get("status") != "ok":
                raise ValueError("Non-success result")
            for key in ("sources", "unit", "method", "limitations"):
                if not obj.get(key):
                    missing.append(key)
            if plan.candidate_capability != "source" and not obj.get("period"):
                missing.append("period")
            if type(obj.get("rows_used")) is not int or obj["rows_used"] < 0:
                missing.append("rows_used")
            catalog = {s["source_id"] for s in self.executor.analysis.repo.metadata()["sources"]}
            if any(s.get("source_id") not in catalog for s in obj.get("sources", [])):
                reasons.append("unknown_source")
            expected = strict_loads(self.executor.execute(plan).output_json)
            # Exact canonical comparison also rejects booleans substituted for numbers.
            if canonical(obj) != canonical(expected):
                reasons.append("output_not_equal_to_trusted_recalculation")
            if plan.candidate_capability == "scenario" and not obj.get("scenario"):
                missing.append("scenario")
            if draft is not None and draft != render(obj):
                reasons.append("unapproved_claim_or_number: only evidence-bound rendering is supported")
            if missing or reasons:
                return Review("FAIL", tuple(reasons), tuple(missing), "Block; inspect evidence and request correction.")
            evidence = canonical(obj)
            return Review("WARN" if obj.get("warnings") else "PASS", tuple(obj.get("warnings", [])), (),
                          "Render with original limitations.", evidence, hashlib.sha256(evidence.encode()).hexdigest(),
                          dict(self.executor.versions))
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
            return Review("FAIL", (type(exc).__name__ + ": invalid evidence or plan",), tuple(missing), "Block normal answer.")

class Composer:
    def compose(self, review):
        if review.status not in {"PASS", "WARN"}:
            return {"blocked": True, "response": "No hay evidencia validada suficiente para responder."}
        if hashlib.sha256(review.evidence_json.encode()).hexdigest() != review.evidence_sha256:
            return {"blocked": True, "response": "La evidencia cambió después de la revisión."}
        return {"blocked": False, "response": render(strict_loads(review.evidence_json)), "versions": review.versions}

class NextSession:
    """Caller owns this bounded session object; never global cross-user memory."""
    def __init__(self):
        self.planner, self.executor, self.composer = Planner(), Executor(), Composer()
        self.critic = EvidenceCritic(self.executor)
        self.previous = None

    def ask(self, intent, parameters=None):
        plan = self.planner.plan(intent, parameters, self.previous)
        if plan.out_of_scope or plan.missing_inputs or plan.ambiguities:
            return {"plan": asdict(plan), "blocked": True, "response": "Fuera de alcance o faltan parámetros válidos."}
        execution = self.executor.execute(plan)
        review = self.critic.review(plan, execution.output_json)
        if review.status in {"PASS", "WARN"}:
            self.previous = plan
        return {"plan": asdict(plan), "tool": execution.tool, "arguments": strict_loads(execution.arguments_json),
                "output": strict_loads(execution.output_json), "critic": asdict(review), **self.composer.compose(review)}
