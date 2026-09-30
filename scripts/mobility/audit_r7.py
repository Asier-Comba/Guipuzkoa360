"""Consumer-side semantic checks and mutation matrix for frozen R6 outputs."""
import copy
import csv
import hashlib
import io
import json
import math
import re
import zipfile

from prototypes.ir_y_volver import provider_r6 as p
from prototypes.ir_y_volver.schema_r5 import validate as schema_validate
from prototypes.ir_y_volver.snapshot_validation import finite_tree
from scripts.mobility.build_health_r5 import ROOT, DOC, dump

SCHEMA=json.loads((ROOT/'prototypes/ir_y_volver/contracts/v0.3.1/result.schema.json').read_bytes())
HEALTH,_BASE=p.r5._load()
GTFS=ROOT/'datos_originales/movilidad/goierrialdea-3276fcae.zip'
with zipfile.ZipFile(GTFS) as _archive:
    _STOP_TIMES=list(csv.DictReader(io.StringIO(_archive.read('stop_times.txt').decode('utf-8-sig'))))
_ROWS={(r['trip_id'],r['stop_id'],r['stop_sequence']):r for r in _STOP_TIMES}
_OPTIONAL=('arrival_margin_minutes','boarding_margin_minutes','walking_profile_id','snapshot_id','return_deadline')


def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,
                                     separators=(',',':')).encode()).hexdigest()


def _distance(a,b):
    lat1,lat2=map(math.radians,[a[0],b[0]]);dlon=math.radians(b[1]-a[1])
    numerator=math.hypot(math.cos(lat2)*math.sin(dlon),
      math.cos(lat1)*math.sin(lat2)-math.sin(lat1)*math.cos(lat2)*math.cos(dlon))
    denominator=math.sin(lat1)*math.sin(lat2)+math.cos(lat1)*math.cos(lat2)*math.cos(dlon)
    return 6371000*math.atan2(numerator,denominator)


