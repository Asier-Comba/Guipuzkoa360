"""Opt-in R5 dispatcher. The published R4 entry point and bytes stay unchanged."""
import copy
import hashlib
import json
from datetime import date
from pathlib import Path

from . import provider as r4
from .snapshot_validation import SnapshotError, finite_tree, require, strict_loads
from .walking_r5 import PROFILE, distance, duration
from .schema_r5 import validate as schema_validate

VERSION='0.3.0'
ID='official-goierrialdea-go01-health-r5-20260929'
HERE=Path(__file__).resolve().parent
MANIFEST=HERE/'snapshots/allowlist_r5.json'


def _digest(raw): return hashlib.sha256(raw).hexdigest()


def validate_health(h,base):
    finite_tree(h)
    schema=strict_loads((HERE/'contracts/v0.3.0/result.schema.json').read_bytes())
    schema_validate(h['health_destination'],schema['$defs']['HealthDestinationEvidence'],schema)
    for source in h['sources']:
        schema_validate(source,schema['$defs']['SourceReference'],schema)
    for links in h['walking_links'].values():
        for link in links.values(): schema_validate(link,schema['$defs']['WalkingLinkEvidence'],schema)
    require(h['schema_version']==VERSION and h['snapshot_id']==ID and h['scenario_kind']=='health_visit','health identity')
    require(h['walking_profile_id']==PROFILE,'walking profile')
    require(h['validated_date']=='2026-09-29','validated date')
    require(h['origins']==base['origins'],'origin binding')
    e=h['health_destination']
    require(e['centre_id']=='entityBC631DA5' and e['anchor_kind']=='official_centre_point','centre identity')
    require(e['modelled_access'] is True and e['entrance_verified'] is False and e['entrance_verification']=='NOT_VERIFIED','entrance misrepresentation')
    require(e['door_to_door']=='UNAVAILABLE' and e['modelled_network_access']=='PASS','unsupported health evidence')
    require(e['address_conflict']=='conflicting_current_sources' and e['human_review_required'] is True,'source conflict lost')
    require(h['source_conflict']['chosen_source_id']=='HEALTH_PAGE' and h['source_conflict']['human_review_required'] is True,'source priority')
    require(h['walking_links'],'no walking evidence')
    refs={s['source_id']:s for s in h['sources']}
    require(len(refs)==len(h['sources']) and set(refs)=={'GTFS','HEALTH_REGISTRY','HEALTH_PAGE','PADI_2026','OSM','MODEL'},'source identity')
    require(refs['GTFS']['source_sha256']==base['sources'][0]['source_sha256'],'GTFS binding')
    require(refs['OSM']['source_sha256']==h['network_sha256'],'network binding')
    require(refs['MODEL']['source_sha256']==_digest((HERE/'walking_r5.py').read_bytes()),'model binding')
    for sid,links in h['walking_links'].items():
        require(sid in base['stops'] and set(links)=={'outbound','return'},'stop/direction binding')
        stop=base['stops'][sid]; p=[stop['lat'],stop['lon']]
        for direction,link in links.items():
            start,end=(p,e['anchor_coordinates']) if direction=='outbound' else (e['anchor_coordinates'],p)
            require(link['status']=='ok' and link['start_coordinates']==start and link['end_coordinates']==end,'endpoint binding')
            require(link['network_sha256']==h['network_sha256'] and link['walking_profile_id']==PROFILE,'link provenance')
            require(link['entrance_verified'] is False and link['modelled_access'] is True,'link semantics')
            require(link['connector_threshold_m']==100 and all(0<=x<=100 for x in link['connector_metres']),'connector threshold')
            nodes=link['node_ids'];geo=link['geometry']
            require(nodes and len(link['way_ids'])==len(nodes)-1 and len(geo)==len(nodes)+2,'path dimensions')
            require(nodes[0]==link['start_node_id'] and nodes[-1]==link['end_node_id'],'path endpoints')
            require(geo[0]==start and geo[-1]==end,'geometry binding')
            measured=sum(distance(a,b) for a,b in zip(geo,geo[1:]))
            network=sum(distance(a,b) for a,b in zip(geo[1:-1],geo[2:-1]))
            require(abs(measured-link['total_metres'])<1e-6 and abs(network-link['network_metres'])<1e-6,'geometry length')
            require(all(abs(a-b)<1e-6 for a,b in zip(link['connector_metres'],[distance(geo[0],geo[1]),distance(geo[-2],geo[-1])])),'connector length')
            require(type(link['seconds']) is int and link['seconds']==duration(link['total_metres']),'walking seconds')
            require(set(link['source_refs'])<=refs.keys(),'orphan provenance')


