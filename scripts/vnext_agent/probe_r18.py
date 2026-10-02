"""Read-only baseline measurement; never changes a package or calls a model."""
import io
import json
import tempfile
import zipfile
from pathlib import Path
from scripts.vnext_agent import verify_r15 as verifier
from scripts.vnext_agent.build_r17 import ZIP

def run():
    data = ZIP.read_bytes()
    cases = verifier.make_cases(data, json.loads(verifier.ORACLE.read_bytes()))
    for c in cases:
        if c['tool'] == 'obtener_resumen_territorial' and 'periodo' in c['arguments']:
            c['route'] = 'internal'
        c['keep_view'] = True
    cases.append({'id':'access_all','tool':'analizar_acceso_servicios','arguments':{'categoria_servicio':'primary_care','umbral_km':2},'keep_view':True})
    with tempfile.TemporaryDirectory(prefix='r18-baseline-') as d:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(d)
        result = verifier.run_worker(Path(d), cases)
    out = Path('outputs/r18/baseline.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    metrics = sorted({(c['metric_id'],c['unit'],c['entity_type']) for r in result['records'].values() for c in r.get('view',{}).get('claims',[])})
    print(json.dumps({'metrics':metrics,'access_summary_claims':[c for c in result['records']['access_all']['view']['claims'] if c['evidence_path'].startswith('/summary/')]},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    run()
