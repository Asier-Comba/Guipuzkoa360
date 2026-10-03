"""Verified presentation of the complete return journey; raw engine untouched."""

_R24_HEALTH_SCOPE = 'origin_stop_presence_to_return_stop_arrival'
_R24_ANCHOR_MEANING = (
    'Punto de referencia modelado utilizado para el acceso al centro durante '
    'la parte intermedia de la visita; no es el final del intervalo completo '
    'ni representa una entrada física verificada.'
)


def _r24_journey_scope(raw, projected):
    """Bind start, intermediate anchor and end to validated raw, not a prompt."""
    if raw['scenario_kind'] != 'health_visit' or raw['status'] != 'ok':
        raise ContractViolation('journey_scope:invalid_health_state')
    if raw['scope'] != _R24_HEALTH_SCOPE or projected['scope'] != raw['scope']:
        raise ContractViolation('journey_scope:invalid_scope')
    summary = _time_summary(raw)
    if projected['time_summary'] != summary:
        raise ContractViolation('journey_scope:time_summary_mismatch')
    itinerary, shown = raw['itinerary'], projected['itinerary']
    destination = raw['health_destination']
    public_destination = projected['health_destination']
    origin_id = raw['normalized_request']['origin_id']
    destination_id = raw['normalized_request']['destination_id']
    if (projected['effective_parameters'] != raw['normalized_request']
            or destination['entrance_verified'] is not False
            or public_destination['entrance_verified'] is not False
            or public_destination['centre_id'] != destination['centre_id']
            or shown['origin_stop_id'] != itinerary['origin_stop_id']
            or shown['return_stop_id'] != itinerary['return_stop_id']
            or itinerary['outbound']['from_stop_id'] != itinerary['origin_stop_id']
            or itinerary['return']['to_stop_id'] != itinerary['return_stop_id']
            or shown['outbound']['from_stop_id'] != itinerary['origin_stop_id']
            or shown['return']['to_stop_id'] != itinerary['return_stop_id']
            or shown['outbound']['departure_time'] != itinerary['outbound']['departure_time']
            or shown['return']['arrival_time'] != itinerary['return']['arrival_time']
            or itinerary['return']['arrival_time'] != summary['scope_end_clock']
            or itinerary['total_s'] != summary['total_s']
            or destination['centre_id'] == itinerary['return_stop_id']):
        raise ContractViolation('journey_scope:unverified_endpoint_binding')
    for value in (origin_id, destination_id, projected['origin_label'],
                  shown['outbound']['from_stop_label'], shown['return']['to_stop_label'],
                  public_destination['name']):
        if type(value) is not str or not value.strip():
            raise ContractViolation('journey_scope:missing_identity')
    return {
        'scope_kind': raw['scope'], 'includes_return_trip': True,
        'authority': 'time_summary defines the complete interval; health_destination is intermediate',
        'start': {
            'kind': 'origin_stop_presence', 'origin_id': origin_id,
            'origin_label': projected['origin_label'], 'stop_id': itinerary['origin_stop_id'],
            'stop_label': shown['outbound']['from_stop_label'],
            'clock': summary['scope_start_clock'], 'seconds': summary['scope_start_s'],
            'vehicle_departure_clock': itinerary['outbound']['departure_time'],
            'meaning': 'Inicio del intervalo completo por presencia en la parada de origen, antes de la salida del autobús; no desde el domicilio.',
        },
        'health_destination': {
            'kind': 'intermediate_health_anchor', 'destination_id': destination_id,
            'centre_id': destination['centre_id'], 'label': public_destination['name'],
            'entrance_verified': False, 'meaning': _R24_ANCHOR_MEANING,
        },
        'end': {
            'kind': 'return_stop_arrival', 'origin_id': origin_id,
            'origin_label': projected['origin_label'], 'stop_id': itinerary['return_stop_id'],
            'stop_label': shown['return']['to_stop_label'],
            'clock': summary['scope_end_clock'], 'seconds': summary['scope_end_s'],
            'meaning': 'Fin del intervalo completo al llegar de vuelta a las paradas del origen, después de la consulta y del regreso; no en el centro sanitario ni en el domicilio.',
        },
    }


_r23_mobility_view = _mobility_view


def _mobility_view(raw, root, arguments):
    view = _r23_mobility_view(raw, root, arguments)
    results = raw['results'] if 'results' in raw else [raw]
    for result, projected in zip(results, view['scenarios'], strict=True):
        if result['status'] != 'ok' or result['scenario_kind'] != 'health_visit':
            continue
        scope = _r24_journey_scope(result, projected)
        # Create replacements rather than mutate lists/dicts shared with raw.
        old_wording = result['health_destination']['wording']
        projected['health_destination'] = {
            **projected['health_destination'], 'kind': 'intermediate_health_anchor',
            'wording': _R24_ANCHOR_MEANING,
        }
        projected['limitations'] = [
            _R24_ANCHOR_MEANING if text == old_wording else text
            for text in projected['limitations']
        ]
        projected['journey_scope'] = scope
    return view


_r23_mobility_catalog_view = _mobility_catalog_view


def _mobility_catalog_view(root):
    view = _r23_mobility_catalog_view(root)
    if view is None:
        return None
    destination = view['destination']
    if destination['verification']['entrance_verified'] is not False:
        raise ContractViolation('journey_scope:catalog_entrance_unverified')
    view['destination'] = {**destination, 'reference_point_meaning': _R24_ANCHOR_MEANING}
    return view
