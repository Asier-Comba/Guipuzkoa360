"""R6 opt-in provenance refinement; R4/R5 entrypoints and arithmetic stay frozen."""
import copy
import hashlib
import json

from . import provider as r4
from . import provider_r5 as r5

VERSION = '0.3.1'
ID = r5.ID
_OPTIONAL = ('arrival_margin_minutes', 'boarding_margin_minutes', 'walking_profile_id',
             'snapshot_id', 'return_deadline')


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def _source(source_id, role, content, period, transformation):
    return {'source_id': source_id, 'source_role': role,
            'publisher': 'GIPUZKOA360 request/calculation', 'url': None,
            'source_sha256': _digest(content), 'retrieved_date': None,
            'reference_period': period, 'transformation': transformation}


def _provenance(request, normalized):
    if not normalized:
        return [], {}, {}
    explicit = {key: request[key] for key in request if key in normalized}
    defaults = {key: normalized[key] for key in (*_OPTIONAL, 'timezone') if key not in explicit}
    rows = []
    for key, value in normalized.items():
        human = key in explicit
        rows.append({'field': key, 'value': value,
                     'origin': 'human_explicit' if human else 'model_default',
                     'source_ref': 'USER' if human else 'MODEL_DEFAULTS'})
    return rows, explicit, defaults


def _ref(request, field):
    return 'USER' if field in request else 'MODEL_DEFAULTS'


def _upgrade(request, result):
    result = copy.deepcopy(result)
    result['schema_version'] = VERSION
    q = result.get('normalized_request')
    rows, explicit, defaults = _provenance(request, q)
    result['parameter_provenance'] = rows
    result['sources'] = [s for s in result.get('sources', [])
                         if s.get('source_id') not in ('USER', 'MODEL_DEFAULTS', 'DERIVED')]
    period = q['date'] if q else 'request-validation'
    if explicit:
        result['sources'].append(_source('USER', 'user_input', explicit, period,
            'Only fields explicitly supplied by the caller; no provider defaults.'))
    if defaults:
        result['sources'].append(_source('MODEL_DEFAULTS', 'model_parameter', defaults, period,
            'Defaults applied by provider_r6; not observed human choices.'))
    if result.get('components_s') is not None:
        result['sources'].append(_source('DERIVED', 'derived_metric', result['components_s'], period,
            'Intervals derived from explicit inputs, model defaults, schedule and walking model.'))
    if not result.get('components'):
        return result
    walking = ['GTFS', 'OSM', 'HEALTH_REGISTRY', 'MODEL', _ref(request, 'walking_profile_id')]
    refs = {
        'initial_wait': [_ref(request, 'boarding_margin_minutes')],
        'outbound_vehicle': ['GTFS'],
        'destination_walk_outbound': walking,
        'pre_appointment_wait': ['GTFS', 'OSM', 'HEALTH_REGISTRY', 'MODEL', 'USER',
                                 _ref(request, 'arrival_margin_minutes'),
                                 _ref(request, 'walking_profile_id'), 'DERIVED'],
        'appointment': ['USER'],
        'destination_walk_return': walking,
        'return_wait': ['GTFS', 'OSM', 'HEALTH_REGISTRY', 'MODEL', 'USER',
                        _ref(request, 'boarding_margin_minutes'),
                        _ref(request, 'walking_profile_id'), 'DERIVED'],
        'return_vehicle': ['GTFS'],
    }
    for component in result['components']:
        component['source_refs'] = list(dict.fromkeys(refs[component['kind']]))
        if component['kind'] == 'initial_wait':
            component['basis'] = ('user_input' if 'boarding_margin_minutes' in request
                                  else 'model_default')
    return result


def plan_visit(request):
    if isinstance(request, dict) and request.get('snapshot_id', ID) != ID:
        return r4.plan_visit(request)
    if not isinstance(request, dict):
        request = request
        base = r5.plan_visit(request)
        return _upgrade({}, base)
    return _upgrade(request, r5.plan_visit(request))


def compare_visits(requests):
    if type(requests) is not list or not 2 <= len(requests) <= 32:
        return {'schema_version': VERSION, 'status': 'error', 'results': [],
                'comparisons': [], 'error': r5._error('invalid_request_count',
                                                       'Se requieren 2–32 peticiones')}
    if all(isinstance(q, dict) and q.get('snapshot_id', ID) == r4.DEFAULT_SNAPSHOT_ID
           for q in requests):
        return r4.compare_visits(requests)
    base = r5.compare_visits(requests)
    base['schema_version'] = VERSION
    base['results'] = [plan_visit(q) for q in requests]
    return base


def get_capabilities():
    result = copy.deepcopy(r5.get_capabilities())
    result['schema_version'] = VERSION
    result['provider_id'] = 'ir_y_volver_r6'
    for item in result['snapshots']:
        if item['scenario_kind'] == 'health_visit':
            item['contract_version'] = VERSION
    return result
