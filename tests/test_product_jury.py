"""Frozen tools and official data -> product evidence -> standalone jury views."""
from __future__ import annotations
import ast
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import pytest
import tools

ROOT = Path(__file__).resolve().parents[1]
E = json.loads((ROOT/'resultados/evidencia/product_evidence.json').read_text(encoding='utf-8'))
CANONICAL = json.loads((ROOT/'analisis/jury_visual_data.json').read_text(encoding='utf-8'))

@pytest.fixture(autouse=True)
def real_data(monkeypatch):
    monkeypatch.setenv('GIPUZKOA360_DATA_DIR',str(ROOT/'datos_preparados'))
    tools.clear_analysis_cache()

@pytest.fixture(scope='module')
def bundled():
    spec=importlib.util.spec_from_file_location('product_portal_bundle',ROOT/'agentes/gipuzkoa360/portal/tools.py')
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('case',list(E['calls']))
def test_product_evidence_matches_core_and_frozen_bundle(case,bundled):
    saved=E['calls'][case]
    for implementation in (tools,bundled):
        assert json.loads(getattr(implementation,saved['tool'])(**saved['arguments'])) == saved['output']
    encoded=json.dumps(saved['output'],ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
    assert hashlib.sha256(encoded.encode()).hexdigest()==saved['output_sha256']

@pytest.mark.parametrize('index,count',[(0,7),(1,4),(2,2)])
def test_map_canonical_and_compact_rows_agree(index,count):
    c=CANONICAL['cases'][index]
    fresh=json.loads(tools.analizar_coincidencia(**c['arguments'],detalle=True))
    assert fresh.pop('detail_level')=='full'  # Public wrapper adds this presentation metadata.
    assert fresh==c['output']
    assert len(fresh['data'])==len({r['municipality_code'] for r in fresh['data']})==88
    expected=[r for r in fresh['data'] if r['highlighted']]
    assert len(expected)==count
    assert expected==E['calls'][['main','followup','strict'][index]]['output']['data']
    assert {str(f['properties']['municipality_code']) for f in CANONICAL['geometry']['features']}=={r['municipality_code'] for r in fresh['data']}

def test_donostia_displayed_control_matches_original_official_csv():
    with (ROOT/'datos_originales/eustat_demografia_2025.csv').open(encoding='latin-1',newline='') as f:
        raw={r['grandes grupos de edad cumplida']:int(r['2025/01/01']) for r in csv.DictReader(f)
             if r['ámbitos territoriales']=='Donostia / San Sebastián' and r['sexo']=='Total'}
    row=E['calls']['donostia']['output']['data'][0]
    assert row['population_total']==raw['Total']==183388
    assert row['population_65_plus']==raw['>= 65']==48832
    assert row['pct_65_plus']==pytest.approx(100*raw['>= 65']/raw['Total'],abs=.0005)

def test_aduna_distinguishes_no_registers_from_geometric_scenario():
    aduna=E['calls']['aduna']['output']['data'][0]['service_indicators']['primary_care']
    assert aduna['registered_service_count']==0
    assert aduna['nearest_distance_m']==2756.2
    output=E['calls']['scenario']['output']
    assert output['summary']['total_result_rows']==88
    assert output['summary']['affected_rows']==2
    row=next(r for r in output['data'] if r['municipality_name']=='Aduna')
    assert (row['baseline_distance_m'],row['scenario_distance_m'],row['difference_absolute_m'])==(2756.2,0,-2756.2)

@pytest.mark.parametrize('case',['missing','category_error','source_error','period_error'])
def test_errors_never_fabricate_numeric_rows(case):
    error=E['calls'][case]['output']
    assert error['status']=='error'
    assert error['error_code']
    assert 'data' not in error

def test_evidence_fingerprints_match_inputs():
    for name,digest in E['input_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name

def test_validation_kpis_come_from_report_with_original_denominators():
    original=json.loads((ROOT/E['validation']['source']).read_text(encoding='utf-8'))
    for key in ['checks','traceability','open_by_severity','issues']:
        assert E['validation'][key]==original[key]
    for group in ['fault_injection','soak']:
        for key,value in E['validation'][group].items():
            assert value==original[group][key]
    assert E['validation']['traceability']['numerator']==E['validation']['traceability']['denominator']==31545
    assert E['validation']['open_by_severity']['Medium']==1

def test_seven_visible_operations_match_public_runtime_inventory():
    tree=ast.parse((ROOT/'agentes/gipuzkoa360/portal/main.py').read_text(encoding='utf-8'))
    names={n.name for n in tree.body if isinstance(n,ast.FunctionDef) and any(isinstance(d,ast.Name) and d.id=='tool' for d in n.decorator_list)}
    assert names==set(E['inventory']['tools'])
    assert len(names)==7
    renderer=(ROOT/'scripts/jury_view.js').read_text(encoding='utf-8-sig')
    operation_block=renderer.split('const operations=')[1].split('const operationNames=')[0]
    assert all(name in operation_block for name in names)

@pytest.mark.parametrize('filename,mode',[('demo.html','hero'),('informe_principal.html','report'),('scenario_comparison.html','scenario'),('control_center.html','control')])
def test_all_views_embed_exact_evidence_without_network_dependencies(filename,mode):
    html=(ROOT/'resultados'/filename).read_text(encoding='utf-8')
    for script_id,expected in [('jury-data',CANONICAL),('product-data',E)]:
        match=re.search(r'<script id="'+script_id+r'" type="application/json">(.*?)</script>',html,re.S)
        assert json.loads(match.group(1))==expected
    assert f'data-mode="{mode}"' in html
    assert not re.search(r'<(?:script|link|img)[^>]+(?:src|href)="https?://',html)
    assert not re.search(r'\b(?:fetch|XMLHttpRequest|WebSocket)\s*\(',html)
    static_copy=re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>','',html,flags=re.S)
    assert not re.search(r'\b(?:Work [123]|RC[12]|fixture|synthetic|TODO|pending|LLM)\b',static_copy)

def test_public_surfaces_do_not_present_historical_runner_block_as_current():
    public_files=[
        ROOT/'docs/JURY_ONE_PAGER.md',
        ROOT/'docs/DEMO.md',
        ROOT/'docs/PRODUCT_GUIDE.md',
        ROOT/'resultados/demo.html',
        ROOT/'resultados/informe_principal.html',
        ROOT/'resultados/scenario_comparison.html',
        ROOT/'resultados/control_center.html',
    ]
    forbidden=('el último smoke quedó bloqueado','la última prueba quedó bloqueada')
    for path in public_files:
        copy=path.read_text(encoding='utf-8').lower()
        assert all(phrase not in copy for phrase in forbidden),path

def test_regeneration_is_byte_reproducible_and_preserves_frozen_inputs():
    outputs=[ROOT/'resultados'/x for x in ['demo.html','informe_principal.html','scenario_comparison.html','control_center.html','evidencia/product_evidence.json','evidencia/jury_visual_data.json']]
    before=[p.read_bytes() for p in outputs]
    protected={p:(ROOT/p).read_bytes() for p in E['input_sha256']}
    subprocess.run([sys.executable,'scripts/release/build_jury_data.py'],cwd=ROOT,check=True,capture_output=True)
    subprocess.run(['node','scripts/build_jury.mjs'],cwd=ROOT,check=True,capture_output=True)
    assert [p.read_bytes() for p in outputs]==before
    assert all((ROOT/p).read_bytes()==contents for p,contents in protected.items())

def test_prototype_evidence_is_frozen_and_explicitly_offline():
    prototype=E['next_prototype']
    saved=json.loads((ROOT/'resultados/evidencia/next_prototype.json').read_text(encoding='utf-8'))
    assert prototype==saved
    assert prototype['versions']['RUNTIME_VERSION']==E['runtime_sha']
    assert 'OFFLINE PROTOTYPE' in prototype['scope']
    assert 'no LLM routing benchmark' in prototype['scope']
    assert prototype['reconciliation_status']=='complete'
    assert prototype['prototype_test_summary']=={'command':'python -m pytest tests/next -o addopts= -q','passed':77,'failed':0,'date':'2026-09-25'}
    assert prototype['quality_kpis']['tool_selection_accuracy']['denominator']==9
    assert prototype['quality_kpis']['out_of_scope_rejection_rate']['denominator']==6
    assert len(prototype['source_commit'])==40
    assert len(prototype['snapshot_commit'])==40

def test_final_prototype_snapshot_matches_published_work1_contract():
    prototype=E['next_prototype']
    snapshot_keys={'scope','source_commit','source_evidence_path','versions','capabilities',
                   'quality_kpis','prototype_test_summary','adversarial_summary','limitations',
                   'self_improvement_policy'}
    snapshot={key:prototype[key] for key in snapshot_keys}
    canonical=json.dumps(snapshot,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    assert hashlib.sha256(canonical).hexdigest()=='d9fb03065ec883685baabc2dd65714afec7eab93f182eb0b25ad2abd6b7f0267'
