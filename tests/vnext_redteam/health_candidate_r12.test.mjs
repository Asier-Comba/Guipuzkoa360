import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const contract=require('../../scripts/vnext_product/health_contract.js');
const evidence=JSON.parse(fs.readFileSync(new URL('../../resultados/vnext/r12/health_evidence.json',import.meta.url),'utf8'));
const example=JSON.parse(fs.readFileSync(new URL('../../resultados/vnext/r12/example_health_query.json',import.meta.url),'utf8'));
test('R12 exact W2 evidence accepts current import and retains conditional arithmetic',()=>{
  const actual=contract.validate(example,evidence);
  assert.equal(actual.result.itinerary.total_s,8591);
  assert.equal(evidence.outputs.time.result.itinerary.total_s-evidence.outputs.main.result.itinerary.total_s,-2100);
  assert.equal(evidence.classification,'OFFLINE_W2_EXACT_PACKAGE_R12_NOT_AGENT');
});
test('historical producer-only identity cannot be silently imported as current W2 package',()=>{
  const old=structuredClone(example);old.package_sha256=evidence.producer_package_sha256;
  assert.throws(()=>contract.validate(old,evidence));
});
