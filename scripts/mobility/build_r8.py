"""Build delivery-grade evidence around the frozen R6 producer; no runtime writes."""
import hashlib
import json
import math
from pathlib import Path

from prototypes.ir_y_volver import provider_r6 as p
from scripts.mobility.build_health_r5 import ROOT, DOC, dump
from scripts.mobility.verify_health_r5 import oracle, read_raw

DATA=ROOT/'datos_preparados/movilidad'; OUT=DOC/'integration_r8'
GTFS=ROOT/'datos_originales/movilidad/goierrialdea-3276fcae.zip'
PACKAGE_SHA='c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def value_hash(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()


def angular(a,b):
    x,y=map(math.radians,[a[0],b[0]]);dl=math.radians(b[1]-a[1])
    numerator=math.hypot(math.cos(y)*math.sin(dl),math.cos(x)*math.sin(y)-math.sin(x)*math.cos(y)*math.cos(dl))
    denominator=math.sin(x)*math.sin(y)+math.cos(x)*math.cos(y)*math.cos(dl)
    return 6371000*math.atan2(numerator,denominator)


def walk_oracle(link):
    metres=sum(angular(a,b) for a,b in zip(link['geometry'],link['geometry'][1:]));seconds=math.ceil(metres/50)*60+120
    assert abs(metres-link['total_metres'])<0.0001 and seconds==link['seconds']
    return {'verification_method':'independent atan2 geometry length + published walking formula',
      'metres':metres,'seconds':seconds,'network_sha256':link['network_sha256'],
      'way_ids_sha256':value_hash(link['way_ids']),'way_ids':link['way_ids']}


def compact(result):
    return {k:result[k] for k in ('schema_version','normalized_request','status','scenario_kind','time_basis','scope','snapshot_id',
      'itinerary','components_s','components','walking','health_destination','sources','limitations','assumptions','error','parameter_provenance')}


