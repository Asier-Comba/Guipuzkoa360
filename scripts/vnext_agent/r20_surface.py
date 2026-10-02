"""Public adapter appended after the immutable R19 engine and projection.

No producer/dataset/formula modifications; no global call history. This module
translates closed public actions to their existing deterministic engine calls.
"""
_R20_CATEGORY = ['primary_care', 'hospital', 'mental_health', 'other_health']
_R20_SURFACE = {
    'analizar_acceso_general': ('analizar_acceso_servicios', ['categoria_servicio','umbral_km']),
    'analizar_acceso_municipios': ('analizar_acceso_servicios', ['categoria_servicio','umbral_km','municipios']),
    'simular_anadir_servicio': ('simular_escenario', ['categoria_servicio','latitud','longitud','umbral_km']),
    'simular_retirar_servicio': ('simular_escenario', ['categoria_servicio','service_id','umbral_km']),
    'simular_cambiar_umbral': ('simular_escenario', ['categoria_servicio','umbral_actual_km','nuevo_umbral_km']),
}
_R20_DESCRIPTIONS = {
    'analizar_acceso_general': 'Distancia geométrica y clasificación de los 88 puntos municipales, sin selección de municipios. No es población cubierta ni tiempo de viaje.',
    'analizar_acceso_municipios': 'Distancia geométrica y clasificación de municipios concretos; lista obligatoria, resoluble, distinta y no vacía. Incluye identidad observada del registro más próximo.',
    'simular_anadir_servicio': 'Añadir un punto hipotético indicado en coordenadas WGS84; comparación condicional, no predicción ni recomendación.',
    'simular_retirar_servicio': 'Retirar hipotéticamente un registro de identidad observada en un resultado de acceso, nunca inventada; no modifica datos reales.',
    'simular_cambiar_umbral': 'Cambiar exclusivamente el umbral entre dos valores explícitos. No cambia registros ni distancias; no mide población cubierta.',
}

def _r20_field(name):
    kind = 'string_array' if name=='municipios' else 'string' if name in {'categoria_servicio','service_id'} else 'number'
    field = {'name':name,'type':kind,'required':True,'allowed_values':_R20_CATEGORY if name=='categoria_servicio' else []}
    if name=='municipios': field.update(min_items=1,max_items=88,unique_resolved_entities=True,nullable=False)
    if 'umbral' in name: field.update(exclusive_minimum=0,maximum=100,unit='km',finite=True)
    if name in {'latitud','longitud'}: field.update(minimum=-90 if name=='latitud' else -180,maximum=90 if name=='latitud' else 180,finite=True,crs='EPSG:4326')
    if name=='service_id': field.update(min_length=1,decision='registered_identity_from_observed_access_result')
    return field

def _r20_capabilities(view):
    original = view['capabilities']; templates={c['id']:c for c in original};public=[]
    for cap in original:
        if cap['id'] in {'analizar_acceso_servicios','simular_escenario'}:
            for name,(engine,fields) in _R20_SURFACE.items():
                if engine!=cap['id']:continue
                item={**cap,'id':name,'description':_R20_DESCRIPTIONS[name], 'input_fields':[_r20_field(f) for f in fields]}
                item['public_engine_mapping']={'operation':engine,'scope':'internal_only'}
                public.append(item)
        else:
            item={**cap,'input_fields':[dict(f) for f in cap['input_fields']]}
            if item['id']=='comparar_municipios':
                for f in item['input_fields']:
                    if f['name']=='municipios':f.update(min_items=2,max_items=20,unique_resolved_entities=True,nullable=False)
                item['description']='Comparación demográfica pura entre 2–20 municipios distintos; distancias mediante acceso municipal, cruce mediante coincidencia.'
            public.append(item)
    view['capabilities']=public
    view['public_tool_count']=len(public)
    assert len(public)==12 and len({c['id'] for c in public})==12
    # Remove stale public routing hints, without rewriting source identifiers.
    def labels(value):
        if type(value) is dict:return {k:labels(v) for k,v in value.items()}
        if type(value) is list:return [labels(v) for v in value]
        if type(value) is str:return value.replace('analizar_acceso_servicios','analizar_acceso_general / analizar_acceso_municipios').replace('simular_escenario','simular_anadir_servicio / simular_retirar_servicio / simular_cambiar_umbral')
        return value
    # Engine mapping remains precise, not falsely claimed as public tools.
    for item in public:
        for key in ('description','semantic_limits','pure_demographic_semantics'):
            if key in item:item[key]=labels(item[key])
    return view

def _r20_error_view(name, request_id, code, fields, *, message=None, allowed=None):
    return {'schema_version':VERSION,'request_id':request_id,'capability_id':name,'status':'error','claims':[],
        'error':{'code':code,'error_class':'invalid_arguments','message':message or 'La petición no cumple la firma pública; no se ejecutó el cálculo.',
        'invalid_fields':sorted(set(fields)),'retry_same_arguments':False,'retry_same_call':False,'allowed_values':allowed or {},
        'required_next_information':sorted(set(fields)),'corrected_call_possible':False,
        'recommended_next_step':'Aclarar los campos indicados sin cambiar intención; no repetir los mismos argumentos.'}}

