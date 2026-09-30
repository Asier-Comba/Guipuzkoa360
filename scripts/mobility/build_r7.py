"""Build R7 consumer-support evidence without changing the frozen R6 runtime."""
import csv
import hashlib
import io
import json
import zipfile

from prototypes.ir_y_volver import provider as r4
from prototypes.ir_y_volver import provider_r6 as p
from scripts.mobility.build_health_r5 import ROOT, DOC, dump
from scripts.mobility.verify_health_r5 import oracle, read_raw

DATA = ROOT / 'datos_preparados/movilidad'
GTFS = ROOT / 'datos_originales/movilidad/goierrialdea-3276fcae.zip'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(name):
    with zipfile.ZipFile(GTFS) as archive:
        return list(csv.DictReader(io.StringIO(archive.read(name).decode('utf-8-sig'))))


def build_labels():
    health, base = p.r5._load()
    gtfs_source = next(s for s in health['sources'] if s['source_id'] == 'GTFS')
    stop_ids = set(health['walking_links'])
    for origin in health['origins'].values(): stop_ids.update(origin['stop_ids'])
    stops = {r['stop_id']: r['stop_name'] for r in _rows('stops.txt') if r['stop_id'] in stop_ids}
    assert set(stops) == stop_ids
    routes = {r['route_id']: {'short_name':r['route_short_name'], 'long_name':r['route_long_name']}
              for r in _rows('routes.txt') if r['route_short_name'] == 'GO01'}
    assert len(routes) == 1
    catalog = json.loads((DATA/'operational_catalog_r6.json').read_bytes())
    labels = {'schema_version':'1.0.0','contract_version':'0.3.1',
      'snapshot_id':health['snapshot_id'],'scenario_kind':{'id':'health_visit','label':'Visita sanitaria programada'},
      'validated_date':health['validated_date'],
      'scope':{'id':p.r4.SCOPE,'label':'Desde la presencia en la parada de origen hasta la llegada a la parada de regreso'},
      'origins':[{'origin_id':x['origin_id'],'name':x['name'],'municipality_code':x['municipality_code'],
                  'municipality_name':x['municipality_name']} for x in catalog['origins']],
      'stops':[{'stop_id':sid,'name':stops[sid]} for sid in sorted(stops)],
      'destination':{'destination_id':health['destination_id'],'name':health['health_destination']['name'],
        'centre_id':health['health_destination']['centre_id'],'entrance_verified':False,'modelled_access':True},
      'routes':[{'route_id':rid,**value} for rid,value in sorted(routes.items())],
      'walking_profile':{'id':health['walking_profile_id'],'label':'Paseo modelado de referencia: 50 m/min más 120 s por enlace completo'},
      'provenance':[
        {'source_id':'GTFS','source_sha256':gtfs_source['source_sha256'],'reference_period':health['validated_date'],
         'transformation':'Nombres de paradas y ruta seleccionados por IDs del snapshot fijado.'},
        {'source_id':'HEALTH_REGISTRY','source_sha256':next(s for s in health['sources'] if s['source_id']=='HEALTH_REGISTRY')['source_sha256'],
         'reference_period':next(s for s in health['sources'] if s['source_id']=='HEALTH_REGISTRY')['reference_period'],
         'transformation':'Nombre e identidad del centro del snapshot sanitario fijado.'},
        {'source_id':'R6_OPERATIONAL_CATALOG','source_sha256':sha(DATA/'operational_catalog_r6.json'),
         'reference_period':health['validated_date'],'transformation':'Correspondencia uno-a-uno de origin_id y código municipal.'}]}
    dump(DATA/'consumer_labels_r7.json', labels)
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','type':'object','additionalProperties':False,
      'required':list(labels),'properties':{
        'schema_version':{'const':'1.0.0'},'contract_version':{'const':'0.3.1'},
        'snapshot_id':{'const':health['snapshot_id']},'scenario_kind':{'type':'object','additionalProperties':False,
          'required':['id','label'],'properties':{'id':{'const':'health_visit'},'label':{'type':'string','minLength':1}}},
        'validated_date':{'const':health['validated_date']},'scope':{'type':'object','additionalProperties':False,
          'required':['id','label'],'properties':{'id':{'const':p.r4.SCOPE},'label':{'type':'string','minLength':1}}},
        'origins':{'type':'array','minItems':3,'maxItems':3,'items':{'type':'object','additionalProperties':False,
          'required':['origin_id','name','municipality_code','municipality_name'],'properties':{
            'origin_id':{'type':'string'},'name':{'type':'string'},'municipality_code':{'type':'string','pattern':'^[0-9]{5}$'},
            'municipality_name':{'type':'string'}}}},
        'stops':{'type':'array','minItems':9,'items':{'type':'object','additionalProperties':False,
          'required':['stop_id','name'],'properties':{'stop_id':{'type':'string'},'name':{'type':'string','minLength':1}}}},
        'destination':{'type':'object','additionalProperties':False,
          'required':['destination_id','name','centre_id','entrance_verified','modelled_access'],'properties':{
            'destination_id':{'type':'string'},'name':{'type':'string'},'centre_id':{'type':'string'},
            'entrance_verified':{'const':False},'modelled_access':{'const':True}}},
        'routes':{'type':'array','minItems':1,'items':{'type':'object','additionalProperties':False,
          'required':['route_id','short_name','long_name'],'properties':{'route_id':{'type':'string'},
            'short_name':{'type':'string'},'long_name':{'type':'string'}}}},
        'walking_profile':{'type':'object','additionalProperties':False,'required':['id','label'],
          'properties':{'id':{'type':'string'},'label':{'type':'string'}}},
        'provenance':{'type':'array','minItems':3,'items':{'type':'object','additionalProperties':False,
          'required':['source_id','source_sha256','reference_period','transformation'],'properties':{
            'source_id':{'type':'string'},'source_sha256':{'type':'string','pattern':'^[0-9a-f]{64}$'},
            'reference_period':{'type':'string'},'transformation':{'type':'string'}}}}}}
    dump(DATA/'consumer_labels_r7.schema.json', schema)
    return labels


