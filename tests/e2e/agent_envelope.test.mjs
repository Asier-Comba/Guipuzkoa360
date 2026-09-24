import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';

const root=path.resolve(import.meta.dirname,'../..');
const fixture=JSON.parse(fs.readFileSync(path.join(root,'tests/fixtures/synthetic_agent_result.json'),'utf8'));
const temp=()=>fs.mkdtempSync(path.join(os.tmpdir(),'g360-agent-'));
const envelope=()=>({run_id:'TEST-RUN-1',agent_version:'agent-test/1',question:fixture.question,tool_events:[{tool:'consultar_datos_test',arguments:{age_group:'65+'},output:{comparison:fixture.comparison,analysis:{total_units:4,matched_count:1,matched_unit_ids:['TEST_C'],older_population_total:5790},metrics:fixture.metrics,sources:fixture.sources,input_files:[{path:'fixture',sha256:'test',rows:4}]}}],result:{...structuredClone(fixture),analysis:{total_units:4,matched_count:1,matched_unit_ids:['TEST_C'],older_population_total:5790}}});
function adapt(data){const dir=temp(),input=path.join(dir,'in.json'),outputFile=path.join(dir,'out.json');fs.writeFileSync(input,JSON.stringify(data));const p=spawnSync(process.execPath,[path.join(root,'scripts/adapt_work2_envelope.mjs'),input,outputFile],{encoding:'utf8'});return {dir,outputFile,...p}}

test('adapta solo una ejecución con salida observada de tool',()=>{const x=adapt(envelope());assert.equal(x.status,0,x.stderr);const d=JSON.parse(fs.readFileSync(x.outputFile,'utf8'));assert.equal(d.trace.execution_mode,'agent');assert.equal(d.trace.question_id,'TEST-RUN-1');assert.match(d.trace.result_ref,/^TOOL-/);assert.equal(d.trace.tool_calls[0].output_ref,d.trace.result_ref);fs.rmSync(x.dir,{recursive:true,force:true})});
test('rechaza cifra narrativa que no coincide con tool',()=>{const e=envelope();e.result.comparison[0].population++;const x=adapt(e);assert.notEqual(x.status,0);assert.match(x.stderr,/comparison/);fs.rmSync(x.dir,{recursive:true,force:true})});
test('rechaza evento sin salida observada',()=>{const e=envelope();delete e.tool_events[0].output;const x=adapt(e);assert.notEqual(x.status,0);assert.match(x.stderr,/salida observada/);fs.rmSync(x.dir,{recursive:true,force:true})});
