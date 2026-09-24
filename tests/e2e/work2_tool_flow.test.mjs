import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import vm from 'node:vm';

const root=path.resolve(import.meta.dirname,'../..'),example=name=>path.join(root,'docs/examples',name);
const tmp=()=>fs.mkdtempSync(path.join(os.tmpdir(),'g360-work2-'));
function call(script,args){return spawnSync(process.execPath,[path.join(root,'scripts',script),...args],{cwd:root,encoding:'utf8'})}
function convert(dir,name,tool,file){const output=path.join(dir,`${name}.json`),p=call('adapt_agent_tool_result.mjs',['--tool',tool,'--input',file,'--output',output]);assert.equal(p.status,0,p.stderr);return{output,data:JSON.parse(fs.readFileSync(output,'utf8'))}}

test('dos ejecuciones reales de Work 2 → contrato → geometría → HTML',()=>{
  const dir=tmp(),aFile=example('coincidence_primary_care_65.json'),bFile=example('coincidence_primary_care_65_q85.json');
  const a=convert(dir,'q75','analizar_coincidencia',aFile),b=convert(dir,'q85','analizar_coincidencia',bFile);
  assert.equal(a.data.analysis.matched_count,7);assert.equal(b.data.analysis.matched_count,2);
  assert.equal(a.data.analysis.total_units,88);assert.notEqual(a.data.trace.result_ref,b.data.trace.result_ref);
  assert.equal(a.data.trace.execution_mode,'agent_tool');
  assert.equal(a.data.trace.input_files[0].sha256,createHash('sha256').update(fs.readFileSync(aFile)).digest('hex'));
  const mapped=path.join(dir,'mapped.json');assert.equal(call('enrich_work1_result.mjs',[a.output,mapped]).status,0);
  const enriched=JSON.parse(fs.readFileSync(mapped,'utf8'));assert.equal(enriched.map_features.length,5);
  const htmlDir=path.join(dir,'html'),built=call('build_results.mjs',[mapped,htmlDir]);assert.equal(built.status,0,built.stderr);
  const html=fs.readFileSync(path.join(htmlDir,'demo.html'),'utf8');for(const marker of ['HERRAMIENTA DE WORK 2 EJECUTADA','Cuantil 0.75','"matched_count":7',a.data.trace.result_ref])assert.ok(html.includes(marker),marker);
  fs.rmSync(dir,{recursive:true,force:true});
});

test('comparación y escenario de Work 2 preservan cifras observadas',()=>{
  const dir=tmp(),c=convert(dir,'comparison','comparar_municipios',example('comparison_tolosa_beasain_azpeitia.json'));
  assert.equal(c.data.comparison.length,3);assert.equal(c.data.comparison.find(x=>x.unit_id==='20071').population,20048);
  assert.equal(c.data.analysis.total_units,3);assert.equal(c.data.analysis.older_population_total,c.data.comparison.reduce((n,r)=>n+r.age_65_count,0));
  const s=convert(dir,'scenario','simular_escenario',example('scenario_add_primary_care_beasain.json'));
  assert.equal(s.data.analysis.matched_count,1);assert.equal(s.data.scenario.unit_id,'20019');
  assert.equal(s.data.scenario.baseline_distance_km,3.6173);assert.equal(s.data.scenario.scenario_distance_km,0);assert.equal(s.data.scenario.distance_delta_km,-3.6173);
  fs.rmSync(dir,{recursive:true,force:true});
});

const original=JSON.parse(fs.readFileSync(example('coincidence_primary_care_65.json'),'utf8'));
for(const [label,change,pattern] of [
  ['distancia adulterada',d=>{d.data[0].nearest_distance_m+=1000},/Distancia de tool y Work 1 difiere/],
  ['porcentaje adulterado',d=>{d.data[0].pct_65_plus+=10},/Porcentaje de tool y Work 1 difiere/],
  ['código repetido',d=>{d.data[1].municipality_code=d.data[0].municipality_code},/Código duplicado/],
  ['fuente ausente',d=>{d.sources=d.sources.filter(s=>s.source_id!=='EUSTAT_EMH_2025')},/Fuente requerida ausente/],
  ['cuantil fuera de rango',d=>{d.filters.quantile_threshold=1.2},/cuantil válido/],
  ['error de herramienta',d=>{d.status='error';d.error_code='missing_metric';d.message='sin dato'},/missing_metric/]
])test(`rechaza salida Work 2: ${label}`,()=>{const dir=tmp(),input=path.join(dir,'bad.json');const d=structuredClone(original);change(d);fs.writeFileSync(input,JSON.stringify(d));const p=call('adapt_agent_tool_result.mjs',['--tool','analizar_coincidencia','--input',input,'--output',path.join(dir,'out.json')]);assert.notEqual(p.status,0);assert.match(p.stderr,pattern);fs.rmSync(dir,{recursive:true,force:true})});

test('error de municipio inexistente no se convierte en cifra',()=>{const d=JSON.parse(fs.readFileSync(example('error_unknown_municipality.json'),'utf8'));assert.equal(d.status,'error');assert.equal(d.error_code,'municipality_not_found');assert.ok(!('data' in d))});
test('los HTML principales entregan datos reales de Work 2 y JavaScript válido',()=>{for(const file of ['demo.html','informe_principal.html','scenario_comparison.html']){const html=fs.readFileSync(path.join(root,'resultados',file),'utf8');assert.match(html,/"data_mode":"real"/);assert.match(html,/"execution_mode":"agent_tool"/);assert.ok(!html.includes('DATOS SINTÉTICOS DE DESARROLLO'));const start=html.indexOf('<script>')+8,end=html.indexOf('</script>',start);assert.ok(start>7&&end>start);new vm.Script(html.slice(start,end),{filename:file})}});
