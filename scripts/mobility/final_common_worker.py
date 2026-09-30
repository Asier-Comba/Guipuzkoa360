"""Offline paired territorial tools; no model, private corpus or runtime writes."""
import importlib.util
import json
from pathlib import Path
import sys
import time

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()


def producer_result(envelope):
    value = envelope.get('raw_result_json')
    return json.loads(value) if isinstance(value, str) else value


def run(config):
    root = Path(config['root']).resolve()
    sys.path.insert(0, str(root))
    sys.addaudithook(lambda event, args: (_ for _ in ()).throw(RuntimeError('offline'))
                     if event in {'socket.connect', 'socket.getaddrinfo'} else None)
    import tools
    spec = importlib.util.spec_from_file_location('frozen_v4', config['v4'])
    v4 = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = v4
    spec.loader.exec_module(v4)
    v4._default_data_dir = lambda: root / 'datos_preparados'
    rows = []
    for case in config['cases']:
        name, args = case['tool'], case['args']
        before = time.perf_counter()
        old = json.loads(getattr(v4, name)(**args, detalle=True))
        v4_s = time.perf_counter() - before
        before = time.perf_counter()
        envelope = tools.execute(name, args, 'FINAL_COMMON', root=root)
        public = json.loads(tools.public_result(envelope, root=root))
        next_s = time.perf_counter() - before
        raw = producer_result(envelope)
        # Same prepared files and identical full territorial raw result required.
        identical = canonical(old) == canonical(raw)
        rows.append(dict(case_id=case['id'], tool=name, args=args, v4=old,
                         vnext_raw=raw, vnext_public=public, identical_raw=identical,
                         v4_s=v4_s, vnext_s=next_s))
    return dict(status='PASS' if all(r['identical_raw'] for r in rows) else 'FAIL',
                records=rows, scope='Offline common deterministic tools; not LLM A/B or winner')


if __name__ == '__main__':
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(run(json.load(sys.stdin)), ensure_ascii=False, allow_nan=False))