def build_cases():
    health,_=p.r5._load();raw=read_raw()
    common={'origin_id':'zegama_center_stops','destination_id':health['destination_id'],'date':health['validated_date'],'duration_minutes':20}
    requests={'MAIN':{**common,'appointment_time':'09:30'},
      'VARIATION_TIME':{**common,'appointment_time':'09:45'},
      'VARIATION_DURATION':{**common,'appointment_time':'09:45','duration_minutes':26},
      'LIMIT_DATE':{**common,'appointment_time':'09:30','date':'2026-09-30'},
      'LIMIT_SCOPE':{**common,'appointment_time':'09:30','destination_id':'outside_catalog'}}
    cases={}
    for case_id,request in requests.items():
        result=p.plan_visit(request);item={'case_id':case_id,'request':request,'provider_result':compact(result)}
        if case_id.startswith('LIMIT_'):
            item['verification']={'classification':'CONTRACT_STATUS_FIXTURE','expected_status':result['status']}
        else:
            expected=oracle(raw,request,health);assert expected['status']==result['status']=='ok' and expected['total_s']==result['itinerary']['total_s']
            walks={direction:walk_oracle(result['walking'][direction]) for direction in ('outbound','return')}
            item['independent_oracle']={'gtfs':expected,'walking':walks,'status':'PASS'}
        item['layer_separation']={
          'DATA':['GTFS schedule','official health anchor','OSM network'],
          'MODEL':['50 m/min','120 s per complete directed walking link','connector threshold <=100 m','provider defaults'],
          'USER':['origin_id','destination_id','date','appointment_time','duration_minutes','explicit margins when supplied'],
          'DERIVED':['selected pair','waits','slack','total']}
        cases[case_id]=item
    side=[]
    for origin in sorted(health['origins']):
        request={**common,'origin_id':origin,'appointment_time':'09:30'};result=p.plan_visit(request);expected=oracle(raw,request,health)
        assert result['status']=='ok' and result['itinerary']['total_s']==expected['total_s']
        side.append({'request':request,'provider_result':compact(result),'independent_oracle':{'gtfs':expected,
          'walking':{d:walk_oracle(result['walking'][d]) for d in ('outbound','return')},'status':'PASS'}})
    cases['ORIGIN_SIDE_BY_SIDE']={'case_id':'ORIGIN_SIDE_BY_SIDE','comparison_semantics':'side_by_side_only_no_formal_delta',
      'held_constant':['destination_id','date','appointment_time','duration_minutes'],'scenarios':side}
    left=cases['MAIN'];right=cases['VARIATION_TIME'];li=left['provider_result']['itinerary'];ri=right['provider_result']['itinerary']
    delta=ri['total_s']-li['total_s'];assert delta==-2100
    claim={'claim_id':'R8-DELTA-ZEGAMA-0930-0945','text':'Con los demás parámetros iguales, el total modelado de 09:45 es 2.100 s (35 min) menor que el de 09:30 en el snapshot validado.',
      'value':delta,'unit':'second','left_request':left['request'],'right_request':right['request'],
      'left_total_s':li['total_s'],'right_total_s':ri['total_s'],'signed_delta_s':delta,'absolute_delta_s':abs(delta),
      'source_data':['GTFS','OSM','HEALTH_REGISTRY'],'raw_rows':{'left':left['independent_oracle']['gtfs']['rows'],'right':right['independent_oracle']['gtfs']['rows']},
      'walking_evidence':{'left':left['independent_oracle']['walking'],'right':right['independent_oracle']['walking']},
      'model_assumptions':['50 m/min','120 s per complete directed walking link','boarding margin default 3 min','arrival margin default 10 min'],
      'transformation':'right_total_s - left_total_s; totals independently reconstructed from raw GTFS rows, fixed walking evidence, human inputs and published formula',
      'oracle_result':{'left_total_s':left['independent_oracle']['gtfs']['total_s'],'right_total_s':right['independent_oracle']['gtfs']['total_s'],'delta_s':delta,'status':'PASS'},
      'provider_result':{'left_total_s':li['total_s'],'right_total_s':ri['total_s'],'delta_s':delta},
      'hashes':{'gtfs_zip':sha(GTFS),'snapshot':sha(p.r5.HERE/f'snapshots/{p.ID}.json'),'walking_model':sha(p.r5.HERE/'walking_r5.py')}}
    artifact={'evidence_version':'r8.0','runtime_changed':False,'runtime_contract':'0.3.1','runtime_package_sha256':PACKAGE_SHA,
      'cases':cases,'directly_contrasted_claim':claim,'separation':{
        'DATA':['GTFS schedule','health anchor','OSM network'],'MODEL':['50 m/min','+120 s','connector <=100 m','provider defaults'],
        'USER':['origin','date','appointment time','duration','explicit margins if supplied'],
        'DERIVED':['selected pair','waits','slack','total','comparison delta']}}
    dump(DOC/'DELIVERY_EVIDENCE_R8.json',artifact)
    md=['# Evidencia canónica de entrega R8','','Runtime R6 0.3.1 congelado. Todos los tiempos son programados/modelados, no realtime.',
      '',f"**Cifra contrastada:** {claim['text']}",'', '| Caso | Resultado | Total |','|---|---|---:|']
    for cid in ('MAIN','VARIATION_TIME','VARIATION_DURATION','LIMIT_DATE','LIMIT_SCOPE'):
        result=cases[cid]['provider_result'];total=result['itinerary']['total_s'] if result['itinerary'] else '—';md.append(f"| {cid} | `{result['status']}` | {total} |")
    md += ['', 'Los tres orígenes se muestran lado a lado; no se declara un delta formal entre orígenes.',
      'La entrada física del centro no está verificada. La fecha distinta se informa como no validada, no como ausencia de autobuses.']
    (DOC/'DELIVERY_EVIDENCE_R8.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    return artifact


def build_claims(evidence):
    claims=[]
    mapping=[('total_s','itinerary.total_s','derived_exact',['GTFS','OSM','HEALTH_REGISTRY','MODEL','MODEL_DEFAULTS'],'end_s - start_s = sum components'),
      ('initial_wait_s','components_s.initial_wait_s','modelled_with_assumption',['MODEL_DEFAULTS'],'boarding_margin_minutes * 60 when omitted'),
      ('bus_out_s','components_s.outbound_vehicle_s','derived_exact',['GTFS'],'outbound arrival - departure'),
      ('walk_out_s','components_s.destination_walk_outbound_s','modelled_with_assumption',['OSM','HEALTH_REGISTRY','MODEL'],'ceil(metres/50)*60+120'),
      ('preappointment_wait_s','components_s.pre_appointment_wait_s','derived_exact',['GTFS','OSM','HEALTH_REGISTRY','MODEL','USER','MODEL_DEFAULTS'],'appointment - arrival - walk_out'),
      ('appointment_s','components_s.appointment_s','human_input',['USER'],'duration_minutes * 60'),
      ('walk_return_s','components_s.destination_walk_return_s','modelled_with_assumption',['OSM','HEALTH_REGISTRY','MODEL'],'ceil(metres/50)*60+120'),
      ('return_wait_s','components_s.return_wait_s','derived_exact',['GTFS','OSM','HEALTH_REGISTRY','MODEL','USER'],'return departure - appointment - duration - walk_return'),
      ('bus_return_s','components_s.return_vehicle_s','derived_exact',['GTFS'],'return arrival - departure'),
      ('return_slack_s','itinerary.return_slack_s','derived_exact',['GTFS','OSM','HEALTH_REGISTRY','MODEL','USER','MODEL_DEFAULTS'],'return_wait_s - boarding_margin_s')]
    for scenario in ('MAIN','VARIATION_TIME','VARIATION_DURATION'):
        result=evidence['cases'][scenario]['provider_result']
        for metric,path,classification,refs,transformation in mapping:
            value=result
            for part in path.split('.'):value=value[part]
            claims.append({'claim_id':f'{scenario}:{metric}','scenario_id':scenario,'entity':'Zegama → Ambulatorio de Beasain → Zegama',
              'metric':metric,'value':value,'unit':'second','classification':classification,'source_refs':refs,
              'reference_period':'2026-09-29','data_ref':f'DELIVERY_EVIDENCE_R8.json#/cases/{scenario}',
              'transformation':transformation,'assumptions':result['assumptions'],'limitations':result['limitations'],
              'verification_method':'raw GTFS oracle + independent walking geometry/formula','dag_node_id':f'{scenario}:{metric}'})
        it=result['itinerary']
        for name,value in [('outbound_departure_time',it['outbound']['departure_time']),('outbound_arrival_time',it['outbound']['arrival_time']),
          ('return_departure_time',it['return']['departure_time']),('return_arrival_time',it['return']['arrival_time']),
          ('outbound_trip_id',it['outbound']['trip_id']),('return_trip_id',it['return']['trip_id']),
          ('outbound_stop_id',it['outbound']['to_stop_id']),('return_stop_id',it['return']['from_stop_id'])]:
            claims.append({'claim_id':f'{scenario}:{name}','scenario_id':scenario,'entity':'GO01 scheduled journey','metric':name,'value':value,
              'unit':'HH:MM:SS' if name.endswith('_time') else 'identifier','classification':'direct_observation' if 'time' in name else 'derived_exact',
              'source_refs':['GTFS'],'reference_period':'2026-09-29','data_ref':f'DELIVERY_EVIDENCE_R8.json#/cases/{scenario}/independent_oracle/gtfs/rows',
              'transformation':'selected raw GTFS row field','assumptions':['Static scheduled GTFS; timepoint=0'],
              'limitations':['Not realtime; selected within bounded direct-search scenario'],'verification_method':'exact raw CSV row match','dag_node_id':f'{scenario}:selected_pair'})
    delta=evidence['directly_contrasted_claim'];claims.append({'claim_id':delta['claim_id'],'scenario_id':'MAIN_vs_VARIATION_TIME',
      'entity':'Zegama canonical comparison','metric':'comparison_delta_s','value':delta['signed_delta_s'],'unit':'second','classification':'derived_exact',
      'source_refs':['GTFS','OSM','HEALTH_REGISTRY','MODEL','USER','MODEL_DEFAULTS'],'reference_period':'2026-09-29',
      'data_ref':'DELIVERY_EVIDENCE_R8.json#/directly_contrasted_claim','transformation':'VARIATION_TIME.total_s - MAIN.total_s',
      'assumptions':delta['model_assumptions'],'limitations':['Scenario delta, not causality or guaranteed real travel saving'],
      'verification_method':'two independent raw-data reconstructions then subtraction','dag_node_id':'COMPARE:delta_s'})
    artifact={'ledger_version':'r8.0','claims':claims};dump(DOC/'CLAIM_LEDGER_R8.json',artifact);return artifact


def build_dag(claims):
    nodes=[];edges=[]
    def node(node_id,kind,label):
        if not any(x['id']==node_id for x in nodes):nodes.append({'id':node_id,'kind':kind,'label':label})
    def edge(source,target,operation):edges.append({'from':source,'to':target,'operation':operation})
    for sid,label in [('src:GTFS','Static scheduled GTFS'),('src:OSM','OSM path geometry'),('src:HEALTH','Official health-centre anchor'),
      ('model:walking','50 m/min +120 s walking model'),('model:defaults','Provider defaults')]:node(sid,'source_or_model',label)
    for scenario in ('MAIN','VARIATION_TIME','VARIATION_DURATION'):
        for name in ('origin','date','appointment_time','duration_minutes'):node(f'{scenario}:input:{name}','human_input',name)
        node(f'{scenario}:selected_pair','derived', 'Selected outbound/return GTFS pair')
        for src in ('src:GTFS',f'{scenario}:input:origin',f'{scenario}:input:date',f'{scenario}:input:appointment_time',f'{scenario}:input:duration_minutes','model:defaults'):
            edge(src,f'{scenario}:selected_pair','SELECTS')
        for direction in ('out','return'):
            wid=f'{scenario}:walk_{direction}_s';node(wid,'modelled','Walking seconds')
            for src in ('src:OSM','src:HEALTH','model:walking'):edge(src,wid,'USES')
        node(f'{scenario}:initial_wait_s','modelled','Initial boarding margin')
        edge('model:defaults',f'{scenario}:initial_wait_s','DERIVES')
        for metric,label in [('bus_out_s','Outbound vehicle seconds'),('preappointment_wait_s','Wait before appointment'),
          ('appointment_s','Hypothetical appointment duration'),('return_wait_s','Wait after return walk including boarding margin'),
          ('bus_return_s','Return vehicle seconds'),('return_slack_s','Return wait minus boarding margin'),
          ('total_s','Whole journey total'),('walk_out_s','Outbound walking seconds'),('walk_return_s','Return walking seconds')]:node(f'{scenario}:{metric}','derived',label)
        edge('src:GTFS',f'{scenario}:bus_out_s','SUBTRACTS');edge('src:GTFS',f'{scenario}:bus_return_s','SUBTRACTS')
        edge(f'{scenario}:walk_out_s',f'{scenario}:preappointment_wait_s','SUBTRACTS');edge('src:GTFS',f'{scenario}:preappointment_wait_s','SUBTRACTS');edge(f'{scenario}:input:appointment_time',f'{scenario}:preappointment_wait_s','BOUNDS')
        edge(f'{scenario}:input:duration_minutes',f'{scenario}:appointment_s','DERIVES')
        edge(f'{scenario}:walk_return_s',f'{scenario}:return_wait_s','SUBTRACTS');edge('src:GTFS',f'{scenario}:return_wait_s','SUBTRACTS');edge(f'{scenario}:input:appointment_time',f'{scenario}:return_wait_s','SUBTRACTS');edge(f'{scenario}:input:duration_minutes',f'{scenario}:return_wait_s','SUBTRACTS')
        edge(f'{scenario}:return_wait_s',f'{scenario}:return_slack_s','SUBTRACTS');edge('model:defaults',f'{scenario}:return_slack_s','SUBTRACTS')
        edge(f'{scenario}:walk_out_s',f'{scenario}:walk_out_s','DERIVES') if False else None
        edge(f'{scenario}:walk_out_s',f'{scenario}:total_s','ADDS');edge(f'{scenario}:walk_return_s',f'{scenario}:total_s','ADDS')
        edge(f'{scenario}:initial_wait_s',f'{scenario}:total_s','ADDS')
        for metric in ('bus_out_s','preappointment_wait_s','appointment_s','return_wait_s','bus_return_s'):edge(f'{scenario}:{metric}',f'{scenario}:total_s','ADDS')
    node('COMPARE:delta_s','derived','VARIATION_TIME total minus MAIN total');edge('MAIN:total_s','COMPARE:delta_s','SUBTRACTS');edge('VARIATION_TIME:total_s','COMPARE:delta_s','SUBTRACTS')
    artifact={'dag_version':'r8.0','runtime_finding':'W1-R7-F01','runtime_status':'RUNTIME_FINDING_RETAINED',
      'resolution':'EXPLANATORY_DAG_RESOLVED_EXTERNALLY','nodes':nodes,'edges':edges,
      'formulae':{'initial_wait':'boarding_margin_s','pre_appointment_wait':'appointment_time - outbound_arrival - walk_out_s',
        'return_wait':'return_departure - appointment_time - appointment_s - walk_return_s',
        'return_slack':'return_wait_s - boarding_margin_s','total':'sum of eight contiguous components'},
      'note':'return_wait includes the boarding-margin interval; return_slack removes it. DERIVED is not a source node.'}
    dump(DOC/'DERIVATION_DAG_R8.json',artifact)
    (DOC/'DERIVATION_DAG_R8.md').write_text('# DAG de derivación R8\n\nEl DAG externo elimina `DERIVED` como fuente mágica. Las hojas son inputs humanos, GTFS, OSM, anchor sanitario y parámetros del modelo.\n\n- `initial_wait = boarding_margin_s`.\n- `pre_appointment_wait = appointment - llegada de ida - paseo de ida`.\n- `return_wait = salida de vuelta - appointment - duración - paseo de vuelta`.\n- `return_slack = return_wait - boarding_margin`. No son la misma magnitud.\n- `total = suma de ocho componentes contiguos`.\n\nW1-R7-F01 queda `RUNTIME_FINDING_RETAINED / EXPLANATORY_DAG_RESOLVED_EXTERNALLY`; no se afirma que el runtime haya cambiado.\n',encoding='utf-8')
    return artifact


def build_source_ledger(evidence):
    health,_=p.r5._load();sources=[]
    titles={'GTFS':'GTFS Lurraldebus Goierrialdea','HEALTH_REGISTRY':'Centros de salud públicos en Euskadi',
      'HEALTH_PAGE':'Ambulatorio de Beasain','PADI_2026':'Consultas PADI Gipuzkoa 2026','OSM':'OpenStreetMap bounded network extract','MODEL':'Walking model parameters'}
    locals={'GTFS':'datos_originales/movilidad/goierrialdea-3276fcae.zip',
      'HEALTH_REGISTRY':'prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-health-r5-20260929.json',
      'HEALTH_PAGE':'datos_originales/movilidad/r5/beasain-official.html','PADI_2026':'datos_originales/movilidad/r5/padi-2026.pdf',
      'OSM':'datos_originales/movilidad/beasain-network-r4-public.osm','MODEL':'prototypes/ir_y_volver/walking_r5.py'}
    for source in health['sources']:
        osm=source['source_id']=='OSM';external=source['source_id'] not in ('MODEL',)
        sources.append({'source_id':source['source_id'],'institution':source['publisher'],'title':titles[source['source_id']],
          'url':source['url'],'reference_period':source['reference_period'],'acquisition_date':source['retrieved_date'],
          'content_sha256':source['source_sha256'],'local_prepared_artifact':locals[source['source_id']],
          'transformation':source['transformation'],'role':source['source_role'],
          'license_terms_status':'ODbL_1.0_DOCUMENTED' if osm else ('NOT_APPLICABLE_INTERNAL_MODEL' if not external else 'NOT_VERIFIED'),
          'redistribution_status':'ATTRIBUTION_AND_ODBL_APPLY' if osm else ('INTERNAL_CODE' if not external else 'REVIEW_SPECIFIC_TERMS_BEFORE_ADDITIONAL_REDISTRIBUTION'),
          'known_limitations':['Official source does not by itself establish a specific redistribution license'] if external and not osm else (['Model, not observed behaviour'] if not external else ['Modelled network; no verified physical entrance'])})
    canonical={k:v['request'] for k,v in evidence['cases'].items() if isinstance(v,dict) and 'request' in v}
    sources += [{'source_id':'MODEL_DEFAULTS','institution':'GIPUZKOA360','title':'R6 normalized defaults','url':None,'reference_period':'0.3.1',
      'acquisition_date':None,'content_sha256':value_hash({'arrival_margin_minutes':10,'boarding_margin_minutes':3,'walking_profile_id':p.r5.PROFILE,'snapshot_id':p.ID,'return_deadline':None,'timezone':'Europe/Madrid'}),
      'local_prepared_artifact':'prototypes/ir_y_volver/provider_r6.py','transformation':'Applied only when caller omits the field','role':'model_parameter',
      'license_terms_status':'NOT_APPLICABLE_INTERNAL_MODEL','redistribution_status':'INTERNAL_CODE','known_limitations':['Defaults are not observed human choices']},
      {'source_id':'HUMAN_REQUEST','institution':'Caller','title':'Canonical hypothetical requests R8','url':None,'reference_period':'2026-09-29 scenarios',
      'acquisition_date':None,'content_sha256':value_hash(canonical),'local_prepared_artifact':'docs/vnext/w1/DELIVERY_EVIDENCE_R8.json',
      'transformation':'Explicit request fields only','role':'human_input','license_terms_status':'NOT_APPLICABLE_INPUT',
      'redistribution_status':'EVIDENCE_FIXTURE_ONLY','known_limitations':['Hypothetical request, not medical appointment data']}]
    assert len({x['source_id'] for x in sources})==len(sources)
    artifact={'ledger_version':'r8.0','license_note':'Official source does not automatically imply a verified redistribution license.',
      'sources':sources};dump(DOC/'SOURCE_LEDGER_R8.json',artifact);return artifact


def build_answerability():
    rows=[]
    def add(cap,status,inputs,source,reason,allowed,forbidden,next_action):rows.append({'capability':cap,'status':status,'required_inputs':inputs,'source':source,'reason':reason,'allowed_wording':allowed,'forbidden_interpretation':forbidden,'safe_next_action':next_action})
    add('trip_supported_origin_date','AVAILABLE_DIRECT',['origin_id','date','appointment_time','duration_minutes'],'GTFS+catalog','Within fixed GO01/date/catalog scope','Hay una combinación programada viable…','Garantía de viaje o puntualidad','Show schedule/model limitations')
    add('change_appointment_time','DERIVABLE_EXACT',['supported request with new time'],'GTFS+model','Provider recomputes pair','Al cambiar la hora, el escenario recalculado…','Causal or guaranteed saving','Compare same-origin scenarios')
    add('change_duration','DERIVABLE_EXACT',['supported request with duration'],'GTFS+human input','Return selection is recomputed','Con esta duración hipotética…','Official appointment duration','State duration is user input')
    add('change_margins','DERIVABLE_EXACT',['arrival/boarding margin'],'model defaults or human input','Margins enter deterministic constraints','Con este margen solicitado…','Observed passenger behaviour','Expose margin and provenance')
    add('walking_to_centre_anchor','ESTIMABLE_WITH_ASSUMPTIONS',['supported stop/anchor'],'OSM+health anchor+MODEL','Fixed walking model','Paseo modelado hasta el punto oficial…','Verified door or accessibility','State entrance not verified')
    add('scheduled_bus_times','AVAILABLE_DIRECT',['supported trip/date'],'GTFS','Raw scheduled rows','Horario programado…','Realtime or observed punctuality','Check operator realtime externally')
    add('return_slack','DERIVABLE_EXACT',['return wait','boarding margin'],'GTFS+model+inputs','return_wait minus boarding margin','Holgura modelada de regreso…','Return wait itself','Show both quantities')
    add('same_origin_comparison','DERIVABLE_EXACT',['2-32 same-scope requests'],'provider 0.3.1','Formal delta defined','La diferencia entre estos escenarios…','Causality or guaranteed saving','Preserve held constants')
    add('cross_origin_side_by_side','AVAILABLE_DIRECT',['same remaining parameters'],'individual results','Individual scenarios available','Resultados lado a lado…','Formal comparable delta','Avoid ranking/inference')
    add('cross_origin_formal_delta','UNAVAILABLE',['formal metric definition'],'none','Provider declares not comparable','No se ofrece delta formal entre orígenes','Subtract totals as supported comparison','Show side-by-side only')
    for cap,reason,next_action in [('other_date','Snapshot date not validated','Use unknown; obtain validated snapshot'),('other_destination','Outside destination catalog','Use unsupported; obtain scoped evidence'),('home_to_stop','Origin begins at stop presence','Request separate access evidence'),('door_to_door','Physical entrance not verified','Human/field verification'),('transfers','Direct GO01 only','Use a multimodal planner'),('other_operators','Only fixed Goierrialdea feed','Acquire and validate operators'),('realtime','Static schedule only','Consult authoritative realtime'),('delays','No observed operations','Consult realtime/operator'),('appointment_availability','No appointment system data','Consult Osakidetza'),('centre_assignment','No patient assignment data','Consult Osakidetza'),('health_capacity','No capacity data','Obtain official capacity dataset'),('quality_of_care','No quality evidence','Use appropriate official indicators'),('verified_physical_entrance','Anchor is not verified entrance','Human/field verification'),('universal_accessibility','Network model is not accessibility audit','Obtain accessibility audit'),('individual_elderly_walking_behaviour','Generic walking assumption only','Do not individualize; collect consented assessment')]:
        status='OUT_OF_SCOPE' if cap in ('appointment_availability','centre_assignment','health_capacity','quality_of_care','individual_elderly_walking_behaviour') else 'UNAVAILABLE'
        add(cap,status,[], 'none',reason,'No disponible en este alcance',f'Claim {cap} as known',next_action)
    artifact={'matrix_version':'r8.0','allowed_statuses':['AVAILABLE_DIRECT','DERIVABLE_EXACT','ESTIMABLE_WITH_ASSUMPTIONS','UNAVAILABLE','OUT_OF_SCOPE'],'capabilities':rows}
    dump(DOC/'MOBILITY_ANSWERABILITY_R8.json',artifact);return artifact


def build_status_semantics(evidence):
    fixtures={'ok':evidence['cases']['MAIN']['request'],'no_feasible_journey':{**evidence['cases']['MAIN']['request'],'appointment_time':'22:00'},
      'unknown':evidence['cases']['LIMIT_DATE']['request'],'unsupported':evidence['cases']['LIMIT_SCOPE']['request'],
      'error':{**evidence['cases']['MAIN']['request'],'duration_minutes':'20'}}
    meanings={
      'ok':('A valid itinerary exists within the fixed snapshot and constraints.','Selected scheduled/modelled result is known.','Real operation, punctuality, entrance and appointment availability are not known.','Se encontró un itinerario programado/modelado en este alcance.','Guaranteed real journey.','Show sources, date and limitations.'),
      'no_feasible_journey':('No pair meets all modeled constraints in the searched snapshot.','Search completed within catalog/stops/constraints.','It does not prove that transport does not exist.','No se encontró una pareja viable dentro del snapshot, paradas y restricciones modeladas.','No existe transporte.','Change supported inputs or consult a broader planner.'),
      'unknown':('The provider lacks validated evidence for the request, notably another date.','Requested value is outside validated evidence.','It does not prove no buses run.','La fecha no está validada por este snapshot.','No hay autobuses ese día.','Obtain a validated snapshot; never substitute 2026-09-29 silently.'),
      'unsupported':('The request is outside declared catalog/capability.','The provider recognizes the request but cannot model it.','It is not an infrastructure failure.','La petición queda fuera del alcance disponible.','El sistema está caído.','Use catalog IDs or obtain new scoped evidence.'),
      'error':('The request structure/value is invalid.','Validation failed before a journey claim.','It is not an HTTP/network timeout.','La petición no tiene un formato o valor válido.','Fallo de red o ausencia de servicio.','Correct the input and retry.')}
    rows=[]
    for status,request in fixtures.items():
        result=p.plan_visit(request);assert result['status']==status
        technical,known,unknown,allowed,forbidden,recovery=meanings[status]
        rows.append({'status':status,'technical_meaning':technical,'what_is_known':known,'what_is_not_known':unknown,
          'allowed_user_facing_meaning':allowed,'forbidden_inference':forbidden,'safe_recovery':recovery,
          'fixture_request':request,'fixture_result':{'status':result['status'],'error':result['error']}})
    artifact={'semantics_version':'r8.0','statuses':rows,'relative_date_policy':{
      'natural_language_owner':'W2 agent, before calling W1','examples':['hoy','mañana','este viernes'],
      'rule':'Resolve to a real date. If it is not 2026-09-29, pass it unchanged; never silently substitute the validated date.',
      'expected_w1_status_for_other_date':'unknown'}}
    dump(DOC/'STATUS_SEMANTICS_R8.json',artifact);return artifact


def build_timeline(evidence):
    labels=json.loads((DATA/'consumer_labels_r7.json').read_bytes());stop={x['stop_id']:x['name'] for x in labels['stops']}
    timelines=[]
    for cid in ('MAIN','VARIATION_TIME','VARIATION_DURATION'):
        result=evidence['cases'][cid]['provider_result'];it=result['itinerary'];q=result['normalized_request'];parts={x['kind']:x for x in result['components']}
        events=[('presence_required',it['start_s'],stop[it['outbound']['from_stop_id']]),('outbound_departure',p.r4._clock_seconds(it['outbound']['departure_time']),stop[it['outbound']['from_stop_id']]),
          ('outbound_arrival',p.r4._clock_seconds(it['outbound']['arrival_time']),stop[it['outbound']['to_stop_id']]),('anchor_arrival',parts['destination_walk_outbound']['end_s'],labels['destination']['name']),
          ('appointment_start',p.r4._clock_seconds(q['appointment_time']),labels['destination']['name']),('appointment_end',parts['appointment']['end_s'],labels['destination']['name']),
          ('return_stop_arrival',parts['destination_walk_return']['end_s'],stop[it['return']['from_stop_id']]),('return_departure',p.r4._clock_seconds(it['return']['departure_time']),stop[it['return']['from_stop_id']]),
          ('origin_arrival',p.r4._clock_seconds(it['return']['arrival_time']),stop[it['return']['to_stop_id']])]
        timelines.append({'scenario_id':cid,'events':[{'event':name,'seconds_since_midnight':seconds,'time':f'{seconds//3600:02d}:{seconds%3600//60:02d}:{seconds%60:02d}','label':label} for name,seconds,label in events],
          'walking':{'outbound':result['walking']['outbound']['seconds'],'return':result['walking']['return']['seconds'],'classification':'modelled'},
          'limitations':result['limitations']})
    artifact={'timeline_version':'r8.0','timelines':timelines};dump(DOC/'TIMELINE_EVIDENCE_R8.json',artifact)
    lines=['# Timelines canónicos R8','']
    for timeline in timelines:
        lines += [f"## {timeline['scenario_id']}",'']+[f"- {x['time']} — {x['event']}: {x['label']}" for x in timeline['events']]+['']
    lines += ['Paseos modelados; horarios programados; consulta hipotética; entrada física no verificada.']
    (DOC/'TIMELINE_EVIDENCE_R8.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');return artifact


def build_raw_contrast(evidence):
    claim=evidence['directly_contrasted_claim'];rows=[]
    for side in ('left','right'):
        for row in claim['raw_rows'][side]:rows.append({'side':side,'trip_id':row['trip_id'],'stop_id':row['stop_id'],'arrival_time':row['arrival_time'],'departure_time':row['departure_time'],'csv_line':row['csv_line']})
    artifact={'claim_id':claim['claim_id'],'raw_gtfs_rows':rows,'walking_evidence':claim['walking_evidence'],
      'appointment_inputs':{'left':claim['left_request'],'right':claim['right_request']},
      'calculation':f"{claim['right_total_s']} - {claim['left_total_s']} = {claim['signed_delta_s']} s",
      'final_result':{'signed_delta_s':claim['signed_delta_s'],'absolute_delta_s':claim['absolute_delta_s']},'status':'PASS'}
    dump(DOC/'RAW_DATA_CONTRAST_R8.json',artifact);return artifact


def build_cost_guidance():
    perf=json.loads((DOC/'PERFORMANCE_R7.json').read_bytes())
    artifact={'guidance_version':'r8.0','source':'docs/vnext/w1/PERFORMANCE_R7.json','source_sha256':sha(DOC/'PERFORMANCE_R7.json'),
      'evidence':perf['measurements'],'interpretation':['Two scenarios are the natural comparison case.','Eight or more scenarios materially increase local cost and payload.','Contract permits at most 32; W2 chooses exposed limits based on UX/context.','Never silently truncate requests.','These are not portal latency, SLA, RSS or network throughput.']}
    dump(DOC/'CONSUMER_COST_GUIDANCE_R8.json',artifact);return artifact


def build_manifest():
    OUT.mkdir(parents=True,exist_ok=True)
    paths=[DOC/'CURRENT.json',DOC/'RUNTIME_MANIFEST_R6.json',DATA/'operational_catalog_r6.json',DATA/'consumer_labels_r7.json',
      DOC/'CONSUMER_CONFORMANCE_R7.json',DOC/'CONSUMER_CHECKLIST_R7.json',DOC/'DELIVERY_EVIDENCE_R8.json',DOC/'CLAIM_LEDGER_R8.json',
      DOC/'DERIVATION_DAG_R8.json',DOC/'SOURCE_LEDGER_R8.json',DOC/'MOBILITY_ANSWERABILITY_R8.json',DOC/'STATUS_SEMANTICS_R8.json',
      DOC/'TIMELINE_EVIDENCE_R8.json',DOC/'RAW_DATA_CONTRAST_R8.json',DOC/'CONSUMER_COST_GUIDANCE_R8.json']
    roles=['pin','runtime_manifest','catalog','labels','conformance','consumer_checklist','canonical_evidence','claim_ledger','derivation_dag','source_ledger','answerability','status_semantics','timeline','raw_contrast','cost_guidance']
    artifact={'manifest_version':'r8.0','runtime_inclusion':False,'runtime_package_sha256':PACKAGE_SHA,
      'files':[{'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size,'role':role} for path,role in zip(paths,roles)]}
    dump(OUT/'INTEGRATION_MANIFEST_R8.json',artifact)
    (OUT/'README.md').write_text('# Integration evidence R8\n\nEste directorio no duplica el runtime. `INTEGRATION_MANIFEST_R8.json` referencia los artefactos canónicos, sus roles, bytes y SHA-256.\n',encoding='utf-8')
    return artifact


def run():
    evidence=build_cases();claims=build_claims(evidence);dag=build_dag(claims);sources=build_source_ledger(evidence)
    answerability=build_answerability();statuses=build_status_semantics(evidence);timeline=build_timeline(evidence)
    raw=build_raw_contrast(evidence);cost=build_cost_guidance();manifest=build_manifest()
    print(json.dumps({'cases':len(evidence['cases']),'claims':len(claims['claims']),'dag_nodes':len(dag['nodes']),
      'sources':len(sources['sources']),'answerability':len(answerability['capabilities']),'statuses':len(statuses['statuses']),
      'timelines':len(timeline['timelines']),'manifest_files':len(manifest['files'])}))
    return evidence


if __name__=='__main__':run()
