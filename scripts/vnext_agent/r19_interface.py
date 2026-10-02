"""R19 model boundary: no raw handler, formula, asset or provider changes."""

_R19_REMOVED = {
    'consultar_capacidades': {'pregunta_o_dimension'},
    'obtener_resumen_territorial': {'periodo'},
    'analizar_envejecimiento': {'periodo'},
    'analizar_acceso_servicios': {'periodo'},
    'analizar_coincidencia': {'periodo'},
    'simular_escenario': {'periodo'},
    'comparar_municipios': {'periodo','categoria_servicio','umbral_km'},
}
_R19_ENUMS = {
    'grupo_edad':['65','75'], 'medida':['percentage','count'],
    'categoria_servicio':['primary_care','hospital','mental_health','other_health'],
    'accion':['add_service','remove_service','change_threshold'],
}

def _r19_age(claim, raw, effective):
    metric=claim['metric_id']
    fields=[metric, ((claim.get('numerator') or {}).get('data_ref') or {}).get('field','')]
    for group in ('65','75'):
        if any(field in {'population_'+group+'_plus','pct_'+group+'_plus','rate_per_10000_'+group+'_plus'} for field in fields):
            return group
    if metric in {'value','age_cut_percent'}:
        return raw.get('filters',{}).get('age_group',effective.get('parameters',{}).get('grupo_edad'))
    return None

def _r19_derivation(group,root):
    if group=='75':return _age_group_derivation(root)
    if group!='65':raise ContractViolation('presentation:unknown_age_group')
    source=_catalog(root)['EUSTAT_EMH_2025']
    if source['reference_period']!='2025-01-01' or 'pivote de total/65+' not in source.get('method',''):
        raise ContractViolation('presentation:unverified_age65_metadata')
    return {'source_id':source['source_id'],'institution':source['institution'],
            'reference_period':source['reference_period'],'output_field':'population_65_plus',
            'source_field':'grupo de edad 65+ de la consulta Eustat preparada',
            'method':'Recuento del grupo 65+ de la consulta municipal, sexo total; pivote preparado. Porcentaje = recuento / población total × 100, redondeado a tres decimales.',
            'meaning':'Población de 65 años o más en la referencia indicada.',
            'limitation':'Recuento municipal agregado, no edad exacta ni circunstancias individuales; no se infiere un corte por año de nacimiento.'}

def _r19_catalog(view,root):
    periods=territorial.DataRepository(root/'datos_preparados').available_periods()
    if periods!=['2025-01-01']:raise ContractViolation('presentation:fixed_demography_changed')
    for cap in view.get('capabilities',[]):
        removed=_R19_REMOVED.get(cap['id'],set())
        cap['input_fields']=[field for field in cap.get('input_fields',[]) if field['name'] not in removed]
        cap.pop('period_policy',None)
        for field in cap['input_fields']:
            if field['name'] in _R19_ENUMS:field['allowed_values']=_R19_ENUMS[field['name']]
            if cap['id']=='consultar_fuente' and field['name']=='source_id':
                field['required']=True;field['nullable']=False
                field['allowed_values']=sorted(_catalog(root))
        if cap['id']=='comparar_municipios':
            cap['description']='Comparación demográfica municipal; distancias mediante analizar_acceso_servicios con varios municipios; cruce mediante analizar_coincidencia.'
            cap['semantic_contract']=dict(subject='municipios solicitados',measures='población y proporción municipal del grupo de edad',limits='Solo diferencias entre magnitudes demográficas compatibles; no viaje ni servicio en esta operación.')
        if cap['id']=='consultar_capacidades':cap['description']='Catálogo completo sin argumentos; incluye fuentes y cobertura. No ejecuta análisis.'
        if cap['id'] in _R19_REMOVED and cap['id']!='consultar_capacidades':
            cap['snapshot_policy']='Referencias fijas versionadas; las fechas de fuentes siguen en resultados/procedencia. No hay selección histórica pública.'
    view['sources_catalog']=[{key:source[key] for key in ('source_id','title','institution','reference_period','url') if key in source} for source in _catalog(root).values()]

