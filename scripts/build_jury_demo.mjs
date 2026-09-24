import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';

const root=path.resolve(import.meta.dirname,'..');
const out=path.resolve(process.argv[2]||path.join(root,'resultados/demo_real'));
fs.mkdirSync(out,{recursive:true});
const cases=[
  {id:'panorama',label:'1 · Panorama',prompt:'¿Qué municipios combinan ≥25 % de población ≥65 con más de 2 km de distancia geométrica a atención primaria?',args:['--age','65','--share','25','--distance','2','--service','primary_care']},
  {id:'variacion',label:'2 · Nuevo umbral',prompt:'Repite la consulta con un umbral de más de 2,5 km.',args:['--age','65','--share','25','--distance','2.5','--service','primary_care']},
  {id:'comparacion',label:'3 · Comparar',prompt:'Compara Donostia / San Sebastián, Legazpi y Hondarribia con el cálculo territorial anterior.',args:['--age','65','--share','25','--distance','2','--service','primary_care','--compare-codes','20069,20051,20036']},
  {id:'limite',label:'4 · Caso límite',prompt:'¿Qué ocurre con ≥90 % de población ≥75 y más de 100 km?',args:['--age','75','--share','90','--distance','100','--service','primary_care']}
];
function run(script,args){const p=spawnSync(process.execPath,[path.join(root,'scripts',script),...args],{cwd:root,encoding:'utf8'});if(p.status!==0)throw new Error(`${script}: ${p.stderr||p.stdout}`);process.stdout.write(p.stdout)}
for(const [i,c] of cases.entries()){
  const raw=path.join(out,`${c.id}.json`),mapped=path.join(out,`${c.id}_mapa.json`),htmlDir=path.join(out,c.id);
  run('run_local_analysis.mjs',['--output',raw,'--generated-at',`2026-09-24T17:0${i}:00+02:00`,...c.args]);
  run('enrich_work1_result.mjs',[raw,mapped]);
  run('build_results.mjs',[mapped,htmlDir]);
  const d=JSON.parse(fs.readFileSync(mapped,'utf8'));c.count=d.analysis.matched_count;c.ref=d.trace.result_ref;
}
const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const cards=cases.map(c=>`<article><small>${escape(c.label)}</small><h2>${escape(c.prompt)}</h2><p><b>${c.count} de 88</b> municipios cumplen los criterios. Ejecución <code>${escape(c.ref)}</code>.</p><a href="${c.id}/demo.html">Abrir resultado</a> · <a href="${c.id}.json">Ver JSON de herramienta</a></article>`).join('\n');
fs.writeFileSync(path.join(out,'index.html'),`<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GIPUZKOA 360 · Recorrido de jurado</title><style>body{font:16px/1.5 system-ui,sans-serif;background:#f4f7f7;color:#143746;margin:0}header{background:#103747;color:white;padding:32px max(24px,calc((100vw - 1060px)/2))}main{max-width:1060px;margin:auto;padding:28px 24px}h1{font-size:2rem;margin:0 0 8px}h2{font-size:1.1rem}p{max-width:850px}section{display:grid;grid-template-columns:1fr 1fr;gap:16px}article{background:white;border:1px solid #d8e5e5;border-radius:12px;padding:20px}small{color:#16767b;font-weight:800;text-transform:uppercase}a{color:#076e75}code{font-size:.8rem;word-break:break-all}.notice{padding:14px;background:#dcefed;border-left:4px solid #16767b;margin-bottom:24px}@media(max-width:680px){section{grid-template-columns:1fr}}</style></head><body><header><h1>GIPUZKOA 360</h1><p>Recorrido reproducible de datos → herramienta local → resultado estructurado → mapa e informe.</p></header><main><div class="notice"><b>Datos reales de Work 1; cálculo local reproducible.</b> La integración del agente de Work 2 sigue pendiente. Cada pantalla muestra fuente, periodo, unidad, método y límites. Las distancias son geométricas desde un punto representativo municipal.</div><section>${cards}</section><p>Fuentes y periodos: población Eustat 2025-01-01; centros públicos Open Data Euskadi 2026-09-20; límites geoEuskadi 2025-05-07. La diferencia máxima entre periodos documentada por Work 1 es 627 días. Ningún resultado estima tiempo de viaje ni acceso individual.</p></main></body></html>`);
console.log(`Recorrido listo: ${path.join(out,'index.html')}`);
