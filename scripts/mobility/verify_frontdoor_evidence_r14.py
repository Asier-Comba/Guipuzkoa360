"""Bind independent flat-call records to the frozen public R13 truth pack."""
import argparse
import json
from pathlib import Path
from scripts.mobility.frontdoor_worker_r14 import producer_result
from scripts.mobility.verify_r13 import dump


def verify(truth, targeted):
    records = {r['case_id']: r for r in targeted['records']}
    totals = {}
    checks = []
    for case in truth['cases']:
        record = records['TRUTH_' + case['case_id']]
        envelope, public = record['direct_envelope'], record['public_result']
        assert public['status'] == case['expected_consumer_envelope_status']
        raw = producer_result(envelope)
        if raw is not None:
            assert raw['status'] == case['expected_status']
            assert raw['sources'] == case['source_facts']
            for key, expected in case['critical_semantic_facts'].items():
                assert raw.get(key) == expected, (case['case_id'], key)
            for claim in case['numeric_claims']:
                actual = raw['itinerary']['total_s'] if claim['metric'] == 'total_s' else raw['components_s'][claim['metric']]
                assert actual == claim['value'], (case['case_id'], claim['metric'])
            if case['numeric_claims']:
                totals[case['case_id']] = raw['itinerary']['total_s']
        else:
            assert case['case_id'] in {'ERROR', 'UNKNOWN_SNAPSHOT'}
            assert public['status'] == 'error' and not public['claims'] and not public['outcomes']
        checks.append({'case_id': case['case_id'], 'status': 'PASS', 'producer_raw_present': raw is not None})
    assert totals['MAIN'] == 10691 and totals['VARIATION'] == 8591
    assert totals['VARIATION'] - totals['MAIN'] == -2100
    return dict(status='PASS', cases=checks, contrast=truth['contrast'], scope='Structured M04 representation, not LLM or served-schema acceptance')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--targeted', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    report = verify(json.loads((root / 'docs/vnext/w1/FINAL_ORACLE_R13.json').read_bytes()), json.loads(args.targeted.read_bytes()))
    dump(args.output, report)
    print(json.dumps(report))
