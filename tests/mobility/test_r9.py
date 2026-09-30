import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
from openpyxl import Workbook

from scripts.mobility import audit_upstream_r9, source_watch_r9


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/vnext/w1"


def load(name):
    return json.loads((DOC / name).read_text(encoding="utf-8"))


def digest(path, basis="exact_bytes"):
    raw = path.read_bytes()
    if basis == "canonical_lf":
        raw = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(raw).hexdigest(), len(raw)


def test_clean_room_manifest_is_truthful_and_consistent():
    report = load("CLEAN_ROOM_REPRO_R9.json")
    assert report["network_used"] is False
    assert report["workspace_parent_on_pythonpath"] is False
    assert report["candidate_reproducible_from_pinned_raw_and_pinned_derived"] is True
    assert report["source_to_claim_fully_raw_reproducible"] is False
    assert report["comparisons"]["r4_snapshot"]["identical"] is True
    assert report["comparisons"]["health_snapshot"]["identical"] is True
    assert report["comparisons"]["canonical_claims"]["identical_delta"] is True
    assert report["comparisons"]["canonical_claims"]["delta_s"] == -2100
    classes = {stage["classification"] for stage in report["stages"]}
    assert classes <= {"REPRODUCED_FROM_PINNED_RAW", "REPRODUCED_FROM_PINNED_DERIVED", "SOURCE_BYTES_NOT_AVAILABLE", "NOT_REPRODUCIBLE", "NOT_APPLICABLE"}
    assert not any("C:\\Users" in json.dumps(command) for command in report["commands"])


def test_upstream_drift_uses_closed_classification_and_no_silent_rebuild():
    report = load("UPSTREAM_DRIFT_R9.json")
    allowed = {"UNCHANGED_BYTES", "CHANGED_BYTES_SEMANTICALLY_EQUIVALENT_USED_FIELDS", "CHANGED_METADATA_ONLY", "CHANGED_USED_FIELDS", "SOURCE_UNAVAILABLE", "INDETERMINATE"}
    rows = {row["source_id"]: row for row in report["sources"]}
    assert set(rows) == {"GTFS", "HEALTH_REGISTRY", "HEALTH_PAGE", "PADI_2026", "OSM"}
    assert all(row["classification"] in allowed for row in rows.values())
    assert report["automatic_pin_replacement"] is False
    assert all(row["whether_runtime_rebuild_is_required"] is False for row in rows.values())
    assert rows["GTFS"]["classification"] == "UNCHANGED_BYTES"
    assert rows["PADI_2026"]["classification"] == "UNCHANGED_BYTES"
    assert rows["HEALTH_REGISTRY"]["classification"] == "CHANGED_BYTES_SEMANTICALLY_EQUIVALENT_USED_FIELDS"
    assert rows["HEALTH_PAGE"]["classification"] == "CHANGED_BYTES_SEMANTICALLY_EQUIVALENT_USED_FIELDS"
    assert rows["OSM"]["classification"] == "CHANGED_BYTES_SEMANTICALLY_EQUIVALENT_USED_FIELDS"
    assert sum(report["summary"].values()) == 5


def test_gtfs_canonical_rows_ignore_line_endings_row_order_and_zip_metadata(tmp_path):
    headers = "route_id,route_short_name\n"
    variants = [("1,GO01\n2,X\n", "a.zip"), ("2,X\r\n1,GO01\r\n", "b.zip")]
    hashes = []
    for body, name in variants:
        path = tmp_path / name
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("routes.txt", headers.replace("\n", "\r\n") + body if name == "b.zip" else headers + body)
        with zipfile.ZipFile(path) as archive:
            hashes.append(audit_upstream_r9.stable_hash(audit_upstream_r9.canonical_rows(archive, "routes.txt")))
    assert hashes[0] == hashes[1]


def test_health_semantic_comparison_uses_only_relevant_centre_fields(tmp_path):
    pinned = audit_upstream_r9.health_record(ROOT / "datos_originales/centros-salud.xlsx")
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Nombre", "Código del centro", "LATWGS84", "LONWGS84", "Dirección", "Teléfono", "Unused"])
    sheet.append([pinned["name"], pinned["entity_id"], pinned["latitude"], pinned["longitude"], pinned["address"], pinned["telephone"], "changed metadata"])
    path = tmp_path / "health.xlsx"
    workbook.save(path)
    assert audit_upstream_r9.health_record(path) == pinned


def test_license_and_distribution_structures_are_explicit():
    licenses = load("SOURCE_LICENSE_R9.json")
    allowed = set(licenses["status_values"])
    by_id = {row["source_id"]: row for row in licenses["sources"]}
    assert set(by_id) == {"GTFS", "HEALTH_REGISTRY", "HEALTH_PAGE", "PADI_2026", "OSM"}
    assert all(row["license_status"] in allowed for row in by_id.values())
    assert by_id["OSM"]["license_status"] == "VERIFIED_SPECIFIC"
    assert by_id["HEALTH_PAGE"]["license_status"] == "NOT_VERIFIED"
    assert by_id["PADI_2026"]["license_status"] == "NOT_VERIFIED"
    assert by_id["HEALTH_REGISTRY"]["license_status"] == "VERIFIED_GENERAL_TERMS_APPLY"
    distribution = load("SOURCE_DISTRIBUTION_R9.json")
    policies = set(distribution["policy_values"])
    assert all(row["delivery_bundle_policy"] in policies for row in distribution["files"])
    assert all(row["currently_committed"] for row in distribution["files"])
    assert all(not row["is_runtime_required"] for row in distribution["files"])


