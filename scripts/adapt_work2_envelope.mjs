import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';

const [input,output]=process.argv.slice(2);
if(!input||!output)throw new Error('Uso: node scripts/adapt_work2_envelope.mjs envelope_agente.json resultado_canonico.json');
const envelope=JSON.parse(fs.readFileSync(input,'utf8'));
const present=x=>typeof x==='string'&&x.trim().length>0;
if(!present(envelope.run_id)||!present(envelope.agent_version)||!present(envelope.question)||!Array.isArray(envelope.tool_events)||!envelope.tool_events.length||!envelope.result||typeof envelope.result!=='object')throw new Error('Envelope del agente incompleto');
const result=structuredClone(envelope.result);
if(result.question!==envelope.question)throw new Error('La pregunta del resultado no coincide con la ejecución');
const events=envelope.tool_events.map(event=>{
  if(!present(event.tool)||!event.arguments||typeof event.arguments!=='object'||!event.output||typeof event.output!=='object')throw new Error('Evento de herramienta sin argumentos o salida observada');
  if(!Array.isArray(event.output.comparison)||!event.output.analysis||!Array.isArray(event.output.metrics)||!Array.isArray(event.output.sources))throw new Error('Salida de herramienta incompleta');
  const ref='TOOL-'+createHash('sha256').update(JSON.stringify(event.output)).digest('hex').slice(0,16);
  return {tool:event.tool,arguments:event.arguments,output_ref:ref,output:event.output};
});
const observed=events.at(-1).output;
for(const key of ['comparison','analysis','metrics','sources']){
  if(JSON.stringify(result[key])!==JSON.stringify(observed[key]))throw new Error(`El resultado no coincide con la salida observada de la herramienta: ${key}`);
}
const sourceIds=new Set(result.sources.map(s=>s.source_id));
result.trace={execution_mode:'agent',question_id:envelope.run_id,agent_version:envelope.agent_version,tool_calls:events.map(({tool,arguments:args,output_ref})=>({tool,arguments:args,output_ref})),data_refs:[...sourceIds],result_ref:events.at(-1).output_ref,input_files:observed.input_files||[]};
fs.mkdirSync(path.dirname(path.resolve(output)),{recursive:true});
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(`Adaptada ejecución ${envelope.run_id}: ${events.length} tool(s) observadas → ${output}`);