def _load():
    m=strict_loads(MANIFEST.read_bytes())
    require(m['snapshot_id']==ID and m['file']==ID+'.json' and m['schema_version']==VERSION,'health allowlist')
    raw=(MANIFEST.parent/m['file']).read_bytes()
    require(_digest(raw)==m['sha256'],'health snapshot hash')
    h=strict_loads(raw);base=r4._load_snapshot(h['base_snapshot_id'])
    require(_digest((MANIFEST.parent/(h['base_snapshot_id']+'.json')).read_bytes())==h['base_snapshot_sha256'],'base snapshot hash')
    validate_health(h,base)
    return h,base


def _base(status,normalized=None,h=None,error=None):
    return {'schema_version':VERSION,'normalized_request':normalized,'status':status,
            'scenario_kind':'health_visit','time_basis':'scheduled','scope':r4.SCOPE,'snapshot_id':ID,
            'itinerary':None,'components_s':None,'components':None,'walking':None,
            'health_destination':copy.deepcopy(h['health_destination']) if h else None,
            'sources':copy.deepcopy(h['sources']) if h else [],'limitations':h['limitations'][:] if h else [],
            'assumptions':['50 m/min y 120 s por enlace completo y sentido; hipótesis no específica por edad.',
                           'Solo GO01 directa; inicio y fin en paradas, no en domicilio.'],
            'error':error}


def _error(code,message): return {'code':code,'message':message}


