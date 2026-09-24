import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';

const root=path.resolve(import.meta.dirname,'..'),args=process.argv.slice(2);
const option=(name,fallback)=>{const i=args.indexOf(`--${name}`);return i<0?fallback:args[i+1]};
const tool=option('tool',null),input=option('input',null),output=option('output',null);
if(!tool||!input||!output)throw new Error('Uso: node scripts/adapt_agent_tool_result.mjs --tool analizar_coincidencia|comparar_municipios|simular_escenario --input salida_tool.json --output resultado.json');
if(!['analizar_coincidencia','comparar_municipios','simular_escenario'].includes(tool))throw new Error('Tool no compatible');
const rawBytes=fs.readFileSync(input),raw=JSON.parse(rawBytes.toString('utf8'));
if(raw.status!=='ok')throw new Error(`La tool devolvió ${raw.error_code||raw.status}: ${raw.message||'sin resultado'}`);
if(!Array.isArray(raw.data)||!raw.data.length||!Array.isArray(raw.sources)||!raw.method||!raw.period)throw new Error('Salida de Work 2 incompleta');
const metricsPath=path.join(root,'resultados/metricas_municipales.csv'),metadataPath=path.join(root,'datos_preparados/metadata_sources.json');
const metricsBytes=fs.readFileSync(metricsPath),metadataBytes=fs.readFileSync(metadataPath);
const sha=x=>createHash('sha256').update(x).digest('hex');
const lines=metricsBytes.toString('utf8').trim().split(/\r?\n/),header=lines.shift().split(',');
const prepared=lines.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[header[i],v])));
if(prepared.length!==88)throw new Error('Work 1: se esperaban 88 municipios');
const byCode=new Map(prepared.map(r=>[r.municipality_code,r]));
if(byCode.size!==88)throw new Error('Work 1: código municipal duplicado');
const metadata=JSON.parse(metadataBytes.toString('utf8'));
const sourceIds=['EUSTAT_EMH_2025','ODE_HEALTH_CENTRES_2026','GEOEUSKADI_MUNICIPIOS_2025'];
const sources=sourceIds.map(id=>{const s=metadata.find(x=>x.source_id===id);if(!s?.url||!s.reference_period||!s.license)throw new Error(`Fuente ausente: ${id}`);return{source_id:id,title:s.title,url:s.url,period:s.reference_period,unit:id==='EUSTAT_EMH_2025'?'personas':id==='ODE_HEALTH_CENTRES_2026'?'centros y metros':'polígonos municipales',license:s.license,method:id==='EUSTAT_EMH_2025'?'Censo municipal por grupo de edad':id==='ODE_HEALTH_CENTRES_2026'?'Puntos de servicios públicos; distancia euclídea derivada':'Límites municipales y punto representativo'}});
const rawSourceIds=new Set(raw.sources.map(s=>s.source_id));
for(const id of rawSourceIds)if(!sourceIds.includes(id))throw new Error(`Fuente de tool desconocida: ${id}`);
for(const id of (tool==='simular_escenario'?['GEOEUSKADI_MUNICIPIOS_2025','ODE_HEALTH_CENTRES_2026']:sourceIds))if(!rawSourceIds.has(id))throw new Error(`Fuente requerida ausente en tool: ${id}`);
const codes=new Set();for(const row of raw.data){const c=String(row.municipality_code);if(codes.has(c)||!byCode.has(c))throw new Error(`Código duplicado o sin datos en tool: ${c}`);codes.add(c)}
if(tool!=='comparar_municipios'&&raw.data.length!==88)throw new Error('Salida territorial incompleta: no contiene 88 municipios');
const age=String(raw.filters?.age_group||'65').replace('+','');if(!['65','75'].includes(age))throw new Error('Grupo de edad de Work 2 no compatible');
const category=raw.filters?.service_category;if(!['primary_care','hospital'].includes(category))throw new Error('Categoría de servicio no compatible');
const distanceField=category==='primary_care'?'distance_to_nearest_primary_care_m':'distance_to_nearest_hospital_m',countField=category==='primary_care'?'services_primary_care':'services_hospital';
const ageCountField=age==='65'?'population_65_plus':'population_75_plus',agePctField=age==='65'?'pct_65_plus':'pct_75_plus';
const serviceLabel=category==='primary_care'?'atención primaria':'hospital';
const threshold=Number(raw.filters?.threshold_km??raw.scenario?.baseline?.threshold_km??1);
if(!Number.isFinite(threshold)||threshold<0)throw new Error('Umbral de Work 2 inválido');
function approx(a,b,tolerance=0.11){return Number.isFinite(Number(a))&&Number.isFinite(Number(b))&&Math.abs(Number(a)-Number(b))<=tolerance}
function comparisonRow(toolRow,scenario=false){const code=String(toolRow.municipality_code),p=byCode.get(code);if(!p)throw new Error(`Sin fila Work 1: ${code}`);const population=Number(p.population_total),age65=Number(p.population_65_plus),age75=Number(p.population_75_plus),baseline=Number(p[distanceField]);if(!Number.isInteger(population)||!Number.isInteger(age65)||!Number.isInteger(age75)||age75>age65||age65>population)throw new Error(`Demografía inválida ${code}`);const toolDistance=scenario?toolRow.baseline_distance_m:toolRow.nearest_distance_m;if(!approx(toolDistance,baseline))throw new Error(`Distancia de tool y Work 1 difiere en ${code}`);if(toolRow.population_total!==undefined&&Number(toolRow.population_total)!==population)throw new Error(`Población de tool y Work 1 difiere en ${code}`);if(toolRow[agePctField]!==undefined&&!approx(toolRow[agePctField],p[agePctField],0.002))throw new Error(`Porcentaje de tool y Work 1 difiere en ${code}`);return{unit_id:code,name:p.municipality_name,population,age_65_count:age65,age_75_count:age75,service_distance_km:baseline/1000,service_count:Number(p[countField]),period:p.metrics_reference_period,row_ref:`resultados/metricas_municipales.csv#municipality_code=${code}`,source_ids:sourceIds}}
let selected,matchedCodes,matchLabel,criteriaLabel,scenario=null,question,summary;
if(tool==='analizar_coincidencia'){
  if(raw.rows_used!==88||!Number.isFinite(Number(raw.filters?.quantile_threshold))||Number(raw.filters.quantile_threshold)<0.5||Number(raw.filters.quantile_threshold)>0.95)throw new Error('Coincidencia sin 88 filas o cuantil válido');
  matchedCodes=raw.data.filter(r=>r.highlighted===true).map(r=>String(r.municipality_code));
  selected=raw.data.filter(r=>r.highlighted===true).slice(0,5);if(selected.length<2)selected.push(...raw.data.filter(r=>!selected.includes(r)).slice(0,5-selected.length));
  matchLabel='Municipios destacados por ambos cuantiles';criteriaLabel=`Cuantil ${raw.filters.quantile_threshold} en porcentaje ≥${age} y distancia geométrica`;
  question=`¿Qué municipios están en el cuantil superior de población ≥${age} y distancia geométrica aproximada a ${serviceLabel}?`;
  summary=`La herramienta de Work 2 destaca ${matchedCodes.length} de 88 municipios por ambos cuantiles. El umbral de ${threshold} km informa la columna de cercanía, pero no define el grupo destacado. Se muestran hasta cinco municipios.`;
}else if(tool==='comparar_municipios'){
  if(raw.data.length<2||raw.data.length>5||raw.rows_used!==raw.data.length)throw new Error('Comparación de Work 2 incompleta');
  selected=raw.data;matchedCodes=raw.data.map(r=>String(r.municipality_code));
  matchLabel='Municipios comparados';criteriaLabel='Comparación por municipio, sin clasificación conjunta';
  question=`¿Cómo se comparan ${raw.data.map(r=>r.municipality_name).join(', ')} en población mayor y distancia geométrica a ${serviceLabel}?`;
  summary=`Se comparan ${raw.data.length} municipios por código territorial, sin índice compuesto ni clasificación de “mejor/peor”.`;
}else{
  if(!raw.scenario||!Array.isArray(raw.scenario.assumptions))throw new Error('Escenario de Work 2 incompleto');
  const changed=raw.data.filter(r=>Number(r.difference_absolute_m)!==0);
  if(!changed.length)throw new Error('Escenario sin cambio de distancia: no se inventa efecto');
  const chosen=changed.slice().sort((a,b)=>Math.abs(b.difference_absolute_m)-Math.abs(a.difference_absolute_m))[0];
  selected=[chosen,...raw.data.filter(r=>r!==chosen).sort((a,b)=>b.baseline_distance_m-a.baseline_distance_m).slice(0,4)];
  matchedCodes=changed.map(r=>String(r.municipality_code));matchLabel='Municipios cuya distancia cambia';criteriaLabel='Escenario hipotético: distancia antes y después';
  const delta=Number(chosen.difference_absolute_m)/1000;
  if(!approx(Number(chosen.scenario_distance_m)-Number(chosen.baseline_distance_m),chosen.difference_absolute_m))throw new Error('Diferencia de escenario incoherente');
  scenario={label:'ESCENARIO HIPOTÉTICO',change:`${raw.scenario.changed_parameters.action}: ${raw.scenario.changed_parameters.service_id||'servicio'}; punto hipotético (${raw.scenario.changed_parameters.latitude}, ${raw.scenario.changed_parameters.longitude})`,unit_id:String(chosen.municipality_code),distance_delta_km:delta,baseline_distance_km:Number(chosen.baseline_distance_m)/1000,scenario_distance_km:Number(chosen.scenario_distance_m)/1000,assumptions:[...raw.scenario.assumptions,...raw.scenario.limitations]};
  question=`¿Cómo cambia hipotéticamente la distancia geométrica a ${serviceLabel} al añadir el servicio de prueba?`;
  summary=`La herramienta de Work 2 recalcula 88 municipios; ${changed.length} cambia de distancia. Para ${chosen.municipality_name}, la base es ${chosen.baseline_distance_m} m y el escenario ${chosen.scenario_distance_m} m. Es un contrafactual, no una predicción.`;
}
const comparison=selected.map(r=>comparisonRow(r,tool==='simular_escenario'));
const populationScope=tool==='comparar_municipios'?comparison:prepared;
const olderTotal=populationScope.reduce((sum,r)=>sum+Number(r[tool==='comparar_municipios'?(age==='65'?'age_65_count':'age_75_count'):ageCountField]),0),populationTotal=populationScope.reduce((sum,r)=>sum+Number(r[tool==='comparar_municipios'?'population':'population_total']),0);
const ref='WORK2-TOOL-'+sha(rawBytes).slice(0,16),generated=option('generated-at',new Date().toISOString());
if(!Number.isFinite(Date.parse(generated)))throw new Error('Fecha de generación inválida');
const result={schema_version:'1.0.0',data_mode:'real',title:'Envejecimiento y servicios sanitarios en Gipuzkoa',question,summary,generated_at:generated,period:'Demografía 2025-01-01 · centros 2026-09-20 · límites 2025-05-07',geography:'Gipuzkoa · 88 municipios',parameters:{age_group:`${age}+`,older_share_threshold_pct:null,criteria_label:criteriaLabel,service:category,distance_threshold_km:threshold},analysis:{total_units:tool==='comparar_municipios'?raw.data.length:88,matched_count:matchedCodes.length,matched_unit_ids:matchedCodes,older_population_total:olderTotal,match_label:matchLabel},metrics:[{id:'population_total',label:'Población total',value:populationTotal,unit:'personas',period:'2025-01-01',source_ids:['EUSTAT_EMH_2025']},{id:'older_population_total',label:`Población ≥${age}`,value:olderTotal,unit:'personas',period:'2025-01-01',source_ids:['EUSTAT_EMH_2025']},{id:'selected_municipalities',label:matchLabel,value:matchedCodes.length,unit:'municipios',period:'2025/2026',source_ids:sourceIds}],comparison,map_layers:[{id:'older_share',label:`Población ≥${age}`,metric:`age_${age}_count / population * 100`,unit:'%',period:'2025-01-01',source_ids:['EUSTAT_EMH_2025']},{id:'service_distance',label:`Distancia geométrica aproximada a ${serviceLabel}`,metric:'service_distance_km',unit:'km',period:'2026-09-20',source_ids:['ODE_HEALTH_CENTRES_2026','GEOEUSKADI_MUNICIPIOS_2025']}],scenario,sources,method:raw.method+' Se muestran recuentos demográficos de Work 1 unidos por municipality_code; distancias de Work 2 contrastadas con Work 1 (tolerancia 0,1 m).',limitations:[...new Set([...raw.limitations,...(raw.warnings||[]),'No demuestra acceso individual, tiempo de viaje ni capacidad de los centros.'])],trace:{execution_mode:'agent_tool',question_id:'WORK2-Q-'+ref.slice(-12),agent_version:'Work 2 tool direct/1.0 (sin coordinador del portal)',tool_calls:[{tool,arguments:raw.filters,output_ref:ref}],data_refs:sourceIds,result_ref:ref,input_files:[{path:path.relative(root,input).replaceAll('\\','/'),sha256:sha(rawBytes),rows:raw.rows_used},{path:'resultados/metricas_municipales.csv',sha256:sha(metricsBytes),rows:88},{path:'datos_preparados/metadata_sources.json',sha256:sha(metadataBytes),rows:metadata.length}],original_question:raw.question}};
fs.mkdirSync(path.dirname(path.resolve(output)),{recursive:true});fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(`${tool}: ${matchedCodes.length}/${result.analysis.total_units}; ${comparison.length} filas → ${output}`);
