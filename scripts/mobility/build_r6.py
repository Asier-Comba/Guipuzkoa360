"""Generate closed 0.3.1 schemas and the operational catalog from pinned artifacts."""
import csv
import hashlib
import json
from pathlib import Path

from prototypes.ir_y_volver import provider_r6 as provider
from scripts.mobility.build_health_r5 import ROOT, BASE, DOC, dump

OUT = BASE / 'contracts/v0.3.1'
CATALOG = ROOT / 'datos_preparados/movilidad/operational_catalog_r6.json'


def _schema(name):
    source = json.loads((BASE / f'contracts/v0.3.0/{name}.schema.json').read_bytes())
    def replace(value):
        if isinstance(value, dict): return {k: replace(v) for k, v in value.items()}
        if isinstance(value, list): return [replace(v) for v in value]
        return '0.3.1' if value == '0.3.0' else value
    return replace(source)


def build_schemas():
    schemas = {name: _schema(name) for name in ('request', 'result', 'comparison', 'capabilities')}
    provenance = {'type': 'array', 'items': {'type': 'object', 'properties': {
        'field': {'type': 'string', 'minLength': 1},
        'value': {'type': ['string', 'integer', 'null']},
        'origin': {'enum': ['human_explicit', 'model_default']},
        'source_ref': {'enum': ['USER', 'MODEL_DEFAULTS']}},
        'required': ['field', 'value', 'origin', 'source_ref'], 'additionalProperties': False}}
    for schema in schemas.values():
        if 'HealthResult' in schema.get('$defs', {}):
            health = schema['$defs']['HealthResult']
            health['properties']['parameter_provenance'] = provenance
            health['required'].append('parameter_provenance')
        if 'TimelineComponent' in schema.get('$defs', {}):
            schema['$defs']['TimelineComponent']['properties']['basis']['enum'].append('model_default')
    result = schemas['result']
    result['properties']['parameter_provenance'] = provenance
    result['required'].append('parameter_provenance')
    schemas['capabilities']['properties']['provider_id']['const'] = 'ir_y_volver_r6'
    schemas['catalog'] = {
      '$schema':'https://json-schema.org/draft/2020-12/schema','type':'object','additionalProperties':False,
      'required':['catalog_version','provider_entrypoint','contract_version','snapshot_id','snapshot_sha256',
        'scenario_kind','validated_date','origins','destination','walking','defaults','ranges','restrictions','cross_origin_comparison'],
      'properties':{
        'catalog_version':{'const':'r6.0'},'provider_entrypoint':{'const':'prototypes.ir_y_volver.provider_r6'},
        'contract_version':{'const':'0.3.1'},'snapshot_id':{'type':'string','minLength':1},
        'snapshot_sha256':{'type':'string','pattern':'^[0-9a-f]{64}$'},'scenario_kind':{'const':'health_visit'},
        'validated_date':{'type':'string','pattern':'^[0-9]{4}-[0-9]{2}-[0-9]{2}$'},
        'origins':{'type':'array','minItems':1,'items':{'type':'object','additionalProperties':False,
          'required':['origin_id','name','municipality_code','municipality_name','stop_ids'],
          'properties':{'origin_id':{'type':'string'},'name':{'type':'string'},
            'municipality_code':{'type':'string','pattern':'^[0-9]{5}$'},'municipality_name':{'type':'string'},
            'stop_ids':{'type':'array','minItems':1,'items':{'type':'string'}}}}},
        'destination':{'type':'object'},'walking':{'type':'object'},'defaults':{'type':'object'},
        'ranges':{'type':'object'},'restrictions':{'type':'array','items':{'type':'string'}},
        'cross_origin_comparison':{'const':'side_by_side_only; numeric delta is not supported across origins'}}
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, schema in schemas.items(): dump(OUT / f'{name}.schema.json', schema)


def build_catalog():
    health, base = provider.r5._load()
    with (ROOT / 'datos_preparados/demografia.csv').open(encoding='utf-8-sig', newline='') as fh:
        names = {r['municipality_name'].casefold(): r['municipality_code'] for r in csv.DictReader(fh)}
    origins = []
    for origin_id, item in sorted(health['origins'].items()):
        municipality = item['name'].removeprefix('Paradas centrales de ').removeprefix('Paradas Herriko Plaza de ')
        code = names[municipality.casefold()]
        origins.append({'origin_id': origin_id, 'name': item['name'], 'municipality_code': code,
                        'municipality_name': municipality, 'stop_ids': item['stop_ids']})
    assert len(origins) == len({x['municipality_code'] for x in origins}) == len(health['origins'])
    request = json.loads((OUT / 'request.schema.json').read_bytes())['properties']
    catalog = {'catalog_version': 'r6.0', 'provider_entrypoint': 'prototypes.ir_y_volver.provider_r6',
      'contract_version': '0.3.1', 'snapshot_id': health['snapshot_id'],
      'snapshot_sha256': hashlib.sha256((BASE/f"snapshots/{health['snapshot_id']}.json").read_bytes()).hexdigest(),
      'scenario_kind': 'health_visit', 'validated_date': health['validated_date'], 'origins': origins,
      'destination': {'destination_id': health['destination_id'], 'name': health['health_destination']['name'],
        'centre_id': health['health_destination']['centre_id'], 'reference_point_meaning': health['health_destination']['wording'],
        'verification': {'centre_identity': health['health_destination']['centre_identity'],
          'centre_anchor': health['health_destination']['centre_anchor'], 'entrance_verified': False,
          'modelled_access': True}},
      'walking': {'profile_id': health['walking_profile_id'], 'distance_unit': 'metre', 'time_unit': 'second',
        'formula': 'ceil(total_metres/50)*60+120'},
      'defaults': {'arrival_margin_minutes': base['defaults']['arrival_margin_minutes'],
        'boarding_margin_minutes': base['defaults']['boarding_margin_minutes'],
        'walking_profile_id': health['walking_profile_id'], 'snapshot_id': health['snapshot_id'],
        'return_deadline': None, 'timezone': 'Europe/Madrid'},
      'ranges': {k: {x: request[k][x] for x in ('minimum','maximum') if x in request[k]}
                 for k in ('duration_minutes','arrival_margin_minutes','boarding_margin_minutes')},
      'restrictions': ['GO01 direct only', 'static schedule; not realtime', 'same civil day',
        'origin stop presence to return stop arrival', 'validated date only',
        'not assigned centre, appointment availability, universal accessibility or verified entrance'],
      'cross_origin_comparison': 'side_by_side_only; numeric delta is not supported across origins'}
    dump(CATALOG, catalog)
    return catalog


def run():
    build_schemas(); catalog=build_catalog()
    dump(DOC/'CAPABILITY_DESCRIPTOR_R6.json', provider.get_capabilities())
    return catalog


if __name__ == '__main__': print(json.dumps(run(), ensure_ascii=False))
