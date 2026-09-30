"""Deterministic final delivery manifest; support only, no runtime/portal edits."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def build(benchmark, output):
    output.mkdir(parents=True, exist_ok=True)
    for name in ['DELIVERY_COPY.md', 'FINAL_EVIDENCE.md', 'FINAL_GATE.md']:
        data = (ROOT / 'docs/vnext/final_delivery' / name).read_bytes().replace(b'\r\n', b'\n')
        assert b'C:\\' not in data and b'/Users/' not in data
        (output / name).write_bytes(data)
    reports = {}
    for name in ['public_summary.json', 'public_raw.json', 'common_summary.json', 'common_raw.json', 'common_source_identity.json', 'holdout_seal.json', 'upstream_identity.json', 'capability_claim_audit.json', 'release_state.json']:
        data = (benchmark / name).read_bytes()
        reports[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'path': 'resultados/vnext/final_benchmark/' + name}
    truth = json.loads((ROOT / 'docs/vnext/w1/FINAL_ORACLE_R13.json').read_bytes())
    metadata = json.loads((ROOT / 'datos_preparados/metadata_sources.json').read_bytes())
    manifest = dict(project='GIPUZKOA 360', team='DeustoAI Labs — Universidad de Deusto',
        members=['Oier Duñabeitia Berezo', 'Asier Comba Lopez', 'Hugo Fernández Díez'],
        audit_base='4bf975511ecea46c25662becfccb65713d381aa0', audit_head='Commit containing this manifest; exact SHA/CI in PR15/PR18/Issue16 checkpoint',
        candidate='PENDING_FINAL_AGENT_GREEN', track='PENDING_HUMAN_SELECTION', publication='PENDING_HUMAN_GATE', RELEASE_GO='NO',
        hotfix_sha='094745b26bc57aee5cc1a5e003401743d96a914f', package_sha256='9c6fa5c692df178afe36366c6291e7c0e7c3da06134381b09d853f55d6707252', package_bytes=226337,
        manifest_sha256='d6c0122b475284c468fdfc3e343b9ab0d9d175cf20513048c915281cedf4e911',
        package_url='https://github.com/Asier-Comba/Guipuzkoa360/blob/094745b26bc57aee5cc1a5e003401743d96a914f/scripts/vnext_agent/dist/r14/gipuzkoa360-r14-binding.zip',
        manifest_url='https://github.com/Asier-Comba/Guipuzkoa360/blob/094745b26bc57aee5cc1a5e003401743d96a914f/scripts/vnext_agent/dist/r14/gipuzkoa360-r14-binding-manifest.json',
        W1_RUNTIME_CHANGED='NO', V4_PRESERVED='YES', v4='195b4980fa5998b096c308296a55e452380b0371', PORTAL_LLM='FAIL_M05_EXTERNAL_EVIDENCE_NOT_RETESTED_BY_W1',
        current_agent={'critical': 0, 'high': 1, 'medium': 3}, w1_historical_medium=3,
        ci={'w1_r14': 36770251523, 'hotfix': 36765784442, 'w3_f4fd0a3': 36774476469, 'this_audit': 'Exact same-SHA result in final checkpoint'},
        sources={'health_truth_source_facts': truth['cases'][0]['source_facts'], 'territorial_metadata': metadata},
        contrast=truth['contrast'], reports=reports,
        links=['https://asier-comba.github.io/Guipuzkoa360/', 'https://github.com/Asier-Comba/Guipuzkoa360'],
        distribution={'raw_HTML_PADI': 'EXCLUDED_NOT_VERIFIED', 'health_derivative': 'PINNED_DERIVED_NOT_RAW', 'OSM': 'OpenStreetMap contributors; ODbL1.0'},
        holdout='SEALED_NOT_OPENED; custody not physically verified by W1',
        next_exact_action='Agent owner reviews optional-field generation against M05 and served interface; changed candidate needs new identity and independent acceptance')
    data = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    (output / 'FINAL_MANIFEST.json').write_bytes(data)
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--benchmark', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.benchmark, args.output), sort_keys=True))
