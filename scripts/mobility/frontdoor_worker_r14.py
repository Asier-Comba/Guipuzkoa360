"""Independent offline flat-boundary exercise against an unchanged extracted ZIP."""
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import random
import sys
import time
import typing

REQUIRED = ['origin_id', 'destination_id', 'date', 'appointment_time', 'duration_minutes']
OPTIONAL = ['arrival_margin_minutes', 'boarding_margin_minutes', 'walking_profile_id', 'snapshot_id', 'return_deadline']
ORIGINS = ['zegama_center_stops', 'segura_herriko_plaza_stops', 'idiazabal_center_stops']


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def producer_result(envelope):
    value = envelope.get('raw_result_json')
    return json.loads(value) if isinstance(value, str) else value


def valid_domain_result(envelope):
    raw = producer_result(envelope)
    return isinstance(raw, dict) and raw.get('status') in {'ok', 'no_feasible_journey'}


def generated(index, base):
    rng = random.Random(360114 + index)
    request = {**base, 'origin_id': ORIGINS[index % 3]}
    mode = index % 10
    if mode < 3:
        request.update(appointment_time=rng.choice(['09:30', '09:45', '10:15', '11:00']), duration_minutes=rng.choice([1, 20, 26, 720]))
        if mode == 1:
            request.update(arrival_margin_minutes=10, boarding_margin_minutes=3)
        elif mode == 2:
            request.update(arrival_margin_minutes=rng.choice([0, 1, 45, 240]), boarding_margin_minutes=rng.choice([0, 1, 15, 120]))
        return request, False, 'valid_domain'
    fields = ['origin_id', 'destination_id', 'date', 'duration_minutes', 'arrival_margin_minutes', 'snapshot_id', 'appointment_time']
    key = fields[mode - 3]
    bad = {
        'origin_id': ['', 'not_an_origin', 42, [], {}],
        'destination_id': ['', 'not_a_destination', False, [], {}],
        'date': ['', '2026-02-30', 'tomorrow', 42, {}],
        'duration_minutes': [0, 721, '20', True, 1.5, [], {}],
        'arrival_margin_minutes': [-1, 241, '10', True, [], {}],
        'snapshot_id': ['', 'not_a_snapshot', 42, [], {}],
        'appointment_time': ['', '25:00', '09:61', 930, [], {}],
    }
    request[key] = rng.choice(bad[key])
    return request, True, key