def _summary(result, evidence_class):
    item={'evidence_class':evidence_class,'contract_version':result['schema_version'],
      'expected_status':result['status'],'expected_normalized_fields':result['normalized_request'],
      'identity':{'snapshot_id':result.get('snapshot_id'),'scenario_kind':result.get('scenario_kind'),
                  'scope':result.get('scope')},'error':result.get('error')}
    if result['status']=='ok':
        it=result['itinerary']; item.update(selected_trip_ids=[it['outbound']['trip_id'],it['return']['trip_id']],
          selected_stop_ids=[it['outbound']['from_stop_id'],it['outbound']['to_stop_id'],it['return']['from_stop_id'],it['return']['to_stop_id']],
          scheduled_times=[it['outbound']['departure_time'],it['outbound']['arrival_time'],it['return']['departure_time'],it['return']['arrival_time']],
          components=result['components_s'],total_s=it['total_s'],return_slack_s=it['return_slack_s'],walking=result.get('walking'),
          health_destination_flags={k:result['health_destination'][k] for k in ('centre_id','modelled_access','entrance_verified','address_conflict')}
          if result.get('health_destination') else None, parameter_provenance=result.get('parameter_provenance'),
          required_source_roles=sorted({s.get('source_role',s.get('classification')) for s in result['sources']}),
          limitations=result['limitations'])
    return item


