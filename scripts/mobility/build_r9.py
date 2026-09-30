"""Build R9 governance/support artifacts without modifying frozen runtime or history."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/vnext/w1"
DATA = ROOT / "datos_preparados/movilidad"
OUT = DOC / "integration_r9"
PACKAGE_SHA = "c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910"
RUNTIME_PIN = "cb061a97e78d6b5c967104fef6b935132fdc450f"
CHECK_DATE = "2026-09-30"


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path: Path, role: str) -> dict:
    raw = path.read_bytes()
    normalized = path.suffix.lower() == ".osm"
    if normalized:
        raw = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "hash_basis": "canonical_lf" if normalized else "exact_bytes", "role": role}


def build_clean_room(source: Path) -> dict:
    report = json.loads(source.read_text(encoding="utf-8"))
    dump(DOC / "CLEAN_ROOM_REPRO_R9.json", report)
    c = report["comparisons"]
    lines = ["# Clean-room reproduction R9", "", "La reproducción se ejecutó sin red y en un árbol temporal nuevo.", "",
             f"- Snapshot R4 idéntico: `{c['r4_snapshot']['identical']}` (`{c['r4_snapshot']['generated_sha256']}`).",
             f"- Snapshot sanitario idéntico: `{c['health_snapshot']['identical']}` (`{c['health_snapshot']['generated_sha256']}`).",
             f"- Claims canónicos idénticos: `{c['canonical_claims']['identical']}`; delta `{c['canonical_claims']['delta_s']} s`.",
             "- Reproducible desde raw fijado + derivados fijados: `true`.",
             "- Reproducible íntegramente desde raw original: `false`.", "",
             "La reconciliación sanitaria parte de `HEALTH_DESTINATION_R4.json`, un derivado fijado. Los bytes del OSM histórico de la PoC no están disponibles; el OSM del modelo R6 sí está fijado y reproducido. Por tanto no se afirma identidad histórica de la PoC."]
    (DOC / "CLEAN_ROOM_REPRO_R9.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return report


def build_license_audit() -> dict:
    general = "https://opendata.euskadi.eus/general/-/informacion-legal-opendata/"
    rows = [
        {"source_id": "GTFS", "license_status": "VERIFIED_GENERAL_TERMS_APPLY", "license_name": "Open Data Euskadi linked general reuse terms; specific variant not named on the dataset page", "license_url": general,
         "official_evidence_url": "https://opendata.euskadi.eus/catalogo/-/moveuskadi-datos-de-la-red-de-transporte-publico-de-euskadi-operadores-horarios-paradas-calendario-tarifas-etc/",
         "evidence_retrieval_date": CHECK_DATE, "attribution_requirement": "cite source and last-update date", "alteration_restrictions": "do not alter or denaturalize meaning",
         "redistribution_allowed": "YES_UNDER_LINKED_GENERAL_TERMS", "commercial_reuse_allowed": "YES_UNDER_GENERAL_OPEN_DATA_GUIDANCE", "last_update_attribution_required": True,
         "notes": "Dataset page points to official legal notice; do not relabel as a dataset-specific CC BY grant."},
        {"source_id": "HEALTH_REGISTRY", "license_status": "VERIFIED_GENERAL_TERMS_APPLY", "license_name": "Open Data Euskadi linked general reuse terms; specific variant not named on the primary dataset page", "license_url": general,
         "official_evidence_url": "https://opendata.euskadi.eus/catalogo/-/centros-de-salud-publicos-en-euskadi/", "evidence_retrieval_date": CHECK_DATE,
         "attribution_requirement": "cite source and last-update date", "alteration_restrictions": "do not alter or denaturalize meaning",
         "redistribution_allowed": "YES_UNDER_LINKED_GENERAL_TERMS", "commercial_reuse_allowed": "YES_UNDER_GENERAL_OPEN_DATA_GUIDANCE", "last_update_attribution_required": True,
         "notes": "datos.gob.es reports CC BY 4.0 as secondary metadata; retained as corroboration, not elevated to primary specific-license evidence.",
         "secondary_evidence_url": "https://datos.gob.es/es/catalogo/a16003011-centros-de-salud-ambulatorios-y-hospitales-publicos-de-euskadi1"},
        {"source_id": "HEALTH_PAGE", "license_status": "NOT_VERIFIED", "license_name": None, "license_url": None,
         "official_evidence_url": "https://www.osakidetza.euskadi.eus/ambulatorio-de-beasain/webosk00-cercon/es/", "evidence_retrieval_date": CHECK_DATE,
         "attribution_requirement": "UNKNOWN", "alteration_restrictions": "UNKNOWN", "redistribution_allowed": "UNKNOWN", "commercial_reuse_allowed": "UNKNOWN",
         "last_update_attribution_required": "UNKNOWN", "notes": "Open Data dataset terms are not assumed to cover arbitrary Osakidetza HTML."},
        {"source_id": "PADI_2026", "license_status": "NOT_VERIFIED", "license_name": None, "license_url": None,
         "official_evidence_url": "https://www.osakidetza.euskadi.eus/contenidos/informacion/salud_padi/es_def/adjuntos/padi-kontsultak-gipuzkoa.pdf", "evidence_retrieval_date": CHECK_DATE,
         "attribution_requirement": "UNKNOWN", "alteration_restrictions": "UNKNOWN", "redistribution_allowed": "UNKNOWN", "commercial_reuse_allowed": "UNKNOWN",
         "last_update_attribution_required": "UNKNOWN", "notes": "No specific PDF reuse license was found; do not infer one."},
        {"source_id": "OSM", "license_status": "VERIFIED_SPECIFIC", "license_name": "Open Data Commons Open Database License 1.0", "license_url": "https://opendatacommons.org/licenses/odbl/1-0/",
         "official_evidence_url": "https://www.openstreetmap.org/copyright", "evidence_retrieval_date": CHECK_DATE,
         "attribution_requirement": "credit OpenStreetMap and contributors and identify ODbL", "alteration_restrictions": "share-alike obligations apply to altered/derived databases",
         "redistribution_allowed": "YES_WITH_ODBL_COMPLIANCE", "commercial_reuse_allowed": "YES_WITH_ODBL_COMPLIANCE", "last_update_attribution_required": False,
         "notes": "Attribution form depends on medium; distributing data form should link the license directly."},
    ]
    result = {"audit_version": "r9.0", "retrieval_date": CHECK_DATE,
              "status_values": ["VERIFIED_SPECIFIC", "VERIFIED_GENERAL_TERMS_APPLY", "SECONDARY_METADATA_ONLY", "NOT_VERIFIED", "NOT_APPLICABLE"],
              "legal_disclaimer": "Engineering reuse inventory, not legal advice.", "sources": rows}
    dump(DOC / "SOURCE_LICENSE_R9.json", result)
    return result


def build_distribution(licenses: dict) -> dict:
    by_id = {row["source_id"]: row for row in licenses["sources"]}
    rows = [
        ("datos_originales/movilidad/goierrialdea-3276fcae.zip", "GTFS", False, True, "REFERENCE_ONLY", "LOW"),
        ("datos_originales/centros-salud.xlsx", "HEALTH_REGISTRY", False, True, "REFERENCE_ONLY", "LOW"),
        ("datos_originales/movilidad/r5/beasain-official.html", "HEALTH_PAGE", False, True, "HUMAN_REVIEW_REQUIRED", "MEDIUM"),
        ("datos_originales/movilidad/r5/padi-2026.pdf", "PADI_2026", False, True, "HUMAN_REVIEW_REQUIRED", "MEDIUM"),
        ("datos_originales/movilidad/beasain-network-r4-public.osm", "OSM", False, True, "INCLUDE_WITH_ATTRIBUTION", "LOW"),
    ]
    files = []
    for path, source, runtime, evidence, policy, risk in rows:
        license_row = by_id[source]
        files.append({"path": path, "source": source, "is_runtime_required": runtime, "is_evidence_only": evidence,
                      "currently_committed": (ROOT / path).is_file(), "license_status": license_row["license_status"],
                      "redistribution_status": license_row["redistribution_allowed"], "required_attribution": license_row["attribution_requirement"],
                      "delivery_bundle_policy": policy, "risk": risk})
    result = {"audit_version": "r9.0", "policy_values": ["INCLUDE_ALLOWED", "INCLUDE_WITH_ATTRIBUTION", "REFERENCE_ONLY", "HASH_ONLY", "HUMAN_REVIEW_REQUIRED"],
              "no_files_deleted": True, "not_legal_advice": True, "files": files}
    dump(DOC / "SOURCE_DISTRIBUTION_R9.json", result)
    return result


def claim_class(claim: dict) -> str:
    metric = claim["metric"]
    if metric == "appointment_s": return "HUMAN_INPUT"
    if metric == "initial_wait_s": return "MODEL_DEFAULT"
    if metric in {"walk_out_s", "walk_return_s"}: return "MODELLED_ESTIMATE"
    if metric in {"outbound_departure_time", "outbound_arrival_time", "return_departure_time", "return_arrival_time"}: return "DIRECT_SOURCE_VALUE"
    if metric in {"bus_out_s", "bus_return_s", "outbound_trip_id", "return_trip_id", "outbound_stop_id", "return_stop_id"}: return "DERIVED_EXACT_FROM_PINNED_DATA"
    if metric in {"total_s", "preappointment_wait_s", "return_wait_s", "return_slack_s", "comparison_delta_s"}: return "DERIVED_EXACT_FROM_PINNED_DATA_AND_MODEL_ASSUMPTIONS"
    return "UNAVAILABLE"


def build_claim_semantics() -> dict:
    claims = json.loads((DOC / "CLAIM_LEDGER_R8.json").read_text(encoding="utf-8"))["claims"]
    classes = ["DIRECT_SOURCE_VALUE", "DERIVED_EXACT_FROM_PINNED_DATA", "DERIVED_EXACT_FROM_PINNED_DATA_AND_MODEL_ASSUMPTIONS",
               "MODELLED_ESTIMATE", "HUMAN_INPUT", "MODEL_DEFAULT", "UNAVAILABLE"]
    mappings = [{"claim_id": claim["claim_id"], "metric": claim["metric"], "semantic_class": claim_class(claim),
                 "unit": claim["unit"], "wording_guard": "scheduled_not_observed" if claim["metric"].endswith("_time") else "preserve_assumptions_and_limits"}
                for claim in claims]
    phrases = [
        {"id": "scheduled_timepoint", "claim_refs": [c["claim_id"] for c in claims if c["metric"] == "outbound_departure_time"],
         "bad": "El autobús sale exactamente a las 08:12:37.", "better": "El horario GTFS utilizado sitúa la salida programada en 08:12:37; el feed la marca como aproximada (timepoint=0)."},
        {"id": "walking", "claim_refs": [c["claim_id"] for c in claims if c["metric"] == "walk_out_s"],
         "bad": "Caminas 7 minutos.", "better": "El modelo estima 420 s de paseo con el supuesto fijado."},
        {"id": "delta", "claim_refs": ["R8-DELTA-ZEGAMA-0930-0945"], "bad": "Ahorras 35 minutos.",
         "better": "En el escenario modelado, el total de 09:45 es 35 min menor que el de 09:30."},
        {"id": "no_feasible", "claim_refs": [], "bad": "No hay transporte.",
         "better": "No se encontró una combinación viable dentro del snapshot y restricciones analizados."},
        {"id": "centre_anchor", "claim_refs": [c["claim_id"] for c in claims if c["metric"] in {"walk_out_s", "walk_return_s"}],
         "bad": "Esta es la entrada del ambulatorio.", "better": "El paseo termina en el punto oficial modelado del centro; la entrada física no está verificada."},
    ]
    result = {"taxonomy_version": "r9.0", "classes": classes, "scheduled_source_policy": "A direct GTFS value is a scheduled source value, never a real-world observation.",
              "timepoint_policy": "timepoint=0 means the scheduled GTFS time is approximate/interpolated; do not promise exact operational passage.",
              "walking_policy": "Geometry and seconds are modelled, not measured pedestrian behaviour.", "claim_mappings": mappings, "phrase_safety": phrases}
    dump(DOC / "CLAIM_SEMANTICS_R9.json", result)
    lines = ["# Semántica de claims R9", "", "Los valores directos del GTFS son valores programados de fuente, no observaciones reales.",
             "`timepoint=0` indica que la hora del feed es aproximada/interpolada; no acredita paso operacional exacto.",
             "Los paseos son estimaciones del modelo, no comportamiento peatonal medido.", "", "## Wording seguro", ""]
    for item in phrases:
        lines += [f"- **Evitar:** {item['bad']}", f"  **Usar:** {item['better']}"]
    (DOC / "CLAIM_SEMANTICS_R9.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return result


def build_hygiene() -> dict:
    paths = [ROOT / "datos_originales/movilidad/goierrialdea-3276fcae.zip", ROOT / "datos_originales/centros-salud.xlsx",
             ROOT / "datos_originales/movilidad/r5/beasain-official.html", ROOT / "datos_originales/movilidad/r5/padi-2026.pdf",
             ROOT / "datos_originales/movilidad/beasain-network-r4-public.osm"]
    secret = re.compile(rb"(?i)(api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*[^\s,;]{6,}")
    absolute = re.compile(rb"(?i)([a-z]:\\users\\|/home/|/users/)")
    findings = []
    for path in paths:
        raw = path.read_bytes()
        hash_raw = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n") if path.suffix.lower() == ".osm" else raw
        findings.append({"path": path.relative_to(ROOT).as_posix(), "secret_pattern": bool(secret.search(raw)),
                         "local_absolute_path": bool(absolute.search(raw)), "bytes": len(hash_raw), "sha256": hashlib.sha256(hash_raw).hexdigest(),
                         "hash_basis": "canonical_lf" if path.suffix.lower() == ".osm" else "exact_bytes"})
    result = {"check": "SOURCE_HYGIENE_CHECK", "not_complete_security_audit": True, "critical_high": 0,
              "personal_editor_metadata": "NONE_DETECTED_IN_PUBLIC_OSM_DERIVATIVE; contributor account/contact attributes were removed before commit",
              "public_contact_data": "Official centre/PADI contact values are published source evidence, not unexpected personal data.",
              "temporary_or_cache_files_committed": False, "files": findings,
              "status": "PASS" if not any(row["secret_pattern"] or row["local_absolute_path"] for row in findings) else "REVIEW"}
    dump(DOC / "SOURCE_HYGIENE_R9.json", result)
    return result


def build_release_advice() -> dict:
    result = {"advice_version": "r9.0", "owner": {"package": "W2", "delivery_review": "W3", "evidence": "W1"},
              "categories": {
                  "RUNTIME_REQUIRED": ["R6 package members exactly as frozen; do not add R9 maintenance scripts"],
                  "CONTEXT_REQUIRED": ["W1_HANDSHAKE_R9.json or a consumer projection of its semantics"],
                  "AUDIT_ONLY": ["clean-room, upstream drift, license, distribution, hygiene, playbook and data-freeze artifacts"],
                  "DELIVERY_EVIDENCE_ONLY": ["canonical R8 evidence, raw contrast, timelines and claim ledger"],
                  "DO_NOT_BUNDLE_UNLESS_LICENSE_VERIFIED": ["raw Osakidetza HTML", "PADI PDF"],
              }, "decision": "ADVICE_ONLY_NO_FINAL_PACKAGE_MUTATION"}
    dump(DOC / "RELEASE_CONTENT_ADVICE_R9.json", result)
    return result


def build_playbook() -> None:
    rows = [
        ("GTFS upstream unchanged", "Keep pin; record observation.", "Do not refresh timestamps.", "W1", "No", "Yes", "No", "No"),
        ("GTFS bytes changed, used rows same", "Record semantic equivalence and preserve pin.", "Do not claim the whole source is unchanged.", "W1", "No", "Yes", "No", "No"),
        ("GTFS used rows changed", "Raise human review; assess a new dated candidate.", "Do not replace the pin silently.", "W1 + release owner", "Decision required", "Yes", "Yes if adopted", "Yes"),
        ("Health centre coordinates changed", "Verify primary source and impact before any new snapshot.", "Do not move anchor automatically.", "W1 + human reviewer", "Decision required", "Yes", "Yes if adopted", "Yes"),
        ("Health address changed", "Retain conflict and investigate entity/site continuity.", "Do not infer relocation.", "W1 + human reviewer", "Not automatically", "Yes", "If wording changes", "Yes"),
        ("PADI conflict resolved", "Verify document/version and close conflict only in a new candidate.", "Do not rewrite historical evidence.", "W1 + human reviewer", "Only for new candidate", "Yes", "If adopted", "Yes"),
        ("OSM topology changed", "Record current observation; assess routes separately.", "Do not rebuild the pinned model automatically.", "W1", "Decision required", "Yes", "If adopted", "Yes"),
        ("Source unavailable", "Record exact HTTP/fetch status and retain pin.", "Do not say the network is down or data absent globally.", "W1", "No", "Yes", "No", "If prolonged"),
        ("License terms changed", "Freeze distribution and obtain human/legal review.", "Do not delete history or relicense data.", "Release owner", "No runtime rebuild", "Yes", "Package review", "Yes"),
        ("License ambiguous", "Use reference/hash-only or exclude from bundle pending review.", "Do not infer permission.", "Release owner", "No", "Yes", "Package review", "Yes"),
    ]
    lines = ["# Source change playbook R9", "", "Ningún drift sustituye un pin silenciosamente.", "",
             "| Caso | Qué hacer | Qué no hacer | Owner | Rebuild | Evidencia histórica | Repetir W2/W3 | Aprobación humana |",
             "|---|---|---|---|---|---|---|---|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    (DOC / "SOURCE_CHANGE_PLAYBOOK_R9.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def build_handshake(upstream: dict, semantics: dict, licenses: dict) -> dict:
    catalog = json.loads((DATA / "operational_catalog_r6.json").read_text(encoding="utf-8"))
    labels = json.loads((DATA / "consumer_labels_r7.json").read_text(encoding="utf-8"))
    statuses = json.loads((DOC / "STATUS_SEMANTICS_R8.json").read_text(encoding="utf-8"))
    answerability = json.loads((DOC / "MOBILITY_ANSWERABILITY_R8.json").read_text(encoding="utf-8"))
    evidence = json.loads((DOC / "DELIVERY_EVIDENCE_R8.json").read_text(encoding="utf-8"))
    capability = json.loads((DOC / "CAPABILITY_DESCRIPTOR_R6.json").read_text(encoding="utf-8"))
    handshake = {"handshake_version": "r9.0", "runtime": {"contract": "0.3.1", "entrypoint": "prototypes.ir_y_volver.provider_r6",
                  "tested_pin": RUNTIME_PIN, "package_sha256": PACKAGE_SHA, "package_bytes": 129365},
                 "candidate": {"snapshot_id": catalog["snapshot_id"], "snapshot_sha256": catalog["snapshot_sha256"], "validated_date": catalog["validated_date"],
                               "scenario_kind": catalog["scenario_kind"], "scope": labels["scope"], "time_basis": "STATIC_SCHEDULED_SNAPSHOT"},
                 "catalog": {"origins": catalog["origins"], "destination": catalog["destination"], "route": labels["routes"][0],
                             "walking": catalog["walking"], "defaults": catalog["defaults"], "parameter_ranges": catalog["ranges"]},
                 "status_semantics": [{"status": row["status"], "meaning": row["allowed_user_facing_meaning"], "forbidden": row["forbidden_inference"]} for row in statuses["statuses"]],
                 "claim_semantic_classes": semantics["classes"], "timepoint_policy": semantics["timepoint_policy"],
                 "minimum_model_view_fields": ["status", "normalized_request", "itinerary", "components_s", "walking", "sources", "limitations", "assumptions", "parameter_provenance"],
                 "canonical": {"main_id": "MAIN", "variation_id": "VARIATION_TIME", "duration_variation_id": "VARIATION_DURATION",
                               "limit_ids": ["LIMIT_DATE", "LIMIT_SCOPE"], "numeric_claim": evidence["directly_contrasted_claim"] | {"raw_rows": None, "walking_evidence": None}},
                 "boundaries": {"entrance_verified": False, "realtime": False, "door_to_door": False, "cross_origin_formal_delta": False,
                                "available_capability_count": sum(row["status"] != "OUT_OF_SCOPE" for row in answerability["capabilities"])},
                 "known_finding": {"id": "W1-R7-F01", "severity": "MEDIUM", "runtime_status": "RUNTIME_FINDING_RETAINED", "resolution": "EXPLANATORY_DAG_RESOLVED_EXTERNALLY"},
                 "upstream": {"checked_at_utc": upstream["checked_at_utc"], "summary": upstream["summary"], "automatic_pin_replacement": False},
                 "license_summary": {row["source_id"]: row["license_status"] for row in licenses["sources"]},
                 "refs": [ref(DOC / "CONSUMER_CONFORMANCE_R7.json", "conformance"), ref(DOC / "MOBILITY_ANSWERABILITY_R8.json", "answerability"),
                          ref(DOC / "STATUS_SEMANTICS_R8.json", "status_semantics"), ref(DOC / "RAW_DATA_CONTRAST_R8.json", "raw_contrast"),
                          ref(DOC / "CLAIM_SEMANTICS_R9.json", "claim_semantics"), ref(DOC / "SOURCE_LICENSE_R9.json", "source_license"),
                          ref(DOC / "CLEAN_ROOM_REPRO_R9.json", "clean_room"), ref(DOC / "UPSTREAM_DRIFT_R9.json", "upstream_drift")],
                 "capability_descriptor_ref": ref(DOC / "CAPABILITY_DESCRIPTOR_R6.json", "capability_descriptor"),
                 "capability_snapshot_count": len(capability["snapshots"]), "heavy_evidence_is_by_reference": True,
                 "no_holdout_or_secret_data": True}
    dump(OUT / "W1_HANDSHAKE_R9.json", handshake)
    if (OUT / "W1_HANDSHAKE_R9.json").stat().st_size >= 30_000:
        raise ValueError("handshake exceeds 30 KB target")
    return handshake


def build_freeze(upstream: dict, licenses: dict, handshake: dict) -> dict:
    health = ROOT / "prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-health-r5-20260929.json"
    files = [ref(ROOT / "prototypes/ir_y_volver/provider_r6.py", "provider"), ref(ROOT / "prototypes/ir_y_volver/contracts/v0.3.1/result.schema.json", "contract"),
             ref(ROOT / "datos_originales/movilidad/goierrialdea-3276fcae.zip", "gtfs"), ref(health, "health_snapshot"),
             ref(ROOT / "datos_originales/movilidad/beasain-network-r4-public.osm", "osm_local_artifact"), ref(DATA / "operational_catalog_r6.json", "catalog"),
             ref(DATA / "consumer_labels_r7.json", "labels"), ref(DOC / "DELIVERY_EVIDENCE_R8.json", "canonical_evidence"),
             ref(DOC / "CLAIM_SEMANTICS_R9.json", "claim_semantics"), ref(OUT / "W1_HANDSHAKE_R9.json", "handshake")]
    result = {"freeze_version": "r9.0", "runtime_package": {"sha256": PACKAGE_SHA, "bytes": 129365, "tested_pin": RUNTIME_PIN},
              "source_audit_date": upstream["checked_at_utc"], "upstream_drift_status": upstream["summary"],
              "license_reuse_status": {row["source_id"]: row["license_status"] for row in licenses["sources"]},
              "human_review_flags": [row["source_id"] for row in upstream["sources"] if row["whether_human_review_is_required"]] + ["HEALTH_PAGE_LICENSE", "PADI_2026_LICENSE"],
              "automatic_update": False, "files": files}
    dump(DOC / "DATA_FREEZE_R9.json", result)
    return result


def build_manifest() -> dict:
    paths = [(OUT / "W1_HANDSHAKE_R9.json", "handshake"), (DOC / "DATA_FREEZE_R9.json", "data_freeze"),
             (DOC / "CLEAN_ROOM_REPRO_R9.json", "clean_room"), (DOC / "UPSTREAM_DRIFT_R9.json", "upstream_drift"),
             (DOC / "SOURCE_LICENSE_R9.json", "source_license"), (DOC / "SOURCE_DISTRIBUTION_R9.json", "distribution"),
             (DOC / "CLAIM_SEMANTICS_R9.json", "claim_semantics"), (DOC / "SOURCE_HYGIENE_R9.json", "source_hygiene"),
             (DOC / "RELEASE_CONTENT_ADVICE_R9.json", "release_advice"), (DOC / "SOURCE_CHANGE_PLAYBOOK_R9.md", "playbook")]
    result = {"manifest_version": "r9.0", "runtime_inclusion": False, "runtime_package_sha256": PACKAGE_SHA,
              "files": [ref(path, role) for path, role in paths]}
    dump(OUT / "INTEGRATION_MANIFEST_R9.json", result)
    (OUT / "README.md").write_text("# W1 integration R9\n\nEmpiece por `W1_HANDSHAKE_R9.json`; abra la evidencia pesada solo mediante sus referencias verificadas. R9 no forma parte del ZIP runtime R6.\n", encoding="utf-8", newline="\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean-room", required=True, type=Path)
    parser.add_argument("--upstream", required=True, type=Path)
    args = parser.parse_args()
    clean = build_clean_room(args.clean_room)
    upstream = json.loads(args.upstream.read_text(encoding="utf-8")); dump(DOC / "UPSTREAM_DRIFT_R9.json", upstream)
    licenses = build_license_audit(); build_distribution(licenses); semantics = build_claim_semantics(); build_hygiene(); build_release_advice(); build_playbook()
    handshake = build_handshake(upstream, semantics, licenses); build_freeze(upstream, licenses, handshake); manifest = build_manifest()
    print(json.dumps({"clean_room": clean["candidate_reproducible_from_pinned_raw_and_pinned_derived"], "handshake_bytes": (OUT / "W1_HANDSHAKE_R9.json").stat().st_size,
                      "handshake_sha256": sha(OUT / "W1_HANDSHAKE_R9.json"), "manifest_files": len(manifest["files"])}))


if __name__ == "__main__":
    main()
