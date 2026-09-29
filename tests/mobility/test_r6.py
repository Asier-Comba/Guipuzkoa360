import copy
import hashlib
import json
import tempfile
from pathlib import Path

from prototypes.ir_y_volver import provider, provider_r5, provider_r6
from prototypes.ir_y_volver.schema_r5 import validate
from scripts.mobility.build_health_r5 import ROOT
from scripts.mobility.build_r6 import build_catalog, build_schemas

BASE = dict(origin_id='zegama_center_stops', destination_id='beasain_official_centre_anchor',
            date='2026-09-29', appointment_time='09:45', duration_minutes=20)


def test_implicit_and_explicit_default_are_distinguished():
    implicit = provider_r6.plan_visit(BASE)
    explicit = provider_r6.plan_visit({**BASE, 'boarding_margin_minutes': 3,
                                      'walking_profile_id': provider_r5.PROFILE})
    assert implicit['itinerary'] == explicit['itinerary']
    by_kind = {c['kind']: c for c in implicit['components']}
    assert by_kind['initial_wait']['basis'] == 'model_default'
    assert by_kind['initial_wait']['source_refs'] == ['MODEL_DEFAULTS']
    by_kind = {c['kind']: c for c in explicit['components']}
    assert by_kind['initial_wait']['basis'] == 'user_input'
    assert by_kind['initial_wait']['source_refs'] == ['USER']
    assert by_kind['destination_walk_outbound']['source_refs'][-1] == 'USER'


def test_user_hash_contains_only_explicit_fields():
    result = provider_r6.plan_visit(BASE)
    user = next(s for s in result['sources'] if s['source_id'] == 'USER')
    raw = json.dumps(BASE, sort_keys=True, ensure_ascii=False, allow_nan=False,
                     separators=(',', ':')).encode()
    assert user['source_sha256'] == hashlib.sha256(raw).hexdigest()
    assert next(x for x in result['parameter_provenance']
                if x['field'] == 'boarding_margin_minutes')['origin'] == 'model_default'
    assert next(x for x in result['parameter_provenance']
                if x['field'] == 'duration_minutes')['origin'] == 'human_explicit'


def test_r6_keeps_r5_arithmetic_and_snapshot():
    old, new = provider_r5.plan_visit(BASE), provider_r6.plan_visit(BASE)
    for key in ('normalized_request', 'status', 'snapshot_id', 'itinerary', 'components_s',
                'walking', 'health_destination', 'limitations', 'assumptions', 'error'):
        assert new[key] == old[key]


def test_r4_explicit_dispatch_is_byte_equivalent():
    q = dict(origin_id='zegama_center_stops', destination_id='beasain_center_stop_pair',
             date='2026-09-29', appointment_time='09:30', duration_minutes=30,
             snapshot_id=provider.DEFAULT_SNAPSHOT_ID)
    assert provider_r6.plan_visit(q) == provider.plan_visit(q)


def test_closed_schemas_accept_outputs():
    build_schemas()
    root = ROOT / 'prototypes/ir_y_volver/contracts/v0.3.1'
    samples = {'result': provider_r6.plan_visit(BASE),
               'comparison': provider_r6.compare_visits([BASE, {**BASE, 'duration_minutes': 26}]),
               'capabilities': provider_r6.get_capabilities()}
    for name, sample in samples.items():
        schema = json.loads((root / f'{name}.schema.json').read_bytes())
        validate(sample, schema, schema)


def test_component_invariants_and_references():
    result = provider_r6.plan_visit(BASE)
    components = result['components']
    assert sum(c['seconds'] for c in components) == result['itinerary']['total_s']
    assert all(c['seconds'] == c['end_s'] - c['start_s'] for c in components)
    assert all(a['end_s'] == b['start_s'] for a, b in zip(components, components[1:]))
    source_ids = {s['source_id'] for s in result['sources']}
    assert all(set(c['source_refs']) <= source_ids for c in components)
    assert {c['kind'] for c in components if c['source_refs'] == ['GTFS']} == {
        'outbound_vehicle', 'return_vehicle'}


def test_catalog_is_derived_and_one_to_one():
    first = build_catalog(); second = build_catalog()
    assert first == second
    assert {x['municipality_code'] for x in first['origins']} == {'20025', '20043', '20070'}
    assert len({x['origin_id'] for x in first['origins']}) == len(first['origins']) == 3
    assert first['destination']['verification']['entrance_verified'] is False
    schema = json.loads((ROOT / 'prototypes/ir_y_volver/contracts/v0.3.1/catalog.schema.json').read_bytes())
    validate(first, schema, schema)


def test_negative_boundaries_and_mixed_comparison():
    assert provider_r6.plan_visit({**BASE, 'date': '2026-09-30'})['status'] == 'unknown'
    assert provider_r6.plan_visit({**BASE, 'walking_profile_id': 'unknown'})['status'] == 'error'
    assert provider_r6.plan_visit({**BASE, 'destination_id': 'unknown'})['status'] == 'unsupported'
    assert provider_r6.plan_visit({**BASE, 'appointment_time': '23:50'})['status'] == 'unsupported'
    r4q = dict(origin_id='zegama_center_stops', destination_id='beasain_center_stop_pair',
               date='2026-09-29', appointment_time='09:30', duration_minutes=30,
               snapshot_id=provider.DEFAULT_SNAPSHOT_ID)
    mixed = provider_r6.compare_visits([BASE, r4q])
    assert [x['schema_version'] for x in mixed['results']] == ['0.3.1', '0.2.0']
    assert mixed['comparisons'][0]['comparability'] == 'not_comparable'


def test_corrupted_walking_link_is_controlled_unknown():
    original = provider_r5.MANIFEST
    manifest = json.loads(original.read_bytes())
    snapshot_path = original.parent / manifest['file']
    snapshot = json.loads(snapshot_path.read_bytes())
    snapshot['walking_links']['7219']['outbound']['seconds'] += 1
    raw = (json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder)
        (target / manifest['file']).write_bytes(raw)
        base_name = snapshot['base_snapshot_id'] + '.json'
        (target / base_name).write_bytes((original.parent / base_name).read_bytes())
        manifest['sha256'] = hashlib.sha256(raw).hexdigest()
        (target / 'allowlist.json').write_text(json.dumps(manifest), encoding='utf-8')
        provider_r5.MANIFEST = target / 'allowlist.json'
        try:
            result = provider_r6.plan_visit(BASE)
        finally:
            provider_r5.MANIFEST = original
    assert result['status'] == 'unknown'
    assert result['error']['code'] == 'invalid_health_snapshot'


def test_r5_historic_files_unchanged():
    manifest = json.loads((ROOT / 'docs/vnext/w1/RUNTIME_MANIFEST_R5.json').read_bytes())
    for entry in manifest['files']:
        path = ROOT / entry['path']
        assert path.stat().st_size == entry['bytes']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
