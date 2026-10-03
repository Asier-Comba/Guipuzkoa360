import fs from 'node:fs/promises';
import path from 'node:path';
import {Presentation,PresentationFile,FileBlob} from 'file:///C:/Users/oier.dunabeitia/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import {finalizePresentation,resolvePresentationFont} from 'file:///C:/Users/oier.dunabeitia/.codex/plugins/cache/openai-primary-runtime/presentations/26.905.11957/skills/presentations/container_tools/artifact_tool_utils.mjs';
const root=path.resolve('.');
const build=path.join(root,'outputs/r25/private-build');
const out=path.join(root,'outputs/r25/presentation');
await fs.mkdir(out,{recursive:true});
const font=resolvePresentationFont({fontFamily:'Arial'});
const p=Presentation.create({slideSize:{width:960,height:540}});
const color={bg:'#071F36',cyan:'#72D4F7',white:'#FFFFFF',muted:'#C3D5E2'};
function text(s,t,x,y,w,h,size=25,ink=color.white,bold=false){const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=t;a.text.style={typeface:font,fontSize:size,color:ink,bold,autoFit:'none'};return a;}
function slide(title,note){const s=p.slides.add();s.background.fill=color.bg;text(s,title,48,50,864,75,40,color.white,true);text(s,'GIPUZKOA 360',48,500,700,25,15,color.muted);text(s,String(p.slides.items.length),875,500,40,25,15,color.muted);s.speakerNotes.textFrame.setText(note);return s;}
function table(s,values,y,widths){const t=s.tables.add({rows:values.length,columns:values[0].length,left:48,top:y,width:864,height:values.length*37,columnWidths:widths,values});t.borders.assign({fill:'#28475F',width:0.6,style:'solid'});for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){let a=t.getCell(r,c);a.fill=r===0?'#123C56':color.bg;a.text.style={typeface:font,fontSize:20,color:r===0?color.cyan:color.white,bold:r===0};}return t;}
let s=slide('GIPUZKOA 360','Alcance: análisis territorial. No se presenta el cálculo de visitas sanitarias. Equipo proporcionado por el usuario.');
text(s,'Envejecimiento y servicios sanitarios\nen los 88 municipios de Gipuzkoa',48,157,864,128,38,color.cyan,true);
text(s,'Datos para saber dónde profundizar',48,310,864,55,28);
text(s,'DeustoAI Labs / Universidad de Deusto\nOier Duñabeitia, Asier Comba y Hugo Fernández',48,415,864,62,21,color.muted);
s=slide('La pregunta territorial','Pregunta y destinatario de la entrega. La propuesta es exploratoria, no priorización de inversión.');
text(s,'¿Dónde coinciden una mayor proporción de personas mayores y una mayor distancia a servicios sanitarios registrados?',48,145,864,140,31,color.cyan,true);
text(s,'Para personal técnico municipal y territorial.\n\nPermite comparar municipios y decidir qué información adicional necesita un estudio más completo.',48,307,864,145,25);
s=slide('Qué hace el agente','Funciones territoriales de la versión v4. Fuentes y metodología: https://github.com/Asier-Comba/Guipuzkoa360');
text(s,'Interpreta la pregunta y ejecuta un cálculo sobre datos preparados.',48,150,864,85,29,color.cyan,true);
text(s,'Permite consultar un municipio, comparar grupos de edad y explorar escenarios hipotéticos.\n\nLa respuesta conserva cifras, unidades, periodo, fuentes y límites. Las hipótesis no se presentan como predicciones.',48,263,864,185,27);
s=slide('Caso principal: siete municipios','Evidencia real de v4, herramienta analizar_coincidencia. 88 filas. 65 o más, atención primaria, periodo 2025-01-01, cuantil 0.75, umbral 2 km. Fuente: conversación territorial guardada y salida JSON.');
text(s,'65 o más años y atención primaria. Cortes: 23,973 % y 2.019,2 m.',48,124,864,44,21,color.cyan);
table(s,[['Municipio','Población 65+','Distancia geométrica'],['Legazpi','27,170 %','2.624,8 m'],['Ezkio-Itsaso','25,949 %','2.110,1 m'],['Hondarribia','25,808 %','2.583,5 m'],['Hernialde','25,387 %','2.192,5 m'],['Oñati','24,806 %','2.149,6 m'],['Idiazabal','24,528 %','2.311,2 m'],['Errenteria','24,302 %','3.925,5 m']],180,[330,235,299]);
s=slide('Otra edad, otro nivel de exigencia','Evidencia existente de v4 y visualización territorial. 75 o más, cuantil 0.80, umbral 3 km, periodo 2025-01-01. Cortes 12.9796 % y 2138.6 m. Se analizan 88 filas.');
text(s,'Con 75 o más años y un corte más exigente, aparecen cuatro municipios.',48,143,864,87,31,color.cyan,true);
text(s,'Legazpi, Errenteria, Hondarribia e Idiazabal.\n\nSon consultas distintas. Cambiar la edad o el criterio hace que el agente recalcule.\n\nEl radio de 3 km se muestra aparte: no determina por sí solo la coincidencia estadística.',48,254,864,205,25);
s=slide('Cómo se calcula y de dónde sale','Fuentes: https://github.com/Asier-Comba/Guipuzkoa360/blob/main/FUENTES.md y metodología del repositorio. Las fechas se contrastaron con la salida real territorial.');
table(s,[['Fuente','Información','Referencia'],['Eustat','Población municipal','01/01/2025'],['geoEuskadi','Geometría municipal','07/05/2025'],['Open Data Euskadi','Registro sanitario','20/09/2026']],151,[280,320,264]);
text(s,'El cuantil 0,75 o 0,80 fija un corte relativo en cada indicador. Se cruzan los municipios que alcanzan ambos cortes.\n\nLas fuentes tienen fechas distintas. No describen una misma fotografía temporal.',48,330,864,137,23);
s=slide('Límites que importan','Limitaciones documentadas de la versión territorial y las fuentes. No hay evidencia de tiempos de viaje, plantilla, citas ni capacidad.');
text(s,'La distancia se calcula desde un punto municipal, no desde cada vivienda.',48,145,864,88,31,color.cyan,true);
text(s,'No mide tiempos de viaje ni accesibilidad real.\n\nCero servicios registrados no demuestra ausencia de atención sanitaria.\n\nNo conocemos citas disponibles, personal ni capacidad. El análisis no predice el futuro ni decide dónde invertir.',48,259,864,204,25);
s=slide('Un resultado que se puede contrastar','Enlaces públicos: https://asier-comba.github.io/Guipuzkoa360/ y https://github.com/Asier-Comba/Guipuzkoa360. La visualización es territorial, con resultados guardados, no un agente conectado.');
text(s,'Legazpi: 27,170 % de población de 65 o más años y 2.624,8 m al registro más cercano.',48,145,864,105,32,color.cyan,true);
text(s,'La conversación muestra el cálculo real.\nLa visualización permite explorar los resultados territoriales.\nEl repositorio conserva datos preparados, fuentes y metodología.',48,282,864,128,25);
text(s,'asier-comba.github.io/Guipuzkoa360/\ngithub.com/Asier-Comba/Guipuzkoa360',48,425,864,55,20,color.muted);
const candidatePath=path.join(build,'territorial-candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(candidatePath);
const skill='C:/Users/oier.dunabeitia/.codex/plugins/cache/openai-primary-runtime/presentations/26.905.11957/skills/presentations';
const finalPath=path.join(out,'GIPUZKOA 360.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath,finalPath,pythonExecutable:'C:/Users/oier.dunabeitia/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','9144000,5143500','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','4','--require-native-table-slide','6'],explicitTotalSlideCount:8,requiredNativeTableOwnerSlides:[4,6],fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:path.join(build,'presentation-validation.json')});
const final=await PresentationFile.importPptx(await FileBlob.load(finalPath));
for(let i=0;i<final.slides.items.length;i++){const png=await final.slides.items[i].export({format:'png',scale:1});await fs.writeFile(path.join(build,`final-slide-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));}
console.log(JSON.stringify({finalPath,result}));
