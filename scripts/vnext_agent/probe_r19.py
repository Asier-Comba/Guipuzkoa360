"""Reproduce the observed R18 boundary defects without changing runtime."""
import io
import json
import tempfile
import zipfile
from pathlib import Path
from scripts.vnext_agent.build_r18 import ZIP, ROOT, sha
from scripts.vnext_agent.verify_r15 import run_worker

def run():
    cases = [
        ('discovery_empty', 'consultar_capacidades', {'pregunta_o_dimension': ''}),
        ('ranking_empty', 'analizar_envejecimiento', {'grupo_edad': '75', 'periodo': ''}),
        ('comparison_empty', 'comparar_municipios', {'municipios': ['Legorreta', 'Alegia'], 'grupo_edad': '75', 'categoria_servicio': ''}),
        ('ranking65', 'analizar_envejecimiento', {'grupo_edad': '65', 'medida': 'percentage', 'top_n': 5}),
        *[(f'access_empty_{i}', 'analizar_acceso_servicios', {'categoria_servicio': 'mental_health', 'umbral_km': 1, 'periodo': '', 'municipios': ['Getaria']}) for i in range(3)],
        ('access_dot', 'analizar_acceso_servicios', {'categoria_servicio': 'mental_health', 'umbral_km': 1, 'periodo': '.', 'municipios': ['Getaria']}),
        ('access_supported', 'analizar_acceso_servicios', {'categoria_servicio': 'mental_health', 'umbral_km': 1, 'municipios': ['Getaria']}),
    ]
    cases = [dict(id=i, tool=t, arguments=a, keep_view=True) for i,t,a in cases]
    data=ZIP.read_bytes()
    with tempfile.TemporaryDirectory(prefix='r19-baseline-') as directory:
        with zipfile.ZipFile(io.BytesIO(data)) as bundle: bundle.extractall(directory)
        result=run_worker(Path(directory), cases)
    records=result['records']
    assert all(records[x]['status']=='error' for x in ['discovery_empty','ranking_empty','comparison_empty','access_empty_0','access_empty_1','access_empty_2','access_dot'])
    age=records['ranking65']['view']['age_group_derivation']
    assert age['output_field']=='population_75_plus' and '1949' in age['condition']
    assert records['access_supported']['status']=='valid'
    out=ROOT/'outputs/r19/baseline-reproduction.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'classification':'R18_OFFLINE_DEFECT_REPRODUCTION_NOT_LLM_REPLAY','zip_sha256':sha(data),'records':records,'observed_real_trace_root':'../gipuzkoa360-r18/outputs/r18/portal','findings':['M01 optional empty strings','M02 age65 attached age75 semantics','M03 identical invalid access arguments reproducible; real retry behavior documented in preserved R18 traces']},ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'baseline':'PASS_REPRODUCED','cases':len(cases),'M01':True,'M02':True,'M03_invalid_arguments':True,'M03_LLM_retry':'HISTORICAL_TRACE_NOT_NEW_MODEL_CALL'}))

if __name__=='__main__':run()
