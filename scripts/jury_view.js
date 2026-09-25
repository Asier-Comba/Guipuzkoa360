/* Browser view: formatting and selection only; numerical results come from the agent. */
const jury=JSON.parse(document.getElementById('jury-data').textContent);
const el=id=>document.getElementById(id);
const number=(n,d=1)=>new Intl.NumberFormat('es-ES',{maximumFractionDigits:d,minimumFractionDigits:d}).format(n);
function cell(row,value){const td=document.createElement('td');td.textContent=value;row.append(td);}
function metric(label,value){const box=document.createElement('div');box.className='metric';const strong=document.createElement('strong');strong.textContent=value;const span=document.createElement('span');span.textContent=label;box.append(strong,span);return box;}
function drawCase(index){
 const c=jury.cases[index],out=c.output,age='pct_'+c.age_group+'_plus';
 document.querySelectorAll('.case-button').forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));
 el('answer').textContent=c.highlighted_count+' municipios cumplen ambos cortes en las 88 filas analizadas';
 el('names').textContent=c.municipalities.join(' · ');
 el('kpis').replaceChildren(metric('Corte '+c.age_group+'+',number(c.age_cut_percent,4)+' %'),metric('Corte de distancia',number(c.distance_cut_m)+' m'),metric('Cuantil solicitado',number(c.quantile,2)),metric('Umbral de proximidad',number(c.threshold_km,0)+' km'));
 el('method').textContent='Porcentaje = población del grupo / total × 100. Destacado si alcanza ambos cuantiles; el umbral no sustituye al cuantil. Población: '+out.period+'.';
 el('age-label').textContent=c.age_group+'+ (%)';
 el('rows').replaceChildren();el('all-rows').replaceChildren();
 out.data.forEach(r=>{const tr=document.createElement('tr');[r.municipality_name,number(r[age],3),number(r.nearest_distance_m),r.highlighted?'Sí':'No'].forEach(v=>cell(tr,v));el('all-rows').append(tr);if(r.highlighted){const short=document.createElement('tr');[r.municipality_name,number(r[age],3),number(r.nearest_distance_m)].forEach(v=>cell(short,v));el('rows').append(short);}});
 el('trace').textContent='Cálculo local guardado\nHerramienta: '+c.tool+'\nArgumentos: '+JSON.stringify(c.arguments)+'\nFilas usadas: '+out.rows_used+'\nRuntime: '+jury.runtime_sha+'\nFuentes: '+out.sources.map(s=>s.source_id).join(', ');
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 600 470');svg.setAttribute('role','group');svg.setAttribute('aria-label','Mapa de los 88 municipios');
 const rings=f=>f.geometry.type==='Polygon'?f.geometry.coordinates:f.geometry.coordinates.flat();
 const cosine=Math.cos(43*Math.PI/180),points=jury.geometry.features.flatMap(f=>rings(f).flat()),xs=points.map(p=>p[0]*cosine),ys=points.map(p=>p[1]);
 const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),scale=Math.min(560/(maxX-minX),430/(maxY-minY));
 const project=p=>[20+(p[0]*cosine-minX)*scale,450-(p[1]-minY)*scale];
 jury.geometry.features.forEach(f=>{const code=String(f.properties.municipality_code),r=out.data.find(r=>r.municipality_code===code);if(!r)throw Error('Geometría sin dato: '+code);const p=document.createElementNS(ns,'path');p.setAttribute('d',rings(f).map(ring=>ring.map((v,i)=>{const a=project(v);return(i?'L':'M')+a[0].toFixed(2)+' '+a[1].toFixed(2);}).join(' ')+' Z').join(' '));p.setAttribute('fill',r.highlighted?'#cf9b43':'#d8e6e4');p.setAttribute('fill-rule','evenodd');p.setAttribute('stroke','#4a686c');p.setAttribute('stroke-width','.65');p.setAttribute('tabindex','0');p.setAttribute('role','button');p.setAttribute('data-code',code);const label=r.municipality_name+': '+number(r[age],3)+' %, '+number(r.nearest_distance_m)+' m'+(r.highlighted?', destacado':'');p.setAttribute('aria-label',label);const t=document.createElementNS(ns,'title');t.textContent=label;p.append(t);const select=()=>{el('selected').textContent=label;svg.querySelectorAll('path').forEach(x=>x.setAttribute('stroke-width',x===p?'2.5':'.65'));};p.addEventListener('click',select);p.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}});svg.append(p);});
 el('map').replaceChildren(svg);el('selected').textContent='Selecciona un municipio con el ratón o el teclado.';
}
jury.cases.forEach((c,i)=>{const b=document.createElement('button');b.className='case-button';b.textContent=c.age_group+'+ · q'+number(c.quantile,2)+' · '+number(c.threshold_km,0)+' km';b.addEventListener('click',()=>drawCase(i));el('cases').append(b);});
const aduna=jury.aduna_scenario.data.find(r=>r.municipality_name==='Aduna');
el('scenario-values').replaceChildren(metric('Distancia observada',number(aduna.baseline_distance_m)+' m'),metric('Distancia hipotética',number(aduna.scenario_distance_m)+' m'),metric('Diferencia',number(aduna.difference_absolute_m)+' m'),metric('Registros sanitarios totales',jury.aduna_scenario.scenario.baseline.service_count+' → '+jury.aduna_scenario.scenario.scenario.service_count));
jury.sources.filter(s=>['EUSTAT_EMH_2025','ODE_HEALTH_CENTRES_2026','GEOEUSKADI_MUNICIPIOS_2025'].includes(s.source_id)).forEach(s=>{const div=document.createElement('div');div.className='source';const a=document.createElement('a');a.href=s.url;a.textContent=s.title;a.target='_blank';a.rel='noopener';const p=document.createElement('p');p.textContent=s.source_id+' · '+s.reference_period+' · '+s.unit;div.append(a,p);el('source-list').append(div);});
drawCase(0);
