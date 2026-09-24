import fs from 'node:fs';
import path from 'node:path';

const [input, output, geometryFile, metadataFile] = process.argv.slice(2);
if (!input || !output) throw new Error('Uso: node scripts/enrich_work1_result.mjs resultado_agente.json salida.json [runtime_municipios.geojson] [metadata_sources.json]');
const root=path.resolve(import.meta.dirname,'..');
const geoPath=path.resolve(geometryFile||path.join(root,'datos_preparados/runtime_municipios.geojson'));
const metaPath=path.resolve(metadataFile||path.join(root,'datos_preparados/metadata_sources.json'));
const result=JSON.parse(fs.readFileSync(input,'utf8'));
const geo=JSON.parse(fs.readFileSync(geoPath,'utf8'));
const metadata=JSON.parse(fs.readFileSync(metaPath,'utf8'));
const source=metadata.find(s=>s.source_id==='GEOEUSKADI_MUNICIPIOS_2025');
if (!source) throw new Error('Falta fuente GEOEUSKADI_MUNICIPIOS_2025 en metadata_sources.json');
const byCode=new Map(geo.features.map(f=>[String(f.properties.municipality_code),f]));
if (byCode.size!==geo.features.length) throw new Error('Códigos geométricos duplicados');
result.map_features=result.comparison.map(row=>{
  const feature=byCode.get(String(row.unit_id));
  if (!feature) throw new Error(`Sin geometría para ${row.unit_id}`);
  return {unit_id:String(row.unit_id),geometry:feature.geometry,source_ids:[source.source_id]};
});
if (!result.sources.some(s=>s.source_id===source.source_id)) result.sources.push({source_id:source.source_id,title:source.title,url:source.url,period:source.reference_period,unit:'polígono municipal',license:source.license,method:'Contorno municipal simplificado para visualización; fuente maestra en datos_preparados/municipios.geojson'});
result.trace.data_refs=[...new Set([...result.trace.data_refs,source.source_id])];
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(`Geometría añadida para ${result.map_features.length} unidades: ${output}`);
