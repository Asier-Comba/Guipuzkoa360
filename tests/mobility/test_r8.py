import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path

from prototypes.ir_y_volver import provider_r6
from scripts.mobility import build_r8


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/vnext/w1"


def load(name):
    return json.loads((DOC / name).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_canonical_evidence_rebuilds_from_frozen_provider_and_raw_oracle():
    evidence = build_r8.build_cases()
    assert evidence["runtime_changed"] is False
    assert evidence["runtime_package_sha256"] == build_r8.PACKAGE_SHA
    assert evidence["cases"]["MAIN"]["provider_result"]["itinerary"]["total_s"] == 10691
    assert evidence["cases"]["VARIATION_TIME"]["provider_result"]["itinerary"]["total_s"] == 8591
    assert evidence["cases"]["VARIATION_DURATION"]["provider_result"]["itinerary"]["total_s"] == 10372
    claim = evidence["directly_contrasted_claim"]
    assert claim["signed_delta_s"] == -2100
    assert claim["absolute_delta_s"] == 2100
    assert claim["oracle_result"]["status"] == "PASS"


def test_claim_ledger_values_are_bound_to_canonical_evidence():
    evidence = load("DELIVERY_EVIDENCE_R8.json")
    ledger = load("CLAIM_LEDGER_R8.json")
    allowed = {"direct_observation", "derived_exact", "modelled_with_assumption", "human_input"}
    assert len(ledger["claims"]) == len({c["claim_id"] for c in ledger["claims"]}) == 55
    assert {c["classification"] for c in ledger["claims"]} <= allowed
    by_id = {c["claim_id"]: c for c in ledger["claims"]}
    assert by_id["MAIN:initial_wait_s"]["value"] == evidence["cases"]["MAIN"]["provider_result"]["components_s"]["initial_wait_s"] == 180
    assert by_id["MAIN:total_s"]["value"] == 10691
    assert by_id["R8-DELTA-ZEGAMA-0930-0945"]["value"] == -2100


def test_derivation_dag_is_acyclic_and_every_claim_reaches_a_leaf():
    dag = load("DERIVATION_DAG_R8.json")
    nodes = {n["id"]: n for n in dag["nodes"]}
    assert len(nodes) == len(dag["nodes"])
    incoming = defaultdict(list)
    outgoing = defaultdict(list)
    indegree = {node_id: 0 for node_id in nodes}
    for edge in dag["edges"]:
        assert edge["from"] in nodes and edge["to"] in nodes
        incoming[edge["to"]].append(edge["from"])
        outgoing[edge["from"]].append(edge["to"])
        indegree[edge["to"]] += 1
    queue = deque(node_id for node_id, degree in indegree.items() if degree == 0)
    visited = []
    while queue:
        node_id = queue.popleft()
        visited.append(node_id)
        for target in outgoing[node_id]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    assert len(visited) == len(nodes)
    leaves = {node_id for node_id, node in nodes.items() if node["kind"] in {"source_or_model", "human_input"}}
    for claim in load("CLAIM_LEDGER_R8.json")["claims"]:
        frontier = [claim["dag_node_id"]]
        seen = set()
        reached = set()
        while frontier:
            node_id = frontier.pop()
            if node_id in seen:
                continue
            seen.add(node_id)
            if node_id in leaves:
                reached.add(node_id)
            frontier.extend(incoming[node_id])
        assert reached, claim["claim_id"]
    assert dag["runtime_status"] == "RUNTIME_FINDING_RETAINED"
    assert dag["resolution"] == "EXPLANATORY_DAG_RESOLVED_EXTERNALLY"


def test_source_ledger_is_explicit_and_local_references_exist():
    ledger = load("SOURCE_LEDGER_R8.json")
    sources = {row["source_id"]: row for row in ledger["sources"]}
    assert set(sources) == {"GTFS", "HEALTH_REGISTRY", "HEALTH_PAGE", "PADI_2026", "OSM", "MODEL", "MODEL_DEFAULTS", "HUMAN_REQUEST"}
    for source in sources.values():
        assert (ROOT / source["local_prepared_artifact"]).is_file()
        assert source["license_terms_status"]
        assert source["redistribution_status"]
    assert sources["OSM"]["license_terms_status"] == "ODbL_1.0_DOCUMENTED"
    for source_id in ("GTFS", "HEALTH_REGISTRY", "HEALTH_PAGE", "PADI_2026"):
        assert sources[source_id]["license_terms_status"] == "NOT_VERIFIED"


def test_answerability_has_one_valid_enum_and_forbids_overclaiming():
    matrix = load("MOBILITY_ANSWERABILITY_R8.json")
    allowed = set(matrix["allowed_statuses"])
    rows = {row["capability"]: row for row in matrix["capabilities"]}
    assert len(rows) == len(matrix["capabilities"]) == 25
    assert all(row["status"] in allowed for row in rows.values())
    assert rows["walking_to_centre_anchor"]["status"] == "ESTIMABLE_WITH_ASSUMPTIONS"
    assert rows["cross_origin_formal_delta"]["status"] == "UNAVAILABLE"
    assert rows["realtime"]["status"] == "UNAVAILABLE"
    assert rows["appointment_availability"]["status"] == "OUT_OF_SCOPE"


def test_status_semantics_fixtures_are_reproducible():
    semantics = load("STATUS_SEMANTICS_R8.json")
    assert {row["status"] for row in semantics["statuses"]} == {"ok", "no_feasible_journey", "unknown", "unsupported", "error"}
    for row in semantics["statuses"]:
        actual = provider_r6.plan_visit(row["fixture_request"])
        assert actual["status"] == row["status"]
        assert row["forbidden_inference"] and row["safe_recovery"]
    policy = semantics["relative_date_policy"]
    assert policy["natural_language_owner"] == "W2 agent, before calling W1"
    assert policy["expected_w1_status_for_other_date"] == "unknown"


def test_timelines_are_ordered_and_totals_remain_consistent():
    evidence = load("DELIVERY_EVIDENCE_R8.json")
    timelines = load("TIMELINE_EVIDENCE_R8.json")["timelines"]
    for timeline in timelines:
        seconds = [event["seconds_since_midnight"] for event in timeline["events"]]
        assert seconds == sorted(seconds)
        result = evidence["cases"][timeline["scenario_id"]]["provider_result"]
        assert seconds[-1] - seconds[0] == result["itinerary"]["total_s"]
        assert timeline["walking"]["classification"] == "modelled"


def test_raw_data_contrast_is_complete_and_arithmetic_is_exact():
    contrast = load("RAW_DATA_CONTRAST_R8.json")
    assert contrast["status"] == "PASS"
    assert contrast["calculation"] == "8591 - 10691 = -2100 s"
    assert contrast["final_result"] == {"signed_delta_s": -2100, "absolute_delta_s": 2100}
    assert {row["side"] for row in contrast["raw_gtfs_rows"]} == {"left", "right"}
    assert all(row["csv_line"] for row in contrast["raw_gtfs_rows"])


def test_integration_manifest_hashes_every_referenced_file():
    manifest = load("integration_r8/INTEGRATION_MANIFEST_R8.json")
    assert manifest["runtime_inclusion"] is False
    assert manifest["runtime_package_sha256"] == build_r8.PACKAGE_SHA
    assert len(manifest["files"]) == 15
    for item in manifest["files"]:
        path = ROOT / item["path"]
        assert path.is_file()
        assert digest(path) == item["sha256"]
        assert path.stat().st_size == item["bytes"]


def test_r6_runtime_and_r7_evidence_remain_byte_identical():
    expected = {
        "prototypes/ir_y_volver/provider_r6.py": "c9fe7e4c8078ba7f9bf2eb2a51e050b729d9f01e6021dbcc6909f951d2e936e8",
        "prototypes/ir_y_volver/contracts/v0.3.1/result.schema.json": "5408f0869cc243f901ce5d142865af968bac00b02113cfa0e793ed2b1a96226a",
        "prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-health-r5-20260929.json": "59fcded9e4236ee094eeb0881c4eb94f521b96fb6c8c89c881c3e9f6d5140901",
        "prototypes/ir_y_volver/walking_r5.py": "0f3a02e69f8065f892ce19a0115ae7e3c661c32725bd37a423f3d283ae1a2a7d",
        "datos_preparados/movilidad/operational_catalog_r6.json": "c7bd3cc8ffe50956ce839bec0ef90a13578160a4d5b4053b09673d2dc4c4ec17",
        "docs/vnext/w1/RUNTIME_MANIFEST_R6.json": "4968d003e225db03d7fba57c5fb72088332a4246c2a266f1fc3843deacef5940",
        "docs/vnext/w1/CONSUMER_CONFORMANCE_R7.json": "4eb364265710336ecdd86b2c541953f130f3b0a80bbefc9cf1f27904bac55dea",
        "docs/vnext/w1/METAMORPHIC_STRESS_R7.json": "8c337e5c618a189f9a2aaec5ab4e4bfa6e3f18e76847b1a3f6c8dd7d6cb3a82f",
    }
    for name, sha256 in expected.items():
        assert digest(ROOT / name) == sha256
