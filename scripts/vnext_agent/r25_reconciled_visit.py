"""Public duration ledger from verified, disjoint provider intervals only."""

_R25_COMPONENTS = (
    ('initial_wait_s', 'Espera inicial en la parada'),
    ('outbound_vehicle_s', 'Autobús de ida'),
    ('destination_walk_outbound_s', 'Paseo modelado de ida'),
    ('pre_appointment_wait_s', 'Espera en destino antes de la cita'),
    ('appointment_s', 'Consulta'),
    ('destination_walk_return_s', 'Paseo modelado de regreso'),
    ('return_wait_s', 'Espera del autobús de regreso'),
    ('return_vehicle_s', 'Autobús de regreso'),
)


def _r25_duration_ledger(raw, projected):
    summary = _time_summary(raw)
    values, intervals = raw['components_s'], raw['components']
    keys = [key for key, _ in _R25_COMPONENTS]
    if (set(values) != set(keys) or len(intervals) != len(keys)
            or projected['components_s'] != values
            or projected['time_summary'] != summary):
        raise ContractViolation('duration_ledger:inconsistent_projection')
    rows, cursor = [], summary['scope_start_s']
    for (key, label), interval in zip(_R25_COMPONENTS, intervals, strict=True):
        seconds = values[key]
        if (type(seconds) is not int or seconds < 0
                or interval['kind'] != key.removesuffix('_s')
                or type(interval['start_s']) is not int
                or type(interval['end_s']) is not int
                or type(interval['seconds']) is not int
                or interval['start_s'] != cursor
                or interval['end_s'] - cursor != seconds
                or interval['seconds'] != seconds):
            raise ContractViolation('duration_ledger:non_partition')
        rows.append({
            'component_id': key, 'label': label, 'seconds': seconds,
            'human': _duration_hms(seconds),
            'start_clock': _civil_clock(cursor),
            'end_clock': _civil_clock(interval['end_s']),
            'evidence_path': '/components_s/' + key,
        })
        cursor = interval['end_s']
    total = sum(row['seconds'] for row in rows)
    if cursor != summary['scope_end_s'] or total != summary['total_s']:
        raise ContractViolation('duration_ledger:unreconciled_total')
    # Margins constrain feasibility and are already contained in waits. They
    # must never be appended as independent durations to this partition.
    relation = ('Los ocho componentes son consecutivos y no se solapan. '
                'Los márgenes exigidos ya están incluidos en las esperas; '
                'no se suman otra vez. El margen de regreso no es otro trayecto.')
    lines = ['| Componente | Duración |', '|---|---:|']
    lines.extend(f"| {row['label']} | {row['human']} |" for row in rows)
    lines.append(f"| **Total** | **{_duration_hms(total)}** |")
    return {
        'total_seconds': total, 'total_human': _duration_hms(total),
        'start_clock': summary['scope_start_clock'],
        'end_clock': summary['scope_end_clock'],
        'components': rows, 'component_sum_seconds': total,
        'partition_verified': True, 'margin_relationship': relation,
        'answer_table_markdown': '\n'.join(lines),
        'presentation_rule': 'Reproduce la tabla completa sin agrupar, omitir ni recalcular filas. Total es resumen, no otro sumando. Conserva el alcance, fuentes, supuestos y límites del escenario.',
    }


_r24_mobility_view = _mobility_view


def _mobility_view(raw, root, arguments):
    view = _r24_mobility_view(raw, root, arguments)
    results = raw['results'] if 'results' in raw else [raw]
    for result, projected in zip(results, view['scenarios'], strict=True):
        if result['status'] == 'ok' and result['scenario_kind'] == 'health_visit':
            projected['duration_ledger'] = _r25_duration_ledger(result, projected)
    return view
