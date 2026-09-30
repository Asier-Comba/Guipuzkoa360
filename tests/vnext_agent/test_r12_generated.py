"""R12: exercise the actual two-editor artifact, not acceptance logic in runtime."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from scripts.vnext_agent.build_package import ZIP, main as build_package


WORKER = r'''
import copy,hashlib,json,os,socket,sys
from pathlib import Path
directory=Path(sys.argv[1])
sys.path.insert(0,str(directory/'agentes/gipuzkoa360_vnext_r12') if sys.argv[2]=='declared_nested' else str(directory))
socket.socket=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('network forbidden'))
import tools,main
assert tools._workspace_root()==directory
fixture=json.load(sys.stdin) if sys.argv[2].startswith('declared_') else json.loads((directory/'datos_preparados/vnext/w1_conformance_r7.json').read_text())
cases={c['case_id']:c for c in fixture['cases']}
health=cases['health_defaults_omitted']['request']
legacy=cases['legacy_r4_explicit']['request']
def run(request):
    evidence=tools.execute('plan_visit',{'request':request},'TEST_R12',root=directory)
    response=json.loads(tools.public_result(evidence))
    assert len(tools.public_result(evidence).encode())<=tools.MAX_PUBLIC_BYTES
    assert 'raw_result_json' not in response
    return evidence,response
if sys.argv[2]=='legacy_cold':
    evidence,view=run(legacy)
    assert evidence['status']==view['status']=='valid',view
    print(json.dumps({'cold_legacy':'PASS'}));sys.exit()
for case in fixture['cases']:
    evidence,view=run(case.get('request',case.get('requests')))
    assert evidence['status']==view['status'],(case['case_id'],view)
    if case['case_id']=='invalid_structural':
        assert view['status']=='error' and not view['claims']
    elif 'requests' in case:
        assert view['status']=='valid' and len(view['outcomes'])==len(case['requests'])
    else:
        assert view['outcomes'][0]['status']==case['expected']['expected_status']
        assert view['mobility']['scenarios'][0]['status']==case['expected']['expected_status']
    if evidence['raw_result_json']:
        from prototypes.ir_y_volver import provider_r6
        raw=json.loads(evidence['raw_result_json'])
        request=case.get('request',case.get('requests'))
        expected=provider_r6.compare_visits(request) if isinstance(request,list) else provider_r6.plan_visit(request)
        assert raw==expected,(case['case_id'],'W1 raw parity')
for sequence in ([health,legacy,health],[legacy,health,legacy],[health,{**health,'date':'2026-09-30'},health]):
    outputs=[run(request)[1] for request in sequence]
    assert outputs[0]['status']==outputs[2]['status']=='valid'
    assert outputs[0]['mobility']==outputs[2]['mobility']
    assert outputs[1]['status']==('error' if sequence[1].get('date')=='2026-09-30' else 'valid')
for requests in ([legacy,{**legacy,'duration_minutes':25}],[health,{**health,'duration_minutes':25}],[legacy,health]):
    evidence,view=run(requests)
    assert view['status']=='valid' and len(view['mobility']['scenarios'])==2,view
for count in range(1,5):
    request=health if count==1 else [health]*count
    assert run(request)[1]['status']=='valid'
assert run([health]*5)[1]['status']=='error'
labels=json.loads((directory/'datos_preparados/vnext/consumer_labels_r7.json').read_text())
assert len(labels['stops'])==9 and len(labels['origins'])==3
stop_labels={r['stop_id']:r['name'] for r in labels['stops']}
route_labels={r['route_id']:r['short_name'] for r in labels['routes']}
for origin in labels['origins']:
    evidence,view=run({**health,'origin_id':origin['origin_id']})
    assert view['status']=='valid',view
    scenario=view['mobility']['scenarios'][0]
    assert scenario['origin_label']==origin['name']
    assert scenario['health_destination']['centre_id']==labels['destination']['centre_id']
    assert scenario['destination_label']==scenario['health_destination']['name']==labels['destination']['name']
    for leg in scenario['itinerary']['outbound'],scenario['itinerary']['return']:
        assert leg['from_stop_label']==stop_labels[leg['from_stop_id']]
        assert leg['to_stop_label']==stop_labels[leg['to_stop_id']]
        assert leg['route_label']==route_labels[leg['route_id']]
    assert not scenario['health_destination']['entrance_verified']
    assert scenario['health_destination']['address_conflict']
    assert scenario['walking'] and scenario['components_s'] and scenario['sources']
# Exhaustive lookup of all nine pinned GTFS stop labels, not four literal examples.
evidence,view=run(health)
raw=json.loads(evidence['raw_result_json'])
for stop_id,name in stop_labels.items():
    probe=copy.deepcopy(raw)
    probe['itinerary']['outbound']['from_stop_id']=stop_id
    projected=tools._mobility_view(probe,directory,health)
    assert projected['scenarios'][0]['itinerary']['outbound']['from_stop_label']==name
for request,wait_source in ((health,'MODEL_DEFAULTS'),({**health,'boarding_margin_minutes':5},'USER')):
    evidence,view=run(request)
    claims={c['metric_id']:c for c in evidence['claims']}
    assert claims['appointment_s']['source_ids']==['USER']
    assert claims['initial_wait_s']['source_ids']==[wait_source]
    for source in view['mobility']['scenarios'][0]['sources']:
        info=json.loads(main.consultar_fuente(source['catalog_source_id']))
        assert info['status']=='valid' and info['source_metadata'][0]['title']
evidence,view=run(legacy)
source=view['mobility']['scenarios'][0]['sources'][0]
assert source['contract_version']=='0.2.0' and 'transformation' not in source
assert json.loads(main.consultar_fuente(source['catalog_source_id']))['status']=='valid'
assert view['mobility']['scenarios'][0]['scenario_kind']=='stop_only'
# Five generated territorial regressions: binding, unit, unsupported rate,
# numerator lineage, and complete explicit comparison.
bad=tools.execute('obtener_resumen_territorial',{'municipio':'Eibar'},'TEST_BIND',transport=lambda handler,args:handler(**{**args,'municipio':'Tolosa'}))
assert bad['status']=='error' and not bad['claims']
coincidence=json.loads(main.analizar_coincidencia('primary_care',umbral_km=2,cuantil=.75))
claim=next(c for c in coincidence['claims'] if c['metric_id']=='highlighted_count')
assert claim['value']==7 and claim['unit']=='municipios'
aduna=json.loads(main.obtener_resumen_territorial('Aduna'))
assert aduna['status']=='valid' and all('rate_per_10000' not in c['evidence_path'] for c in aduna['claims'])
rate=tools.execute('obtener_resumen_territorial',{'municipio':'Eibar'},'TEST_RATE')
next(c for c in rate['claims'] if 'per_10000' in c['metric_id'])['numerator']['value']+=1
assert json.loads(tools.public_result(rate))['status']=='error'
comparison=json.loads(main.comparar_municipios(['Eibar','Tolosa'],categoria_servicio='primary_care'))
assert comparison['status']=='valid' and comparison['selection']['returned_entities']==2
assert {c['entity_label'] for c in comparison['claims'] if c['entity_type']=='municipality'}=={'Eibar','Tolosa'}
full_evidence,_=run([health]*4)
maximum=len(tools.public_result(full_evidence).encode())
original_limit=tools.MAX_PUBLIC_BYTES
tools.MAX_PUBLIC_BYTES=100
limited=json.loads(tools.public_result(full_evidence))
assert limited['status']=='error' and not limited['claims'] and 'mobility' not in limited
assert len(tools.public_result(full_evidence).encode())<=100
tools.MAX_PUBLIC_BYTES=original_limit
# Failed projection must not leak the original numeric itinerary or stack.
labels_path=directory/'datos_preparados/vnext/consumer_labels_r7.json'
saved=labels_path.read_bytes();labels_path.write_bytes(b'{}')
invalid=json.loads(tools.public_result(full_evidence))
assert invalid['status']=='error' and not invalid['claims'] and 'mobility' not in invalid
labels_path.write_bytes(saved)
for invalid_root in ('',str(directory/'missing')):
    os.environ['GIPUZKOA360_VNEXT_ROOT']=invalid_root
    failed=json.loads(main.plan_visit(health))
    assert failed['status']=='error' and not failed['claims'] and 'mobility' not in failed
    assert failed['error']['origin']=='data'
os.environ.pop('GIPUZKOA360_VNEXT_ROOT')
assert json.loads(main.plan_visit(health))['status']=='valid'
print(json.dumps({'fourteen_cases':'PASS','sequences':'PASS','territorial_probes':5,'stop_labels':9,'origins':3,'max_four_scenario_public_bytes':maximum,'cwd':str(Path.cwd()),'root':str(tools._workspace_root())}))
'''


@pytest.mark.parametrize("mode", ["candidate_cwd", "foreign_data_cwd", "legacy_cold", "declared_freeze", "declared_nested"])
def test_generated_r12_end_to_end(tmp_path: Path, mode: str):
    build_package()
    directory = tmp_path / "candidate"
    with zipfile.ZipFile(ZIP) as archive:
        fixture = json.loads(archive.read("datos_preparados/vnext/w1_conformance_r7.json"))
        if mode.startswith("declared_"):
            import ast
            tree = ast.parse(archive.read("main.py").decode("utf-8"))
            context = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "STUDIO_CONTEXT_FILES" for target in node.targets))
            for member in context:
                archive.extract(member, directory)
            code_directory = directory / "agentes/gipuzkoa360_vnext_r12" if mode == "declared_nested" else directory
            code_directory.mkdir(parents=True, exist_ok=True)
            for member in ("main.py", "tools.py"):
                archive.extract(member, code_directory)
            assert not (directory / "tests").exists()
            assert not (directory / "datos_preparados/vnext/w1_conformance_r7.json").exists()
        else:
            archive.extractall(directory)
    observer = tmp_path / "observer"
    (observer / "datos_preparados").mkdir(parents=True)
    (observer / "datos_preparados/metadata_sources.json").write_text("[]")
    environment = {**os.environ, "PYTHONPATH": "", "PYTHONNOUSERSITE": "1", "PYTHONUTF8": "1", "GIPUZKOA360_DATA_DIR": str(observer / "datos_preparados")}
    environment.pop("GIPUZKOA360_VNEXT_ROOT", None)
    run = subprocess.run([sys.executable, "-c", WORKER, str(directory), mode],
                         cwd=directory if mode == "candidate_cwd" else observer,
                         env=environment, input=json.dumps(fixture) if mode.startswith("declared_") else None,
                         text=True, encoding="utf-8", capture_output=True, timeout=180)
    assert run.returncode == 0, run.stderr + run.stdout
    print(run.stdout)


def test_r12_double_build_identical():
    build_package()
    first = hashlib.sha256(ZIP.read_bytes()).hexdigest()
    build_package()
    assert hashlib.sha256(ZIP.read_bytes()).hexdigest() == first