def plan_visit(request):
    if isinstance(request,dict) and request.get('snapshot_id',ID)!=ID:
        return r4.plan_visit(request)
    try: h,base=_load()
    except (OSError,ValueError,KeyError,TypeError,RecursionError) as exc:
        return _base('unknown',error=_error('invalid_health_snapshot',str(exc)))
    context={**base,'snapshot_id':ID,'walking_profiles':{PROFILE:{}},
             'defaults':{**base['defaults'],'walking_profile_id':PROFILE}}
    try: q=r4._normalize(request,context)
    except (ValueError,TypeError) as exc: return _base('error',h=h,error=_error('invalid_request',str(exc)))
    if q['origin_id'] not in h['origins'] or q['destination_id']!=h['destination_id']:
        return _base('unsupported',q,h,_error('catalog_scope','Origen o destino fuera del catálogo sanitario'))
    if q['date']!=h['validated_date']: return _base('unknown',q,h,_error('date_not_validated','Fecha no validada'))
    ap=r4._clock_seconds(q['appointment_time']);dur=q['duration_minutes']*60
    am=q['arrival_margin_minutes']*60;bm=q['boarding_margin_minutes']*60
    if ap+dur>=86400: return _base('unsupported',q,h,_error('cross_day_appointment','Fuera del mismo día'))
    deadline=r4._clock_seconds(q['return_deadline']) if q['return_deadline'] else 86399
    active=r4._active_services(base,date.fromisoformat(q['date']))
    origins=set(h['origins'][q['origin_id']]['stop_ids']); stops=set(h['walking_links'])
    outs=r4._legs(base,active,origins,stops);backs=r4._legs(base,active,stops,origins)
    if any(l['arrival_s']>=86400 or l['departure_s']>=86400 for l in outs+backs):
        return _base('unsupported',q,h,_error('multiday_service','Viaje fuera del día civil'))
    candidates=[]
    for out in outs:
        wo=h['walking_links'][out['to_stop_id']]['outbound']
        if out['departure_s']<bm or out['arrival_s']+wo['seconds']>ap-am: continue
        for back in backs:
            wr=h['walking_links'][back['from_stop_id']]['return']
            slack=back['departure_s']-ap-dur-wr['seconds']-bm
            if slack<0 or back['arrival_s']>deadline: continue
            total=back['arrival_s']-out['departure_s']+bm
            key=(total,wo['total_metres']+wr['total_metres'],-out['departure_s'],back['arrival_s'],
                 out['trip_id'],back['trip_id'],out['to_stop_id'],back['from_stop_id'])
            candidates.append((key,out,back,wo,wr,slack))
    if not candidates: return _base('no_feasible_journey',q,h,_error('no_pair_in_complete_direct_search','Sin pareja viable en paradas/red admitidas'))
    key,out,back,wo,wr,slack=min(candidates,key=lambda item:item[0])
    values=[bm,out['arrival_s']-out['departure_s'],wo['seconds'],ap-out['arrival_s']-wo['seconds'],
            dur,wr['seconds'],back['departure_s']-ap-dur-wr['seconds'],back['arrival_s']-back['departure_s']]
    kinds=['initial_wait','outbound_vehicle','destination_walk_outbound','pre_appointment_wait','appointment',
           'destination_walk_return','return_wait','return_vehicle']
    r=_base('ok',q,h); components=[];cursor=out['departure_s']-bm
    for kind,seconds in zip(kinds,values):
        refs=['USER'] if kind in ('initial_wait','appointment') else ['GTFS'] if kind.endswith('vehicle') else ['GTFS','OSM','HEALTH_REGISTRY','MODEL','USER','DERIVED']
        components.append({'kind':kind,'start_s':cursor,'end_s':cursor+seconds,'seconds':seconds,
            'basis':'user_input' if kind in ('initial_wait','appointment') else 'official_schedule' if kind.endswith('vehicle') else 'modelled_derived',
            'derivation':'end_s - start_s','source_refs':refs});cursor+=seconds
    assert cursor==back['arrival_s'] and sum(values)==key[0]
    r.update(itinerary={'outbound':{k:v for k,v in out.items() if not k.endswith('_s')},
        'return':{k:v for k,v in back.items() if not k.endswith('_s')},'total_s':key[0],
        'start_s':out['departure_s']-bm,'end_s':back['arrival_s'],'vehicle_span_s':back['arrival_s']-out['departure_s'],
        'origin_stop_id':out['from_stop_id'],'return_stop_id':back['to_stop_id'],'return_slack_s':slack,
        'alternatives_evaluated':len(candidates)},components=components,
        components_s={k+'_s':v for k,v in zip(kinds,values)},walking={'outbound':copy.deepcopy(wo),'return':copy.deepcopy(wr)})
    for sid,role,content,explanation in [
        ('USER','user_input',q,'Normalized request: appointment, duration and margins are hypothetical human inputs'),
        ('DERIVED','derived_metric',r['components_s'],'Derived scheduled intervals, not measured journey times')]:
        r['sources'].append({'source_id':sid,'source_role':role,'publisher':'GIPUZKOA360 request/calculation','url':None,
            'source_sha256':_digest(json.dumps(content,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()),
            'retrieved_date':None,'reference_period':q['date'],'transformation':explanation})
    return r


def compare_visits(requests):
    if type(requests) is not list or not 2<=len(requests)<=32:
        return {'schema_version':VERSION,'status':'error','results':[],'comparisons':[],
                'error':_error('invalid_request_count','Se requieren 2–32 peticiones')}
    if all(isinstance(q,dict) and q.get('snapshot_id',ID)==r4.DEFAULT_SNAPSHOT_ID for q in requests):
        return r4.compare_visits(requests)
    results=[plan_visit(q) for q in requests];pairs=[]
    for i,left in enumerate(results):
        for j in range(i+1,len(results)):
            right=results[j];a=left['normalized_request'];b=right['normalized_request']
            same=left['status']==right['status']=='ok' and all(a.get(k)==b.get(k) for k in
                ('snapshot_id','date','timezone','origin_id','destination_id','walking_profile_id'))
            changes=[];held=[]
            if a and b:
                for k in sorted(a.keys()|b.keys()):
                    if a.get(k)==b.get(k): held.append(k)
                    else: changes.append({'field':k,'left':a.get(k),'right':b.get(k)})
            pairs.append({'left_index':i,'right_index':j,'comparability':'comparable' if same else 'not_comparable',
                'requested_changes':changes,'held_constant':held,
                'total_difference_s':right['itinerary']['total_s']-left['itinerary']['total_s'] if same else None,
                'limitations':['Delta hipotético, no causalidad ni ahorro garantizado; escenarios/snapshots distintos no se comparan.']})
    return {'schema_version':VERSION,'status':'ok','results':results,'comparisons':pairs,'error':None}


def get_capabilities():
    snapshots=[]
    for s in r4.get_capabilities()['snapshots']:
        snapshots.append({'snapshot_id':s['snapshot_id'],'contract_version':'0.2.0','scenario_kind':'stop_only',
            'scope':r4.SCOPE,'destination_semantics':'stop_only','modelled_access':False,'entrance_verified':False,
            'origins':s['origins'],'destinations':s['destinations'],'validated_dates':s['coverage']['validated_dates'],
            'walking_profile_id':'stop_only'})
    try:
        h,_=_load()
        snapshots.append({'snapshot_id':ID,'contract_version':VERSION,'scenario_kind':'health_visit',
            'scope':r4.SCOPE,'destination_semantics':'official_centre_point_not_verified_entrance',
            'modelled_access':True,'entrance_verified':False,'origins':sorted(h['origins']),
            'destinations':[h['destination_id']],'validated_dates':[h['validated_date']],'walking_profile_id':PROFILE})
        error=None
    except (OSError,ValueError,KeyError,TypeError,RecursionError) as exc: error=_error('invalid_health_snapshot',str(exc))
    return {'schema_version':VERSION,'provider_id':'ir_y_volver_r5','snapshots':snapshots,'error':error}
