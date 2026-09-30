/* Offline W1 viewer input contract. Schema compatibility is not provenance. */
const ImportContract = (() => {
  'use strict';
  const reqKeys = new Set(['origin_id','destination_id','date','appointment_time','duration_minutes','arrival_margin_minutes','boarding_margin_minutes','walking_profile_id','snapshot_id']);
  const required = ['origin_id','destination_id','date','appointment_time','duration_minutes'];
  const resultKeys = ['schema_version','normalized_request','status','time_basis','scope','snapshot_id','itinerary','components_s','sources','assumptions','limitations','error'];
  const componentKeys = ['origin_access_outbound_s','outbound_vehicle_s','destination_walk_outbound_s','pre_appointment_wait_s','appointment_s','destination_walk_return_s','return_wait_s','return_vehicle_s','origin_access_return_s'];
  const legKeys = ['trip_id','route_id','service_id','from_stop_id','to_stop_id','from_stop_sequence','to_stop_sequence','departure_time','arrival_time','pickup_type','drop_off_type','from_timepoint','to_timepoint'];
  const normKeys = ['origin_id','destination_id','date','appointment_time','duration_minutes','arrival_margin_minutes','boarding_margin_minutes','walking_profile_id','snapshot_id','timezone'];
  const own = (x,k) => Object.prototype.hasOwnProperty.call(x,k);
  const obj = x => x !== null && typeof x === 'object' && !Array.isArray(x);
  const fail = reason => { throw new Error(reason); };
  const keys = (x, allowed, label) => {
    if (!obj(x) || Object.keys(x).length !== allowed.length || !allowed.every(k=>own(x,k))) fail(label+' tiene campos ausentes o inesperados.');
  };
  const short = (x,label,max=500) => {
    if(typeof x!=='string'||!x||x.length>max||/[\u0000-\u001f\u007f]/.test(x)) fail(label+' debe ser texto acotado.');
  };
  const integer = (x,min,max,label) => {
    if(!Number.isSafeInteger(x)||x<min||x>max) fail(label+' fuera de rango o no entero seguro.');
  };
  const finiteTree = (x,depth=0) => {
    if(depth>16) fail('JSON demasiado profundo.');
    if(typeof x==='number'&&!Number.isFinite(x)) fail('Número no finito.');
    if(Array.isArray(x)){if(x.length>100)fail('Lista excesiva.');x.forEach(v=>finiteTree(v,depth+1));}
    else if(obj(x)){if(Object.keys(x).length>100)fail('Objeto excesivo.');Object.values(x).forEach(v=>finiteTree(v,depth+1));}
  };
  const clock = (x,label) => {
    if(typeof x!=='string'||!/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(x)) fail(label+' debe ser HH:MM[:SS].');
    return x.length===5?x+':00':x;
  };
  const textList = (x,label) => {
    if(!Array.isArray(x)||x.length>20) fail(label+' debe ser una lista acotada.');
    x.forEach(v=>short(v,label));
  };
  const verifySource = (sources,reference,status) => {
    if(!Array.isArray(sources)||sources.length>1) fail('Fuentes duplicadas o excesivas.');
    if(sources.length===0){if(!['unknown','error'].includes(status))fail('Falta fuente del resultado.');return;}
    const source=sources[0];
    keys(source,Object.keys(reference),'Fuente');
    for(const k of Object.keys(reference)) if(source[k]!==reference[k]) fail('La fuente no coincide con el catálogo fijado.');
    for(const k of ['url','index_url']) {
      let parsed;try{parsed=new URL(source[k]);}catch{fail('URL de fuente inválida.');}
      if(parsed.protocol!=='https:'||parsed.hostname!=='opendata.euskadi.eus'||source[k]!==reference[k])fail('URL de fuente no permitida.');
    }
  };
  const verifyLeg = (leg,label) => {
    keys(leg,legKeys,label);
    for(const k of ['trip_id','route_id','service_id','from_stop_id','to_stop_id'])short(leg[k],label+'.'+k,120);
    for(const k of ['from_stop_sequence','to_stop_sequence'])integer(leg[k],0,10000,label+'.'+k);
    for(const k of ['pickup_type','drop_off_type','from_timepoint','to_timepoint'])integer(leg[k],0,3,label+'.'+k);
    clock(leg.departure_time,label+'.departure_time');clock(leg.arrival_time,label+'.arrival_time');
  };
  function validate(payload,evidence){
    finiteTree(payload);
    keys(payload,['schema_version','classification','provider_head','snapshot_sha256','output'],'Archivo');
    if(payload.schema_version!=='W3-PROVIDER-QUERY-1'||payload.classification!=='OFFLINE_DETERMINISTIC_PROVIDER_OUTPUT'||payload.provider_head!==evidence.provider_head||payload.snapshot_sha256!==evidence.snapshot_sha256)fail('El archivo no corresponde al proveedor y snapshot fijados.');
    const item=payload.output;
    keys(item,['id','title','source_case_id','changed_request_fields','request','result'],'Salida');
    if(item.id!=='local_query'||item.source_case_id!==null||item.changed_request_fields!==null)fail('Metadatos de salida no permitidos.');
    const q=item.request,r=item.result;
    if(!obj(q)||Object.keys(q).length>reqKeys.size||Object.keys(q).some(k=>!reqKeys.has(k))||required.some(k=>!own(q,k)))fail('Solicitud con campos ausentes o inesperados.');
    for(const k of ['origin_id','destination_id'])short(q[k],k,120);
    if(typeof q.date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(q.date)||Number.isNaN(Date.parse(q.date+'T00:00:00Z')))fail('Fecha inválida.');
    const appointment=clock(q.appointment_time,'Cita');
    integer(q.duration_minutes,0,10000,'Duración');
    for(const k of ['arrival_margin_minutes','boarding_margin_minutes'])if(own(q,k))integer(q[k],0,10000,k);
    for(const k of ['walking_profile_id','snapshot_id'])if(own(q,k))short(q[k],k,120);
    keys(r,resultKeys,'Resultado');
    if(r.schema_version!=='0.1.0'||!['ok','no_feasible_journey','unsupported','unknown','error'].includes(r.status)||r.time_basis!=='scheduled'||r.scope!=='stop_to_stop_with_destination_walk')fail('Contrato de resultado incompatible.');
    const pinnedId=evidence.outputs[0].result.snapshot_id;
    const requestedId=own(q,'snapshot_id')?q.snapshot_id:pinnedId;
    if(r.snapshot_id!==requestedId)fail('Snapshot efectivo distinto de la solicitud.');
    if(requestedId!==pinnedId && !(r.status==='unknown'&&r.error?.code==='snapshot_not_found'&&r.normalized_request===null))fail('Snapshot distinto del fijado.');
    const n=r.normalized_request;
    if(n===null){if(!['unknown','error'].includes(r.status))fail('Falta solicitud normalizada.');}
    else{
      keys(n,normKeys,'Solicitud normalizada');
      const defaults=evidence.outputs[0].result.normalized_request;
      for(const k of ['origin_id','destination_id','date','duration_minutes'])if(n[k]!==q[k])fail(k+' efectivo distinto.');
      if(n.appointment_time!==appointment)fail('Cita efectiva distinta.');
      for(const k of ['arrival_margin_minutes','boarding_margin_minutes','walking_profile_id'])if(n[k]!== (own(q,k)?q[k]:defaults[k]))fail(k+' efectivo distinto.');
      if(n.snapshot_id!==requestedId||n.timezone!=='Europe/Madrid')fail('Snapshot o zona efectivos distintos.');
    }
    textList(r.assumptions,'Supuestos');textList(r.limitations,'Límites');
    verifySource(r.sources,evidence.outputs[0].result.sources[0],r.status);
    if(r.status==='ok'){
      if(n===null||requestedId!==pinnedId||r.error!==null)fail('Resultado viable sin contexto completo.');
      keys(r.itinerary,['outbound','return','total_s','alternatives_evaluated'],'Itinerario');
      verifyLeg(r.itinerary.outbound,'Ida');verifyLeg(r.itinerary.return,'Vuelta');
      integer(r.itinerary.total_s,0,864000,'Total');integer(r.itinerary.alternatives_evaluated,0,1000000,'Alternativas');
      keys(r.components_s,componentKeys,'Componentes');
      let sum=0;for(const k of componentKeys){integer(r.components_s[k],0,864000,k);sum+=r.components_s[k];}
      if(sum!==r.itinerary.total_s)fail('Componentes y total no concuerdan.');
    }else{
      if(r.itinerary!==null||r.components_s!==null)fail('Estado sin viaje contiene cifras.');
      keys(r.error,['code','message'],'Error');short(r.error.code,'Código de error',100);short(r.error.message,'Mensaje de error',500);
      if(r.status==='no_feasible_journey'&&n===null)fail('Búsqueda no viable sin solicitud normalizada.');
    }
    return item;
  }
  return {validate,MAX_FILE_BYTES:262144};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=ImportContract;
