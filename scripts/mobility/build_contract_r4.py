"""Generate explicit candidate schemas and synthetic consumer examples."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'prototypes/ir_y_volver/contracts/v0.2.0'


def obj(properties, required=None):
    return {'type': 'object', 'additionalProperties': False,
            'required': list(properties) if required is None else required, 'properties': properties}


def build():
    text = {'type': 'string', 'minLength': 1}
    integer = {'type': 'integer', 'minimum': 0}
    clock = {'type': 'string', 'pattern': r'^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$'}
    request = json.loads((OUT.parent / 'round_trip_request.schema.json').read_text())
    request['$id'] = 'urn:g360:mobility:0.2.0:request'
    request['properties']['return_deadline'] = {'anyOf': [clock, {'type': 'null'}]}
    component = obj({'kind': text, 'start_s': integer, 'end_s': integer,
                     'seconds': integer, 'basis': text, 'derivation': text})
    result = obj({
        'schema_version': {'const': '0.2.0'},
        'normalized_request': {'type': ['object', 'null']},
        'status': {'enum': ['ok', 'no_feasible_journey', 'unknown', 'unsupported', 'error']},
        'scenario_kind': {'enum': ['stop_only', 'health_visit', None]},
        'time_basis': {'const': 'scheduled'},
        'scope': {'const': 'origin_stop_presence_to_return_stop_arrival'},
        'snapshot_id': {'type': ['string', 'null']},
        'itinerary': {'type': ['object', 'null']},
        'components_s': {'type': ['object', 'null'], 'additionalProperties': integer},
        'components': {'type': ['array', 'null'], 'items': component},
        'sources': {'type': 'array', 'items': {'type': 'object'}},
        'assumptions': {'type': 'array', 'items': text},
        'limitations': {'type': 'array', 'items': text},
        'error': {'type': ['object', 'null']},
    })
    result['allOf'] = [{'if': {'properties': {'status': {'const': 'ok'}}},
        'then': {'properties': {'itinerary': {'type': 'object'}, 'components_s': {'type': 'object'},
                               'components': {'type': 'array', 'minItems': 8, 'maxItems': 8}, 'error': {'type': 'null'}}},
        'else': {'properties': {'itinerary': {'type': 'null'}, 'components_s': {'type': 'null'},
                               'components': {'type': 'null'}, 'error': {'type': 'object'}}}}]
    capabilities = obj({'schema_version': {'const': '0.2.0'}, 'provider_id': {'const': 'ir_y_volver'},
        'time_basis': {'const': 'scheduled'}, 'scope': result['properties']['scope'],
        'statuses': {'type': 'array', 'items': text}, 'snapshots': {'type': 'array', 'items': {'type': 'object'}}})
    comparison = obj({'schema_version': {'const': '0.2.0'}, 'status': {'enum': ['ok', 'error']},
        'results': {'type': 'array', 'items': result}, 'comparisons': {'type': 'array', 'items': {'type': 'object'}},
        'differences_s': {'type': 'array', 'items': {'type': 'object'}}, 'error': {'type': ['object', 'null']}})
    for name, value in [('request', request), ('result', result), ('capabilities', capabilities), ('comparison', comparison)]:
        value['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
        value['$id'] = f'urn:g360:mobility:0.2.0:{name}'
        (OUT / f'{name}.schema.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
    base = dict(schema_version='0.2.0', normalized_request=None, status='unknown', scenario_kind=None,
        time_basis='scheduled', scope='origin_stop_presence_to_return_stop_arrival', snapshot_id='TEST_CONTRACT',
        itinerary=None, components_s=None, components=None, sources=[{'classification':'SYNTHETIC'}],
        assumptions=['Synthetic consumer fixture only'], limitations=['Not runtime data'],
        error={'code':'snapshot_not_found','message':'Synthetic unknown example'})
    req = dict(origin_id='TEST_A',destination_id='TEST_B',date='2026-09-29',appointment_time='10:00:00',
        duration_minutes=30,arrival_margin_minutes=10,boarding_margin_minutes=3,walking_profile_id='stop_only',
        snapshot_id='TEST_CONTRACT',timezone='Europe/Madrid',return_deadline=None)
    kinds = ['initial_wait','outbound_vehicle','destination_walk_outbound','pre_appointment_wait','appointment','destination_walk_return','return_wait','return_vehicle']
    bounds = [32220,32400,34800,34800,36000,37800,37800,38400,40800]
    comps = [dict(kind=k,start_s=a,end_s=b,seconds=b-a,basis='SYNTHETIC',derivation='end_s - start_s') for k,a,b in zip(kinds,bounds,bounds[1:])]
    good = {**base,'status':'ok','scenario_kind':'stop_only','normalized_request':req,'error':None,
        'components':comps,'components_s':{c['kind']+'_s':c['seconds'] for c in comps},
        'itinerary':dict(start_s=32220,end_s=40800,total_s=8580,vehicle_span_s=8400,return_slack_s=420,
                        origin_stop_id='TEST_A',return_stop_id='TEST_A',outbound={},**{'return':{}})}
    bad = {**base,'status':'no_feasible_journey','scenario_kind':'stop_only','normalized_request':{**req,'duration_minutes':500},'error':{'code':'no_pair_in_complete_direct_search','message':'No ordinary direct pair in synthetic coverage'}}
    examples = {'classification':'SYNTHETIC_CONTRACT_ONLY','viable':good,'no_viable':bad,'unknown':base,
                'mixed_comparison':dict(schema_version='0.2.0',status='ok',results=[good,bad,base],comparisons=[],differences_s=[],error=None)}
    for left,right in ((0,1),(0,2),(1,2)):
        examples['mixed_comparison']['comparisons'].append({
            'left_index':left,'right_index':right,'comparability':'not_comparable',
            'requested_changes':{'duration_minutes':{'left':30,'right':500}} if (left,right)==(0,1) else {},
            'held_constant':{k:v for k,v in req.items() if k!='duration_minutes'} if (left,right)==(0,1) else {},
            'limitations':['At least one outcome is not ok; no delta or favourable averaging.']})
    (OUT / 'examples.json').write_text(json.dumps(examples,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__ == '__main__':
    build()
