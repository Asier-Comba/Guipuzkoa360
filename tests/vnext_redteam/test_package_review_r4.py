"""Portable package checks use invented bytes; no portal package is accepted here."""

import hashlib
import json
import zipfile

import pytest

from scripts.vnext_product.package_review import review_assembly, review_zip
from scripts.vnext_product.score_runs import strict_json


def digest(data):
    return hashlib.sha256(data).hexdigest()


def example(tmp_path, code=b"import json\n"):
    source = tmp_path / "source.py"
    source.write_bytes(code)
    package = tmp_path / "candidate.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("main.py", code)
    data = tmp_path / "data.json"
    data.write_bytes(b'{"data":"test"}\n')
    return {"schema_version": "W3_ASSEMBLY_1", "runtime_commit": "a" * 40,
            "package_file": package.name, "package_sha256": digest(package.read_bytes()),
            "data_manifest_file": data.name, "data_manifest_sha256": digest(data.read_bytes()),
            "members": {"main.py": digest(code)}, "source_shas": {source.name: digest(code)},
            "model_id": "fixture", "model_config": {"temperature": 0},
            "context_mode": "isolated", "generation_command": "fixture build", "external_imports": []}


def test_portable_review_without_git(tmp_path):
    report = review_assembly(tmp_path, example(tmp_path))
    assert report["members"] == 1
    assert report["imports"] == ["json"]


def test_zip_rejects_traversal_duplicate_secrets_and_undeclared_imports(tmp_path):
    package = tmp_path / "bad.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("../outside.py", "x")
    with pytest.raises(ValueError, match="Unsafe"):
        review_zip(package, {"../outside.py": digest(b"x")}, [])
    with pytest.warns(UserWarning, match="Duplicate name"):
        with zipfile.ZipFile(package, "w") as archive:
            archive.writestr("main.py", "x")
            archive.writestr("main.py", "x")
    with pytest.raises(ValueError, match="duplicates"):
        review_zip(package, {"main.py": digest(b"x")}, [])
    with pytest.raises(ValueError, match="credential"):
        review_assembly(tmp_path, example(tmp_path, b"-----BEGIN PRIVATE KEY-----\n"))
    with pytest.raises(ValueError, match="Undeclared"):
        review_assembly(tmp_path, example(tmp_path, b"import invented_dependency\n"))


def test_manifest_relationships_and_duplicate_json_keys(tmp_path):
    manifest = example(tmp_path)
    manifest["members"]["main.py"] = "b" * 64
    with pytest.raises(ValueError, match="related"):
        review_assembly(tmp_path, manifest)
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        strict_json('{"identity":{"runtime_commit":"a","runtime_commit":"b"}}')
