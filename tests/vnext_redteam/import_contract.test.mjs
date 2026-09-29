import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const contract=require('../../scripts/vnext_product/import_contract.js');
const evidence=JSON.parse(readFileSync(new URL('../../resultados/vnext/provider_evidence.json',import.meta.url),'utf8'));
const clone=x=>JSON.parse(JSON.stringify(x));
function base(){
  return {schema_version:'W3-PROVIDER-QUERY-1',classification:'OFFLINE_DETERMINISTIC_PROVIDER_OUTPUT',
    provider_head:evidence.provider_head,snapshot_sha256:evidence.snapshot_sha256,
    output:{id:'local_query',title:'Consulta local importada',source_case_id:null,changed_request_fields:null,
      request:clone(evidence.outputs[0].request),result:clone(evidence.outputs[0].result)}};
}
function rejects(mutator,label){const x=base();mutator(x);assert.throws(()=>contract.validate(x,evidence),label);}

test('compatible result is accepted but not authenticated by the validator',()=>{
  assert.equal(contract.validate(base(),evidence).result.itinerary.total_s,8411);
});
test('every rendered source must match the pinned catalog',()=>{
  rejects(p=>{const s=p.output.result.sources[0];p.output.result.sources=[{...s,url:'javascript:void(0)'},s];},/Fuentes duplicadas/);
  rejects(p=>{p.output.result.sources[0].url='data:text/html,x';},/fuente/i);
  rejects(p=>{p.output.result.sources[0].publisher='Not the catalog';},/fuente/i);
  rejects(p=>{p.output.result.sources=[];},/Falta fuente/);
});
test('effective time, margins, profile and identity must equal the request',()=>{
  rejects(p=>{p.output.result.normalized_request.appointment_time='09:30:59';},/Cita efectiva/);
  rejects(p=>{p.output.request.arrival_margin_minutes=15;},/arrival_margin_minutes/);
  rejects(p=>{p.output.request.boarding_margin_minutes=8;},/boarding_margin_minutes/);
  rejects(p=>{p.output.request.walking_profile_id='other';},/walking_profile_id/);
  rejects(p=>{p.output.request.snapshot_id='other';},/Snapshot/);
  rejects(p=>{p.output.request.origin_id='segura_herriko_plaza_stops';},/origin_id/);
  rejects(p=>{p.output.request.destination_id='other';},/destination_id/);
  rejects(p=>{p.output.request.duration_minutes=31;},/duration_minutes/);
});
test('ok requires complete legs, components and safe totals',()=>{
  rejects(p=>{delete p.output.result.itinerary.return;},/Itinerario/);
  rejects(p=>{p.output.result.itinerary.total_s=Number.MAX_SAFE_INTEGER+1;},/Total/);
  rejects(p=>{delete p.output.result.components_s.return_vehicle_s;},/Componentes/);
  rejects(p=>{p.output.result.components_s.appointment_s=1;},/concuerdan/);
});
test('valid unknown without normalized request preserves observed cause',()=>{
  const p=base();p.output.request.snapshot_id='missing-snapshot';
  const r=p.output.result;r.status='unknown';r.snapshot_id='missing-snapshot';r.normalized_request=null;
  r.itinerary=null;r.components_s=null;r.sources=[];
  r.error={code:'snapshot_not_found',message:'El snapshot solicitado no está disponible'};
  assert.equal(contract.validate(p,evidence).result.error.code,'snapshot_not_found');
});
test('non-viable and error states cannot carry invented itinerary',()=>{
  rejects(p=>{p.output.result.status='unknown';p.output.result.error={code:'date_not_validated',message:'Sin validación'};},/Estado sin viaje/);
  rejects(p=>{p.output.result.status='ok';p.output.result.error={code:'bad',message:'bad'};},/Resultado viable/);
});
test('unknown keys, types, nonfinite numbers, huge lists and active text are rejected',()=>{
  rejects(p=>{p.output.extra=true;},/Salida/);
  rejects(p=>{p.output.request.duration_minutes='30';},/Duración/);
  rejects(p=>{p.output.result.itinerary.total_s=Infinity;},/Número no finito/);
  rejects(p=>{p.output.result.assumptions=Array(101).fill('x');},/Lista excesiva/);
  rejects(p=>{p.output.result.assumptions=['<img src=x onerror=alert(1)>'];p.output.result.sources[0].url='javascript:alert(1)';},/fuente/i);
});
