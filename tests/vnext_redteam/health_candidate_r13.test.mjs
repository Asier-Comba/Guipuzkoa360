import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRequire} from 'node:module';
const contract=createRequire(import.meta.url)('../../scripts/vnext_product/health_contract.js');
const read=path=>JSON.parse(fs.readFileSync(new URL(path,import.meta.url),'utf8'));
const evidence=read('../../resultados/vnext/r13/health_evidence.json');
const example=read('../../resultados/vnext/r13/example_health_query.json');
test('R13 exact accepted package imports independently calculated variation, not agent output',()=>{
  assert.equal(contract.validate(example,evidence).result.itinerary.total_s,8591);
  assert.equal(evidence.classification,'OFFLINE_W2_EXACT_PACKAGE_R13_NOT_AGENT');
  assert.equal(evidence.portal_health_status,'BLOCKED_REQUEST_BINDING_R13_M04');
});
test('R12 identity is rejected by current patch3 viewer',()=>{
  const old=read('../../resultados/vnext/r12/example_health_query.json');
  assert.throws(()=>contract.validate(old,evidence),/Identidad/);
});
test('actual portal error envelope cannot be rendered as an imported health journey',()=>{
  const smoke=read('../../resultados/vnext/r13/PORTAL_SMOKE_R13.json');
  const fake=structuredClone(example);fake.output.result=smoke.turns[3].tool_outputs[0];
  assert.throws(()=>contract.validate(fake,evidence));
});
