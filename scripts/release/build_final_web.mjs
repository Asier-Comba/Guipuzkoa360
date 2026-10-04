import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const html=fs.readFileSync(path.join(root,'resultados/index.html'),'utf8');
const literal=html.match(/const visits = ([\s\S]*?);\s*function showVisit/);
if(!literal) throw new Error('Missing visit data');
const visits=vm.runInNewContext('('+literal[1]+')',Object.create(null),{timeout:1000});
const evidence={reviewed_on:'2026-10-04',service_date:'2026-09-29',
  portal_version:'GIPUZKOA 360 · R28 final · v2',
  code_revision:'a20026663f85c984b1acde54c6a77f294c4d44a4',
  integration:'https://github.com/Asier-Comba/Guipuzkoa360/pull/36',
  journey_scope:'From origin stops to the modelled Beasain health-centre point and back to origin stops.',
  limitations:['Stored verified examples; no new query is executed on this page.',
    'Scheduled transport and modelled walking; no realtime or home-to-home route.',
    'Conditional comparison, not observed savings or an appointment recommendation.',
    'No appointment availability, healthcare capacity or verified physical entrance.'],visits};
fs.mkdirSync(path.join(root,'resultados/evidencia'),{recursive:true});
fs.writeFileSync(path.join(root,'resultados/evidencia/final_visits.json'),JSON.stringify(evidence,null,2)+'\n');
fs.copyFileSync(path.join(root,'tests/vnext_agent/fixtures/threshold_2_3_observed.json'),path.join(root,'resultados/evidencia/threshold_2_3_observed.json'));
for(const file of ['demo.html','control_center.html','informe_principal.html','scenario_comparison.html']){
  const target=path.join(root,'resultados',file);
  const original=fs.readFileSync(target,'utf8');
  const updated=original.replace('<nav aria-label="Navegación"><a href="demo.html">','<nav aria-label="Navegación"><a href="index.html">Inicio</a><a href="demo.html">');
  fs.writeFileSync(target,updated.replace(/\r\n/g,'\n'));
}
console.log('Final landing, stored visit evidence and return navigation ready.');
