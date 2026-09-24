import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';

const root=path.resolve(import.meta.dirname,'..'),out=path.resolve(process.argv[2]||path.join(root,'resultados/demo_work2'));
fs.mkdirSync(out,{recursive:true});
const items=[
  {id:'coincidencia',label:'1 · Pregunta principal',tool:'analizar_coincidencia',file:'coincidence_primary_care_65.json',prompt:'¿Qué municipios coinciden en el cuantil 0,75 de población ≥65 y distancia geométrica a atención primaria?'},
  {id:'variacion',label:'2 · Nuevo cálculo',tool:'analizar_coincidencia',file:'coincidence_primary_care_65_q85.json',prompt:'Repite con cuantil 0,85. ¿Cambia el grupo destacado?'},
  {id:'comparacion',label:'3 · Comparación',tool:'comparar_municipios',file:'comparison_tolosa_beasain_azpeitia.json',prompt:'Compara Tolosa, Beasain y Azpeitia por código municipal.'},
  {id:'escenario',label:'4 · Escenario',tool:'simular_escenario',file:'scenario_add_primary_care_beasain.json',prompt:'¿Qué cambia si se añade hipotéticamente un centro de atención primaria en el punto del ejemplo de Beasain?'}
];
function run(name,args){const p=spawnSync(process.execPath,[path.join(root,'scripts',name),...args],{encoding:'utf8',cwd:root});if(p.status!==0)throw new Error(`${name}: ${p.stderr||p.stdout}`);process.stdout.write(p.stdout)}
for(const [i,item] of items.entries()){
  const raw=path.join(root,'docs/examples',item.file),canonical=path.join(out,`${item.id}.json`),mapped=path.join(out,`${item.id}_mapa.json`);
  run('adapt_agent_tool_result.mjs',['--tool',item.tool,'--input',raw,'--output',canonical,'--generated-at',`2026-09-24T18:0${i}:00+02:00`]);
  run('enrich_work1_result.mjs',[canonical,mapped]);
  run('build_results.mjs',[mapped,path.join(out,item.id)]);
  const d=JSON.parse(fs.readFileSync(canonical,'utf8'));item.count=d.analysis.matched_count;item.total=d.analysis.total_units;item.ref=d.trace.result_ref;
}
const error=JSON.parse(fs.readFileSync(path.join(root,'docs/examples/error_unknown_municipality.json'),'utf8'));
if(error.status!=='error'||error.error_code!=='municipality_not_found')throw new Error('El caso de municipio inexistente no es un error controlado');
const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const cards=items.map(x=>`<article><small>${escape(x.label)}</small><h2>${escape(x.prompt)}</h2><p><b>${x.count}/${x.total}</b> · <code>${escape(x.ref)}</code></p><a href="${x.id}/demo.html">Abrir resultado</a> · <a href="${x.id}.json">JSON adaptado</a> · <a href="../../docs/examples/${x.file}">Salida original de Work 2</a></article>`).join('');
const errorCard=`<article><small>5 · Dato ausente</small><h2>¿Qué ocurre si se consulta un municipio inexistente?</h2><p>La herramienta responde <code>${escape(error.error_code)}</code> y no devuelve una cifra. ${escape(error.message)}</p><a href="../../docs/examples/error_unknown_municipality.json">Ver error original</a></article>`;
fs.writeFileSync(path.join(out,'index.html'),`<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GIPUZKOA 360 · Demo Work 2</title><style>body{font:16px/1.5 system-ui,sans-serif;background:#f3f7f7;color:#143746;margin:0}header{background:#103747;color:#fff;padding:32px max(24px,calc((100vw - 1080px)/2))}main{max-width:1080px;margin:auto;padding:28px 24px}h1{font-size:2rem;margin:0 0 8px}h2{font-size:1.12rem}section{display:grid;grid-template-columns:1fr 1fr;gap:16px}article{background:#fff;border:1px solid #d8e5e5;border-radius:12px;padding:20px}small{color:#16767b;font-weight:800;text-transform:uppercase}a{color:#076e75}code{font-size:.8rem;word-break:break-all}.notice{padding:14px;background:#dcefed;border-left:4px solid #16767b;margin-bottom:24px}@media(max-width:680px){section{grid-template-columns:1fr}}</style></head><body><header><h1>GIPUZKOA 360</h1><p>Datos reales → herramientas de Work 2 → contrato verificado → mapa e informe.</p></header><main><div class="notice"><b>Herramientas reales ejecutadas directamente.</b> Falta probar el coordinador con una versión fija en el portal. La coincidencia se define por cuantiles en ambas métricas; el umbral de 1 km solo informa la bandera de cercanía de la tool. Las distancias son euclídeas desde puntos representativos municipales.</div><section>${cards}${errorCard}</section><p>Fuentes: Eustat 2025-01-01, centros públicos 2026-09-20 y límites municipales 2025-05-07. Un escenario es hipotético y no predice efectos sociales ni recomienda una ubicación.</p></main></body></html>`);
for(const [source,target] of [['coincidencia/demo.html','demo.html'],['coincidencia/informe_principal.html','informe_principal.html'],['escenario/scenario_comparison.html','scenario_comparison.html']])fs.copyFileSync(path.join(out,source),path.join(root,'resultados',target));
console.log(`Demo de Work 2: ${path.join(out,'index.html')}`);
