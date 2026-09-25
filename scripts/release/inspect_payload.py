"""Record compact payload sizes without changing the frozen tool."""
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'agentes/gipuzkoa360'))
os.environ['GIPUZKOA360_DATA_DIR']=str(ROOT/'datos_preparados')
import tools

analysis=tools._analysis()
aduna=analysis.repo.municipality_lookup('Aduna')
samples=[]
for label,kwargs in (
    ('extreme_threshold_1_to_10',{'accion':'change_threshold','categoria_servicio':'primary_care','umbral_km':1,'periodo':'2025-01-01','nuevo_umbral_km':10}),
    ('jury_aduna',{'accion':'add_service','categoria_servicio':'primary_care','umbral_km':2,'periodo':'2025-01-01','latitud':aduna['latitude'],'longitud':aduna['longitude'],'service_id':'HYPOTHETICAL_ADUNA'}),
):
    raw=tools.simular_escenario(**kwargs)
    value=json.loads(raw)
    samples.append({'case':label,'arguments':kwargs,'chars':len(raw),'data_rows':len(value['data']),
                    'summary':value['summary'],'strict_json':json.dumps(value,allow_nan=False) is not None})
report={'runtime_changed':False,'cases':samples,
        'decision':'Evidence preservation accepted as design tradeoff; Medium remains open until the extreme is exercised in the portal. A smaller successful scenario does not establish that.',
        'portal_extreme_test':'NOT_EXECUTED_INFRASTRUCTURE_BLOCKED'}
(ROOT/'analisis/payload_decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
