"""Two byte-identical builds, exact archive members and frozen context matching."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from verify_runtime_identity import ROOT, audit

def main():
    if audit()["status"] != "PASS":
        raise SystemExit("Frozen runtime mismatch")
    spec = importlib.util.spec_from_file_location("release_package", ROOT/"scripts/agent/build_portal_package.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    blobs = []
    for _ in range(2):
        subprocess.run([sys.executable, str(ROOT/"scripts/agent/build_portal_package.py")], cwd=ROOT, check=True, capture_output=True)
        blobs.append(builder.OUTPUT.read_bytes())
    with zipfile.ZipFile(builder.OUTPUT) as archive:
        assert sorted(archive.namelist()) == sorted(builder.FILES.values())
        for source, dest in builder.FILES.items():
            assert archive.read(dest) == builder.canonical_bytes(ROOT/source), dest
        members = archive.namelist()
    assert blobs[0] == blobs[1], "Nondeterministic archive"
    report = {"status": "PASS", "scope": "same toolchain, two builds; not all zlib versions",
              "bytes": len(blobs[0]), "sha256": hashlib.sha256(blobs[0]).hexdigest(), "members": members}
    (ROOT/"work").mkdir(exist_ok=True)
    (ROOT/"work/package-gate.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report))

if __name__ == "__main__":
    main()