def _r19_error(view,root):
    view['claims']=[]
    for key in ('mobility','capabilities','mobility_catalog','source_metadata','age_group_derivation','age_group_derivations','municipal_classifications'):
        view.pop(key,None)
    error=view.get('error') or {'code':'unavailable','message':'No hay evidencia válida para esta llamada.'}
    args=(view.get('normalized_input') or {}).get('arguments',{})
    operation=view.get('capability_id')
    if operation=='plan_visit':args=args.get('request',args)
    fields=[];options={};coverage={}
    try:
        cap=next((row for row in _registry(root) if row['id']==operation),None)
        if cap is not None:
            coverage=cap.get('coverage',{})
            names={row['name'] for row in cap['input_fields']}
            # Exception messages name validated fields; this never parses user prose.
            message=error.get('message','')
            fields=[name for name in names|set(args) if name in message.split(':')]
            for row in cap['input_fields']:
                name=row['name']
                values=_R19_ENUMS.get(name,row.get('allowed_values',[]))
                if values and (not fields or name in fields):options[name]=values
            if operation=='consultar_fuente':options['source_id']=sorted(_catalog(root))
            if operation=='plan_visit':
                catalog=_mobility_catalog_view(root)
                if catalog is not None:coverage=catalog
    except Exception:
        # Missing/unverified workspace never manufactures a catalogue.
        pass
    error.update(retry_same_call=False,invalid_fields=sorted(fields),allowed_values=options,
                 coverage=coverage,recommended_next_step='No repetir la misma llamada. Corregir solo con opciones verificadas; si falta una elección o cambiaría la petición, preguntar. Si no hay cobertura, explicar el límite sin cifras.')
    view['error']=error
    return view

def _r19_projection(view,evidence,root):
    view.pop('age_group_derivation',None)
    if view.get('status')!='valid':return _r19_error(view,root)
    raw=strict_loads(evidence['raw_result_json']) if evidence.get('raw_result_json') else {}
    groups=set()
    for claim in view.get('claims',[]):
        claim.setdefault('forbidden_inferences',_SUBJECT_LIMITS)
        group=_r19_age(claim,raw,view.get('effective_request') or {})
        if group is not None:
            if group not in {'65','75'}:raise ContractViolation('presentation:unverified_claim_age')
            if 'EUSTAT_EMH_2025' not in claim['source_ids']:raise ContractViolation('presentation:age_without_demographic_source')
            groups.add(group);claim['age_group']=group
            claim['age_derivation_ref']='/age_group_derivations/'+group
    # A source card may legitimately describe both prepared indicators; a
    # single-age analytical result contains only its own indicator metadata.
    if evidence['capability_id']=='consultar_fuente' and any(row['source_id']=='EUSTAT_EMH_2025' for row in view.get('source_metadata',[])):
        groups.update(('65','75'))
    if groups:view['age_group_derivations']={group:_r19_derivation(group,root) for group in sorted(groups)}
    if evidence['capability_id']=='consultar_capacidades':_r19_catalog(view,root)
    if evidence['capability_id']=='comparar_municipios':
        view['operation_semantics']={'subject':'municipios solicitados','measures':'población y proporción municipal del grupo de edad','interpretation':'comparación demográfica; servicios mediante acceso o composición'}
    if len(canonical(view).encode('utf-8'))>MAX_PUBLIC_BYTES:raise ContractViolation('presentation:r19_payload_too_large')
    return view

def _public_result(evidence,root):
    return canonical(_r19_projection(strict_loads(_r18_public_result(evidence,root)),evidence,root))

_r19_validating_public_result=public_result
def public_result(evidence,root=None):
    # Also strengthen errors generated by the existing validation boundary.
    view=strict_loads(_r19_validating_public_result(evidence,root=root))
    if view.get('status')!='valid':view=_r19_error(view,root)
    return canonical(view)
