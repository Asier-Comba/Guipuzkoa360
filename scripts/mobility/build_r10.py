"""Build compact R10 consumer support without mutating frozen runtime or R9 evidence."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from prototypes.ir_y_volver import provider_r5, provider_r6
from scripts.mobility.build_r9 import capability_status_counts


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/vnext/w1"
OUT = DOC / "integration_r10"
R9 = DOC / "integration_r9/W1_HANDSHAKE_R9.json"
PACKAGE_SHA = "c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910"
RUNTIME_PIN = "cb061a97e78d6b5c967104fef6b935132fdc450f"


def encoded(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path: Path, role: str) -> dict:
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "role": role, "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(), "hash_basis": "exact_bytes"}


BASE = {
    "origin_id": "zegama_center_stops",
    "destination_id": "beasain_official_centre_anchor",
    "date": "2026-09-29",
    "appointment_time": "09:45",
    "duration_minutes": 20,
}


def explain(status: str, code: str | None) -> str:
    exact = {
        ("unknown", "date_not_validated"): "La fecha solicitada no está validada por este snapshot.",
        ("unknown", "invalid_health_snapshot"): "La evidencia sanitaria fijada no pudo validarse o cargarse; no se puede verificar el resultado.",
        ("unsupported", "catalog_scope"): "El origen o destino queda fuera del catálogo fijado.",
        ("unsupported", "cross_day_appointment"): "La cita termina fuera del día civil admitido por el modelo.",
        ("unsupported", "multiday_service"): "El viaje usa tiempos fuera del día civil admitido por el modelo.",
        ("error", "invalid_request"): "La petición contiene un formato o valor no válido.",
        ("no_feasible_journey", "no_pair_in_complete_direct_search"): "No se encontró una combinación viable tras completar la búsqueda dentro del snapshot y restricciones analizados.",
    }
    if (status, code) in exact:
        return exact[(status, code)]
    generic = {
        "unknown": "La evidencia disponible no permite verificar el resultado; no se atribuye una causa no observada.",
        "unsupported": "La petición queda fuera del alcance declarado; no implica un fallo del sistema.",
        "error": "No se pudo procesar la petición; consulte el código técnico sin atribuir una causa no observada.",
        "no_feasible_journey": "No se encontró una combinación viable dentro del alcance analizado; no demuestra ausencia global de transporte.",
        "ok": "Se encontró un itinerario programado y modelado dentro del alcance fijado.",
    }
    return generic.get(status, "La evidencia no permite una explicación más específica.")


def observed(request: dict) -> dict:
    result = provider_r6.plan_visit(request)
    error = result.get("error") or {}
    return {"request": request, "status": result["status"], "error": error,
            "user_facing": explain(result["status"], error.get("code")),
            "technical_code_preserved": error.get("code"), "fixture_kind": "PROVIDER_OBSERVED"}


def build_status_semantics() -> dict:
    rows = [
        observed({**BASE, "date": "2026-09-30"}),
        observed({**BASE, "destination_id": "outside_catalog"}),
        observed({**BASE, "duration_minutes": "20"}),
        observed({**BASE, "appointment_time": "22:00"}),
        observed({**BASE, "appointment_time": "23:59"}),
    ]
    original = provider_r5._load
    try:
        provider_r5._load = lambda: (_ for _ in ()).throw(ValueError("R10 controlled invalid snapshot fixture"))
        rows.append(observed(BASE))
    finally:
        provider_r5._load = original
    rows.append({"request": None, "status": "unknown", "error": {"code": "future_unknown_code", "message": "fixture"},
                 "user_facing": explain("unknown", "future_unknown_code"), "technical_code_preserved": "future_unknown_code",
                 "fixture_kind": "CONSUMER_FALLBACK_ONLY"})
    return {"mapping_version": "r10.0", "key": "status+error.code", "runtime_changed": False,
            "generic_unknown_rule": "Evidence is insufficient or unverifiable; never invent date, HTTP, network or service absence.",
            "preserve_technical_error_in_audit": True, "cases": rows}


def build_provenance() -> dict:
    requests = {
        "default_omitted": dict(BASE),
        "default_explicit_same_value": {**BASE, "boarding_margin_minutes": 3},
        "explicit_distinct_value": {**BASE, "boarding_margin_minutes": 8},
    }
    rows = []
    for case_id, request in requests.items():
        result = provider_r6.plan_visit(request)
        provenance = {row["field"]: row["origin"] for row in result["parameter_provenance"]}
        rows.append({"case_id": case_id, "request": request, "status": result["status"],
                     "total_s": result["itinerary"]["total_s"],
                     "initial_wait_s": result["components_s"]["initial_wait_s"],
                     "boarding_margin_origin": provenance["boarding_margin_minutes"]})
    return {"version": "r10.0", "runtime_changed": False,
            "rule": "human_explicit means supplied by the caller. In an agent the caller may be an LLM; it does not prove human authorship.",
            "consumer_wording": "Use caller-supplied or default-applied unless human authorship is independently established.",
            "preserve_original_provenance": True, "cases": rows,
            "same_arithmetic_different_provenance": rows[0]["total_s"] == rows[1]["total_s"]}


def build_schema() -> dict:
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "g360-w1-handshake-r10.schema.json",
            "title": "G360 W1 compact consumer handshake R10", "type": "object", "additionalProperties": False,
            "required": ["handshake_version", "runtime", "candidate", "catalog", "boundaries", "status_error_semantics_ref", "caller_provenance_ref", "refs"],
            "properties": {
                "handshake_version": {"const": "r10.0-support"}, "runtime": {"type": "object"},
                "candidate": {"type": "object"}, "catalog": {"type": "object"}, "status_semantics": {"type": "array"},
                "claim_semantic_classes": {"type": "array"}, "timepoint_policy": {"type": "string"},
                "minimum_model_view_fields": {"type": "array"}, "canonical": {"type": "object"},
                "boundaries": {"type": "object"}, "known_finding": {"type": "object"},
                "upstream": {"type": "object"}, "license_summary": {"type": "object"}, "refs": {"type": "array"},
                "capability_descriptor_ref": {"type": "object"}, "capability_snapshot_count": {"type": "integer"},
                "heavy_evidence_is_by_reference": {"type": "boolean"}, "no_holdout_or_secret_data": {"type": "boolean"},
                "support_patch": {"type": "object"}, "status_error_semantics_ref": {"type": "object"},
                "caller_provenance_ref": {"type": "object"}}}


def build() -> dict:
    answerability = json.loads((DOC / "MOBILITY_ANSWERABILITY_R8.json").read_text(encoding="utf-8"))
    counts = capability_status_counts(answerability["capabilities"])
    status = build_status_semantics(); dump(DOC / "STATUS_ERROR_SEMANTICS_R10.json", status)
    provenance = build_provenance(); dump(DOC / "CALLER_PROVENANCE_R10.json", provenance)
    dump(OUT / "W1_HANDSHAKE_R10.schema.json", build_schema())
    errata = {"errata_version": "r10.0", "superseded_support": "r9.0", "runtime_changed": False,
              "defects": [
                  {"id": "R9-HANDSHAKE-CAPABILITY-COUNT", "old": {"available_capability_count": 20},
                   "cause": "UNAVAILABLE was counted as available because only OUT_OF_SCOPE was excluded.", "corrected": counts},
                  {"id": "R9-HANDSHAKE-UNKNOWN-SEMANTICS", "old": "unknown always means date not validated",
                   "cause": "The provider also emits unknown for invalid/unloadable snapshot and may gain other codes.",
                   "corrected_ref": "docs/vnext/w1/STATUS_ERROR_SEMANTICS_R10.json"}],
              "historical_r9_sha256": sha(R9),
              "consumer_action": "Use W1_HANDSHAKE_R10.json; retain R9 only as historical evidence."}
    dump(DOC / "ERRATA_R9_R10.json", errata)
    handshake = copy.deepcopy(json.loads(R9.read_text(encoding="utf-8")))
    handshake["handshake_version"] = "r10.0-support"
    handshake["support_patch"] = {"supersedes_handshake_version": "r9.0", "runtime_changed": False,
                                  "schema_version": "r10.0", "schema_ref": ref(OUT / "W1_HANDSHAKE_R10.schema.json", "schema")}
    handshake["boundaries"].pop("available_capability_count", None)
    handshake["boundaries"]["answerability"] = counts
    handshake["boundaries"]["producer_interfaces"] = {"count": 3,
        "names": ["get_capabilities", "plan_visit", "compare_visits"], "not_equivalent_to_answerability_entries": True}
    handshake["status_error_semantics_ref"] = ref(DOC / "STATUS_ERROR_SEMANTICS_R10.json", "status_error_semantics")
    handshake["caller_provenance_ref"] = ref(DOC / "CALLER_PROVENANCE_R10.json", "caller_provenance")
    handshake["refs"] += [ref(DOC / "ERRATA_R9_R10.json", "errata")]
    dump(OUT / "W1_HANDSHAKE_R10.json", handshake)
    manifest = {"manifest_version": "r10.0", "runtime_inclusion": False,
                "runtime_package_sha256": PACKAGE_SHA, "runtime_tested_pin": RUNTIME_PIN,
                "files": [ref(OUT / "W1_HANDSHAKE_R10.json", "handshake"), ref(OUT / "W1_HANDSHAKE_R10.schema.json", "schema"),
                          ref(DOC / "ERRATA_R9_R10.json", "errata"), ref(DOC / "STATUS_ERROR_SEMANTICS_R10.json", "status_error_semantics"),
                          ref(DOC / "CALLER_PROVENANCE_R10.json", "caller_provenance"),
                          ref(ROOT / "scripts/mobility/verify_candidate_parity_r10.py", "parity_runner")]}
    dump(OUT / "INTEGRATION_MANIFEST_R10.json", manifest)
    (OUT / "README.md").write_text("# W1 integration R10\n\nUse `W1_HANDSHAKE_R10.json`; R9 remains historical. The parity runner is support-only and is not part of runtime R6.\n", encoding="utf-8", newline="\n")
    return {"handshake_bytes": (OUT / "W1_HANDSHAKE_R10.json").stat().st_size,
            "handshake_sha256": sha(OUT / "W1_HANDSHAKE_R10.json"), "counts": counts}


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, allow_nan=False))
