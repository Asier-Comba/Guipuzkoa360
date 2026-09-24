import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';

const root=path.resolve(import.meta.dirname,'..');
const argv=process.argv.slice(2);
function option(name,fallback){const i=argv.indexOf(`--${name}`);return i<0?fallback:argv[i+1]}
const output=option('output',null);
if (!output) throw new Error('Uso: node scripts/run_local_analysis.mjs --output salida.json [--age 65|75] [--share 25] [--distance 2] [--service primary_care|hospital] [--compare-codes 20069,20051]');
const age=option('age','65'),service=option('service','primary_care');
const share=Number(option('share','25')),distance=Number(option('distance','2'));
if (!['65','75'].includes(age) || !['primary_care','hospital'].includes(service) || !Number.isFinite(share) || share<0 || share>100 || !Number.isFinite(distance) || distance<0) throw new Error('Parámetros inválidos');
const metricsPath=path.resolve(option('metrics-file',path.join(root,'resultados/metricas_municipales.csv')));
const metadataPath=path.resolve(option('metadata-file',path.join(root,'datos_preparados/metadata_sources.json')));
const sourceBytes=fs.readFileSync(metricsPath),metadataBytes=fs.readFileSync(metadataPath);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');

function parseCsv(text){
  const records=[];let row=[],field='',quoted=false;
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(c==='"'){if(quoted&&text[i+1]==='"'){field+='"';i++}else quoted=!quoted}
    else if(c===','&&!quoted){row.push(field);field=''}
    else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(field);field='';if(row.some(v=>v!==''))records.push(row);row=[]}
    else field+=c;
  }
  if(quoted)throw new Error('CSV: comillas sin cerrar');
  if(field!==''||row.length){row.push(field);records.push(row)}
  const header=records.shift()?.map((x,i)=>i===0?x.replace(/^\uFEFF/,''):x);
  if(!header||new Set(header).size!==header.length)throw new Error('CSV: cabecera ausente o duplicada');
  return records.map((values,i)=>{if(values.length!==header.length)throw new Error(`CSV: columnas incorrectas en fila ${i+2}`);return Object.fromEntries(header.map((key,j)=>[key,values[j]]))});
}
function integer(raw,label){if(!/^\d+$/.test(raw))throw new Error(`${label}: entero ausente/inválido`);return Number(raw)}
function numeric(raw,label){if(!/^(?:\d+)(?:\.\d+)?$/.test(raw))throw new Error(`${label}: número ausente/inválido`);return Number(raw)}
const rawRows=parseCsv(sourceBytes.toString('utf8'));
if(rawRows.length!==88)throw new Error(`Se esperaban 88 municipios, hay ${rawRows.length}`);
const codes=new Set();
const rows=rawRows.map((r,i)=>{
  const code=r.municipality_code;
  if(!/^\d{5}$/.test(code)||codes.has(code))throw new Error(`Código municipal ausente/duplicado en fila ${i+2}`);codes.add(code);
  const population=integer(r.population_total,`población ${code}`),age65=integer(r.population_65_plus,`65+ ${code}`),age75=integer(r.population_75_plus,`75+ ${code}`);
  if(!population||age75>age65||age65>population)throw new Error(`Denominador o edades imposibles en ${code}`);
  const distM=numeric(r[service==='primary_care'?'distance_to_nearest_primary_care_m':'distance_to_nearest_hospital_m'],`distancia ${code}`);
  const count=integer(r[service==='primary_care'?'services_primary_care':'services_hospital'],`servicios ${code}`);
  if(!r.reference_period||!r.metrics_reference_period||!r.municipality_name)throw new Error(`Metadatos ausentes ${code}`);
  return {unit_id:code,name:r.municipality_name,population,age_65_count:age65,age_75_count:age75,service_distance_km:distM/1000,service_count:count,period:r.metrics_reference_period,row_ref:`resultados/metricas_municipales.csv#municipality_code=${code}`,source_ids:['EUSTAT_EMH_2025','ODE_HEALTH_CENTRES_2026','GEOEUSKADI_MUNICIPIOS_2025']};
});
const metadata=JSON.parse(metadataBytes.toString('utf8'));
const sourceIds=['EUSTAT_EMH_2025','ODE_HEALTH_CENTRES_2026','GEOEUSKADI_MUNICIPIOS_2025'];
const sources=sourceIds.map(id=>{const s=metadata.find(x=>x.source_id===id);if(!s||!s.url||!s.reference_period||!s.license)throw new Error(`Metadatos de fuente incompletos: ${id}`);return {source_id:id,title:s.title,url:s.url,period:s.reference_period,unit:id==='EUSTAT_EMH_2025'?'personas':id==='ODE_HEALTH_CENTRES_2026'?'centros y distancia en m':'polígonos municipales',license:s.license,method:id==='EUSTAT_EMH_2025'?'Recuento municipal oficial':id==='ODE_HEALTH_CENTRES_2026'?'Centros públicos; proximidad geométrica derivada desde punto representativo municipal':'Límites municipales usados para punto representativo y mapa'}});
const ageKey=age==='65'?'age_65_count':'age_75_count';
const pct=r=>100*r[ageKey]/r.population;
const matching=rows.filter(r=>pct(r)>=share&&r.service_distance_km>distance).sort((a,b)=>b.service_distance_km-a.service_distance_km||b[ageKey]-a[ageKey]||a.unit_id.localeCompare(b.unit_id));
const compareArg=option('compare-codes',null);
let comparison;
if(compareArg){const requested=compareArg.split(',').map(x=>x.trim());if(requested.length<2||requested.length>5||new Set(requested).size!==requested.length)throw new Error('compare-codes requiere 2–5 códigos distintos');comparison=requested.map(code=>{const row=rows.find(r=>r.unit_id===code);if(!row)throw new Error(`Municipio sin datos: ${code}`);return row})}
else{comparison=matching.slice(0,5);if(comparison.length<2){const rest=rows.filter(r=>!comparison.some(x=>x.unit_id===r.unit_id)).sort((a,b)=>b.service_distance_km-a.service_distance_km||a.unit_id.localeCompare(b.unit_id));comparison.push(...rest.slice(0,5-comparison.length))}}
const label=service==='primary_care'?'atención primaria':'hospital';
const question=`¿Qué municipios tienen al menos ${share}% de población de ${age} años o más y más de ${distance} km de distancia geométrica aproximada desde su punto representativo al centro de ${label} más cercano?`;
const olderTotal=rows.reduce((n,r)=>n+r[ageKey],0),populationTotal=rows.reduce((n,r)=>n+r.population,0);
const args={age_group:`${age}+`,older_share_threshold_pct:share,distance_threshold_km:distance,service,compare_codes:compareArg||null};
const resultRef='LOCAL-'+sha(JSON.stringify({args,input_sha256:sha(sourceBytes),metadata_sha256:sha(metadataBytes),matching:matching.map(r=>r.unit_id)})).slice(0,16);
const generatedAt=option('generated-at',new Date().toISOString());
if(!Number.isFinite(Date.parse(generatedAt)))throw new Error('generated-at inválido');
const result={
  schema_version:'1.0.0',data_mode:'real',title:'Envejecimiento y proximidad a servicios sanitarios',question,
  summary:matching.length?`${matching.length} de 88 municipios cumplen ambos criterios. La tabla muestra ${compareArg?'los municipios solicitados':'hasta cinco municipios que cumplen, ordenados por distancia'}. Las distancias se miden desde un punto representativo municipal.`:`Ninguno de los 88 municipios cumple ambos criterios. La tabla muestra unidades de referencia con mayores distancias para examinar por qué no cumplen; no son resultados positivos.`,
  generated_at:generatedAt,period:'Demografía 2025-01-01 · centros 2026-09-20 · límites 2025-05-07',geography:'Gipuzkoa · 88 municipios',
  parameters:{age_group:`${age}+`,older_share_threshold_pct:share,service,distance_threshold_km:distance},
  analysis:{total_units:rows.length,matched_count:matching.length,matched_unit_ids:matching.map(r=>r.unit_id),older_population_total:olderTotal},
  metrics:[{id:'population_total',label:'Población total',value:populationTotal,unit:'personas',period:'2025-01-01',source_ids:['EUSTAT_EMH_2025']},{id:'older_population_total',label:`Población ≥${age}`,value:olderTotal,unit:'personas',period:'2025-01-01',source_ids:['EUSTAT_EMH_2025']},{id:'matched_municipalities',label:'Municipios que cumplen ambos criterios',value:matching.length,unit:'municipios',period:'2025/2026',source_ids:sourceIds}],
  comparison,map_layers:[{id:'older_share',label:`Población ≥${age}`,metric:`age_${age}_count / population * 100`,unit:'%',period:'2025-01-01',source_ids:['EUSTAT_EMH_2025']},{id:'service_distance',label:`Distancia geométrica aproximada a ${label}`,metric:'service_distance_km',unit:'km',period:'2026-09-20',source_ids:['ODE_HEALTH_CENTRES_2026','GEOEUSKADI_MUNICIPIOS_2025']}],
  scenario:null,sources,
  method:`Por cada municipio: población ≥${age} / población total × 100 ≥${share}%, y distancia euclídea desde un punto representativo municipal al centro de ${label} más cercano >${distance} km. Se leen las 88 filas de resultados/metricas_municipales.csv; m → km dividiendo entre 1.000. Orden por distancia descendente.`,
  limitations:['El punto representativo municipal no está ponderado por población; la distancia no representa el recorrido de una persona concreta.','Distancia euclídea no equivale a tiempo de viaje, accesibilidad universal, apertura, capacidad ni disponibilidad de citas.','Demografía, centros y límites tienen periodos distintos (separación máxima documentada de 627 días).','Un municipio que no cumple estos umbrales no implica ausencia de necesidad; los criterios son exploratorios.'],
  trace:{execution_mode:'local_tool',question_id:'LOCAL-Q-'+resultRef.slice(-12),agent_version:'local-analysis/1.0.0 (sin agente)',tool_calls:[{tool:'compare_municipal_services_local',arguments:args,output_ref:resultRef}],data_refs:sourceIds,result_ref:resultRef,input_files:[{path:path.relative(root,metricsPath).replaceAll('\\','/'),sha256:sha(sourceBytes),rows:rows.length},{path:path.relative(root,metadataPath).replaceAll('\\','/'),sha256:sha(metadataBytes),rows:metadata.length}]}
};
fs.mkdirSync(path.dirname(path.resolve(output)),{recursive:true});fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(`${resultRef}: ${matching.length}/${rows.length} municipios; ${comparison.length} filas comparadas → ${output}`);