def validate_health_result(result,request):
    finite_tree(result);schema_validate(result,SCHEMA,SCHEMA)
    if result['schema_version']!='0.3.1' or result['snapshot_id']!=HEALTH['snapshot_id']: raise ValueError('identity')
    if result['scenario_kind']!='health_visit' or result['scope']!=p.r4.SCOPE: raise ValueError('scenario/scope')
    sources=result['sources'];ids=[s['source_id'] for s in sources]
    if len(ids)!=len(set(ids)): raise ValueError('duplicate source')
    source={s['source_id']:s for s in sources}
    if any(not re.fullmatch('[0-9a-f]{64}',s['source_sha256']) for s in sources): raise ValueError('source hash')
    if any(not s['reference_period'] or not s['transformation'] for s in sources): raise ValueError('source metadata')
    expected_official={s['source_id']:s for s in HEALTH['sources']}
    for sid,expected in expected_official.items():
        if sid not in source or source[sid]!=expected: raise ValueError('official source '+sid)
    q=result['normalized_request']
    if q is None: return True
    provenance=result['parameter_provenance']
    if len(provenance)!=len(q) or {x['field'] for x in provenance}!=set(q): raise ValueError('provenance coverage')
    if len({x['field'] for x in provenance})!=len(provenance): raise ValueError('duplicate provenance')
    explicit={k:request[k] for k in request if k in q}
    defaults={k:q[k] for k in (*_OPTIONAL,'timezone') if k not in explicit}
    for item in provenance:
        human=item['field'] in explicit
        if item['origin']!=('human_explicit' if human else 'model_default'): raise ValueError('provenance origin')
        if item['source_ref']!=('USER' if human else 'MODEL_DEFAULTS'): raise ValueError('provenance ref')
        if item['value']!=q[item['field']]: raise ValueError('provenance value')
    if explicit:
        if source.get('USER',{}).get('source_role')!='user_input' or source['USER']['source_sha256']!=_hash(explicit): raise ValueError('USER content')
    if defaults:
        if source.get('MODEL_DEFAULTS',{}).get('source_role')!='model_parameter' or source['MODEL_DEFAULTS']['source_sha256']!=_hash(defaults): raise ValueError('default content')
    if result['status']!='ok': return True
    if source.get('DERIVED',{}).get('source_role')!='derived_metric' or source['DERIVED']['source_sha256']!=_hash(result['components_s']): raise ValueError('derived content')
    components=result['components'];it=result['itinerary']
    if sum(x['seconds'] for x in components)!=it['total_s'] or it['total_s']!=it['end_s']-it['start_s']: raise ValueError('total')
    if any(x['seconds']!=x['end_s']-x['start_s'] for x in components): raise ValueError('component interval')
    if any(a['end_s']!=b['start_s'] for a,b in zip(components,components[1:])): raise ValueError('component continuity')
    if result['components_s']['appointment_s']!=q['duration_minutes']*60: raise ValueError('appointment duration')
    if any(not set(x['source_refs'])<=set(ids) for x in components): raise ValueError('orphan component source')
    by_kind={x['kind']:x for x in components}
    if by_kind['appointment']['source_refs']!=['USER']: raise ValueError('appointment provenance')
    if by_kind['outbound_vehicle']['source_refs']!=['GTFS'] or by_kind['return_vehicle']['source_refs']!=['GTFS']: raise ValueError('bus provenance')
    if not {'OSM','MODEL','HEALTH_REGISTRY'}<=set(by_kind['destination_walk_outbound']['source_refs']): raise ValueError('walking provenance')
    if 'GTFS' in result['health_destination']['source_refs']: raise ValueError('centre from GTFS')
    if result['health_destination']!=HEALTH['health_destination']: raise ValueError('health destination')
    for direction in ('outbound','return'):
        leg=it[direction];key=(leg['trip_id'],leg['from_stop_id'],str(leg['from_stop_sequence']))
        row=_ROWS.get(key)
        if not row or row['departure_time']!=leg['departure_time']: raise ValueError('GTFS departure')
        key=(leg['trip_id'],leg['to_stop_id'],str(leg['to_stop_sequence']));row=_ROWS.get(key)
        if not row or row['arrival_time']!=leg['arrival_time']: raise ValueError('GTFS arrival')
    for direction,stop_id in [('outbound',it['outbound']['to_stop_id']),('return',it['return']['from_stop_id'])]:
        walk=result['walking'][direction];expected=HEALTH['walking_links'][stop_id][direction]
        if walk!=expected: raise ValueError('walking identity')
        metres=sum(_distance(a,b) for a,b in zip(walk['geometry'],walk['geometry'][1:]))
        if abs(metres-walk['total_metres'])>0.0001: raise ValueError('walking metres')
        if walk['seconds']!=math.ceil(metres/50)*60+120: raise ValueError('walking seconds')
    if it['return_slack_s']!=by_kind['return_wait']['seconds']-q['boarding_margin_minutes']*60: raise ValueError('return slack')
    return True


def provenance_audit(result,request):
    validate_health_result(result,request)
    circular=[x['kind'] for x in result['components'] if 'DERIVED' in x['source_refs']]
    return {'status':'PASS_WITH_EXPLICIT_FINDING','nodes':[s['source_id'] for s in result['sources']],
      'source_ref_integrity':'PASS','parameter_provenance':'PASS','human_vs_default_partition':'PASS',
      'component_semantics':'PASS','findings':[{'id':'W1-R7-F01','severity':'MEDIUM',
        'title':'DERIVED is a conceptually circular component reference','components':circular,
        'impact':'No arithmetic or source hash corruption; the graph is not a strict explanatory DAG.',
        'proposal':'In a future coordinated contract, model derivation as an edge/operation rather than a source_ref from a component to the aggregate derived metric.',
        'contract_change_required_now':False}] if circular else []}


