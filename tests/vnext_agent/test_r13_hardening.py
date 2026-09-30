"""R13 offline audit regressions; not LLM/routing/memory acceptance."""
import copy
import io
import json
import zipfile

import pytest

from scripts.vnext_agent import audit_r13, harden_r13


def fixture():
    with zipfile.ZipFile(harden_r13.ZIP) as archive:
        return json.loads(archive.read("datos_preparados/vnext/w1_conformance_r7.json"))


def test_r13_seeded_corpus_reproducible_covers_requested_categories():
    one = list(harden_r13.generate_fuzz(fixture(), 10000))
    two = list(harden_r13.generate_fuzz(fixture(), 10000))
    assert [harden_r13.stable_hash(v) for v in one] == [harden_r13.stable_hash(v) for v in two]
    assert len(one) == 10000
    assert {r["tool"] for r in one} == set(harden_r13.seeds(fixture())[0])
    assert {r["category"] for r in one} >= {"nonfinite", "legacy_snapshot", "wrong_snapshot", "comparison_0", "comparison_1", "comparison_2", "comparison_4", "comparison_5plus", "oversized", "extra_field", "missing_field", "unicode"}


@pytest.mark.parametrize("name", ["../escape.py", "/absolute.py", "C:/drive.py", "x\\bad.py"])
def test_r13_unsafe_paths_rejected_by_off_candidate_auditor(name):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr(name, b"test")
    if "\\" in name:
        # Windows zipfile normalizes separators while creating an entry. Inject
        # the adversarial filename in both local/central headers after writing.
        data = io.BytesIO(data.getvalue().replace(name.replace("\\", "/").encode(), name.encode()))
    with zipfile.ZipFile(data) as archive, pytest.raises(AssertionError):
        harden_r13.archive_safety(archive)


def test_r13_case_collision_rejected():
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("Data.json", b"a")
        archive.writestr("data.json", b"b")
    with zipfile.ZipFile(data) as archive, pytest.raises(AssertionError):
        harden_r13.archive_safety(archive)


def test_r13_support_is_exact_frozen_identity_not_served_schema():
    report = json.loads((harden_r13.OUT / "PORTAL_SUPPORT_R13.json").read_text())
    manifest = json.loads(harden_r13.MANIFEST.read_text())
    assert report["runtime_commit"] == harden_r13.RUNTIME
    assert harden_r13.digest(harden_r13.ZIP.read_bytes()) == report["zip"]["sha256"] == harden_r13.ZIP_SHA
    assert report["manifest"]["sha256"] == harden_r13.MANIFEST_SHA
    assert len(report["assets"]) == 15 and report["tool_count"] == 9
    assert {p["path"] for p in report["assets"]} == set(manifest["context_paths"])
    assert not report["studio_mount_proven"] and not report["served_schema_proven"]
    assert report["config"] == {"memory": True, "internet": False, "max_iterations": 8}
    assert report["local_llm"] == report["portal_llm_by_w2"] == 0


def test_r13_normalization_does_not_hide_deterministic_tool_state():
    original = {"request_id": "id", "execution": {"request_id": "id", "state": "failed"},
                "status": "error", "error": {"code": "different"}, "claims": []}
    normalized = harden_r13.normalized(original)
    assert normalized == {"execution": {"state": "failed"}, "status": "error", "error": {"code": "different"}, "claims": []}
    assert original["request_id"] == "id"


def test_r13_documentary_gold_is_not_timing_or_gtfs_calculation():
    assert len(audit_r13.QUESTIONS) == 18
    chunks = {c["section_id"]: c for c in audit_r13.retrieve_docs.load_corpus()}
    for _, expected, _ in audit_r13.QUESTIONS:
        assert all(section in chunks for section in expected)
    report = json.loads((harden_r13.OUT / "RAG_AB_R13.json").read_text())
    assert not report["rag_in_candidate"] and report["llm_calls"] == 0
    assert report["decision"] == "RAG_NO_GO"
    assert report["arms"]["B_EXISTING_LEXICAL_SECTION_RETRIEVAL"]["support_completeness"] < report["arms"]["A_NAVIGABLE_FULL_DOCUMENT_LOOKUP"]["support_completeness"]
