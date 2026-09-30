import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const contract=require('../../scripts/vnext_product/health_contract.js');
const evidence=JSON.parse(fs.readFileSync(new URL('../../resultados/vnext/r10/health_evidence.json',import.meta.url),'utf8'));
const payload=(key='main')=>({schema_version:'W3-HEALTH-QUERY-1',provider_pin:evidence.provider_pin,package_sha256:evidence.package_sha256,output:structuredClone(evidence.outputs[key])});
test('0.3.1 real pinned outputs and all five states validate',()=>{for(const key of Object.keys(evidence.outputs))contract.validate(payload(key),evidence);});
test('duplicate keys, oversized/deep JSON and nonfinite numbers reject before render',()=>{
  for(const text of ['{"a":1,"a":2}','{"a":1e999}','['.repeat(35)+'0'+']'.repeat(35),'"'+'x'.repeat(262144)+'"'])assert.throws(()=>contract.parse(text));
});
test('effective time, duration and default margins bind semantically',()=>{
  for(const [field,value] of [['appointment_time','09:30:59'],['duration_minutes',21],['arrival_margin_minutes',15]]){const p=payload();p.output.result.normalized_request[field]=value;assert.throws(()=>contract.validate(p,evidence));}
});
test('every rendered source is pinned and active/duplicate URLs reject',()=>{
  const active=payload();active.output.result.sources[0].url='javascript:void(0)';assert.throws(()=>contract.validate(active,evidence));
  const duplicate=payload();duplicate.output.result.sources.push(duplicate.output.result.sources[0]);assert.throws(()=>contract.validate(duplicate,evidence));
});
test('missing legs, mismatched intervals and total reject',()=>{
  for(const mutate of [r=>delete r.itinerary.return,r=>r.components[0].seconds++,r=>r.itinerary.total_s++]){const p=payload();mutate(p.output.result);assert.throws(()=>contract.validate(p,evidence));}
});
test('entrance verification and prior contract identity cannot be promoted',()=>{
  const p=payload();p.output.result.health_destination.entrance_verified=true;assert.throws(()=>contract.validate(p,evidence));
  const old=payload();old.output.result.schema_version='0.2.0';assert.throws(()=>contract.validate(old,evidence));
});
test('HTML strings remain data and legitimate unknown preserves observed error',()=>{
  const p=payload('date');p.output.result.error.message='<b>Fecha no validada</b>';const r=contract.validate(contract.parse(JSON.stringify(p)),evidence);assert.equal(r.result.error.message,'<b>Fecha no validada</b>');
});

test('model defaults cannot be relabelled as user input or duplicated',()=>{
  const p=payload();const v=p.output.result.parameter_provenance.find(p=>p.field==='boarding_margin_minutes');v.origin='human_explicit';v.source_ref='USER';assert.throws(()=>contract.validate(p,evidence));
  const duplicate=payload();duplicate.output.result.parameter_provenance.push(duplicate.output.result.parameter_provenance[0]);assert.throws(()=>contract.validate(duplicate,evidence));
});
