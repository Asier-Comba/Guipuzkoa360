import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('final_artifacts',ROOT/'scripts/release/verify_final_artifacts.py')
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_frozen_runtime_manifest_and_every_visual_value():
    report=audit.audit()
    assert report['status']=='PASS',report['checks']
    assert len(report['visual_mutations'])==9
