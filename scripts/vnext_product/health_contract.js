/* Explicit W1 0.3.1 import contract; compatibility never proves provenance. */
const HealthContract=(()=>{
  'use strict';
  const MAX_FILE_BYTES=262144;
  const fail=m=>{throw Error(m);};
  const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
  const exact=(x,keys)=>{if(!object(x)||Object.keys(x).length!==keys.length||keys.some(k=>!Object.hasOwn(x,k)))fail('Campos ausentes o inesperados.');};
  function parse(text){
    if(new TextEncoder().encode(text).length>MAX_FILE_BYTES)fail('Archivo demasiado grande.');
    let i=0;const ws=()=>{while(/\s/.test(text[i]||'')&&i<text.length)i++;};
    const string=()=>{const start=i++;while(i<text.length){if(text[i]==='\\'){i+=2;continue;}if(text[i++]==='"'){const v=JSON.parse(text.slice(start,i));if(v.length>2000)fail('Texto excesivo.');return v;}}fail('Texto JSON incompleto.');};
    const value=(depth=0)=>{
      if(depth>30)fail('JSON demasiado profundo.');ws();const c=text[i];
      if(c==='"')return string();
      if(c==='{'){i++;const out=Object.create(null);let count=0;ws();if(text[i]==='}'){i++;return out;}while(true){ws();if(text[i]!=='"')fail('Clave JSON inválida.');const key=string();if(Object.hasOwn(out,key)||++count>100)fail('Clave duplicada u objeto excesivo.');ws();if(text[i++]!==':')fail('JSON inválido.');out[key]=value(depth+1);ws();const next=text[i++];if(next==='}')return out;if(next!==',')fail('JSON inválido.');}}
      if(c==='['){i++;const out=[];ws();if(text[i]===']'){i++;return out;}while(true){if(out.length>=1000)fail('Lista excesiva.');out.push(value(depth+1));ws();const next=text[i++];if(next===']')return out;if(next!==',')fail('JSON inválido.');}}
      const match=text.slice(i).match(/^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/);if(!match)fail('JSON inválido.');i+=match[0].length;const v=JSON.parse(match[0]);if(typeof v==='number'&&(!Number.isFinite(v)||Math.abs(v)>Number.MAX_SAFE_INTEGER))fail('Número fuera de rango.');return v;
    };const result=value();ws();if(i!==text.length)fail('Contenido posterior al JSON.');return result;
  }
  function schema(value,s,root=s){
    if(s.$ref){if(!s.$ref.startsWith('#/'))fail('Referencia de schema externa.');const ref=s.$ref.slice(2).split('/').reduce((a,k)=>a[k.replace(/~1/g,'/').replace(/~0/g,'~')],root);schema(value,ref,root);}
    if(s.const!==undefined&&JSON.stringify(value)!==JSON.stringify(s.const))fail('Valor fuera del contrato.');
    if(s.enum&&!s.enum.some(v=>JSON.stringify(v)===JSON.stringify(value)))fail('Valor fuera del catálogo.');
    const matches=branch=>{try{schema(value,branch,root);return true;}catch{return false;}};
    if(s.anyOf&&!s.anyOf.some(matches))fail('Tipo o estructura incompatible.');
    if(s.allOf)s.allOf.forEach(branch=>schema(value,branch,root));
    if(s.if){const branch=matches(s.if)?s.then:s.else;if(branch)schema(value,branch,root);}
    if(s.type){const types=Array.isArray(s.type)?s.type:[s.type];const good=types.some(t=>t==='null'?value===null:t==='object'?object(value):t==='array'?Array.isArray(value):t==='integer'?Number.isSafeInteger(value):t==='number'?typeof value==='number'&&Number.isFinite(value):typeof value===t);if(!good)fail('Tipo incorrecto.');}
    if(typeof value==='number'&&((s.minimum!==undefined&&value<s.minimum)||(s.maximum!==undefined&&value>s.maximum)))fail('Número fuera de rango.');
    if(typeof value==='string'&&((s.minLength!==undefined&&value.length<s.minLength)||(s.maxLength!==undefined&&value.length>s.maxLength)||(s.pattern&&!new RegExp(s.pattern).test(value))))fail('Texto fuera del contrato.');
    if(Array.isArray(value)){if((s.minItems!==undefined&&value.length<s.minItems)||(s.maxItems!==undefined&&value.length>s.maxItems))fail('Lista fuera del contrato.');if(s.items)value.forEach(v=>schema(v,s.items,root));}
    if(object(value)){if(s.required?.some(k=>!Object.hasOwn(value,k)))fail('Faltan campos requeridos.');for(const [k,v] of Object.entries(value)){if(s.properties?.[k])schema(v,s.properties[k],root);else if(s.additionalProperties===false)fail('Campo inesperado.');else if(object(s.additionalProperties))schema(v,s.additionalProperties,root);}}
  }
  const clock=x=>{if(typeof x!=='string'||!/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(x))fail('Hora inválida.');return x.length===5?x+':00':x;};
  function validate(payload,evidence){
    exact(payload,['schema_version','provider_pin','package_sha256','output']);
    if(payload.schema_version!=='W3-HEALTH-QUERY-1'||payload.provider_pin!==evidence.provider_pin||payload.package_sha256!==evidence.package_sha256)fail('Identidad de paquete incompatible.');
    const item=payload.output;exact(item,['request','result']);const q=item.request,r=item.result;
    const allowed=['origin_id','destination_id','date','appointment_time','duration_minutes','arrival_margin_minutes','boarding_margin_minutes','walking_profile_id','snapshot_id','return_deadline'];
    if(!object(q)||Object.keys(q).some(k=>!allowed.includes(k))||allowed.slice(0,5).some(k=>!Object.hasOwn(q,k)))fail('Solicitud incompatible.');
    for(const k of ['origin_id','destination_id','date'])if(typeof q[k]!=='string'||!q[k]||q[k].length>120)fail('Solicitud inválida.');
    clock(q.appointment_time);if(q.return_deadline!==undefined&&q.return_deadline!==null)clock(q.return_deadline);
    for(const k of ['duration_minutes','arrival_margin_minutes','boarding_margin_minutes'])if(Object.hasOwn(q,k)&&(!Number.isSafeInteger(q[k])||q[k]<0||q[k]>10000))fail('Parámetro numérico inválido.');
    schema(r,evidence.result_schema);
    if(r.schema_version!=='0.3.1'||r.scenario_kind!=='health_visit')fail('Solo contrato sanitario 0.3.1.');
    const n=r.normalized_request;
    if(n){for(const [k,v] of Object.entries(n)){const expected=Object.hasOwn(q,k)?q[k]:evidence.catalog.defaults[k];if(k==='appointment_time'){if(v!==clock(q[k]))fail('Hora efectiva distinta.');}else if(k==='return_deadline'){if(v!==(expected===null?null:clock(expected)))fail('Deadline distinto.');}else if(v!==expected)fail(k+' efectivo distinto.');}}
    if(n){const fields=new Set();for(const p of r.parameter_provenance){if(fields.has(p.field)||!Object.hasOwn(n,p.field)||JSON.stringify(p.value)!==JSON.stringify(n[p.field]))fail('Procedencia de parámetro incoherente.');fields.add(p.field);const explicit=Object.hasOwn(q,p.field);if(p.origin!==(explicit?'human_explicit':'model_default')||p.source_ref!==(explicit?'USER':'MODEL_DEFAULTS'))fail('Default atribuido al usuario.');}if(fields.size!==Object.keys(n).length)fail('Procedencia incompleta.');}
    const references=new Map(evidence.outputs.main.result.sources.map(s=>[s.source_id,s]));const seen=new Set();
    for(const source of r.sources){if(seen.has(source.source_id))fail('Fuente duplicada.');seen.add(source.source_id);const ref=references.get(source.source_id);if(!ref)fail('Fuente no permitida.');for(const k of ['url','source_role','publisher'])if(source[k]!==ref[k])fail('Fuente distinta del catálogo.');if(!['USER','MODEL_DEFAULTS','DERIVED'].includes(source.source_id)&&source.source_sha256!==ref.source_sha256)fail('Hash de fuente distinto.');if(source.url&&new URL(source.url).protocol!=='https:')fail('URL activa.');}
    if(r.status==='ok'){
      if(r.snapshot_id!==evidence.catalog.snapshot_id||!n)fail('Snapshot/contexto incompleto.');
      let cursor=r.itinerary.start_s,sum=0;for(const c of r.components){if(c.start_s!==cursor||c.end_s-c.start_s!==c.seconds||r.components_s[c.kind+'_s']!==c.seconds||c.source_refs.some(id=>!seen.has(id)))fail('Intervalos o fuentes incoherentes.');cursor=c.end_s;sum+=c.seconds;}
      if(cursor!==r.itinerary.end_s||sum!==r.itinerary.total_s||r.components_s.appointment_s!==n.duration_minutes*60)fail('Total o duración incoherentes.');
      if(r.walking.outbound.seconds!==r.components_s.destination_walk_outbound_s||r.walking.return.seconds!==r.components_s.destination_walk_return_s)fail('Paseo y componentes distintos.');
      if(r.health_destination.entrance_verified!==false||r.health_destination.modelled_access!==true)fail('Alcance sanitario alterado.');
    }
    return item;
  }
  return {parse,validate,schema,MAX_FILE_BYTES};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=HealthContract;
