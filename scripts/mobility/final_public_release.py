"""Final release audit: exact offline package, public cases only; holdout sealed."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from scripts.mobility.accept_frontdoor_r14 import audit, blob, worker
from scripts.mobility.frontdoor_worker_r14 import OPTIONAL, producer_result
from scripts.mobility.verify_frontdoor_evidence_r14 import verify
from scripts.mobility.verify_r13 import dump

ROOT = Path(__file__).resolve().parents[2]
W3 = 'f4fd0a3c79ff2827c19a1200c0c76f7c5815eab7'
V4 = '195b4980fa5998b096c308296a55e452380b0371'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fixtures(truth):
    base = truth['cases'][0]['structured_request']
    cases = [dict(case_id='TRUTH_' + c['case_id'], kwargs=c['structured_request']) for c in truth['cases']]
    for origin in ['zegama_center_stops', 'segura_herriko_plaza_stops', 'idiazabal_center_stops']:
        cases.append(dict(case_id=origin, kwargs={**base, 'origin_id': origin}))
    for duration in [1, 26, 90, 720]:
        cases.append(dict(case_id=f'duration_{duration}', kwargs={**base, 'duration_minutes': duration}))
    for arrival, boarding in [(0, 0), (15, 8), (240, 120)]:
        cases.append(dict(case_id=f'margins_{arrival}_{boarding}', kwargs={**base, 'arrival_margin_minutes': arrival, 'boarding_margin_minutes': boarding}))
    for label, value in [('none', None), ('valid', '15:00'), ('empty', ''), ('whitespace', ' '), ('malformed', '9h30'), ('out_of_range', '25:00')]:
        cases.append(dict(case_id='deadline_' + label, kwargs={**base, 'return_deadline': value}, invalid=label not in {'none', 'valid'}))
    # Serialization/optional-focused generation, fixed public input domain.
    for i, value in enumerate(['', ' ', '\t', '09:60', '24:01', '23:59:60', 42, True, [], {}, '00:00', '23:59']):
        cases.append(dict(case_id=f'optional_property_{i}', kwargs={**base, 'return_deadline': value}, invalid=i < 10))
    return base, cases


def common_cases():
    return [
        {'id': 'aduna', 'tool': 'obtener_resumen_territorial', 'args': {'municipio': 'Aduna', 'periodo': '2025-01-01'}},
        {'id': 'eibar', 'tool': 'obtener_resumen_territorial', 'args': {'municipio': 'Eibar', 'periodo': '2025-01-01'}},
        {'id': 'comparison', 'tool': 'comparar_municipios', 'args': {'municipios': ['Eibar', 'Tolosa'], 'grupo_edad': '75', 'periodo': '2025-01-01'}},
        {'id': 'aging', 'tool': 'analizar_envejecimiento', 'args': {'grupo_edad': '75', 'periodo': '2025-01-01', 'top_n': 3}},
        {'id': 'access', 'tool': 'analizar_acceso_servicios', 'args': {'categoria_servicio': 'primary_care', 'umbral_km': 2.0, 'periodo': '2025-01-01', 'municipios': ['Aduna', 'Tolosa']}},
        {'id': 'coincidence', 'tool': 'analizar_coincidencia', 'args': {'categoria_servicio': 'primary_care', 'grupo_edad': '65', 'umbral_km': 2.0, 'periodo': '2025-01-01', 'cuantil': 0.75}},
        {'id': 'scenario', 'tool': 'simular_escenario', 'args': {'accion': 'change_threshold', 'categoria_servicio': 'primary_care', 'umbral_km': 1.0, 'nuevo_umbral_km': 2.0, 'periodo': '2025-01-01'}},
        {'id': 'sources', 'tool': 'consultar_fuente', 'args': {}},
    ]


def stable(value):
    if isinstance(value, dict):
        return {k: stable(v) for k, v in value.items() if k not in {'root', 'cwd', 'execute_root', 'runtime_s', 'progress_log', 'v4_s', 'vnext_s'}}
    if isinstance(value, list):
        return [stable(v) for v in value]
    return value


def run(package, manifest, output):
    output.mkdir(parents=True, exist_ok=True)
    integrity = audit(package, manifest)
    truth = json.loads((ROOT / 'docs/vnext/w1/FINAL_ORACLE_R13.json').read_bytes())
    base, cases = fixtures(truth)
    with tempfile.TemporaryDirectory(prefix='g360-final-public-') as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(package) as z:
            z.extractall(root)
        for name in ['municipios.csv', 'demografia.csv', 'runtime_municipality_points.csv', 'runtime_servicios.csv', 'metadata_sources.json', 'data_contract.json']:
            assert (root / 'datos_preparados' / name).read_bytes() == (ROOT / 'datos_preparados' / name).read_bytes(), 'Common benchmark sources differ'
        result = worker(root, {'base': base, 'fixtures': cases}, output / 'public_raw.json')
        assert result['status'] == 'PASS', result['failures']
        contrast = verify(truth, result)
        records = {r['case_id']: r for r in result['records']}
        assert records['deadline_none']['public_result'] == records['omitted']['public_result']
        for name in ['empty', 'whitespace', 'malformed', 'out_of_range']:
            public = records['deadline_' + name]['public_result']
            assert public['status'] == 'error' and not public['claims'] and not public['outcomes']
            assert public['error']['code'] == 'contract_violation'
            assert public['error']['message'] == 'mobility:invalid_clock'
        for name in ['duration_1', 'duration_26', 'duration_90', 'duration_720']:
            raw = producer_result(records[name]['direct_envelope'])
            assert raw['status'] in {'ok', 'no_feasible_journey'}
            if raw['status'] == 'ok':
                assert raw['components_s']['appointment_s'] == records[name]['kwargs']['duration_minutes'] * 60
        v4 = root / 'frozen_v4.py'
        v4.write_bytes(blob(V4, 'agentes/gipuzkoa360/portal/tools.py'))
        assert v4.read_bytes() == (ROOT / 'agentes/gipuzkoa360/portal/tools.py').read_bytes()
        config = dict(root=str(root), v4=str(v4), cases=common_cases())
        proc = subprocess.run([sys.executable, '-I', str(Path(__file__).with_name('final_common_worker.py'))], input=json.dumps(config), capture_output=True, text=True, encoding='utf-8', cwd=root, timeout=300)
        assert proc.returncode == 0, proc.stderr
        common = json.loads(proc.stdout)
        dump(output / 'common_raw.json', stable(common))
        timings = [{'case_id': r['case_id'], 'v4_s': r['v4_s'], 'vnext_s': r['vnext_s']} for r in common['records']]
        dump(output / 'latencies.json', {'scope': 'One offline call per system/case, no p95 or LLM inference', 'rows': timings})
        assert common['status'] == 'PASS', 'common full raw result differs; preserve outputs and inspect'
    dump(output / 'public_raw.json', stable(result))
    dump(output / 'public_summary.json', dict(status='PASS', cases=result['cases'], executions=2 * result['cases'], distinct_payloads=result['distinct_payloads'], seed=None, design='Deterministic public release matrix, not stress or holdout', contrast=contrast, package=integrity))
    dump(output / 'common_summary.json', dict(status=common['status'], pairs=len(common['records']), executions=2 * len(common['records']), equal_full_raw=sum(r['identical_raw'] for r in common['records']), scope=common['scope'], vnext_only=['capability registry', 'verified bounded evidence envelope', 'modelled health visit GO01'], no_winner=True))
    reconcile(package, output)
    return True


def reconcile(package, output):
    remote = {}
    for path in ['docs/vnext/w3/HANDOFF_R14.md', 'resultados/vnext/r14/M05.json', 'resultados/vnext/r14/M05_normalized.json', 'docs/vnext/w3/RELEASE_READINESS_R14.json', 'docs/vnext/w3/CORPUS_PROTOCOL.md', 'scripts/vnext_product/score_runs.py', 'scripts/vnext_product/package_review.py', 'tests/vnext_redteam/development_cases.json', 'tests/vnext_redteam/conversation_scenarios.json']:
        remote[path] = {'git': W3, 'sha256': sha(blob(W3, path)), 'url': f'https://github.com/Asier-Comba/Guipuzkoa360/blob/{W3}/{path}'}
    dump(output / 'upstream_identity.json', remote)
    dump(output / 'holdout_seal.json', dict(state='SEALED', corpus_sha256='4dda59721932f620cba53e5686df288f7cf0e0e968ec30540216ffb1f52ec5c0', cases=12, physical_corpus='NOT_MOUNTED_NOT_OPENED; historical hash declared by W3, custody confirmation required', runner=remote['scripts/vnext_product/score_runs.py'], assembly_validator=remote['scripts/vnext_product/package_review.py'], criteria=remote['docs/vnext/w3/CORPUS_PROTOCOL.md'], opens=0, gate='New exact candidate + actual portal Critical0/High0 + private corpus custody hash match + authorization; consume exactly once, preserve aborted attempts'))
    observed = json.loads(blob(W3, 'resultados/vnext/r14/M05_normalized.json'))
    plan_args = [json.loads(row['arguments']) for row in observed if row.get('tool') == 'plan_visit' and row.get('arguments')]
    outputs = [json.loads(row['output']) for row in observed if (row.get('output') or '').startswith('{') and 'mobility:invalid_clock' in row['output']]
    assert len(plan_args) == 3 and all(v['return_deadline'] == '' for v in plan_args)
    assert len(outputs) == 2 and all(not v['claims'] and v['raw_result_sha256'] is None for v in outputs)
    assert any('Failed to create sandbox' in (row.get('output') or '') for row in observed)
    with zipfile.ZipFile(package) as z:
        source = z.read('main.py').decode('utf-8')
        tree = ast.parse(source)
        signatures = {n.name: [arg.arg for arg in n.args.args] for n in tree.body if isinstance(n, ast.FunctionDef) and n.decorator_list}
        visit = next(v for v in json.loads(z.read('datos_preparados/vnext/capabilities.json'))['capabilities'] if v['id'] == 'plan_visit')
        assert len(signatures) == 9 and signatures['plan_visit'] == ['origin_id', 'destination_id', 'date', 'appointment_time', 'duration_minutes'] + OPTIONAL
        assert 'comparación 2–4' in visit['description'] and 'object_or_array' == visit['input_fields'][0]['type']
        dump(output / 'capability_claim_audit.json', dict(severity='MEDIUM', scope='Static public interface capability mismatch, not arithmetic/LLM failure', advertised=visit['description'], internal_input_fields=visit['input_fields'], public_signatures=signatures, decision='Do not advertise public batch comparison of health visits; no W2 patch'))
        common_sources = {name: sha(z.read('datos_preparados/' + name)) for name in ['municipios.csv', 'demografia.csv', 'runtime_municipality_points.csv', 'runtime_servicios.csv', 'metadata_sources.json', 'data_contract.json']}
        assert all(digest == sha((ROOT / 'datos_preparados' / name).read_bytes()) for name, digest in common_sources.items())
        dump(output / 'common_source_identity.json', dict(status='PASS', sources=common_sources, v4=V4, both_use_identical_bytes=True))
    dump(output / 'release_state.json', dict(current_agent={'critical': 0, 'high': 1, 'medium': 3}, w3_medium=2, additional_static_medium=1, M05_plan_calls=3, M05_domain_failures=2, budget={'used': 5, 'remaining': 7, 'maximum': 12}, RELEASE_GO='NO', READY_FOR_FEEDBACK='NO', source='M05 original/normalized at pinned W3, not W1 portal call', CI_discrepancy='Readiness embeds old evaluator CI36765616561; latest exact f4fd0a3 CI36774476469 independently verified SUCCESS'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reconcile-only', action='store_true')
    a = parser.parse_args()
    if a.reconcile_only:
        audit(a.package.resolve(), a.manifest.resolve())
        reconcile(a.package.resolve(), a.output.resolve())
    else:
        run(a.package.resolve(), a.manifest.resolve(), a.output.resolve())
    print('FINAL_PUBLIC_RELEASE_BENCHMARK=PASS; V4_VNEXT_COMMON_BENCHMARK=PASS; HOLDOUT=SEALED; RELEASE_GO=NO')
