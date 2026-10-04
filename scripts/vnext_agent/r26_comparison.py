"""Bounded public time comparison using the existing verified provider path."""

_R26_FIELDS = ('origin_id', 'destination_id', 'date', 'appointment_times', 'duration_minutes')
_r26_prior_public_call = public_call


def _r26_comparison(view, arguments):
    scenarios = view['mobility']['scenarios']
    comparisons = view['mobility']['comparisons']
    if len(scenarios) != 2 or len(comparisons) != 1:
        raise ContractViolation('comparison:shape')
    rows = []
    for index, scenario in enumerate(scenarios):
        if scenario['status'] != 'ok' or scenario['scenario_kind'] != 'health_visit':
            raise ContractViolation('comparison:invalid_scenario')
        parameters = scenario['effective_parameters']
        for key in ('origin_id', 'destination_id', 'date', 'duration_minutes'):
            if parameters[key] != arguments[key]:
                raise ContractViolation('comparison:request_identity')
        if parameters['appointment_time'] != arguments['appointment_times'][index] + ':00':
            raise ContractViolation('comparison:time_identity')
        ledger, summary, scope = scenario['duration_ledger'], scenario['time_summary'], scenario['journey_scope']
        total, start, end = ledger['total_seconds'], scope['start']['seconds'], scope['end']['seconds']
        if (any(type(v) is not int for v in (total, start, end))
                or ledger['partition_verified'] is not True
                or ledger['component_sum_seconds'] != total
                or sum(r['seconds'] for r in ledger['components']) != total
                or len(ledger['components']) != 8
                or total != summary['total_s'] or total != end - start
                or start != summary['scope_start_s'] or end != summary['scope_end_s']
                or ledger['total_human'] != _duration_hms(total)
                or ledger['start_clock'] != _civil_clock(start)
                or ledger['end_clock'] != _civil_clock(end)):
            raise ContractViolation('comparison:ledger_mismatch')
        rows.append(dict(appointment_time=arguments['appointment_times'][index],
                         total_seconds=total, total_human=_duration_hms(total),
                         start_seconds=start, end_seconds=end,
                         start_clock=_civil_clock(start), end_clock=_civil_clock(end)))
    a, b = (s['effective_parameters'] for s in scenarios)
    if {k:v for k,v in a.items() if k != 'appointment_time'} != {k:v for k,v in b.items() if k != 'appointment_time'}:
        raise ContractViolation('comparison:other_parameters_changed')
    comparison = comparisons[0]
    left, right = rows
    delta = right['total_seconds'] - left['total_seconds']
    if (comparison['comparability'] != 'comparable'
            or comparison['left_index'] != 0 or comparison['right_index'] != 1
            or type(comparison['total_difference_s']) is not int
            or comparison['total_difference_s'] != delta):
        raise ContractViolation('comparison:provider_delta')
    result = {'left':left, 'right':right, 'comparison_verified':True,
              'direction':'less' if delta < 0 else 'more' if delta > 0 else 'equal',
              'basis':'right_minus_left', 'scope':scenarios[0]['scope']}
    for key, field in [('total','total_seconds'),('start','start_seconds'),('end','end_seconds')]:
        seconds = right[field] - left[field]
        result[key+'_delta_seconds'] = seconds
        result[key+'_delta_human'] = _duration_hms(abs(seconds))
    statement = (f"La cita de {right['appointment_time']} ocupa {result['total_delta_human']} "
                 f"{'menos' if delta < 0 else 'más'} que la de {left['appointment_time']} en estos escenarios programados/modelados."
                 if delta else 'Ambos escenarios tienen la misma duración calculada.')
    for field, label in [('start','El inicio'),('end','El fin')]:
        d = result[field+'_delta_seconds']
        statement += (f" {label} es {result[field+'_delta_human']} {'más tarde' if d > 0 else 'más temprano'}."
                      if d else f' {label} tiene la misma hora en ambos escenarios.')
    result['comparison_sentence'] = statement
    result['comparison_table_markdown'] = '\n'.join([
        '| Cita | Tiempo completo | Inicio | Fin |', '|---|---:|---|---|',
        *[f"| {r['appointment_time']} | {r['total_human']} | {r['start_clock']} | {r['end_clock']} |" for r in rows]])
    result['presentation_rule'] = 'Copia tabla y frase verificadas. No recalcules diferencias, signos, unidades ni desplazamientos. Son escenarios condicionados, no ahorro observado ni recomendación.'
    return result


