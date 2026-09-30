import hashlib
import json

from prototypes.ir_y_volver import provider_r6 as p
from prototypes.ir_y_volver.schema_r5 import validate
from scripts.mobility.audit_r7 import mutation_matrix, provenance_audit, validate_health_result
from scripts.mobility.build_health_r5 import ROOT
from scripts.mobility.build_r7 import build_conformance, build_labels
from scripts.mobility.package_r6 import build as build_r6_package

DOC=ROOT/'docs/vnext/w1';DATA=ROOT/'datos_preparados/movilidad'
BASE=dict(origin_id='zegama_center_stops',destination_id='beasain_official_centre_anchor',
          date='2026-09-29',appointment_time='09:45',duration_minutes=20)


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def test_r6_runtime_manifest_and_identity_are_frozen():
    manifest=json.loads((DOC/'RUNTIME_MANIFEST_R6.json').read_bytes())
    assert manifest['package_sha256']=='c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910'
    assert manifest['package_bytes']==129365
    for entry in manifest['files']:
        path=ROOT/entry['path'];assert path.stat().st_size==entry['bytes'];assert digest(path)==entry['sha256']
    assert digest(DATA/'operational_catalog_r6.json')=='c7bd3cc8ffe50956ce839bec0ef90a13578160a4d5b4053b09673d2dc4c4ec17'


def test_labels_are_reproducible_closed_and_source_derived():
    first=build_labels();second=build_labels();assert first==second
    schema=json.loads((DATA/'consumer_labels_r7.schema.json').read_bytes());validate(first,schema,schema)
    assert len(first['stops'])==9 and {x['short_name'] for x in first['routes']}=={'GO01'}
    assert first['destination']['entrance_verified'] is False


def test_conformance_pack_has_fourteen_distinct_cases_and_classification():
    pack=build_conformance();assert len(pack['cases'])==14
    assert len({x['case_id'] for x in pack['cases']})==14
    assert any(x['expected']['evidence_class']=='CONTRACT_SEMANTICS' for x in pack['cases'])
    assert all('evidence_class' in x['expected'] for x in pack['cases'])
    assert set(pack['evidence_hashes'])=={'gtfs_zip','health_snapshot','result_schema_0_3_1',
      'operational_catalog_r6','consumer_labels_r7','walking_model'}


def test_consumer_semantic_validator_accepts_real_output():
    assert validate_health_result(p.plan_visit(BASE),BASE)


def test_provenance_finding_is_explicit_and_not_silently_fixed():
    audit=provenance_audit(p.plan_visit(BASE),BASE)
    assert audit['status']=='PASS_WITH_EXPLICIT_FINDING'
    finding=audit['findings'][0]
    assert finding['id']=='W1-R7-F01' and finding['severity']=='MEDIUM'
    assert finding['contract_change_required_now'] is False


def test_mutation_matrix_has_no_gap():
    matrix=mutation_matrix();assert matrix['mutations']==29
    assert matrix['counts']['GAP']==0 and matrix['critical_high_gaps']==0


def test_seeded_stress_and_isolation_evidence_passed():
    stress=json.loads((DOC/'METAMORPHIC_STRESS_R7.json').read_bytes())
    isolation=json.loads((DOC/'ISOLATION_R7.json').read_bytes())
    assert stress['seed']==360007 and stress['cases']==500 and stress['first_counterexample'] is None
    assert sum(stress['distribution'].values())==500 and stress['status']=='PASS'
    assert isolation['status']=='PASS' and all(v is True for k,v in isolation.items() if k!='status')


def test_package_integrity_evidence_and_rebuild_match():
    audit=json.loads((DOC/'PACKAGE_INTEGRITY_R7.json').read_bytes())
    assert audit['status']=='PASS' and all(audit['checks'].values())
    rebuilt=build_r6_package(write_manifest=False)
    assert rebuilt['total_bytes']==audit['uncompressed_bytes']


def test_consumer_checklist_covers_required_gates():
    checklist=json.loads((DOC/'CONSUMER_CHECKLIST_R7.json').read_bytes())
    ids={x['id'] for x in checklist['pre_acceptance_checks']}
    assert ids=={'provider_version','snapshot','scenario','destination','modelled_access','entrance_verified',
      'source_roles','parameter_provenance','totals','trip_stop_identity','status','comparison_semantics'}
    assert len(checklist['minimum_model_view'])>=12


def test_r7_support_files_are_not_silently_added_to_r6_runtime():
    manifest=json.loads((DOC/'RUNTIME_MANIFEST_R6.json').read_bytes())
    assert not any('r7' in x['path'].casefold() for x in manifest['files'])
