"""Additive threshold presentation over validated complete raw evidence. No core changes."""

_r27_prior_projection = _public_result


def _r27_require(condition, field):
    if not condition:
        raise ContractViolation('threshold_ledger:' + field)


def _r27_threshold_ledger(evidence, root):
    # Called inside the existing validated projection boundary. Revalidate for
    # direct contract consumers too; hashes alone do not establish semantics.
    validate_evidence(evidence, _catalog(root), root=root)
    raw = strict_loads(evidence['raw_result_json'])
    effective = evidence['effective_request']
    args = effective['parameters']
    _r27_require(effective['operation'] == 'simular_escenario' and args['accion'] == 'change_threshold', 'operation')
    _bind_result_to_arguments(raw, effective, root)
    before, after = args['umbral_km'], args['nuevo_umbral_km']
    for value in (before, after):
        _r27_require(type(value) in (int, float) and math.isfinite(value) and 0 < value <= 100, 'threshold')
    repo = territorial.DataRepository(root / 'datos_preparados')
    analysis = territorial.TerritorialAnalysis(repo)
    reference = analysis.acceso(args['categoria_servicio'], before, args['periodo'])
    for key in ('sources', 'period', 'metric', 'unit', 'rows_used'):
        _r27_require(raw[key] == reference[key], 'source_or_reference_' + key)
    municipalities = {r['municipality_code']: r for r in repo.municipalities()}
    services = [r for r in repo.services() if r['service_category'] == args['categoria_servicio']]
    expected = {r['municipality_code']: r for r in reference['data']}
    rows = raw['data']
    codes = [r['municipality_code'] for r in rows]
    _r27_require(len(codes) == len(set(codes)) and set(codes) == set(expected), 'complete_unique_rows')
    for side in ('baseline', 'scenario'):
        _r27_require(raw['scenario'][side]['service_count'] == len(repo.services()), 'unchanged_services')
    counts = dict(outside_to_inside=0, inside_to_outside=0, stays_inside=0, stays_outside=0)
    changed = []
    for index, row in enumerate(rows):
        code = row['municipality_code']
        municipality = municipalities[code]
        # Same existing unrounded primitive; rounded raw display is never authority.
        distance, _ = nearest_service_projected(municipality['easting_m'], municipality['northing_m'], services)
        _r27_require(type(distance) in (int, float) and math.isfinite(distance) and distance >= 0, 'distance_available')
        _r27_require(row['municipality_name'] == municipality['municipality_name'], 'municipality_name')
        _r27_require(row['baseline_distance_m'] == row['scenario_distance_m'] == round(distance, 1), 'distance_identity')
        _r27_require(row['difference_absolute_m'] == 0 and row['difference_relative_pct'] == (0 if round(distance, 1) else None), 'unchanged_distance')
        b, s = row['baseline_within_threshold'], row['scenario_within_threshold']
        _r27_require(type(b) is bool and type(s) is bool, 'boolean_types')
        _r27_require(b == (distance <= before * 1000) and s == (distance <= after * 1000), 'unrounded_classification')
        transition = {(False, False): 'stays_outside', (False, True): 'outside_to_inside',
                      (True, False): 'inside_to_outside', (True, True): 'stays_inside'}[b, s]
        counts[transition] += 1
        if b != s:
            changed.append(dict(municipality_code=code, municipality_name=row['municipality_name'],
                distance_m=row['baseline_distance_m'], baseline_within_threshold=b,
                scenario_within_threshold=s, transition=transition, evidence_path=f'/data/{index}'))
    total = len(rows)
    _r27_require(sum(counts.values()) == total and len(changed) == counts['outside_to_inside'] + counts['inside_to_outside'], 'partition')
    direction = 'increase' if after > before else 'decrease' if after < before else 'equal'
    _r27_require(not counts['inside_to_outside'] if direction == 'increase' else not counts['outside_to_inside'] if direction == 'decrease' else not changed, 'direction')
    first, second = ('inside_to_outside', 'outside_to_inside') if direction == 'decrease' else ('outside_to_inside', 'inside_to_outside')
    labels = {'inside_to_outside': 'de dentro a fuera', 'outside_to_inside': 'de fuera a dentro'}
    sentence = ('No cambia la clasificación porque ambos umbrales son iguales.' if direction == 'equal' else
        f'Al pasar de {before:g} a {after:g} km, {counts[first]} municipios pasan {labels[first]} del umbral y {counts[second]} pasan {labels[second]}.')
    table = ['| Municipio | Distancia geométrica (m) | Antes | Después |', '|---|---:|---|---|']
    for row in changed:
        name = row['municipality_name'].replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
        table.append(f"| {name} | {row['distance_m']:.1f} | {'Dentro' if row['baseline_within_threshold'] else 'Fuera'} | {'Dentro' if row['scenario_within_threshold'] else 'Fuera'} |")
    return dict(contract_version='v1', verified=True, baseline_threshold_km=before, scenario_threshold_km=after,
        baseline_threshold_m=before * 1000, scenario_threshold_m=after * 1000, threshold_direction=direction,
        counts={**counts, 'total': total}, changed_rows=changed,
        unchanged_counts=dict(inside=counts['stays_inside'], outside=counts['stays_outside']),
        comparison_sentence=sentence, answer_table_markdown='\n'.join(table) if changed else 'Ningún municipio cambia de clasificación.',
        semantic_limit_sentence='Cambiar el umbral es un escenario de clasificación: no cambia las distancias, no demuestra una mejora del acceso sanitario real ni mide población cubierta. No recomienda un umbral.',
        presentation_rule='Use this ledger as authority. Do not reconstruct threshold classifications from other rows or infer omitted municipalities.',
        raw_result_sha256=evidence['raw_result_sha256'], source_ids=[s['source_id'] for s in raw['sources']],
        reference_period=raw['period'], evidence_versions=evidence['versions'],
        classification_rule='unrounded_distance_m <= threshold_m; distance_m is rounded display only',
        scope='Complete partition of evaluated raw municipalities; not population coverage.')


def _public_result(evidence, root):
    rendered = _r27_prior_projection(evidence, root)
    args = (evidence.get('effective_request') or {}).get('parameters', {})
    if evidence.get('status') != 'valid' or evidence.get('capability_id') != 'simular_escenario' or args.get('accion') != 'change_threshold':
        return rendered
    view = strict_loads(rendered)
    _r27_require(view['status'] == 'valid', 'prior_projection')
    view['threshold_transition_ledger'] = _r27_threshold_ledger(evidence, root)
    rendered = canonical(view)
    _r27_require(len(rendered.encode('utf-8')) <= MAX_PUBLIC_BYTES, 'payload_size')
    return rendered
