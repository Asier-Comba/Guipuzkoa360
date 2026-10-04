"""Typed model-facing semantics only. Original raw evidence stays immutable.

This is not a prompt classifier or an LLM answer validator. It constrains the
evidence presented to the model; conversational adherence needs real evaluation.
"""

_SEMANTIC_OPERATIONS = {
    'obtener_resumen_territorial': ('municipio','población agregada y registros sanitarios; distancias entre puntos','fuentes con sus fechas distintas'),
    'comparar_municipios': ('municipios solicitados','población/proporción municipal y, si se pide, distancia entre puntos','diferencias solo entre magnitudes compatibles'),
    'analizar_envejecimiento': ('municipio','recuento de personas o porcentaje sobre población municipal','orden del indicador, no necesidad individual'),
    'analizar_acceso_servicios': ('punto representativo municipal','distancia euclídea y clasificación municipal por umbral','no distribución de residentes'),
    'analizar_coincidencia': ('municipio','proporción municipal de edad y distancia geométrica al registro','coincidencia descriptiva, no causalidad ni cobertura poblacional'),
    'simular_escenario': ('municipio en escenario hipotético','distancia desde punto municipal antes/después','no predicción de uso, impacto o población beneficiada'),
    'consultar_fuente': ('fuente','procedencia, método, fechas y límites','metadata no demuestra disponibilidad operativa ni verdad'),
    'consultar_capacidades': ('operación','cobertura, campos y límites verificados','catálogo no es resultado de análisis'),
    'plan_visit': ('visita programada/modelada entre paradas','intervalo completo, componentes en segundos y paseo modelado','no domicilio, tiempo real, capacidad, citas ni entrada verificada'),
}
_DISTANCE_FIELDS = {'nearest_distance_m','baseline_distance_m','scenario_distance_m','difference_absolute_m','distance_cut_m','minimum_distance_m','maximum_distance_m'}
_MUNICIPAL_COUNTS = {'within_threshold_count','outside_threshold_count','highlighted_count','affected_rows','improved_distance_rows','worsened_distance_rows','threshold_status_changes'}
_OPERATIONAL_FIELDS = {'total_result_rows','returned_rows','joined_rows','rows_used','total_entities','returned_entities','omitted_entities','rank','index','left_index','right_index','unattributed'}
_JOURNEY_FIELDS = {'initial_wait_s','outbound_vehicle_s','destination_walk_outbound_s','pre_appointment_wait_s','appointment_s','destination_walk_return_s','return_wait_s','return_vehicle_s','total_s','return_slack_s','total_difference_s','total_metres'}
_SUBJECT_LIMITS = ['No hay distribución espacial de residentes: no calcular personas, hogares o porcentaje de población dentro de un radio.', 'Un municipio clasificado por distancia no es una persona con acceso efectivo.', 'Registro no prueba capacidad, disponibilidad, calidad ni atención asignada.', 'Asociación no prueba causalidad; escenario no predice ni recomienda.']

def _semantic_kind(field, raw=None):
    """Closed metric registry, never a heuristic on a user question."""
    if field in _OPERATIONAL_FIELDS:
        return ('operational','filas/entidades procesadas','municipios' if field in {'joined_rows','total_result_rows','returned_rows'} else 'conteo operativo')
    if field in _MUNICIPAL_COUNTS:
        return ('analytical','municipios clasificados','municipios')
    if field in _DISTANCE_FIELDS:
        return ('analytical','punto representativo municipal y registro sanitario','m')
    if field in {'population_total','population_65_plus','population_75_plus'}:
        return ('analytical','población municipal agregada','personas')
    if field in {'pct_65_plus','pct_75_plus','age_cut_percent'}:
        return ('analytical','proporción de población municipal del grupo de edad','%')
    if field=='difference_relative_pct':
        return ('analytical','variación relativa de distancia desde punto municipal','%')
    if field=='registered_service_count' or field in {'services_primary_care','services_hospital','services_mental_health','services_other_health','services_total'}:
        return ('analytical','registros sanitarios, no capacidad asistencial','registros')
    if field in {'rate_per_10000_65_plus','rate_per_10000_75_plus'}:
        return ('analytical','registros por población municipal del grupo de edad','registros/10000 personas')
    if field=='value' and raw is not None:
        unit=str(raw.get('unit',''))
        if unit.startswith('%'): return ('analytical','proporción de población municipal del grupo de edad',unit)
        if unit=='personas': return ('analytical','población municipal agregada',unit)
    if field in _JOURNEY_FIELDS:
        return ('analytical','visita programada/modelada entre paradas','m' if field=='total_metres' else 's')
    raise ContractViolation('presentation:unclassified_metric:'+field)

