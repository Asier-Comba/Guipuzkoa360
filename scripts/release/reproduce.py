"""Full release audit from a clean checkout; never downloads or changes runtime logic."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
import zlib
from pathlib import Path

from verify_frozen import ROOT, verify

OUT = ROOT / "work/release-audit"


def main() -> None:
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise SystemExit("FAIL: use a clean checkout before starting the release audit")
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"checkout_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
              "python": platform.python_version(), "os": platform.system(),
              "zlib": zlib.ZLIB_RUNTIME_VERSION, "steps": []}

    def run(label: str, args: list[str]) -> None:
        start = time.perf_counter()
        completed = subprocess.run(args, cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace")
        log = OUT / f"{label}.log"
        log.write_text(completed.stdout + completed.stderr, encoding="utf-8", newline="\n")
        record = {"id": label, "command": ["python" if a == sys.executable else a for a in args],
                  "seconds": round(time.perf_counter()-start, 3), "exit_code": completed.returncode,
                  "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest()}
        report["steps"].append(record)
        print(label, "PASS" if completed.returncode == 0 else "FAIL", flush=True)
        if completed.returncode:
            raise RuntimeError(f"{label}: see {log.relative_to(ROOT)}")

    try:
        report["before"] = verify()
        if report["before"]["status"] != "PASS":
            raise RuntimeError("Runtime differs from portal-validated bytes before build")
        run("dependencies", [sys.executable, "-m", "pip", "check"])
        run("pipeline_snapshot", [sys.executable, "scripts/data/build_all.py", "--offline"])
        run("python_tests", [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", "--junitxml=work/release-audit/pytest.xml"])
        suites = ET.parse(OUT / "pytest.xml").getroot()
        report["python_tests"] = {key: sum(int(s.attrib.get(key, 0)) for s in suites.iter("testsuite"))
                                  for key in ("tests", "failures", "errors", "skipped")}
        cases = list(suites.iter("testcase"))
        report["subset_tests"] = {
            "data": sum(c.attrib.get("classname", "").startswith("tests.data.") for c in cases),
            "golden": sum("test_golden_contract" in c.attrib.get("classname", "") for c in cases),
        }
        run("node_tests", ["node", "--test", "tests/e2e/contract_flow.test.mjs"])
        run("acceptance", [sys.executable, "scripts/agent/run_release_e2e.py"])
        report["acceptance"] = {k: v for k, v in json.loads((ROOT / "analisis/release_e2e_report.json").read_text(encoding="utf-8")).items() if k != "cases"}
        run("bundle_sources", [sys.executable, "scripts/agent/build_portal_sources.py"])
        run("visual_data", [sys.executable, "scripts/agent/build_work3_result.py"])
        run("visual_geometry", ["node", "scripts/enrich_work1_result.mjs", "analisis/work3_agent_result.json", "work/release-audit/visual.json"])
        run("visual_html", ["node", "scripts/build_results.mjs", "work/release-audit/visual.json", "work/release-audit/html"])
        run("benchmark", [sys.executable, "scripts/agent/benchmark_tools.py", "--warm-repetitions", "7", "--output", "work/release-audit/benchmark.json"])
        report["benchmark"] = json.loads((OUT / "benchmark.json").read_text(encoding="utf-8"))
        run("package_1", [sys.executable, "scripts/agent/build_portal_package.py"])
        package_path = ROOT / "dist/gipuzkoa360-urban-challenge-rc2.zip"
        first = package_path.read_bytes()
        run("package_2", [sys.executable, "scripts/agent/build_portal_package.py"])
        second = package_path.read_bytes()
        if first != second:
            raise RuntimeError("Double package build differs")
        with zipfile.ZipFile(package_path) as archive:
            members = [{"path": n, "bytes": len(archive.read(n)), "sha256": hashlib.sha256(archive.read(n)).hexdigest()}
                       for n in archive.namelist()]
        report["package"] = {"bytes": len(second), "sha256": hashlib.sha256(second).hexdigest(),
                             "two_builds_identical": True, "members": members}
        report["after"] = verify()
        if report["after"]["status"] != "PASS":
            raise RuntimeError("Regeneration changed frozen runtime or manifest")
        report["qa"] = json.loads((ROOT / "analisis/data_quality_report.json").read_text(encoding="utf-8"))
        report["tracked_changes_after_build"] = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).decode().splitlines()
        # Other generated reports may contain checkout-specific paths; runtime may not.
        report["status"] = "PASS"
    except Exception as exc:
        report["status"] = "FAIL"
        report["error"] = str(exc)
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(report["status"], "work/release-audit/report.json", flush=True)
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
