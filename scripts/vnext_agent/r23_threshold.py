"""Verified access classification semantics; original arithmetic is unchanged."""

def _r23_threshold_semantics(view, raw, mapped, root):
    threshold = mapped['umbral_km']
    if type(threshold) not in (int, float) or not math.isfinite(threshold) or not 0 < threshold <= 100:
        raise ContractViolation('threshold:invalid_input')
    if raw['filters']['threshold_km'] != threshold or raw['filters']['service_category'] != mapped['categoria_servicio']:
        raise ContractViolation('threshold:argument_raw_mismatch')
    repo = territorial.DataRepository(root / 'datos_preparados')
    towns = {r['municipality_code']: r for r in repo.municipalities()}
    services = [s for s in repo.services() if s['service_category'] == mapped['categoria_servicio']]
    indexed = {}
    for row in raw['data']:
        code = row['municipality_code']
        if code in indexed:
            raise ContractViolation('threshold:duplicate_row')
        town = towns[code]
        # Use the SAME existing engine function and unrounded distance. Display
        # rounding must never move a point across the inclusive boundary.
        distance, service = nearest_service_projected(town['easting_m'], town['northing_m'], services)
        expected = bool(distance is not None and distance <= threshold * 1000)
        if (type(row['within_threshold']) is not bool or row['within_threshold'] != expected
                or row['nearest_distance_m'] != (round(distance, 1) if distance is not None else None)
                or row['nearest_service_id'] != (service['service_id'] if service else None)):
            raise ContractViolation('threshold:raw_classification_mismatch')
        indexed[code] = row
    for item in view.get('municipal_classifications', []):
        if item['metric_id'] != 'within_threshold' or item['value'] is not indexed[item['entity_id']]['within_threshold']:
            raise ContractViolation('threshold:projection_mismatch')
    if not indexed or not view.get('municipal_classifications'):
        raise ContractViolation('threshold:missing_classification')
    return {**view, 'threshold_semantics': {
        'distance_metric': 'nearest_distance_m', 'operator': '<=',
        'threshold_km': threshold, 'threshold_m': threshold * 1000,
        'zero_distance_included': True, 'missing_distance_within_threshold': False,
        'input_constraint': '0 < umbral_km <= 100; solo limita el parámetro recibido, no la distancia calculada.',
        'meaning': 'Un punto municipal está dentro cuando la distancia observada es menor o igual al umbral.',
        'classification_precision': 'Comparación del motor antes del redondeo de presentación a una décima de metro.'}}


_r22_public_call = public_call

def public_call(name, arguments, request_id, *, root=None):
    rendered = _r22_public_call(name, arguments, request_id, root=root)
    if name not in {'analizar_acceso_general', 'analizar_acceso_municipios'}:
        return rendered
    view = strict_loads(rendered)
    if view.get('status') != 'valid':
        return rendered
    try:
        root = _workspace_root(root)
        translated, error = _r20_arguments(name, arguments, root)
        if error: raise ContractViolation('threshold:argument_binding')
        engine, mapped = translated
        # Reobserve the existing deterministic raw engine, never another model
        # tool call. Digest equality binds semantics to the already shown raw.
        result = execute(engine, mapped, request_id, root=root)
        observed = view.get('observed_services', [])
        if (result['status'] != 'valid' or not observed
                or any(s['raw_result_sha256'] != result['raw_result_sha256'] for s in observed)):
            raise ContractViolation('threshold:raw_identity')
        projected = _r23_threshold_semantics(view, strict_loads(result['raw_result_json']), mapped, root)
        encoded = canonical(projected)
        if len(encoded.encode('utf-8')) > MAX_PUBLIC_BYTES:
            raise ContractViolation('threshold:payload_too_large')
        return encoded
    except Exception:
        error = _r20_error_view(name, request_id, 'threshold_semantics_failure', [],
                               message='No se ha podido verificar el umbral y la clasificación; no se proporcionan cifras.')
        error['error']['error_class'] = 'contract_or_data_failure'
        return canonical(error)