def _r18_projection(view, evidence, root):
    raw=strict_loads(evidence['raw_result_json']) if evidence.get('raw_result_json') is not None else {}
    view['evidence_policy']={
        'classification':['AVAILABLE','DERIVABLE_EXACTLY','ESTIMABLE_WITH_ASSUMPTIONS','NOT_AVAILABLE'],
        'preserve':['subject','entity','unit','period','source','scope','assumptions'],
        'derivation':'Operaciones transparentes sobre inputs observados compatibles; sin dato espacial de residentes no hay cobertura poblacional.',
        'forbidden_inferences':_SUBJECT_LIMITS,
        'recovery':'Un error aporta cero cifras; no repetir llamada y argumentos fallidos; una única recuperación inequívoca por causa.',
    }
    if view.get('status')!='valid':
        view['claims']=[]
        # No partial analytical payload survives an error.
        for key in ('mobility','capabilities','mobility_catalog','source_metadata'):
            view.pop(key,None)
        return view
    operation=evidence['capability_id']
    what=_SEMANTIC_OPERATIONS.get(operation)
    if what is None: raise ContractViolation('presentation:unknown_semantic_operation')
    view['operation_semantics']={'subject':what[0],'measures':what[1],'interpretation':what[2]}
    analytical=[]; operational=[]
    for claim in view.get('claims',[]):
        kind,subject,unit=_semantic_kind(claim['metric_id'],raw)
        projected=dict(claim)
        # Preserve original validated evidence untouched; fix ONLY public unit.
        projected['unit']=unit
        if kind=='operational':
            operational.append({'metric_id':claim['metric_id'],'value':claim['value'],'unit':unit,'meaning':subject,'evidence_path':claim['evidence_path']})
            continue
        projected['subject']=subject
        projected['numeric_role']='analytical'
        projected['allowed_transformations']='Solo operaciones exactas compatibles; conservar entidad, sujeto, fuentes, fechas y supuestos.'
        if claim['metric_id'] in _DISTANCE_FIELDS or claim['metric_id'] in _MUNICIPAL_COUNTS:
            projected['forbidden_inferences']=_SUBJECT_LIMITS[:2]
        analytical.append(projected)
    view['claims']=analytical
    view['operational_metadata']={'not_analytical_evidence':True,'counters':operational,'selection':view.pop('selection',{}),'execution':view.pop('execution',{})}
    # Requested values and effective defaults are inputs, not observations.
    view['input_semantics']='normalized_input y effective_request contienen parámetros; no cifras analíticas. defaults_applied son supuestos, no elecciones humanas observadas.'
    for cap in view.get('capabilities',[]):
        semantic=_SEMANTIC_OPERATIONS.get(cap['id'])
        if semantic is not None:
            cap['semantic_contract']={'subject':semantic[0],'measures':semantic[1],'limits':semantic[2],'numeric_evidence':'Solo salida válida de ejecución; conservar unidades, entidades, fechas y fuentes.'}
            if cap['id'] in {'obtener_resumen_territorial','comparar_municipios','analizar_acceso_servicios','analizar_coincidencia','simular_escenario'}:
                cap['semantic_contract']['forbidden_inferences']=_SUBJECT_LIMITS
    # Geometry classification is boolean, explicitly bound to the exact raw row.
    selected_ids={c['entity_id'] for c in analytical if c['entity_type']=='municipality'}
    classifications=[]
    for index,row in enumerate(raw.get('data',[])):
        if type(row) is not dict or row.get('municipality_code') not in selected_ids: continue
        for key in ('within_threshold','baseline_within_threshold','scenario_within_threshold'):
            if key in row:
                if type(row[key]) is not bool: raise ContractViolation('presentation:invalid_threshold_classification')
                classifications.append({'entity_id':row['municipality_code'],'entity_label':row['municipality_name'],'metric_id':key,'value':row[key],'subject':'punto representativo municipal','unit':'clasificación booleana municipal','evidence_path':f'/data/{index}/{key}','source_ids':[s['source_id'] for s in raw['sources']],'forbidden_inferences':_SUBJECT_LIMITS[:2]})
    if classifications: view['municipal_classifications']=classifications
    if operation=='plan_visit':
        view['numeric_semantics']={
            'time_summary':'total_s y componentes: segundos; total_hms es su formato verificado. scope_* define todo el intervalo, no la salida del autobús.',
            'itinerary':'Tiempos y segundos programados de vehículo; no observación de viaje real.',
            'walking':'total_metres en metros y seconds en segundos modelados; coordenadas centre_anchor WGS84 son localización, no accesibilidad.',
            'parameters':'duration_minutes y márgenes: minutos como parámetros; velocidad de paseo: supuesto. índices/contadores: operativos.',
            'sources':'Fecha de servicio, validez del horario y fecha de red son referencias distintas; parámetros no son fuentes de observación.',
        }
    rendered=canonical(view)
    if len(rendered.encode('utf-8'))>MAX_PUBLIC_BYTES:
        raise ContractViolation('presentation:semantic_payload_too_large')
    return view

def _public_result(evidence,root):
    view=strict_loads(_r17_public_result(evidence,root))
    return canonical(_r18_projection(view,evidence,root))
