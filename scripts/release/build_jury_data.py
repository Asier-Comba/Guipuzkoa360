"""Export real frozen-core calculations for the existing jury visual design."""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'agentes/gipuzkoa360'))
from data_access import DataRepository
from tools import TerritorialAnalysis

spec = importlib.util.spec_from_file_location('jury_gate', ROOT / 'scripts/benchmark/verify_jury_results.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def build():
    analysis = TerritorialAnalysis(DataRepository(ROOT / 'datos_preparados'))
    cases = gate.compute_cases()
    assert all(c['status'] == 'PASS' for c in cases)
    for case in cases:
        args = {'categoria_servicio': 'primary_care', 'grupo_edad': case['age_group'],
                'umbral_km': case['threshold_km'], 'periodo': gate.PERIOD, 'cuantil': case['quantile']}
        raw = analysis.coincidencia('primary_care', case['age_group'], case['threshold_km'], gate.PERIOD, case['quantile'])
        case.update({'tool': 'analizar_coincidencia', 'arguments': args, 'output': raw})
    geometry = json.loads((ROOT / 'datos_preparados/runtime_municipios.geojson').read_text(encoding='utf-8'))
    aduna = analysis.repo.municipality_lookup('Aduna')
    scenario = analysis.escenario('add_service', 'primary_care', 2, gate.PERIOD,
                                 aduna['latitude'], aduna['longitude'], 'HYPOTHETICAL_ADUNA')
    return {'execution_mode': 'recorded_local_calculation', 'runtime_sha': '195b4980fa5998b096c308296a55e452380b0371',
            'period': gate.PERIOD, 'cases': cases, 'geometry': geometry,
            'control_comparison': analysis.comparar(['Donostia', 'Eibar', 'Tolosa'], '75', 'primary_care', 2, gate.PERIOD),
            'aduna_scenario': scenario, 'sources': analysis.repo.metadata()['sources']}


if __name__ == '__main__':
    result = build()
    target = ROOT / 'analisis/jury_visual_data.json'
    target.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'file': str(target.relative_to(ROOT)), 'cases': [c['highlighted_count'] for c in result['cases']], 'geometry_count': len(result['geometry']['features'])}))
