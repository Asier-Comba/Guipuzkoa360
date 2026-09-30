"""Read and reproduce the published W1 R6 runtime without mutating its branch."""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUPPORT_PIN = "6ebf41e2f1fe24f1c3678c4be13c6c44cf8cb62b"
TESTED_RUNTIME_COMMIT = "cb061a9e00a6496c40488a596bd94834bc2c49b2"
MANIFEST_PATH = "docs/vnext/w1/RUNTIME_MANIFEST_R6.json"
MANIFEST_SHA256 = "4968d003e225db03d7fba57c5fb72088332a4246c2a266f1fc3843deacef5940"
PACKAGE_SHA256 = "c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910"
LABELS_PATH = "datos_preparados/movilidad/consumer_labels_r7.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(path: str) -> bytes:
    if path.startswith("/") or ".." in Path(path).parts or "\\" in path:
        raise ValueError(f"Unsafe W1 path: {path}")
    return subprocess.check_output(["git", "show", f"{SUPPORT_PIN}:{path}"], cwd=ROOT)


def published_runtime() -> tuple[bytes, dict]:
    manifest_bytes = blob(MANIFEST_PATH)
    if sha(manifest_bytes) != MANIFEST_SHA256:
        raise ValueError("W1 manifest changed")
    manifest = json.loads(manifest_bytes)
    if manifest["entrypoint"] != "prototypes.ir_y_volver.provider_r6" or manifest["contract_versions"] != ["0.2.0", "0.3.0", "0.3.1"]:
        raise ValueError("W1 contract is not the reviewed R6 runtime")
    paths = [item["path"] for item in manifest["files"]]
    if len(paths) != len(set(paths)) or paths != sorted(paths):
        raise ValueError("W1 runtime paths are duplicated or unsorted")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in manifest["files"]:
            data = blob(item["path"])
            if item["role"] != "runtime" or len(data) != item["bytes"] or sha(data) != item["sha256"]:
                raise ValueError(f"W1 pinned blob mismatch: {item['path']}")
            info = zipfile.ZipInfo(item["path"], (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    result = output.getvalue()
    if len(result) != manifest["package_bytes"] or sha(result) != manifest["package_sha256"] or sha(result) != PACKAGE_SHA256:
        raise ValueError("W1 package reproduction mismatch")
    return result, manifest
