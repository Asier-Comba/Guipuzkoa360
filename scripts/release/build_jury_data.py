"""Export real frozen-core calculations for the existing jury visual design."""
from __future__ import annotations
import importlib.util
import ast
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'agentes/gipuzkoa360'))
from data_access import DataRepository
from tools import TerritorialAnalysis
import tools as core

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


def build_product_evidence():
    """Additional presentation evidence. Keep build() and its canonical gate unchanged."""
    calls = {}
    def call(key, operation, arguments, question):
        output = json.loads(getattr(core, operation)(**arguments))
        calls[key] = {'tool': operation, 'arguments': arguments, 'question': question,
                      'execution': 'local_saved', 'output': output}
    previous = os.environ.get('GIPUZKOA360_DATA_DIR')
    os.environ['GIPUZKOA360_DATA_DIR'] = str(ROOT / 'datos_preparados')
    core.clear_analysis_cache()
    try:
        for key, age, quantile, threshold in [('main','65',.75,2),('followup','75',.8,3),('strict','65',.85,2)]:
            call(key, 'analizar_coincidencia', {'categoria_servicio':'primary_care','grupo_edad':age,
                 'umbral_km':threshold,'periodo':gate.PERIOD,'cuantil':quantile},
                 f'Coincidencia de {age}+, atención primaria, cuantil {quantile}, umbral {threshold} km y {gate.PERIOD}.')
        call('comparison','comparar_municipios',{'municipios':['Donostia / San Sebastián','Eibar','Tolosa'],
             'grupo_edad':'75','categoria_servicio':'primary_care','umbral_km':2,'periodo':gate.PERIOD},
             'Compara Donostia / San Sebastián, Eibar y Tolosa para 75+ y atención primaria.')
        for key, name in [('donostia','Donostia / San Sebastián'),('aduna','Aduna'),('eibar','Eibar')]:
            call(key,'obtener_resumen_territorial',{'municipio':name,'periodo':gate.PERIOD},f'Resume {name}.')
        aduna = DataRepository(ROOT / 'datos_preparados').municipality_lookup('Aduna')
        call('scenario','simular_escenario',{'accion':'add_service','categoria_servicio':'primary_care',
             'umbral_km':2,'periodo':gate.PERIOD,'latitud':aduna['latitude'],'longitud':aduna['longitude']},
             'Escenario hipotético: añadir atención primaria en el punto representativo de Aduna.')
        call('source','consultar_fuente',{'source_id':'EUSTAT_EMH_2025'},'¿De dónde sale la población?')
        call('missing','obtener_resumen_territorial',{'municipio':'Villa GPT','periodo':gate.PERIOD},'Resume Villa GPT.')
        call('category_error','analizar_acceso_servicios',{'categoria_servicio':'farmacia','umbral_km':2,'periodo':gate.PERIOD},'Distancia a farmacias.')
        call('source_error','consultar_fuente',{'source_id':'FUENTE_NO_CARGADA'},'Consulta una fuente no cargada.')
        call('period_error','obtener_resumen_territorial',{'municipio':'Aduna','periodo':'2030-01-01'},'Resume Aduna para 2030.')
    finally:
        if previous is None:
            os.environ.pop('GIPUZKOA360_DATA_DIR', None)
        else:
            os.environ['GIPUZKOA360_DATA_DIR'] = previous
        core.clear_analysis_cache()
    for key, record in calls.items():
        expected = 'error' if key in {'missing','category_error','source_error','period_error'} else 'ok'
        if record['output']['status'] != expected:
            raise ValueError(f'Unexpected outcome for {key}')
        raw = json.dumps(record['output'],ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
        record['output_sha256'] = hashlib.sha256(raw.encode()).hexdigest()
    report_path = 'analisis/final/full_validation.json'
    report = json.loads((ROOT / report_path).read_text(encoding='utf-8'))
    validation = (ROOT / 'docs/VALIDATION.md').read_text(encoding='utf-8')
    python_counts = re.search(r'(\d+)/(\d+) tests Python', validation).groups()
    node_counts = re.search(r'(\d+)/(\d+) Node', validation).groups()
    public = ast.parse((ROOT / 'agentes/gipuzkoa360/portal/main.py').read_text(encoding='utf-8'))
    tool_names = [n.name for n in public.body if isinstance(n, ast.FunctionDef)
                  and any(isinstance(d, ast.Name) and d.id == 'tool' for d in n.decorator_list)]
    repo = DataRepository(ROOT / 'datos_preparados')
    inputs = [report_path, 'docs/VALIDATION.md', 'docs/FINAL_RELEASE_GATE.md', 'datos_originales/eustat_demografia_2025.csv',
              'agentes/gipuzkoa360/portal/main.py','agentes/gipuzkoa360/portal/tools.py']
    inputs += [p.as_posix() for p in (Path('datos_preparados') / p.name for p in sorted((ROOT / 'datos_preparados').glob('*'))) if (ROOT / p).is_file()]
    prototype_path = 'resultados/evidencia/next_prototype.json'
    prototype = json.loads((ROOT / prototype_path).read_text(encoding='utf-8')) if (ROOT / prototype_path).exists() else None
    if prototype:
        if prototype['report']['versions']['RUNTIME_VERSION'] != report['runtime_sha']:
            raise ValueError('Prototype evidence belongs to a different runtime')
        inputs.append(prototype_path)
    return {'base_sha':'46c1a48f63c307654f45fcb5c18883f264b660ed','runtime_sha':report['runtime_sha'],
            'next_prototype':prototype,
            'execution':'Cálculos locales guardados; sin conversación en directo en estos HTML.',
            'calls':calls,'sources':repo.metadata()['sources'],
            'inventory':{'municipalities':len(repo.municipalities()),'health_records':len(repo.services()),'tools':tool_names},
            'validation':{'source':report_path,'candidate_sha':report['candidate_sha'],'generated_at':report['generated_at'],
                'checks':report['checks'],'traceability':report['traceability'],'open_by_severity':report['open_by_severity'],
                'fault_injection':{k:report['fault_injection'][k] for k in ['total','controlled_rejection','silent_corruption']},
                'soak':{k:report['soak'][k] for k in ['calls','result_drift','exceptions']},'issues':report['issues'],
                'baseline_tests':{'source':'docs/VALIDATION.md','python':list(map(int,python_counts)),'node':list(map(int,node_counts))}},
            'input_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs}}


if __name__ == '__main__':
    result = build()
    target = ROOT / 'analisis/jury_visual_data.json'
    target.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n', encoding='utf-8', newline='\n')
    product = ROOT / 'resultados/evidencia/product_evidence.json'
    product.parent.mkdir(parents=True, exist_ok=True)
    product.write_text(json.dumps(build_product_evidence(),ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'file': str(target.relative_to(ROOT)), 'cases': [c['highlighted_count'] for c in result['cases']], 'geometry_count': len(result['geometry']['features'])}))
