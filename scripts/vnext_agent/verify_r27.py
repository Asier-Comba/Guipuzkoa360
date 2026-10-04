"""All R26 inherited raw/oracle/fault/property gates on integrated R27 bytes."""
import argparse
import io
import zipfile
from pathlib import Path
from scripts.vnext_agent import verify_r26 as prior, build_r27 as build


def run(output):
    prior.build = build
    result = prior.run(output)
    import json
    report = json.loads(output.read_bytes())
    report['inherited_parity_changed_members'] = report.pop('changed_members')
    report['inherited_parity_base'] = report['base']
    report.pop('base_r21', None)
    report.pop('base_r25_runtime', None)
    with zipfile.ZipFile(io.BytesIO(build.blob(build.BASE_ZIP))) as old, zipfile.ZipFile(build.ZIP) as new:
        assert old.namelist() == new.namelist()
        changed = [n for n in old.namelist() if old.read(n) != new.read(n)]
        assert changed == ['main.py', 'tools.py']
    report.update(
        generation='R27-integrated',
        base_r26_runtime=build.BASE,
        changed_members=changed,
        main_identical_to_r26=False,
        other_members_identical_to_r26=True,
        projection_delta='Deterministic threshold-transition ledger plus bounded presentation guards; raw analytical data and healthcare engine unchanged.',
    )
    output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')
    return {k: v for k, v in report.items() if k != 'records'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=build.ROOT / 'outputs/r27/offline-audit.json')
    result = run(parser.parse_args().output)
    print(__import__('json').dumps(result, sort_keys=True))
    raise SystemExit(result['status'] != 'PASS')
