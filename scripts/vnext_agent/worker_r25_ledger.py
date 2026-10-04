"""Cold-process boundary observer with real provider; no LLM simulation."""
import copy
import json
from pathlib import Path
import sys
from scripts.vnext_agent.worker_r24_scope import run as observe_scope


def run(root):
    result = observe_scope(root)
    import tools as m
    root = Path(root).resolve()
    original = m._r24_mobility_view
    args = {'request': dict(origin_id='segura_herriko_plaza_stops',
            destination_id='beasain_official_centre_anchor', date='2026-09-29',
            appointment_time='10:00', duration_minutes=30)}
    result['additional'] = m.strict_loads(m.public_call('plan_visit', args, 'TEST', root=root))
    result['ledger_faults'] = {}
    for field in ('components_s', 'time_summary'):
        def tampered(*a, **kw):
            view = copy.deepcopy(original(*a, **kw))
            s = view['scenarios'][0]
            if field == 'components_s': s[field]['return_wait_s'] += 1
            else: s[field]['total_hms'] = '0 h 0 min 0 s'
            return view
        m._r24_mobility_view = tampered
        result['ledger_faults'][field] = m.strict_loads(m.public_call('plan_visit', args, 'TEST', root=root))
    m._r24_mobility_view = original
    result['unsupported'] = {}
    for field, value in [('date','2027-01-01'), ('origin_id','mi casa'), ('appointment_time',''), ('duration_minutes',-1)]:
        altered = copy.deepcopy(args); altered['request'][field] = value
        result['unsupported'][field] = m.strict_loads(m.public_call('plan_visit', altered, 'TEST', root=root))
    return result


if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1]), ensure_ascii=False, allow_nan=False))
