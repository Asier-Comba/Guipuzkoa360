from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.vnext_agent import retrieve_docs


def test_lexical_retrieval_cites_existing_section_without_generating_answer():
    result = retrieve_docs.retrieve("¿La distancia geométrica se convierte en tiempo de viaje?", k=3)
    assert result["status"] == "evidence_found" and result["answer_generated"] is False
    approved = {item["section_id"] for item in retrieve_docs.load_corpus()}
    assert all(hit["section_id"] in approved and hit["url"].startswith("https://github.com/Asier-Comba/Guipuzkoa360/blob/") for hit in result["hits"])


def test_missing_documentary_answer_abstains():
    result = retrieve_docs.retrieve("¿Cuántos dragones violetas hay en Marte?")
    assert result["status"] == "abstain" and result["hits"] == []


def test_changed_corpus_bytes_are_rejected(tmp_path: Path):
    source = retrieve_docs.ROOT
    manifest = json.loads((source / "datos_preparados/vnext/document_corpus.json").read_text(encoding="utf-8"))
    target = tmp_path / "datos_preparados/vnext/document_corpus.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(manifest), encoding="utf-8")
    for item in manifest["documents"]:
        destination = tmp_path / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((source / item["path"]).read_bytes())
    with (tmp_path / manifest["documents"][0]["path"]).open("ab") as handle:
        handle.write(b"TEST_TAMPER")
    with pytest.raises(ValueError, match="hash mismatch"):
        retrieve_docs.load_corpus(tmp_path)
