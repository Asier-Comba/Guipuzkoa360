"""Support-generator regressions; candidate execution recorded separately."""
from collections import Counter
import math
import pytest
from scripts.mobility.frontdoor_worker_r14 import REQUIRED, OPTIONAL, ORIGINS, canonical, generated, valid_domain_result
from scripts.mobility.r13_properties import BASE


def test_flat_fields_are_closed_and_distinct():
    assert len(REQUIRED) == len(OPTIONAL) == 5
    assert len(set(REQUIRED + OPTIONAL)) == 10
    assert 'request' not in REQUIRED + OPTIONAL


def test_fuzz_reproducible_and_has_three_origins():
    first = [generated(i, BASE) for i in range(120)]
    assert first == [generated(i, BASE) for i in range(120)]
    assert {q['origin_id'] for q, bad, _ in first if not bad} == set(ORIGINS)
    assert BASE['appointment_time'] == '09:45'


def test_fuzz_campaign_has_valid_and_invalid_inputs():
    distribution = Counter(generated(i, BASE)[2] for i in range(5000))
    assert distribution['valid_domain'] == 1500
    assert len(distribution) == 8
    assert all(distribution[key] == 500 for key in distribution if key != 'valid_domain')


def test_index_partition_is_disjoint_and_complete():
    shards = [set(range(i, 5000, 4)) for i in range(4)]
    assert set.union(*shards) == set(range(5000))
    assert sum(map(len, shards)) == 5000


@pytest.mark.parametrize('value', [math.nan, math.inf, -math.inf])
def test_evidence_canonicalization_rejects_nonfinite(value):
    with pytest.raises(ValueError):
        canonical({'duration_minutes': value})


def test_no_none_or_explicit_default_in_omitted_family():
    for index in range(0, 100, 10):
        q, bad, _ = generated(index, BASE)
        assert not bad and set(q) == set(REQUIRED)
    q, _, _ = generated(1, BASE)
    assert q['arrival_margin_minutes'] == 10 and q['boarding_margin_minutes'] == 3


@pytest.mark.parametrize('public,raw,expected', [('valid', 'ok', True), ('no_data', 'no_feasible_journey', True), ('error', 'error', False), ('no_data', 'unknown', False)])
def test_status_layers_are_not_conflated(public, raw, expected):
    assert valid_domain_result({'status': public, 'raw_result_json': {'status': raw}}) is expected
