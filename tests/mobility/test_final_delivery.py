import hashlib
import json
from pathlib import Path

from scripts.mobility.build_final_delivery import build
from scripts.mobility.final_public_release import common_cases, fixtures, stable

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / 'resultados/vnext/final_benchmark'


def test_release_matrix_freezes_optional_hole_and_origins():
    truth = json.loads((ROOT / 'docs/vnext/w1/FINAL_ORACLE_R13.json').read_bytes())
    _, cases = fixtures(truth)
    ids = {c['case_id'] for c in cases}
    assert {'deadline_none', 'deadline_valid', 'deadline_empty', 'deadline_whitespace', 'deadline_malformed', 'deadline_out_of_range'} <= ids
    assert {'zegama_center_stops', 'segura_herriko_plaza_stops', 'idiazabal_center_stops'} <= ids
    assert len(cases) == 35 and len(common_cases()) == 8


def test_exact_benchmark_reports_and_no_release_transfer():
    report = json.loads((BENCH / 'public_summary.json').read_bytes())
    assert report['status'] == 'PASS' and report['cases'] == 38 and report['executions'] == 76
    common = json.loads((BENCH / 'common_summary.json').read_bytes())
    assert common['status'] == 'PASS' and common['equal_full_raw'] == common['pairs'] == 8
    state = json.loads((BENCH / 'release_state.json').read_bytes())
    assert state['RELEASE_GO'] == 'NO' and state['current_agent']['high'] == 1
    assert state['current_agent']['medium'] == 3 and state['budget']['used'] == 5


def test_holdout_kept_sealed():
    seal = json.loads((BENCH / 'holdout_seal.json').read_bytes())
    assert seal['state'] == 'SEALED' and seal['opens'] == 0 and seal['cases'] == 12
    assert seal['corpus_sha256'] == '4dda59721932f620cba53e5686df288f7cf0e0e968ec30540216ffb1f52ec5c0'
    assert 'NOT_MOUNTED_NOT_OPENED' in seal['physical_corpus']


def test_final_delivery_rebuilds_identically_and_hashes_bind(tmp_path):
    a, b = build(BENCH, tmp_path / 'a'), build(BENCH, tmp_path / 'b')
    assert a == b and len(a) == 4
    manifest = json.loads((tmp_path / 'a/FINAL_MANIFEST.json').read_bytes())
    assert manifest['candidate'] == 'PENDING_FINAL_AGENT_GREEN'
    assert manifest['track'] == 'PENDING_HUMAN_SELECTION' and manifest['publication'] == 'PENDING_HUMAN_GATE'
    for name, identity in manifest['reports'].items():
        assert hashlib.sha256((BENCH / name).read_bytes()).hexdigest() == identity['sha256']


def test_nondeterminism_removed_without_claim_changes():
    assert stable({'cwd': '/temporary', 'value': {'total_s': 10691, 'vnext_s': 1.2}}) == {'value': {'total_s': 10691}}