def build_conformance():
    health,_=p.r5._load();raw=read_raw()
    base=dict(origin_id='zegama_center_stops',destination_id=health['destination_id'],date=health['validated_date'],
              appointment_time='09:45',duration_minutes=20)
    cases=[]
    requests=[('health_defaults_omitted',base),
      ('health_defaults_explicit',{**base,'arrival_margin_minutes':10,'boarding_margin_minutes':3,
                                   'walking_profile_id':health['walking_profile_id'],'snapshot_id':health['snapshot_id'],'return_deadline':None}),
      ('health_nondefault_margins',{**base,'arrival_margin_minutes':5,'boarding_margin_minutes':7}),
      ('health_duration_changes_return',{**base,'duration_minutes':26}),
      ('health_no_feasible',{**base,'appointment_time':'22:00'}),
      ('health_date_not_validated',{**base,'date':'2026-09-30'}),
      ('health_destination_unsupported',{**base,'destination_id':'unknown'}),
      ('health_profile_unsupported',{**base,'walking_profile_id':'unknown'})]
    for case_id,request in requests:
        result=p.plan_visit(request); summary=_summary(result,'PRODUCER_FIXTURE')
        if request['date']==health['validated_date'] and request['destination_id']==health['destination_id'] and request.get('walking_profile_id',health['walking_profile_id'])==health['walking_profile_id']:
            expected=oracle(raw,request,health); summary['independent_gtfs_expected']=expected
            assert result['status']==expected['status']
            if result['status']=='ok': assert result['itinerary']['total_s']==expected['total_s']
        cases.append({'case_id':case_id,'request':request,'expected':summary})
    comparisons=[('compare_same_origin_two_hours',[base,{**base,'appointment_time':'10:00'}]),
      ('compare_duration',[base,{**base,'duration_minutes':26}]),
      ('compare_cross_origin',[base,{**base,'origin_id':'segura_herriko_plaza_stops'}])]
    for case_id,requests in comparisons:
        result=p.compare_visits(requests)
        cases.append({'case_id':case_id,'requests':requests,'expected':{'evidence_class':'PRODUCER_FIXTURE',
          'contract_version':result['schema_version'],'expected_status':result['status'],
          'result_summaries':[_summary(x,'PRODUCER_FIXTURE') for x in result['results']],
          'comparisons':result['comparisons']}})
    r4q={'origin_id':'zegama_center_stops','destination_id':'beasain_center_stop_pair','date':'2026-09-29',
         'appointment_time':'09:30','duration_minutes':30,'snapshot_id':r4.DEFAULT_SNAPSHOT_ID}
    cases.append({'case_id':'legacy_r4_explicit','request':r4q,'expected':_summary(p.plan_visit(r4q),'PRODUCER_FIXTURE_WITH_R4_INDEPENDENT_FIXTURE')})
    mixed=p.compare_visits([base,r4q]); cases.append({'case_id':'mixed_r4_r6','requests':[base,r4q],
      'expected':{'evidence_class':'PRODUCER_FIXTURE','contract_version':mixed['schema_version'],
      'expected_status':mixed['status'],'result_summaries':[_summary(x,'PRODUCER_FIXTURE') for x in mixed['results']],
      'comparisons':mixed['comparisons']}})
    invalid={**base,'duration_minutes':'20'}; cases.append({'case_id':'invalid_structural','request':invalid,
      'expected':_summary(p.plan_visit(invalid),'CONTRACT_SEMANTICS')})
    assert len(cases)==14
    artifact={'pack_version':'r7.0','producer_contract':'0.3.1','producer_entrypoint':'prototypes.ir_y_volver.provider_r6',
      'r6_package_sha256':'c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910',
      'evidence_hashes':{'gtfs_zip':sha(GTFS),
        'health_snapshot':sha(ROOT/f"prototypes/ir_y_volver/snapshots/{health['snapshot_id']}.json"),
        'result_schema_0_3_1':sha(ROOT/'prototypes/ir_y_volver/contracts/v0.3.1/result.schema.json'),
        'operational_catalog_r6':sha(DATA/'operational_catalog_r6.json'),
        'consumer_labels_r7':sha(DATA/'consumer_labels_r7.json'),
        'walking_model':sha(ROOT/'prototypes/ir_y_volver/walking_r5.py')},
      'classification_note':'PRODUCER_FIXTURE values are observations, not independent oracles. independent_gtfs_expected is computed from raw CSV selection.',
      'cases':cases}
    dump(DOC/'CONSUMER_CONFORMANCE_R7.json',artifact)
    md=['# Consumer conformance W1 R7','','Contrato productor: `0.3.1` (R6 congelado).',
      'Los valores `PRODUCER_FIXTURE` son observaciones del productor, no oráculos independientes. Las selecciones temporales marcadas `independent_gtfs_expected` proceden del CSV GTFS bruto.',
      '', '| Caso | Estado | Evidencia |','|---|---|---|']
    for case in cases:
        expected=case['expected'];md.append(f"| `{case['case_id']}` | `{expected['expected_status']}` | `{expected['evidence_class']}` |")
    md += ['', 'W2 debe ejecutar sus resultados contra este pack sin copiar la lógica de selección. W3 puede mutar cada campo y contrastar status, identidades, componentes, procedencia y límites.']
    (DOC/'CONSUMER_CONFORMANCE_R7.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    return artifact


def run(): return {'labels':build_labels(),'conformance':build_conformance()}


if __name__=='__main__':
    result=run();print(json.dumps({'labels':len(result['labels']['stops']),'cases':len(result['conformance']['cases'])}))
