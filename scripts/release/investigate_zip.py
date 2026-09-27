"""Reproduce the historical one-byte ZIP difference from committed bytes."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('package_builder', ROOT / 'scripts/agent/build_portal_package.py')
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def investigate():
    historical = json.loads(subprocess.check_output(['git', 'show', 'a1b0ecb:analisis/full_validation.json'], cwd=ROOT))['build_reproducibility']
    members = {destination: subprocess.check_output(['git', 'show', f'488f46d:{source}'], cwd=ROOT)
               for source, destination in builder.FILES.items()}
    variants = []
    for ending in ('LF', 'CRLF'):
        data = dict(members)
        if ending == 'CRLF':
            data['requirements.txt'] = data['requirements.txt'].replace(b'\n', b'\r\n')
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, content in sorted(data.items()):
                info = zipfile.ZipInfo(name, builder.FIXED_ZIP_TIME)
                info.create_system = 0  # Original Windows builder metadata.
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        payload = buffer.getvalue()
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            differences = []
            for expected in historical['members']:
                actual = archive.getinfo(expected['name'])
                if (actual.file_size, actual.CRC, list(actual.date_time)) != (expected['size'], expected['crc'], expected['timestamp']):
                    differences.append({'name': actual.filename, 'actual_bytes': actual.file_size,
                                        'expected_bytes': expected['size'], 'actual_crc': actual.CRC,
                                        'expected_crc': expected['crc']})
        variants.append({'requirements_eol': ending, 'bytes': len(payload),
                         'sha256': hashlib.sha256(payload).hexdigest(),
                         'member_differences_from_asier': differences,
                         'exact_historical_archive': hashlib.sha256(payload).hexdigest() == historical['sha256']})
    assert variants[0]['bytes'] == 48338
    assert variants[1]['bytes'] == 48339 and variants[1]['exact_historical_archive']
    assert [x['name'] for x in variants[0]['member_differences_from_asier']] == ['requirements.txt']
    report = {'status': 'PASS', 'base_sha': '488f46db7047d9393d4d4a489a869ab246c215b9',
              'root_cause': 'requirements.txt: LF (66 bytes) versus CRLF (67 bytes). All other members and original ZIP metadata unchanged.',
              'variants': variants}
    return report


if __name__ == '__main__':
    report = investigate()
    target = ROOT / 'analisis/zip_root_cause.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
