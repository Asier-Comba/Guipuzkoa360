"""Portable, read-only ZIP and assembly review; hashes prove consistency, not authorship."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import stat
import sys
import zipfile
from pathlib import Path
from typing import Any

MAX_ZIP_BYTES = 24 * 1024 * 1024  # W3 review bound; not an official portal limit.
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_MEMBERS = 100
FORBIDDEN_PARTS = {"__pycache__", ".git", ".env", "secrets", "fixtures", "holdout", "training", "formacion"}
FORBIDDEN_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".pyc"}
SECRET_PATTERNS = [re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
                   re.compile(rb"\b(?:sk-|ghp_)[A-Za-z0-9_\-]{20,}\b")]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> None:
    path = Path(name)
    parts = name.replace("\\", "/").split("/")
    if (not name or name.startswith(("/", "\\")) or "\\" in name or
            ":" in name or any(part in {"", ".", ".."} for part in parts) or
            any(part.casefold() in FORBIDDEN_PARTS for part in parts) or
            path.suffix.casefold() in FORBIDDEN_SUFFIXES):
        raise ValueError(f"Unsafe or forbidden package path: {name}")


def rooted(root: Path, relative: str) -> Path:
    safe_name(relative)
    root = root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"Missing or escaping assembly file: {relative}")
    return path


def review_zip(package: Path, members: dict[str, str], external_imports: list[str]) -> dict:
    if package.stat().st_size > MAX_ZIP_BYTES:
        raise ValueError("Package exceeds W3 review byte bound")
    if not isinstance(members, dict) or not members or len(members) > MAX_MEMBERS:
        raise ValueError("Assembly members must be a bounded nonempty map")
    for name, digest in members.items():
        safe_name(name)
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Invalid member hash")
    with zipfile.ZipFile(package) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)) or set(names) != set(members):
            raise ValueError("ZIP members differ from manifest or contain duplicates")
        total = 0
        imported = set()
        local_modules = {Path(name).stem for name in names if name.endswith(".py")}
        local_modules.update(name.split("/")[0] for name in names
                             if name.endswith("/__init__.py"))
        for info in infos:
            safe_name(info.filename)
            mode = (info.external_attr >> 16) & 0xFFFF
            if (info.flag_bits & 1 or info.is_dir() or
                    (mode and stat.S_IFMT(mode) not in {0, stat.S_IFREG}) or
                    info.file_size > MAX_MEMBER_BYTES):
                raise ValueError(f"Unsupported ZIP member: {info.filename}")
            total += info.file_size
            if total > MAX_TOTAL_BYTES:
                raise ValueError("Expanded ZIP exceeds W3 review byte bound")
            data = archive.read(info)
            if sha(data) != members[info.filename]:
                raise ValueError(f"ZIP member hash mismatch: {info.filename}")
            if any(pattern.search(data) for pattern in SECRET_PATTERNS):
                raise ValueError(f"Potential credential in member: {info.filename}")
            if info.filename.endswith(".py"):
                tree = ast.parse(data.decode("utf-8"), filename=info.filename)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imported.update(alias.name.split(".")[0] for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                        imported.add(node.module.split(".")[0])
        undeclared = imported - local_modules - set(sys.stdlib_module_names) - set(external_imports)
        if undeclared:
            raise ValueError(f"Undeclared package imports: {sorted(undeclared)}")
    return {"members": len(infos), "expanded_bytes": total,
            "package_bytes": package.stat().st_size, "imports": sorted(imported)}


def review_assembly(root: Path, manifest: dict[str, Any]) -> dict:
    required = {"schema_version", "runtime_commit", "package_file", "package_sha256",
                "data_manifest_file", "data_manifest_sha256", "members", "source_shas",
                "model_id", "model_config", "context_mode", "generation_command",
                "external_imports"}
    if not isinstance(manifest, dict) or set(manifest) != required or manifest["schema_version"] != "W3_ASSEMBLY_1":
        raise ValueError("Unsupported W3 assembly manifest")
    if not re.fullmatch(r"[a-f0-9]{40}", manifest["runtime_commit"]):
        raise ValueError("Invalid runtime commit label")
    for key in ("package_sha256", "data_manifest_sha256"):
        if not re.fullmatch(r"[a-f0-9]{64}", manifest[key]):
            raise ValueError(f"Invalid {key}")
    if not manifest["generation_command"] or not isinstance(manifest["generation_command"], str):
        raise ValueError("Missing generation record")
    if (not isinstance(manifest["external_imports"], list) or
            any(not isinstance(name, str) or not name.isidentifier()
                for name in manifest["external_imports"])):
        raise ValueError("Invalid external imports declaration")
    source_shas = manifest["source_shas"]
    if not isinstance(source_shas, dict) or not source_shas:
        raise ValueError("Missing source file identities")
    for relative, digest in source_shas.items():
        if not re.fullmatch(r"[a-f0-9]{64}", digest) or sha(rooted(root, relative).read_bytes()) != digest:
            raise ValueError(f"Source hash mismatch: {relative}")
    package = rooted(root, manifest["package_file"])
    data = rooted(root, manifest["data_manifest_file"])
    if sha(package.read_bytes()) != manifest["package_sha256"] or sha(data.read_bytes()) != manifest["data_manifest_sha256"]:
        raise ValueError("Package or data manifest hash mismatch")
    if not set(manifest["members"].values()).issubset(set(source_shas.values())):
        raise ValueError("Package members are not related to captured source bytes")
    return review_zip(package, manifest["members"], manifest["external_imports"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--assembly-manifest", required=True)
    args = parser.parse_args()
    manifest_path = rooted(args.evidence_root, args.assembly_manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result = review_assembly(args.evidence_root, manifest)
    print(json.dumps({"status": "PASS", "assembly_sha256": sha(manifest_path.read_bytes()), **result}))


if __name__ == "__main__":
    main()
