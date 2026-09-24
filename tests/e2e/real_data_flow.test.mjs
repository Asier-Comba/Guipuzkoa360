import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';

const root=path.resolve(import.meta.dirname,'../..');
const script=name=>path.join(root,'scripts',name);
const tmp=()=>fs.mkdtempSync(path.join(os.tmpdir(),'g360-real-'));
function run(name,args){return spawnSync(process.execPath,[script(name),...args],{cwd:root,encoding:'utf8'})}
function analysis(dir,name,args){const file=path.join(dir,`${name}.json`),p=run('run_local_analysis.mjs',['--output',file,'--generated-at','2026-09-24T17:00:00+02:00',...args]);assert.equal(p.status,0,p.stderr);return {file,data:JSON.parse(fs.readFileSync(file,'utf8'))}}

test('88 filas reales → dos cálculos distintos → GeoJSON → HTML trazable',()=>{
  const dir=tmp();
  const main=analysis(dir,'main',['--age','65','--share','25','--distance','2']);
  const variation=analysis(dir,'variation',['--age','65','--share','25','--distance','2.5']);
  assert.equal(main.data.analysis.total_units,88);
  assert.equal(main.data.analysis.matched_count,5);
  assert.equal(variation.data.analysis.matched_count,2);
  assert.notEqual(main.data.trace.result_ref,variation.data.trace.result_ref);
  assert.equal(main.data.trace.execution_mode,'local_tool');
  const bytes=fs.readFileSync(path.join(root,'resultados/metricas_municipales.csv'));
  assert.equal(main.data.trace.input_files[0].sha256,createHash('sha256').update(bytes).digest('hex'));
  const mapped=path.join(dir,'mapped.json'),enrich=run('enrich_work1_result.mjs',[main.file,mapped]);assert.equal(enrich.status,0,enrich.stderr);
  const enriched=JSON.parse(fs.readFileSync(mapped,'utf8'));
  assert.equal(enriched.map_features.length,5);
  assert.deepEqual(enriched.comparison,main.data.comparison);
  const built=run('build_results.mjs',[mapped,path.join(dir,'html')]);assert.equal(built.status,0,built.stderr);
  const html=fs.readFileSync(path.join(dir,'html/demo.html'),'utf8');
  for(const text of [main.data.question,main.data.trace.result_ref,'DATOS REALES · CÁLCULO LOCAL','EUSTAT_EMH_2025','ODE_HEALTH_CENTRES_2026','GEOEUSKADI_MUNICIPIOS_2025','Mapa de unidades comparadas'])assert.ok(html.includes(text),`Falta ${text}`);
  fs.rmSync(dir,{recursive:true,force:true});
});

test('cifra de Donostia coincide con CSV preparado y fuente original Eustat',()=>{
  const dir=tmp(),x=analysis(dir,'compare',['--compare-codes','20069,20051,20036']);
  const row=x.data.comparison.find(r=>r.unit_id==='20069');
  assert.equal(row.population,183388);
  const source=fs.readFileSync(path.join(root,'datos_originales/eustat_demografia_2025.csv'));
  const lines=source.toString('latin1').split(/\r?\n/);
  assert.ok(lines.some(line=>line.startsWith('"Donostia / San Sebasti')&&line.endsWith('"Total","Total",183388')));
  assert.equal(row.row_ref,'resultados/metricas_municipales.csv#municipality_code=20069');
  fs.rmSync(dir,{recursive:true,force:true});
});

test('umbral extremo devuelve cero sin inventar municipio positivo',()=>{
  const dir=tmp(),x=analysis(dir,'empty',['--age','75','--share','90','--distance','100']);
  assert.equal(x.data.analysis.matched_count,0);
  assert.deepEqual(x.data.analysis.matched_unit_ids,[]);
  assert.match(x.data.summary,/Ninguno de los 88 municipios/);
  assert.equal(x.data.comparison.length,5);
  fs.rmSync(dir,{recursive:true,force:true});
});

for(const [label,args,expected] of [
  ['servicio desconocido',['--service','farmacia'],/Parámetros inválidos/],
  ['umbral negativo',['--distance','-1'],/Parámetros inválidos/],
  ['municipio inexistente',['--compare-codes','20069,99999'],/Municipio sin datos: 99999/],
  ['municipio repetido',['--compare-codes','20069,20069'],/códigos distintos/]
])test(`error controlado: ${label}`,()=>{const dir=tmp(),p=run('run_local_analysis.mjs',['--output',path.join(dir,'x.json'),...args]);assert.notEqual(p.status,0);assert.match(p.stderr,expected);fs.rmSync(dir,{recursive:true,force:true})});

test('CSV corrupto con código duplicado falla antes de producir resultado',()=>{
  const dir=tmp(),source=fs.readFileSync(path.join(root,'resultados/metricas_municipales.csv'),'utf8').split(/\r?\n/);
  source[2]=source[2].replace(/^\d{5}/,source[1].slice(0,5));const bad=path.join(dir,'bad.csv');fs.writeFileSync(bad,source.join('\n'));
  const p=run('run_local_analysis.mjs',['--output',path.join(dir,'x.json'),'--metrics-file',bad]);assert.notEqual(p.status,0);assert.match(p.stderr,/Código municipal ausente\/duplicado/);
  fs.rmSync(dir,{recursive:true,force:true});
});

test('CSV corrupto con valor ausente falla antes de producir resultado',()=>{
  const dir=tmp(),source=fs.readFileSync(path.join(root,'resultados/metricas_municipales.csv'),'utf8').split(/\r?\n/);
  const fields=source[1].split(',');fields[2]='';source[1]=fields.join(',');const bad=path.join(dir,'bad.csv');fs.writeFileSync(bad,source.join('\n'));
  const p=run('run_local_analysis.mjs',['--output',path.join(dir,'x.json'),'--metrics-file',bad]);assert.notEqual(p.status,0);assert.match(p.stderr,/población 20001: entero ausente/);
  fs.rmSync(dir,{recursive:true,force:true});
});