def _r26_catalog(view):
    comparison = {'mode':'deterministic_time_pair', 'batch_supported':True,
                  'min_items':1, 'max_items':2, 'unique_items':True,
                  'cross_origin_comparison':'side_by_side_only; numeric delta is not supported across origins',
                  'procedure':'One plan_visit call with appointment_times [baseline, new time]; same origin, destination, date and duration. Use verified comparison_ledger, never model arithmetic.'}
    def update(value):
        if isinstance(value, dict):
            if value.get('id') == 'plan_visit':
                value['input_fields'] = [dict(name=k, required=True, type='array' if k=='appointment_times' else 'integer' if k=='duration_minutes' else 'string', **({'items':{'type':'string','pattern':r'^(?:[01]\d|2[0-3]):[0-5]\d$'},'minItems':1,'maxItems':2,'uniqueItems':True} if k=='appointment_times' else {})) for k in _R26_FIELDS]
                value['description'] = 'Una visita o comparación determinista de dos horas de la misma visita; cinco campos obligatorios.'
            for key in ('request_fields','required_fields'):
                if key in value and isinstance(value[key],list) and 'appointment_time' in value[key]:
                    value[key] = ['appointment_times' if k=='appointment_time' else k for k in value[key]]
            if isinstance(value.get('comparison'),dict) and value['comparison'].get('mode')=='individual_calls':
                value['comparison'] = dict(comparison)
            for item in value.values(): update(item)
        elif isinstance(value,list):
            for item in value:update(item)
    update(view)
    return view


def public_call(name, arguments, request_id, *, root=None):
    if name != 'plan_visit':
        rendered = _r26_prior_public_call(name, arguments, request_id, root=root)
        if name != 'consultar_capacidades': return rendered
        view = strict_loads(rendered)
        return canonical(_r26_catalog(view)) if view.get('status')=='valid' else rendered
    invalid = []
    if type(arguments) is not dict or set(arguments) != set(_R26_FIELDS):
        invalid = list(_R26_FIELDS)
    else:
        times = arguments['appointment_times']
        if (type(times) is not list or not 1 <= len(times) <= 2
                or any(type(t) is not str or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',t) for t in times)
                or len(set(times)) != len(times)):
            invalid.append('appointment_times')
    if invalid:
        return canonical(_r20_error_view(name,request_id,'invalid_arguments',invalid,
            allowed={'appointment_times':'Una o dos horas HH:MM distintas, en orden [base, nueva].'}))
    try:
        requests = [{**{k:v for k,v in arguments.items() if k!='appointment_times'},'appointment_time':time} for time in times]
        view = strict_loads(_r26_prior_public_call(name,{'request':requests[0] if len(times)==1 else requests},request_id,root=root))
        if view.get('status') != 'valid': return canonical(view)
        if len(times)==2: view['comparison_ledger'] = _r26_comparison(view, arguments)
        view['public_input'] = {'tool':name,'arguments':arguments}
        encoded = canonical(view)
        if len(encoded.encode('utf-8')) > MAX_PUBLIC_BYTES: raise ContractViolation('comparison:payload_size')
        return encoded
    except Exception:
        error = _r20_error_view(name,request_id,'comparison_unverified',[],message='No se ha podido verificar la visita o la comparación completa. No hay cifras verificadas.')
        error['error']['error_class']='contract_or_data_failure'
        return canonical(error)
