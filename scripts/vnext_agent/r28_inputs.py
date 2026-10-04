"""Normalize public visit labels against the hash-verified pinned catalogue only."""

from datetime import date as _r28_date

_r28_prior_public_call = public_call


def _r28_resolve(value, rows, identity, labels):
    if type(value) is not str or not value.strip():
        raise ValueError('missing_label')
    # Exact IDs remain identities, even if another entity has a similar label.
    exact = {row[identity] for row in rows if row[identity] == value}
    matches = exact or {row[identity] for row in rows
                        if any(_normalized_key(value) == _normalized_key(row.get(key))
                               for key in (identity, *labels) if row.get(key))}
    if len(matches) != 1:
        raise ValueError('unknown_or_ambiguous_label')
    return next(iter(matches))


def _r28_normalize_date(value):
    if type(value) is not str:
        raise ValueError('invalid_date')
    if re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        return _r28_date.fromisoformat(value).isoformat()
    if re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', value):
        day, month, year = map(int, value.split('/'))
        return _r28_date(year, month, day).isoformat()
    raise ValueError('use_YYYY_MM_DD_or_DD_MM_YYYY')


def public_call(name, arguments, request_id, *, root=None):
    if name != 'plan_visit' or type(arguments) is not dict or set(arguments) != set(_R26_FIELDS):
        return _r28_prior_public_call(name, arguments, request_id, root=root)
    try:
        catalog = _r15_mobility_catalog_view(root or _workspace_root())
        if catalog is None:
            raise ContractViolation('visit_catalog_missing')
        origins, destinations = catalog['origin_options'], [catalog['destination']]
        normalized = dict(arguments)
        invalid = []
        for field, rows, labels in (
                ('origin_id', origins, ('name', 'municipality_name')),
                ('destination_id', destinations, ('name',))):
            try:
                normalized[field] = _r28_resolve(arguments[field], rows, field, labels)
            except ValueError:
                invalid.append(field)
        try:
            normalized['date'] = _r28_normalize_date(arguments['date'])
        except ValueError:
            invalid.append('date')
        if invalid:
            allowed = {'origin_id': [r['name'] for r in origins],
                       'destination_id': [r['name'] for r in destinations],
                       'date': 'Fecha real YYYY-MM-DD o DD/MM/YYYY (día/mes/año); no se adivinan otros formatos.'}
            return canonical(_r20_error_view(name, request_id, 'invalid_arguments', invalid,
                message='Indica una entidad inequívoca del catálogo y una fecha con formato admitido.',
                allowed={k: allowed[k] for k in invalid}))
        rendered = _r28_prior_public_call(name, normalized, request_id, root=root)
        if normalized == arguments:
            return rendered  # Preserve exact canonical-input public bytes.
        view = strict_loads(rendered)
        view['public_input'] = {'tool': name, 'arguments': arguments}
        view['input_normalization'] = {
            'canonical_arguments': normalized,
            'changed_fields': [k for k in _R26_FIELDS if normalized[k] != arguments[k]],
            'method': 'Unique pinned catalogue identity using existing text normalizer; explicit day/month/year date grammar.'}
        encoded = canonical(view)
        if len(encoded.encode('utf-8')) > MAX_PUBLIC_BYTES:
            raise ContractViolation('normalization:payload_size')
        return encoded
    except Exception:
        return canonical(_r20_error_view(name, request_id, 'input_normalization_unverified', [],
            message='No se pudo verificar el catálogo de entradas. No hay cifras verificadas.'))
