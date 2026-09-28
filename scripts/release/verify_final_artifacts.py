"""Adversarial release checks independent of the public presentation."""
from __future__ import annotations
import ast
import copy
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.ops.runtime_identity import compute_runtime_sha, runtime_files
spec = importlib.util.spec_from_file_location('build_jury', ROOT / 'scripts/release/build_jury_data.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


def validate_visual(candidate, expected):
    # Full equality checks every row/value, source, geometry and scenario, not just KPIs.
    return candidate == expected


def audit():
    tree = ast.parse((ROOT / 'agentes/gipuzkoa360/portal/main.py').read_text(encoding='utf-8'))
    contexts = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'STUDIO_CONTEXT_FILES' for t in n.targets))
    expected_files = runtime_files(ROOT)
    declared_files = [
        'agentes/gipuzkoa360/portal/main.py',
        'agentes/gipuzkoa360/portal/tools.py',
        'agentes/gipuzkoa360/requirements.txt',
        *contexts,
    ]
    runtime = {}
    for file in expected_files:
        actual = (ROOT / file).read_bytes()
        runtime[file] = {'exists': True, 'sha256': hashlib.sha256(actual).hexdigest()}
    runtime_sha = compute_runtime_sha(ROOT)
    manifest = json.loads((ROOT / 'datos_preparados/runtime_manifest.json').read_text(encoding='utf-8'))
    manifest_ok = all((ROOT / item['path']).stat().st_size == item['bytes'] and hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256'] for item in manifest['files'])
    expected = exporter.build()
    html = (ROOT / 'resultados/demo.html').read_text(encoding='utf-8')
    embedded = json.loads(re.search(r'<script id="jury-data" type="application/json">(.*?)</script>',html,re.S).group(1))
    data = json.loads((ROOT / 'analisis/jury_visual_data.json').read_text(encoding='utf-8'))
    attacks = []
    def attack(name, corrupt):
        candidate = copy.deepcopy(expected)
        corrupt(candidate)
        attacks.append({'attack': name, 'rejected': not validate_visual(candidate, expected)})
    attack('alter a visible population percentage', lambda d: d['cases'][0]['output']['data'][0].__setitem__('pct_65_plus',99))
    attack('fixed 25 percent cut',lambda d:d['cases'][0].__setitem__('age_cut_percent',25))
    attack('drop a highlighted municipality',lambda d:d['cases'][0]['municipalities'].pop())
    attack('reuse 65+ answer for 75+ follow-up',lambda d:d['cases'].__setitem__(1,copy.deepcopy(d['cases'][0])))
    attack('invent source',lambda d:d['sources'][0].__setitem__('source_id','TEST_FAKE_SOURCE'))
    attack('remove geometry',lambda d:d['geometry']['features'].pop())
    attack('reverse scenario difference sign',lambda d:d['aduna_scenario']['data'][0].__setitem__('difference_absolute_m',999))
    attack('claim live execution for saved calculation',lambda d:d.__setitem__('execution_mode','live'))
    attack('drop non-highlighted row',lambda d:d['cases'][0]['output']['data'].pop())
    checks = {'runtime_inventory': declared_files == expected_files,
              'runtime_identity': runtime_sha == compute_runtime_sha(ROOT), 'manifest': manifest_ok,
              'visual_data_equals_recalculation': validate_visual(data,expected),
              'html_equals_recalculation': validate_visual(embedded,expected),
              'nine_mutations_rejected': all(x['rejected'] for x in attacks),
              'no_fixed_25_cut': 'r.pct>=25' not in (ROOT/'scripts/build_results.mjs').read_text(encoding='utf-8'),
              'saved_calculation_label': 'esta página no es una conversación en vivo' in html}
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
            'runtime_sha256':runtime_sha,'runtime_files':runtime,
            'manifest_entries':len(manifest['files']),'visual_mutations':attacks}


if __name__ == '__main__':
    report = audit()
    (ROOT/'analisis/final_artifact_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'status':report['status'],'checks':report['checks']},indent=2))
    raise SystemExit(0 if report['status']=='PASS' else 1)
