import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import vm from 'node:vm';

const root=path.resolve(import.meta.dirname,'../..');
const fixture=JSON.parse(fs.readFileSync(path.join(root,'tests/fixtures/synthetic_agent_result.json'),'utf8'));
const runner=path.join(root,'scripts/build_results.mjs');
function run(data){const dir=fs.mkdtempSync(path.join(os.tmpdir(),'g360-e2e-'));const input=path.join(dir,'result.json'),out=path.join(dir,'out');fs.writeFileSync(input,JSON.stringify(data));const p=spawnSync(process.execPath,[runner,input,out],{encoding:'utf8'});return {dir,out,...p};}
function asReal(d){d.data_mode='real';d.parameters.older_share_threshold_pct=25;d.analysis={total_units:4,matched_count:0,matched_unit_ids:[],older_population_total:5790};return d}

test('pregunta → herramienta → dato → resultado → visualización → fuente',()=>{
  const x=run(fixture);assert.equal(x.status,0,x.stderr);
  const html=fs.readFileSync(path.join(x.out,'demo.html'),'utf8');
  for(const token of [fixture.question,fixture.trace.question_id,fixture.trace.tool_calls[0].tool,fixture.trace.result_ref,...fixture.trace.data_refs,'DATOS SINTÉTICOS DE DESARROLLO','Cómo se calculó','OBSERVADO','ESCENARIO HIPOTÉTICO']) assert.ok(html.includes(token),`Falta ${token}`);
  assert.ok(fs.existsSync(path.join(x.out,'informe_principal.html')));
  assert.ok(fs.existsSync(path.join(x.out,'scenario_comparison.html')));
  for(const file of ['demo.html','informe_principal.html','scenario_comparison.html']){
    const page=fs.readFileSync(path.join(x.out,file),'utf8');
    const start=page.indexOf('<script>')+8,end=page.indexOf('</script>',start);
    assert.ok(start>7&&end>start,`${file}: script ausente`);
    new vm.Script(page.slice(start,end),{filename:file});
  }
  fs.rmSync(x.dir,{recursive:true,force:true});
});
test('falla si una fuente no se puede rastrear',()=>{const d=structuredClone(fixture);d.comparison[0].source_ids=['FUENTE_INEXISTENTE'];const x=run(d);assert.notEqual(x.status,0);assert.match(x.stderr,/fuente inexistente/);fs.rmSync(x.dir,{recursive:true,force:true});});
test('falla si el resultado no enlaza con una salida de herramienta',()=>{const d=structuredClone(fixture);d.trace.result_ref='OTRO_RESULTADO';const x=run(d);assert.notEqual(x.status,0);assert.match(x.stderr,/tool sin resultado enlazado/);fs.rmSync(x.dir,{recursive:true,force:true});});
test('falla si un dato real carece de origen',()=>{const d=asReal(structuredClone(fixture));d.trace.execution_mode='local_tool';const x=run(d);assert.notEqual(x.status,0);assert.match(x.stderr,/fuente real sin URL/);fs.rmSync(x.dir,{recursive:true,force:true});});
test('geometría de Work 1 se enlaza por código sin cambiar las cifras',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'g360-geo-'));
  const input=path.join(dir,'input.json'),output=path.join(dir,'output.json'),geo=path.join(dir,'geo.json'),meta=path.join(dir,'meta.json');
  const d=structuredClone(fixture);d.comparison.forEach((r,i)=>r.unit_id=String(20001+i));d.scenario.unit_id=d.comparison[2].unit_id;
  fs.writeFileSync(input,JSON.stringify(d));
  fs.writeFileSync(geo,JSON.stringify({type:'FeatureCollection',features:d.comparison.map((r,i)=>({type:'Feature',properties:{municipality_code:r.unit_id},geometry:{type:'Polygon',coordinates:[[[i,0],[i+0.8,0],[i+0.8,0.8],[i,0.8],[i,0]]]}}))}));
  fs.writeFileSync(meta,JSON.stringify([{source_id:'GEOEUSKADI_MUNICIPIOS_2025',title:'Geometría de prueba',url:'https://example.org/geometry',reference_period:'2025-05-07',license:'test'}]));
  const p=spawnSync(process.execPath,[path.join(root,'scripts/enrich_work1_result.mjs'),input,output,geo,meta],{encoding:'utf8'});assert.equal(p.status,0,p.stderr);
  const enriched=JSON.parse(fs.readFileSync(output,'utf8'));
  assert.equal(enriched.map_features.length,4);
  assert.deepEqual(enriched.comparison,d.comparison);
  assert.ok(enriched.trace.data_refs.includes('GEOEUSKADI_MUNICIPIOS_2025'));
  const built=run(enriched);assert.equal(built.status,0,built.stderr);assert.ok(fs.readFileSync(path.join(built.out,'demo.html'),'utf8').includes('Mapa de unidades comparadas'));
  fs.rmSync(built.dir,{recursive:true,force:true});fs.rmSync(dir,{recursive:true,force:true});
});

const invalidCases=[
  ['umbral negativo',d=>{d.parameters.distance_threshold_km=-1},/parameters inválidos/],
  ['grupo de edad inesperado',d=>{d.parameters.age_group='80+'},/parameters inválidos/],
  ['tipo de población incorrecto',d=>{d.comparison[0].population='6200'},/comparison.population/],
  ['denominador cero',d=>{d.comparison[0].population=0;d.comparison[0].age_65_count=0;d.comparison[0].age_75_count=0},/denominador cero/],
  ['municipio duplicado',d=>{d.comparison[1].unit_id=d.comparison[0].unit_id},/unidad duplicada/],
  ['edad 75 mayor que 65',d=>{d.comparison[0].age_75_count=d.comparison[0].age_65_count+1},/grupos de edad imposibles/],
  ['distancia NaN convertida a null',d=>{d.comparison[0].service_distance_km=NaN},/comparison.service_distance_km/],
  ['source_id desconocido',d=>{d.metrics[0].source_ids=['NO_EXISTE']},/referencia de fuente inexistente/],
  ['escenario con unidad inexistente',d=>{d.scenario.unit_id='NO_EXISTE'},/scenario inválido/],
  ['baseline de escenario contradictoria',d=>{d.scenario.baseline_distance_km=999},/baseline del escenario/],
  ['traza que finge agente con fixture',d=>{asReal(d);d.trace.execution_mode='synthetic_fixture'},/modo de ejecución sintético/],
  ['fecha inválida',d=>{d.generated_at='ayer'},/generated_at/]
];
for(const [name,change,error] of invalidCases) test(`rechaza ${name}`,()=>{const d=structuredClone(fixture);change(d);const x=run(d);assert.notEqual(x.status,0);assert.match(x.stderr,error);fs.rmSync(x.dir,{recursive:true,force:true})});

test('acepta umbral extremo y escenario ausente sin fabricar cifras',()=>{const d=structuredClone(fixture);d.parameters.distance_threshold_km=100000;d.scenario=null;const x=run(d);assert.equal(x.status,0,x.stderr);const html=fs.readFileSync(path.join(x.out,'demo.html'),'utf8');assert.ok(html.includes('100000'));fs.rmSync(x.dir,{recursive:true,force:true})});