def run(config):
    started = time.perf_counter()
    root = Path(config['root']).resolve()
    sys.path.insert(0, str(root))
    def offline(event, args):
        if event in {'socket.connect', 'socket.getaddrinfo'}:
            raise RuntimeError('R14 independent worker: network disabled')
    sys.addaudithook(offline)
    main = importlib.import_module('main')
    tools = importlib.import_module('tools')
    assert Path(main.__file__).parent == root and Path(tools.__file__).parent == root
    # Test-only fixed correlation ID; candidate bytes and production UUID unchanged.
    main.uuid4 = lambda: type('Correlation', (), {'hex': 'W1_R14'})()
    sig = inspect.signature(main.plan_visit)
    hints = typing.get_type_hints(main.plan_visit)
    assert list(sig.parameters) == REQUIRED + OPTIONAL
    assert [hints[k] for k in REQUIRED] == [str, str, str, str, int]
    assert all(sig.parameters[k].default is inspect.Parameter.empty for k in REQUIRED)
    assert all(sig.parameters[k].default is None for k in OPTIONAL)
    assert hints['arrival_margin_minutes'] == hints['boarding_margin_minutes'] == int | None
    assert all(hints[k] == str | None for k in OPTIONAL[2:])
    assert len(main.TOOLS) == 9
    report = dict(status='PASS', signature=str(sig), signature_scope='LOCAL_EXPECTED_NOT_STUDIO_SERVED',
                  tools=9, isolated=bool(sys.flags.isolated), root=str(root), cwd=str(Path.cwd()),
                  seed=360114, wrapper_exceptions=0, mapping_mismatches=0, silent_defaults=0,
                  invalid_accepted=0, valid_rejected=0, semantic_mismatches=0,
                  cases=0, statuses={}, families={}, records=[], failures=[], network='BLOCKED')
    input_hash, output_hash = hashlib.sha256(), hashlib.sha256()
    seen = set()
    original_execute = tools.execute
    captured = []
    def spy(name, arguments, request_id, **kwargs):
        captured.append((name, arguments, request_id, kwargs.get('root')))
        return original_execute(name, arguments, request_id, **kwargs)
    tools.execute = spy

    def exercise(case_id, kwargs, invalid=False, valid=False, detailed=False):
        expected = {k: kwargs[k] for k in REQUIRED}
        expected.update({k: kwargs[k] for k in OPTIONAL if k in kwargs and kwargs[k] is not None})
        captured.clear()
        try:
            flat = json.loads(main.plan_visit(**kwargs))
        except Exception as error:
            report['wrapper_exceptions'] += 1
            raise AssertionError(f'{case_id}: wrapper exception {error}') from error
        if captured != [('plan_visit', {'request': expected}, 'W1_R14', root)]:
            report['mapping_mismatches'] += 1
            raise AssertionError(f'{case_id}: exact execute boundary mismatch: {captured}')
        direct_env = original_execute('plan_visit', {'request': expected}, 'W1_R14', root=root)
        direct = json.loads(tools.public_result(direct_env, root=root))
        if canonical(direct) != canonical(flat):
            report['semantic_mismatches'] += 1
            raise AssertionError(f'{case_id}: entire public result differs')
        if invalid and (flat['status'] == 'ok' or flat['claims'] or any(o.get('status') == 'ok' for o in flat['outcomes'])):
            report['invalid_accepted'] += 1
            raise AssertionError(f'{case_id}: invalid input has authoritative computation')
        if valid and not valid_domain_result(direct_env):
            report['valid_rejected'] += 1
            raise AssertionError(f'{case_id}: supported valid domain rejected: {flat["status"]}')
        report['cases'] += 1
        report['statuses'][flat['status']] = report['statuses'].get(flat['status'], 0) + 1
        data = canonical(kwargs)
        seen.add(data)
        input_hash.update(data + b'\n')
        output_hash.update(canonical(flat) + b'\n')
        if detailed:
            report['records'].append(dict(case_id=case_id, kwargs=kwargs, expected_request=expected,
                                          execute_root=str(root), public_result=flat, direct_envelope=direct_env))
        return flat

    try:
        if config.get('fixtures'):
            for case in config['fixtures']:
                exercise(case['case_id'], case['kwargs'], case.get('invalid', False), detailed=True)
            base = config['base']
            omitted = exercise('omitted', base, detailed=True)
            none = exercise('all_none', {**base, **dict.fromkeys(OPTIONAL)}, detailed=True)
            explicit = exercise('explicit_defaults', {**base, 'arrival_margin_minutes': 10, 'boarding_margin_minutes': 3}, detailed=True)
            assert canonical(omitted) == canonical(none), 'None changed omission provenance'
            a, b = report['records'][-3]['direct_envelope'], report['records'][-1]['direct_envelope']
            report['default_provenance'] = {'omitted_equals_none': True, 'omitted': a.get('raw_result_json'), 'explicit': b.get('raw_result_json')}
            # Raw results may be JSON strings: inspect provenance and arithmetic without guessing public shape.
            raw_a = json.loads(a['raw_result_json']) if isinstance(a['raw_result_json'], str) else a['raw_result_json']
            raw_b = json.loads(b['raw_result_json']) if isinstance(b['raw_result_json'], str) else b['raw_result_json']
            assert raw_a != raw_b, 'Explicit defaults lost provenance distinction'
            assert raw_a['components_s'] == raw_b['components_s']
            assert raw_a['itinerary'] == raw_b['itinerary'] and raw_a['walking'] == raw_b['walking']
            pa = {row['field']: row for row in raw_a['parameter_provenance']}
            pb = {row['field']: row for row in raw_b['parameter_provenance']}
            for key in ['arrival_margin_minutes', 'boarding_margin_minutes']:
                assert pa[key]['value'] == pb[key]['value']
                assert pa[key]['origin'] == 'model_default' and pb[key]['origin'] == 'human_explicit'
            report['default_provenance']['distinct_raw'] = True
        else:
            for index in range(config['shard'], config['count'], config['shards']):
                kwargs, invalid, family = generated(index, config['base'])
                exercise(f'FUZZ_{index}', kwargs, invalid=invalid, valid=not invalid)
                report['families'][family] = report['families'].get(family, 0) + 1
                if report['cases'] % 250 == 0:
                    print(f"shard{config['shard']}: {report['cases']} checked", file=sys.stderr, flush=True)
    except Exception as error:
        report['status'] = 'FAIL'
        report['failures'].append(str(error))
    report.update(distinct_payloads=len(seen), input_sha256=input_hash.hexdigest(), output_sha256=output_hash.hexdigest(),
                  runtime_s=round(time.perf_counter() - started, 3),
                  import_hashes={n: hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for n, m in [('main', main), ('tools', tools)]})
    print(json.dumps(report, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    run(json.load(sys.stdin))
