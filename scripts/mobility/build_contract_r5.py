"""Generate explicit closed 0.3.0 contracts without touching frozen versions."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'prototypes/ir_y_volver/contracts/v0.3.0'
S={'type':'string','minLength':1}
N={'type':'integer','minimum':0}
B={'type':'boolean'}
HASH={'type':'string','pattern':'^[0-9a-f]{64}$'}
CLOCK={'type':'string','pattern':'^([01][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$'}


def obj(props,required=None):
    return {'type':'object','properties':props,'required':list(props) if required is None else required,'additionalProperties':False}


def arr(items): return {'type':'array','items':items}
def ref(name): return {'$ref':'#/$defs/'+name}
def nullable(spec): return {'anyOf':[spec,{'type':'null'}]}
def const(value): return {'const':value}


def build():
    d={}
    request={'origin_id':S,'destination_id':S,'date':{'type':'string','pattern':'^[0-9]{4}-[0-9]{2}-[0-9]{2}$'},
             'appointment_time':CLOCK,'duration_minutes':{'type':'integer','minimum':1,'maximum':720},
             'arrival_margin_minutes':{'type':'integer','minimum':0,'maximum':240},
             'boarding_margin_minutes':{'type':'integer','minimum':0,'maximum':120},
             'walking_profile_id':S,'snapshot_id':S,'return_deadline':nullable(CLOCK)}
    d['NormalizedRequest']=obj({**request,'timezone':const('Europe/Madrid')})
    d['ErrorEnvelope']=obj({'code':S,'message':S})
    d['SourceReference']=obj({'source_id':S,'source_role':{'enum':['official_schedule','official_health_registry','official_health_page','open_network','model_parameter','user_input','derived_metric']},
        'publisher':S,'url':nullable({'type':'string','pattern':'^https://'}),'source_sha256':HASH,
        'retrieved_date':nullable(S),'reference_period':S,'transformation':S})
    leg={k:S for k in ['trip_id','route_id','service_id','from_stop_id','to_stop_id']}
    leg.update({k:N for k in ['from_stop_sequence','to_stop_sequence']})
    leg.update({k:CLOCK for k in ['departure_time','arrival_time']})
    leg.update({k:const(0) for k in ['pickup_type','drop_off_type']})
    leg.update({k:{'enum':[0,1]} for k in ['from_timepoint','to_timepoint']})
    d['Leg']=obj(leg)
    d['Itinerary']=obj({'outbound':ref('Leg'),'return':ref('Leg'),**{k:N for k in ['total_s','start_s','end_s','vehicle_span_s','return_slack_s','alternatives_evaluated']},
                        'origin_stop_id':S,'return_stop_id':S})
    kinds=['initial_wait','outbound_vehicle','destination_walk_outbound','pre_appointment_wait','appointment','destination_walk_return','return_wait','return_vehicle']
    d['TimelineComponent']=obj({'kind':{'enum':kinds},'start_s':N,'end_s':N,'seconds':N,
        'basis':{'enum':['user_input','official_schedule','modelled_derived']},'derivation':S,'source_refs':arr(S)})
    coordinate={'type':'array','prefixItems':[{'type':'number','minimum':-90,'maximum':90},{'type':'number','minimum':-180,'maximum':180}],'minItems':2,'maxItems':2}
    tags=obj({k:S for k in ['highway','area','foot','access','oneway','oneway:foot','foot:forward','foot:backward','tunnel','bridge','layer','indoor','crossing','sidewalk','incline']},[])
    d['WalkingLinkEvidence']=obj({'start_coordinates':coordinate,'end_coordinates':coordinate,
        'start_node_id':S,'end_node_id':S,'connector_metres':{'type':'array','items':{'type':'number','minimum':0,'maximum':100},'minItems':2,'maxItems':2},
        'connector_threshold_m':const(100),'network_sha256':HASH,'builder_version':S,
        'walking_profile_id':const('poc_reference_50m_min_plus_120s'),'entrance_verified':const(False),'modelled_access':const(True),
        'status':const('ok'),'reason':{'type':'null'},'node_ids':arr(S),'way_ids':arr(S),
        'network_metres':{'type':'number','minimum':0},'total_metres':{'type':'number','minimum':0},
        'seconds':{'type':'integer','minimum':120},'geometry':arr(coordinate),'way_tags':arr(tags),'source_refs':arr(S)})
    d['HealthDestinationEvidence']=obj({'centre_id':S,'name':S,'centre_identity':{'enum':['CONFIRMED','CONFLICTED','UNKNOWN']},
        'centre_anchor':{'enum':['CONFIRMED_OFFICIAL_POINT','DERIVED_BUILDING_POINT','UNKNOWN']},
        'anchor_kind':{'enum':['official_centre_point','derived_building_reference_point']},'anchor_coordinates':coordinate,
        'crs':const('EPSG:4326'),'address':S,'address_conflict':{'enum':['same_entity_same_site','same_entity_different_service_address','historical_address','conflicting_current_sources','unresolved']},
        'human_review_required':B,'modelled_network_access':{'enum':['PASS','FAIL','UNKNOWN']},
        'entrance_verification':const('NOT_VERIFIED'),'entrance_verified':const(False),'modelled_access':const(True),
        'door_to_door':const('UNAVAILABLE'),'source_refs':arr(S),'wording':S})
    d['SnapshotCapability']=obj({'snapshot_id':S,'contract_version':{'enum':['0.2.0','0.3.0']},
        'scenario_kind':{'enum':['stop_only','health_visit']},'scope':const('origin_stop_presence_to_return_stop_arrival'),
        'destination_semantics':{'enum':['stop_only','official_centre_point_not_verified_entrance']},
        'modelled_access':B,'entrance_verified':const(False),'origins':arr(S),'destinations':arr(S),'validated_dates':arr(S),'walking_profile_id':S})
    scalar={'type':['string','integer','null']}
    d['ComparisonPair']=obj({'left_index':N,'right_index':N,'comparability':{'enum':['comparable','not_comparable']},
        'requested_changes':arr(obj({'field':{'enum':list(d['NormalizedRequest']['properties'])},'left':scalar,'right':scalar})),
        'held_constant':arr({'enum':list(d['NormalizedRequest']['properties'])}),
        'total_difference_s':nullable({'type':'integer'}),'limitations':arr(S)})
    result=obj({'schema_version':const('0.3.0'),'normalized_request':nullable(ref('NormalizedRequest')),
        'status':{'enum':['ok','no_feasible_journey','unknown','unsupported','error']},'scenario_kind':const('health_visit'),
        'time_basis':const('scheduled'),'scope':const('origin_stop_presence_to_return_stop_arrival'),'snapshot_id':S,
        'itinerary':nullable(ref('Itinerary')),'components_s':nullable(obj({k+'_s':N for k in kinds})),
        'components':nullable(arr(ref('TimelineComponent'))),'walking':nullable(obj({'outbound':ref('WalkingLinkEvidence'),'return':ref('WalkingLinkEvidence')})),
        'health_destination':nullable(ref('HealthDestinationEvidence')),'sources':arr(ref('SourceReference')),
        'limitations':arr(S),'assumptions':arr(S),'error':nullable(ref('ErrorEnvelope'))})
    result['allOf']=[{'if':{'properties':{'status':const('ok')}},'then':{'properties':{k:{'type':t} for k,t in [('itinerary','object'),('components_s','object'),('components','array'),('walking','object'),('health_destination','object')]}}}]
    d['HealthResult']=result
    # Frozen R4 result is an explicitly versioned compatibility branch, not a 0.3 health structure.
    old=json.loads((DEST.parent/'v0.2.0/result.schema.json').read_bytes())
    old.pop('$id',None);old.pop('$schema',None)
    d['LegacyR4Result']=old
    schemas={'request':obj(request,['origin_id','destination_id','date','appointment_time','duration_minutes']),
        'result':result,'capabilities':obj({'schema_version':const('0.3.0'),'provider_id':const('ir_y_volver_r5'),
            'snapshots':arr(ref('SnapshotCapability')),'error':nullable(ref('ErrorEnvelope'))}),
        'comparison':obj({'schema_version':const('0.3.0'),'status':{'enum':['ok','error']},
            'results':arr({'anyOf':[ref('HealthResult'),ref('LegacyR4Result')]}),'comparisons':arr(ref('ComparisonPair')),'error':nullable(ref('ErrorEnvelope'))})}
    DEST.mkdir(parents=True,exist_ok=True)
    for name,schema in schemas.items():
        # Independent copies avoid recursive Python objects when adding definitions to root.
        data=json.loads(json.dumps(schema));data.update({'$schema':'https://json-schema.org/draft/2020-12/schema','$defs':d})
        (DEST/(name+'.schema.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__': build()