def _r20_arguments(name, args, root):
    if type(args) is not dict:return None,_r20_error_view(name,'binding','invalid_arguments',[])
    if name in _R20_SURFACE:
        engine,fields=_R20_SURFACE[name]
        invalid=list(set(args)^set(fields))
        for field in fields:
            if field not in args:continue
            value=args[field]
            if field=='categoria_servicio':valid=type(value) is str and value in _R20_CATEGORY
            elif field in {'latitud','longitud'}:
                bound=90 if field=='latitud' else 180
                valid=type(value) in (float,int) and math.isfinite(value) and -bound<=value<=bound
            elif 'umbral' in field:valid=type(value) in (float,int) and math.isfinite(value) and 0<value<=100
            elif field=='service_id':valid=type(value) is str and bool(value.strip())
            else:valid=type(value) is list and 1<=len(value)<=88 and all(type(v) is str and bool(v.strip()) for v in value)
            if not valid:invalid.append(field)
        if invalid:return None,_r20_error_view(name,'binding','invalid_arguments',invalid,allowed={'categoria_servicio':_R20_CATEGORY})
        mapped=dict(args)
        if name=='simular_cambiar_umbral':mapped['umbral_km']=mapped.pop('umbral_actual_km');mapped['accion']='change_threshold'
        elif name=='simular_anadir_servicio':mapped['accion']='add_service';mapped['service_id']=None
        elif name=='simular_retirar_servicio':mapped['accion']='remove_service'
        # General access omits the selector entirely. Selected never coerces []/None.
    else:
        engine=name;mapped=dict(args)
        if name in {'analizar_acceso_servicios','simular_escenario'}:
            return None,_r20_error_view(name,'binding','public_operation_unavailable',[],allowed={'tools':list(_R20_SURFACE)})
    if 'municipios' in mapped:
        values=mapped['municipios'];minimum,maximum=(2,20) if name=='comparar_municipios' else (1,88)
        if type(values) is not list or not minimum<=len(values)<=maximum or not all(type(v) is str and v.strip() for v in values):
            return None,_r20_error_view(name,'binding','invalid_arguments',['municipios'])
        repo=territorial.DataRepository(root/'datos_preparados')
        try:codes=[repo.municipality_lookup(v)['municipality_code'] for v in values]
        except (DataContractError,ValueError):
            return None,_r20_error_view(name,'binding','entity_not_found',['municipios'],allowed={'municipios':[v['municipality_name'] for v in repo.municipalities()]})
        if len(set(codes))!=len(codes):return None,_r20_error_view(name,'binding','duplicate_entities',['municipios'])
    if name=='simular_retirar_servicio':
        services=territorial.DataRepository(root/'datos_preparados').services()
        choices=[s['service_id'] for s in services if s['service_category']==mapped['categoria_servicio']]
        if mapped['service_id'] not in choices:
            return None,_r20_error_view(name,'binding','entity_not_found',['service_id'],message='Identidad inexistente en esa categoría. Observa primero un resultado de acceso; no inventes un código.')
    return (engine,mapped),None

def public_call(name, arguments, request_id, *, root=None):
    """One public call, no retry loop. Error views never expose partial numbers."""
    try:
        root=_workspace_root(root)
        translated,error=_r20_arguments(name,arguments,root)
        if error:
            error['request_id']=request_id
            return canonical(error)
        engine,mapped=translated
        result=execute(engine,mapped,request_id,root=root)
        view=strict_loads(public_result(result,root=root))
        view['capability_id']=name
        view['public_input']={'tool':name,'arguments':arguments} if view['status']=='valid' else {'tool':name}
        if view['status']!='valid':
            err=view.get('error') or {};code=err.get('code','unverified_result')
            observed=code=='observed_transport_failure' and not err.get('invalid_fields')
            err.update(error_class='observed_transport_failure' if observed else 'invalid_arguments' if code in {'invalid_arguments','entity_not_found','service_not_found','municipality_not_found'} else 'contract_or_data_failure',retry_same_arguments=observed,retry_same_call=observed,maximum_identical_retries=1 if observed else 0,required_next_information=err.get('invalid_fields') or err.get('available_options') or None,corrected_call_possible=False)
            if name=='simular_cambiar_umbral':err['invalid_fields']=['umbral_actual_km' if x=='umbral_km' else x for x in err.get('invalid_fields',[])]
            view['error']=err;view['claims']=[]
        elif name=='consultar_capacidades':view=_r20_capabilities(view)
        elif name in {'analizar_acceso_general','analizar_acceso_municipios'}:
            # Identity is a non-numeric observation from the SAME validated raw
            # rows as the distance claims, not a new dataset or inferred value.
            raw=strict_loads(result['raw_result_json'])
            selected={c['entity_id'] for c in view['claims'] if c['entity_type']=='municipality'}
            view['observed_services']=[{'municipality_code':row['municipality_code'],'municipality_name':row['municipality_name'],'service_id':row['nearest_service_id'],'categoria_servicio':mapped['categoria_servicio'],'evidence_path':f'/data/{i}/nearest_service_id','raw_result_sha256':result['raw_result_sha256'],'source_ids':list(dict.fromkeys(s for c in view['claims'] for s in c['source_ids'])),'meaning':'identidad del registro más cercano, no asignación sanitaria'} for i,row in enumerate(raw['data']) if row['municipality_code'] in selected]
        encoded=canonical(view)
        if len(encoded.encode('utf-8'))>MAX_PUBLIC_BYTES:raise ContractViolation('public:payload_too_large')
        return encoded
    except Exception:
        return canonical({'schema_version':VERSION,'request_id':request_id,'capability_id':name,'status':'error','claims':[],
            'error':{'code':'public_adapter_unverified','error_class':'contract_or_data_failure','invalid_fields':[],'retry_same_arguments':False,'retry_same_call':False,'allowed_values':{},'required_next_information':None,'corrected_call_possible':False,'message':'No se ha podido verificar la petición o el resultado. No hay cifras verificadas.'}})