def mutation_matrix():
    request=dict(origin_id='zegama_center_stops',destination_id=HEALTH['destination_id'],date=HEALTH['validated_date'],
                 appointment_time='09:45',duration_minutes=20)
    baseline=p.plan_visit(request);validate_health_result(baseline,request)
    def mutate(name,fn):
        value=copy.deepcopy(baseline);fn(value)
        try: finite_tree(value);schema_validate(value,SCHEMA,SCHEMA)
        except Exception: return {'mutation':name,'classification':'SCHEMA_CAUGHT'}
        try: validate_health_result(value,request)
        except Exception as exc: return {'mutation':name,'classification':'SEMANTIC_VALIDATOR_CAUGHT','reason':str(exc)}
        return {'mutation':name,'classification':'GAP'}
    changes=[
      ('schema_version',lambda x:x.update(schema_version='9.9.9')),
      ('snapshot_id',lambda x:x.update(snapshot_id='other')),
      ('scenario_kind',lambda x:x.update(scenario_kind='stop_only')),
      ('scope',lambda x:x.update(scope='other')),
      ('trip_id',lambda x:x['itinerary']['outbound'].update(trip_id='fake')),
      ('from_stop_id',lambda x:x['itinerary']['outbound'].update(from_stop_id='fake')),
      ('to_stop_id',lambda x:x['itinerary']['return'].update(to_stop_id='fake')),
      ('departure_time',lambda x:x['itinerary']['outbound'].update(departure_time='00:00:00')),
      ('arrival_time',lambda x:x['itinerary']['return'].update(arrival_time='00:00:00')),
      ('total_s',lambda x:x['itinerary'].update(total_s=x['itinerary']['total_s']+1)),
      ('return_slack_s',lambda x:x['itinerary'].update(return_slack_s=x['itinerary']['return_slack_s']+1)),
      ('component_seconds',lambda x:x['components'][0].update(seconds=x['components'][0]['seconds']+1)),
      ('component_interval',lambda x:x['components'][0].update(end_s=x['components'][0]['end_s']+1)),
      ('walking_metres',lambda x:x['walking']['outbound'].update(total_metres=x['walking']['outbound']['total_metres']+1)),
      ('walking_seconds',lambda x:x['walking']['outbound'].update(seconds=x['walking']['outbound']['seconds']+60)),
      ('walking_source_refs',lambda x:x['walking']['outbound'].update(source_refs=['GTFS'])),
      ('centre_id',lambda x:x['health_destination'].update(centre_id='fake')),
      ('modelled_access',lambda x:x['health_destination'].update(modelled_access=False)),
      ('entrance_verified',lambda x:x['health_destination'].update(entrance_verified=True)),
      ('address_conflict',lambda x:x['health_destination'].update(address_conflict='unresolved')),
      ('parameter_provenance',lambda x:x['parameter_provenance'][0].update(origin='model_default')),
      ('USER_hash',lambda x:next(s for s in x['sources'] if s['source_id']=='USER').update(source_sha256='0'*64)),
      ('MODEL_DEFAULTS_hash',lambda x:next(s for s in x['sources'] if s['source_id']=='MODEL_DEFAULTS').update(source_sha256='0'*64)),
      ('GTFS_source_hash',lambda x:next(s for s in x['sources'] if s['source_id']=='GTFS').update(source_sha256='0'*64)),
      ('source_role',lambda x:next(s for s in x['sources'] if s['source_id']=='USER').update(source_role='derived_metric')),
      ('missing_source',lambda x:x['sources'].pop()),
      ('duplicate_source',lambda x:x['sources'].append(copy.deepcopy(x['sources'][0]))),
      ('non_finite',lambda x:x['walking']['outbound'].update(total_metres=float('nan'))),
      ('extra_unknown_key',lambda x:x.update(unknown=True))]
    results=[mutate(name,fn) for name,fn in changes]
    counts={name:sum(x['classification']==name for x in results) for name in ('SCHEMA_CAUGHT','SEMANTIC_VALIDATOR_CAUGHT','NOT_REQUIRED_BY_CONTRACT','GAP')}
    return {'baseline_status':'PASS','mutations':len(results),'counts':counts,'critical_high_gaps':0 if counts['GAP']==0 else counts['GAP'],'results':results}


def run():
    request=dict(origin_id='zegama_center_stops',destination_id=HEALTH['destination_id'],date=HEALTH['validated_date'],
                 appointment_time='09:45',duration_minutes=20)
    provenance=provenance_audit(p.plan_visit(request),request);matrix=mutation_matrix()
    dump(DOC/'PROVENANCE_AUDIT_R7.json',provenance);dump(DOC/'MUTATION_MATRIX_R7.json',matrix)
    print(json.dumps({'provenance':provenance['status'],'mutation_counts':matrix['counts']}));return provenance,matrix


if __name__=='__main__':run()
