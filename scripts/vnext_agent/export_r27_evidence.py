"""Capture reproducible W1 contract examples from the actual packaged public tools."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from scripts.vnext_agent import build_r27 as build


def run(output):
    cases = [dict(id='threshold', tool='simular_cambiar_umbral', arguments=dict(categoria_servicio='primary_care', umbral_actual_km=2, nuevo_umbral_km=3), keep_raw=True),
             dict(id='registered', tool='obtener_resumen_territorial', arguments=dict(municipio='Aduna'), keep_raw=True)]
    for label, origin, times, duration in [('zegama', 'zegama_center_stops', ['09:30', '09:45'], 20),
                                         ('segura', 'segura_herriko_plaza_stops', ['10:00', '10:15'], 30)]:
        cases.append(dict(id=label, tool='plan_visit', arguments=dict(origin_id=origin,
            destination_id='beasain_official_centre_anchor', date='2026-09-29', appointment_times=times, duration_minutes=duration)))
    with tempfile.TemporaryDirectory(prefix='r27-evidence-') as directory:
        with zipfile.ZipFile(build.ZIP) as z:
            z.extractall(directory)
        result = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'scripts.vnext_agent.worker_r20', directory],
            cwd=build.ROOT, input=json.dumps(dict(cases=cases)), text=True, encoding='utf-8', capture_output=True, check=True)
    records = json.loads(result.stdout)['records']
    assert all(r['status'] == 'valid' for r in records.values())
    ledger = records['threshold']['view']['threshold_transition_ledger']
    counts = [c for c in records['registered']['claims'] if 'registered_service_count' in c['metric_id']]
    assert ledger['verified']
    health = {label: records[label]['view']['comparison_ledger'] for label in ('zegama', 'segura')}
    assert (health['zegama']['left']['total_seconds'], health['zegama']['right']['total_seconds'], health['zegama']['total_delta_seconds']) == (10691, 8591, -2100)
    assert (health['segura']['left']['total_seconds'], health['segura']['right']['total_seconds'], health['segura']['total_delta_seconds']) == (9323, 11123, 1800)
    report = dict(contract='threshold_transition_ledger/v1', base_sha=build.BASE,
        zip_sha256=build.sha(build.ZIP.read_bytes()), manifest_sha256=build.sha(build.MANIFEST.read_bytes()),
        package_bytes=build.ZIP.stat().st_size, threshold_input=cases[0]['arguments'],
        threshold_transition_ledger=ledger, registered_count_input=cases[1]['arguments'],
        registered_count_claims=counts,
        registered_count_publicly_exposed=bool(counts),
        registered_count_raw=records['registered']['raw']['data'][0]['service_indicators'],
        healthcare_regression=health,
        public_json_bytes=len(json.dumps(records['threshold']['view'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()),
        portal_llm='NOT_RUN', main_changed=False, context_assets_changed=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')
    return {k: v for k, v in report.items() if k not in ('threshold_transition_ledger', 'registered_count_claims', 'registered_count_raw', 'healthcare_regression')}


if __name__ == '__main__':
    print(json.dumps(run(Path(sys.argv[1]) if len(sys.argv) > 1 else build.ROOT / 'work/r27-contract.json'), sort_keys=True))
