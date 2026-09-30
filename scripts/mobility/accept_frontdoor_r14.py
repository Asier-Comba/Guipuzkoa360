"""W1 independent pinned-package audit and cold flat-boundary acceptance."""
import argparse
import ast
import concurrent.futures
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import zipfile
from scripts.mobility import intake_candidate_r12 as gate
from scripts.mobility.verify_r13 import dump

ROOT = Path(__file__).resolve().parents[2]
WORKER = Path(__file__).with_name('frontdoor_worker_r14.py')
HOTFIX = '094745b26bc57aee5cc1a5e003401743d96a914f'
BASE = '8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243'
ZIP_HASH = '9c6fa5c692df178afe36366c6291e7c0e7c3da06134381b09d853f55d6707252'
MANIFEST_HASH = 'd6c0122b475284c468fdfc3e343b9ab0d9d175cf20513048c915281cedf4e911'


def blob(sha, path):
    return subprocess.check_output(['git', 'show', f'{sha}:{path}'], cwd=ROOT)


def audit(package, manifest):
    assert gate.digest(package.read_bytes()) == ZIP_HASH
    assert gate.digest(manifest.read_bytes()) == MANIFEST_HASH
    metadata = gate.strict_json(manifest.read_text(encoding='utf-8'))
    checked = gate.inspect(package, metadata)
    assert checked['compatible'] and not checked['policy'], 'package policy/pin'
    old_bytes = blob(BASE, 'scripts/vnext_agent/dist/gipuzkoa360-vnext-w2.zip')
    assert gate.digest(old_bytes) == '3951b290b6ca59c336886a3f0acee77a68036d4fbcbc06c2cedfe22400c08616'
    with zipfile.ZipFile(package) as new, zipfile.ZipFile(io.BytesIO(old_bytes)) as old:
        assert new.namelist() == old.namelist(), 'member inventory changed'
        changed = [name for name in new.namelist() if new.read(name) != old.read(name)]
        assert changed == ['main.py'], changed
        old_ast, new_ast = ast.parse(old.read('main.py')), ast.parse(new.read('main.py'))
        def stable(tree):
            return [ast.dump(n, include_attributes=False) for n in tree.body
                    if not (isinstance(n, ast.FunctionDef) and n.name == 'plan_visit')
                    and not (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SYSTEM_PROMPT' for t in n.targets))]
        assert stable(old_ast) == stable(new_ast), 'unrelated coordinator AST change'
        old_prompt = next(ast.literal_eval(n.value) for n in old_ast.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SYSTEM_PROMPT' for t in n.targets))
        new_prompt = next(ast.literal_eval(n.value) for n in new_ast.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SYSTEM_PROMPT' for t in n.targets))
        assert new_prompt.startswith(old_prompt)
        addition = new_prompt[len(old_prompt):]
        assert all(token not in addition for token in ['-35', '10691', '8591', '2100', '09:30', '09:45', 'MAIN', 'VARIATION'])
        assert addition.strip() == 'plan_visit recibe campos estructurados separados; nunca envíes una petición en prosa como argumento de la tool.\nCuando incluyas una cifra territorial o tasa derivada, indica brevemente fuente y periodo, y su derivación cuando cambie la interpretación.'
        def rebuild():
            out = io.BytesIO()
            with zipfile.ZipFile(out, 'w') as archive:
                for info in old.infolist():
                    archive.writestr(info, new.read(info.filename), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            return gate.digest(out.getvalue())
        builds = [rebuild(), rebuild()]
        assert builds == [ZIP_HASH, ZIP_HASH], 'independent double build differs'
        paths = gate.declared_freeze(new)
        assert set(paths) == set(metadata['freeze_paths'])
    return dict(status='PASS', hotfix_sha=HOTFIX, package_sha256=ZIP_HASH, manifest_sha256=MANIFEST_HASH,
                package_bytes=package.stat().st_size, changed_members=changed, double_build=builds,
                preserved_members=len(metadata['members']) - 1, declared_paths=paths, integrity=checked,
                prompt_audit='Only two generic rules; no answer gold, totals, phrase routing or capability additions',
                source_diff=subprocess.check_output(['git', 'diff', '--name-only', BASE, HOTFIX], cwd=ROOT, text=True).splitlines())


def worker(root, config, output):
    env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'TMPDIR', 'COMSPEC', 'PATHEXT', 'LANG', 'LC_ALL'}}
    env['PYTHONIOENCODING'] = 'utf-8'
    config = {**config, 'root': str(root)}
    run = subprocess.run([sys.executable, '-I', str(WORKER)], input=json.dumps(config, ensure_ascii=False, allow_nan=False),
                         capture_output=True, text=True, encoding='utf-8', cwd=root, env=env, timeout=1800)
    assert run.returncode == 0, run.stderr
    report = gate.strict_json(run.stdout)
    report['progress_log'] = run.stderr
    assert report['import_hashes']['main'] == 'bc955c57558ae3f8f00aa6d8ad1452732ad7ead40faea794fa9e0f1e39ee6f23'
    assert report['import_hashes']['tools'] == '46498d6be4f65642784e3a721e408b7d22a0910f937f91660d095b7e57de807c'
    dump(output, report)
    return report


def run(package, manifest, output, fuzz):
    started = time.perf_counter()
    output.mkdir(parents=True, exist_ok=True)
    proof = audit(package, manifest)
    dump(output / 'package.json', proof)
    truth = gate.strict_json((ROOT / 'docs/vnext/w1/FINAL_ORACLE_R13.json').read_text(encoding='utf-8'))
    assert gate.digest((ROOT / 'docs/vnext/w1/FINAL_ORACLE_R13.json').read_bytes()) == '2f57634fcab245a63c95b2a4e833895f664b8a43b52592214470b913b6b1ba53'
    base = truth['cases'][0]['structured_request']
    with tempfile.TemporaryDirectory(prefix='g360-w1-r14-') as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(package) as archive:
            # Complete verified extraction, never a W2 checkout import.
            archive.extractall(root)
        if not fuzz:
            fixtures = [{'case_id': c['case_id'], 'kwargs': c['request']} for c in gate.acceptance_cases() if c['operation'] == 'plan' and isinstance(c['request'], dict) and all(k in c['request'] for k in ['origin_id', 'destination_id', 'date', 'appointment_time', 'duration_minutes'])]
            fixtures += [{'case_id': 'TRUTH_' + c['case_id'], 'kwargs': c['structured_request']} for c in truth['cases']]
            fixtures += [{'case_id': origin, 'kwargs': {**base, 'origin_id': origin}} for origin in ['zegama_center_stops', 'segura_herriko_plaza_stops', 'idiazabal_center_stops']]
            for key, value in [('origin_id', ''), ('destination_id', 'bad'), ('date', '2026-02-30'), ('duration_minutes', '20'), ('arrival_margin_minutes', -1), ('snapshot_id', 'bad'), ('appointment_time', '')]:
                fixtures.append({'case_id': 'INVALID_' + key, 'kwargs': {**base, key: value}, 'invalid': True})
            result = worker(root, dict(base=base, fixtures=fixtures), output / 'targeted.json')
            print(json.dumps({k: result[k] for k in ['status', 'cases', 'failures', 'runtime_s']}), flush=True)
            return result['status'] == 'PASS'
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(worker, root, dict(base=base, shard=i, shards=4, count=5000), output / f'fuzz-{i}.json') for i in range(4)]
            reports = [f.result() for f in futures]
        report = dict(status='PASS' if all(r['status'] == 'PASS' for r in reports) and sum(r['cases'] for r in reports) == 5000 else 'FAIL',
                      cases=sum(r['cases'] for r in reports), executions=2 * sum(r['cases'] for r in reports), seed=360114,
                      partition='global generator index modulo 4; separate cold offline workers',
                      classification='Independent generated binding/mapping fuzz, not independent tests or LLM acceptance',
                      runtime_s=round(time.perf_counter() - started, 3),
                      failures=[v for r in reports for v in r['failures']],
                      counters={k: sum(r[k] for r in reports) for k in ['wrapper_exceptions', 'mapping_mismatches', 'silent_defaults', 'invalid_accepted', 'valid_rejected', 'semantic_mismatches']},
                      reports=[{'path': f'fuzz-{i}.json', 'sha256': gate.digest((output / f'fuzz-{i}.json').read_bytes())} for i in range(4)])
        dump(output / 'fuzz-summary.json', report)
        print(json.dumps(report), flush=True)
        return report['status'] == 'PASS'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fuzz', action='store_true')
    a = parser.parse_args()
    raise SystemExit(0 if run(a.package.resolve(), a.manifest.resolve(), a.output.resolve(), a.fuzz) else 1)
