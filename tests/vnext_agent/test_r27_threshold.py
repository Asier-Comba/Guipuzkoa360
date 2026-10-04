import copy
import importlib.util
import io
import json
import math
import random
import subprocess
import sys
import zipfile
import pytest
from scripts.vnext_agent import build_r27 as build

CATEGORIES = ['primary_care', 'hospital', 'mental_health', 'other_health']


@pytest.fixture(scope='module')
def runtime(tmp_path_factory):
    build.build()
    root = tmp_path_factory.mktemp('r27')
    with zipfile.ZipFile(build.ZIP) as z:
        z.extractall(root)
    spec = importlib.util.spec_from_file_location('r27_threshold_test_tools', root / 'tools.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, root


def observe(runtime, category, before, after):
    m, root = runtime
    args = dict(accion='change_threshold', categoria_servicio=category, umbral_km=before, nuevo_umbral_km=after)
    evidence = m.execute('simular_escenario', args, 'r27-test', root=root)
    view = json.loads(m.public_result(evidence, root=root))
    assert view['status'] == 'valid', view
    return evidence, view['threshold_transition_ledger']


def independent_distances(runtime, category):
    m, root = runtime
    repo = m.DataRepository(root / 'datos_preparados')
    services = [s for s in repo.services() if s['service_category'] == category]
    return {r['municipality_code']: min(math.hypot(r['easting_m'] - s['easting_m'], r['northing_m'] - s['northing_m']) for s in services)
            for r in repo.municipalities()}


def check(runtime, category, before, after):
    evidence, ledger = observe(runtime, category, before, after)
    raw = json.loads(evidence['raw_result_json'])
    expected = independent_distances(runtime, category)
    counts = dict(outside_to_inside=0, inside_to_outside=0, stays_inside=0, stays_outside=0)
    changed = {}
    for code, distance in expected.items():
        b, s = distance <= before * 1000, distance <= after * 1000
        transition = 'stays_inside' if b and s else 'stays_outside' if not b and not s else 'outside_to_inside' if s else 'inside_to_outside'
        counts[transition] += 1
        if b != s:
            changed[code] = (b, s, round(distance, 1), transition)
    assert ledger['counts'] == {**counts, 'total': len(expected)}
    rows = ledger['changed_rows']
    assert len(rows) == len(changed) == len({r['municipality_code'] for r in rows})
    assert {r['municipality_code'] for r in rows} == set(changed)
    for row in rows:
        assert (row['baseline_within_threshold'], row['scenario_within_threshold'], row['distance_m'], row['transition']) == changed[row['municipality_code']]
        source = runtime[0]._pointer(raw, row['evidence_path'])
        assert source['municipality_code'] == row['municipality_code']
        assert row['municipality_name'] in ledger['answer_table_markdown']
    assert ledger['raw_result_sha256'] == evidence['raw_result_sha256']
    return ledger


def test_legazpi_regression(runtime):
    ledger = check(runtime, 'primary_care', 2, 3)
    row, = [r for r in ledger['changed_rows'] if r['municipality_code'] == '20051']
    assert row['municipality_name'] == 'Legazpi' and row['distance_m'] == 2624.8
    assert row['baseline_within_threshold'] is False and row['scenario_within_threshold'] is True
    assert row['transition'] == 'outside_to_inside'


@pytest.mark.parametrize('category', CATEGORIES)
@pytest.mark.parametrize('pair', [(2, 3), (3, 2), (1, 1), (.001, 100), (100, .001), (1, 1.000001)])
def test_generalization_and_reverse(runtime, category, pair):
    a = check(runtime, category, *pair)
    b = check(runtime, category, *reversed(pair))
    assert a['counts']['outside_to_inside'] == b['counts']['inside_to_outside']
    assert a['counts']['inside_to_outside'] == b['counts']['outside_to_inside']
    assert {r['municipality_code']: r['distance_m'] for r in a['changed_rows']} == {r['municipality_code']: r['distance_m'] for r in b['changed_rows']}


@pytest.mark.parametrize('category', CATEGORIES)
def test_seeded_properties_and_real_boundaries(runtime, category):
    rng = random.Random(27004)
    for _ in range(30):
        check(runtime, category, rng.uniform(.001, 100), rng.uniform(.001, 100))
    for distance in list(independent_distances(runtime, category).values())[:8]:
        threshold = distance / 1000
        for delta in (-1e-8, 0, 1e-8):
            check(runtime, category, threshold + delta, threshold + 1e-6)


def test_boundary_rounding_and_zero(runtime, monkeypatch):
    m, root = runtime
    municipalities = [dict(municipality_code=str(i), municipality_name=f'Point {i}', easting_m=d, northing_m=0)
                      for i, d in enumerate([0.0, 999.999999, 1000.0, 1000.000001])]
    service = dict(service_id='synthetic', service_category='primary_care', easting_m=0.0, northing_m=0.0,
                   source_id='ODE_HEALTH_CENTRES_2026', reference_period='2026-09-20')
    # Synthetic coordinates exercise the existing engine, not a mocked classifier.
    monkeypatch.setattr(m.DataRepository, 'municipalities', lambda self: municipalities)
    monkeypatch.setattr(m.DataRepository, 'services', lambda self: [service])
    _, ledger = observe(runtime, 'primary_care', .5, 1)
    assert ledger['counts'] == dict(outside_to_inside=2, inside_to_outside=0, stays_inside=1, stays_outside=1, total=4)
    assert [r['municipality_code'] for r in ledger['changed_rows']] == ['1', '2']
    assert all(r['distance_m'] == 1000 for r in ledger['changed_rows'])


@pytest.mark.parametrize('fault', ['duplicate', 'omitted', 'bool_int', 'classification', 'distance', 'name', 'source', 'threshold', 'nan', 'missing_distance', 'hash', 'delta', 'service_count'])
def test_fail_closed(runtime, fault):
    m, root = runtime
    evidence, _ = observe(runtime, 'primary_care', 2, 3)
    evidence = copy.deepcopy(evidence)
    raw = json.loads(evidence['raw_result_json'])
    if fault == 'duplicate': raw['data'].append(copy.deepcopy(raw['data'][0]))
    elif fault == 'omitted': raw['data'].pop()
    elif fault == 'bool_int': raw['data'][0]['baseline_within_threshold'] = 0
    elif fault == 'classification': raw['data'][0]['scenario_within_threshold'] = not raw['data'][0]['scenario_within_threshold']
    elif fault == 'distance': raw['data'][0]['baseline_distance_m'] += .1
    elif fault == 'name': raw['data'][0]['municipality_name'] = 'wrong'
    elif fault == 'source': raw['sources'] = []
    elif fault == 'threshold': raw['scenario']['scenario']['threshold_km'] += .1
    elif fault == 'missing_distance': raw['data'][0]['baseline_distance_m'] = None
    elif fault == 'delta': raw['data'][0]['difference_absolute_m'] = 1
    elif fault == 'service_count': raw['scenario']['scenario']['service_count'] += 1
    elif fault == 'nan': raw['data'][0]['baseline_distance_m'] = float('nan')
    evidence['raw_result_json'] = json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    evidence['raw_result_sha256'] = m.digest(evidence['raw_result_json']) if fault != 'hash' else '0' * 64
    view = json.loads(m.public_result(evidence, root=root))
    assert view['status'] == 'error' and not view['claims'] and 'threshold_transition_ledger' not in view


def test_payload_fail_closed(runtime, monkeypatch):
    m, root = runtime
    evidence, _ = observe(runtime, 'primary_care', .001, 100)
    monkeypatch.setattr(m, 'MAX_PUBLIC_BYTES', 100)
    view = json.loads(m.public_result(evidence, root=root))
    assert view['status'] == 'error' and not view['claims'] and 'threshold_transition_ledger' not in view


def test_public_and_health_parity(runtime, tmp_path):
    _, root = runtime
    baseline = tmp_path / 'baseline'
    with zipfile.ZipFile(io.BytesIO(build.blob(build.BASE_ZIP))) as z:
        z.extractall(baseline)
    cases = [dict(id='threshold', tool='simular_cambiar_umbral', arguments=dict(categoria_servicio='primary_care', umbral_actual_km=2, nuevo_umbral_km=3), keep_raw=True),
             dict(id='aduna', tool='obtener_resumen_territorial', arguments=dict(municipio='Aduna'), keep_raw=True), dict(id='caps', tool='consultar_capacidades', arguments={})]
    for origin in ('zegama_center_stops', 'segura_herriko_plaza_stops', 'idiazabal_center_stops'):
        for times in (['09:30'], ['09:30', '09:45'], ['10:00', '10:15']):
            cases.append(dict(id=origin+str(times), tool='plan_visit', arguments=dict(origin_id=origin, destination_id='beasain_official_centre_anchor', date='2026-09-29', appointment_times=times, duration_minutes=20), keep_raw=True))
    def run(path):
        p = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'scripts.vnext_agent.worker_r20', str(path)], cwd=build.ROOT,
            input=json.dumps(dict(cases=cases)), text=True, encoding='utf-8', capture_output=True, timeout=180)
        assert p.returncode == 0, p.stderr
        return json.loads(p.stdout)
    left, right = run(baseline), run(root)
    assert left['signatures'] == right['signatures'] and len(right['signatures']) == 10
    for key, record in right['records'].items():
        prior = left['records'][key]
        assert record['status'] == prior['status'] == 'valid'
        assert record['execute_calls'] == 1
        for field in ('raw_sha256', 'effective_request', 'claims'):
            assert record[field] == prior[field]
        if key.startswith(('zegama', 'segura', 'idiazabal')):
            assert record['view'] == prior['view']
    assert right['records']['threshold']['view']['threshold_transition_ledger']['verified']
    summary = right['records']['aduna']
    assert summary['raw']['data'][0]['service_indicators']['primary_care']['registered_service_count'] == 0
    # Existing projection does NOT expose the nested counts to the model.
    # Record this limitation; do not broaden R27 to change unrelated claims.
    assert not any('registered_service_count' in c['metric_id'] for c in summary['claims'])


def test_frozen_members_double_build_and_no_special_cases():
    first = build.build()
    second = build.build()
    assert first == second
    with zipfile.ZipFile(io.BytesIO(build.blob(build.BASE_ZIP))) as old, zipfile.ZipFile(build.ZIP) as new:
        assert old.namelist() == new.namelist()
        assert [n for n in old.namelist() if old.read(n) != new.read(n)] == ['main.py', 'tools.py']
        assert new.read('main.py') == (build.PORTAL / 'main.py').read_bytes()
        assert new.read('tools.py').startswith(old.read('tools.py'))
    text = (build.ROOT / 'scripts/vnext_agent/r27_threshold.py').read_text(encoding='utf-8')
    assert not any(token in text for token in ('Legazpi', '20051', '2624.8'))