def test_claim_semantics_maps_every_r8_claim_without_observation_wording():
    r8 = load("CLAIM_LEDGER_R8.json")["claims"]
    semantics = load("CLAIM_SEMANTICS_R9.json")
    assert len(semantics["claim_mappings"]) == len(r8) == 55
    assert {row["claim_id"] for row in semantics["claim_mappings"]} == {row["claim_id"] for row in r8}
    assert "direct_observation" not in json.dumps(semantics).casefold()
    classes = set(semantics["classes"])
    assert all(row["semantic_class"] in classes for row in semantics["claim_mappings"])
    assert "timepoint=0" in semantics["timepoint_policy"]
    assert "never a real-world observation" in semantics["scheduled_source_policy"]


def test_handshake_is_compact_complete_and_hash_bound():
    path = DOC / "integration_r9/W1_HANDSHAKE_R9.json"
    handshake = json.loads(path.read_text(encoding="utf-8"))
    assert path.stat().st_size < 30_000
    assert handshake["runtime"]["contract"] == "0.3.1"
    assert handshake["runtime"]["entrypoint"] == "prototypes.ir_y_volver.provider_r6"
    assert handshake["runtime"]["package_sha256"] == "c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910"
    assert handshake["candidate"]["validated_date"] == "2026-09-29"
    assert len(handshake["catalog"]["origins"]) == 3
    assert handshake["catalog"]["destination"]["verification"]["entrance_verified"] is False
    assert handshake["boundaries"] == handshake["boundaries"] | {"entrance_verified": False, "realtime": False, "door_to_door": False, "cross_origin_formal_delta": False}
    assert handshake["canonical"]["numeric_claim"]["signed_delta_s"] == -2100
    assert handshake["canonical"]["numeric_claim"]["raw_rows"] is None
    for item in handshake["refs"] + [handshake["capability_descriptor_ref"]]:
        actual, size = digest(ROOT / item["path"], item["hash_basis"])
        assert (actual, size) == (item["sha256"], item["bytes"])


def test_playbook_and_data_freeze_cover_required_governance():
    playbook = (DOC / "SOURCE_CHANGE_PLAYBOOK_R9.md").read_text(encoding="utf-8")
    for phrase in ("GTFS upstream unchanged", "GTFS used rows changed", "Health centre coordinates changed", "PADI conflict resolved", "OSM topology changed", "Source unavailable", "License terms changed", "License ambiguous"):
        assert phrase in playbook
    freeze = load("DATA_FREEZE_R9.json")
    assert freeze["automatic_update"] is False
    assert freeze["runtime_package"]["sha256"] == "c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910"
    for item in freeze["files"]:
        actual, size = digest(ROOT / item["path"], item["hash_basis"])
        assert (actual, size) == (item["sha256"], item["bytes"])


class FakeResponse:
    status = 200
    headers = {"Content-Length": "3"}
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def getcode(self): return self.status
    def read(self, size=-1): return b"abc"


def test_source_watch_allowlist_bounds_and_no_overwrite(tmp_path):
    output = tmp_path / "body.bin"
    result = source_watch_r9.fetch("https://opendata.euskadi.eus/example", output, opener=lambda request, timeout: FakeResponse())
    assert result["status"] == "FETCHED" and output.read_bytes() == b"abc"
    with pytest.raises(FileExistsError):
        source_watch_r9.fetch("https://opendata.euskadi.eus/example", output, opener=lambda request, timeout: FakeResponse())
    for url in ("http://opendata.euskadi.eus/example", "https://example.com/example", "https://opendata.euskadi.eus/example?token=x"):
        with pytest.raises(ValueError):
            source_watch_r9.validate_url(url)


def test_integration_manifest_and_source_hygiene_are_consistent():
    manifest = load("integration_r9/INTEGRATION_MANIFEST_R9.json")
    assert manifest["runtime_inclusion"] is False
    for item in manifest["files"]:
        actual, size = digest(ROOT / item["path"], item["hash_basis"])
        assert (actual, size) == (item["sha256"], item["bytes"])
    hygiene = load("SOURCE_HYGIENE_R9.json")
    assert hygiene["check"] == "SOURCE_HYGIENE_CHECK"
    assert hygiene["not_complete_security_audit"] is True
    assert hygiene["critical_high"] == 0 and hygiene["status"] == "PASS"
    assert all(not row["secret_pattern"] and not row["local_absolute_path"] for row in hygiene["files"])


def test_runtime_r7_and_r8_remain_frozen():
    expected = {
        "prototypes/ir_y_volver/provider_r6.py": "c9fe7e4c8078ba7f9bf2eb2a51e050b729d9f01e6021dbcc6909f951d2e936e8",
        "prototypes/ir_y_volver/contracts/v0.3.1/result.schema.json": "5408f0869cc243f901ce5d142865af968bac00b02113cfa0e793ed2b1a96226a",
        "docs/vnext/w1/CONSUMER_CONFORMANCE_R7.json": "4eb364265710336ecdd86b2c541953f130f3b0a80bbefc9cf1f27904bac55dea",
        "docs/vnext/w1/METAMORPHIC_STRESS_R7.json": "8c337e5c618a189f9a2aaec5ab4e4bfa6e3f18e76847b1a3f6c8dd7d6cb3a82f",
        "docs/vnext/w1/DELIVERY_EVIDENCE_R8.json": "578fbd5140185fde07771f3adc9f61353cce1c83074fe574862300eff1d8b87b",
        "docs/vnext/w1/CLAIM_LEDGER_R8.json": "c1e16171264edf173b55e720b567e592b80aaf32ba384e591ac5c53ba9b06be8",
        "docs/vnext/w1/integration_r8/INTEGRATION_MANIFEST_R8.json": "4a9b3c9d397c7b0e332db71195018b09086db288fb149a2f7b7a797d4035dd86",
    }
    for name, expected_hash in expected.items():
        assert digest(ROOT / name)[0] == expected_hash
