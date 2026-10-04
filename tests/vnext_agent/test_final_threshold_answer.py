"""Regression for the observed 63-versus-82 portal explanation error."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'tests/vnext_agent/fixtures/threshold_2_3_observed.json'


@pytest.fixture
def coordinator(monkeypatch):
    monkeypatch.setitem(sys.modules, 'tools', SimpleNamespace())
    spec = importlib.util.spec_from_file_location('final_coordinator', ROOT / 'agentes/gipuzkoa360_vnext/portal_final/main.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_observed_total_includes_newly_inside(coordinator):
    payload = json.loads(FIXTURE.read_bytes())
    answer = coordinator._threshold_answer(json.dumps(payload))
    assert '| Dentro del umbral | 63 | 82 |' in answer
    assert '| Fuera del umbral | 25 | 6 |' in answer
    assert '| Municipios evaluados | 88 | 88 |' in answer
    assert '| Legazpi | 2624.8 | Fuera | Dentro |' in answer
    assert payload['threshold_transition_ledger']['answer_table_markdown'] in answer


def test_reverse_threshold_partition(coordinator):
    payload = json.loads(FIXTURE.read_bytes())
    ledger = payload['threshold_transition_ledger']
    ledger['baseline_threshold_km'], ledger['scenario_threshold_km'] = 3, 2
    ledger['counts']['outside_to_inside'], ledger['counts']['inside_to_outside'] = 0, 19
    answer = coordinator._threshold_answer(json.dumps(payload))
    assert '| Dentro del umbral | 82 | 63 |' in answer
    assert '| Fuera del umbral | 6 | 25 |' in answer


@pytest.mark.parametrize('kind', ['unverified', 'negative', 'bool', 'partition', 'row_count', 'invalid_json', 'error'])
def test_invalid_evidence_is_not_rendered(coordinator, kind):
    payload = json.loads(FIXTURE.read_bytes())
    ledger = payload['threshold_transition_ledger']
    if kind == 'unverified': ledger['verified'] = False
    elif kind == 'negative': ledger['counts']['stays_inside'] = -1
    elif kind == 'bool': ledger['counts']['stays_inside'] = True
    elif kind == 'partition': ledger['counts']['total'] = 87
    elif kind == 'row_count': ledger['changed_rows'].pop()
    elif kind == 'error': payload['status'] = 'error'
    raw = 'not JSON' if kind == 'invalid_json' else json.dumps(payload)
    assert coordinator._threshold_answer(raw) is None


def test_public_wrapper_uses_fresh_evidence(coordinator, monkeypatch):
    calls = []
    def execute(name, args):
        calls.append((name, args))
        return FIXTURE.read_text(encoding='utf-8')
    monkeypatch.setattr(coordinator, '_run', execute)
    answer = coordinator.simular_cambiar_umbral('primary_care', 2, 3)
    assert calls == [('simular_cambiar_umbral', {'categoria_servicio':'primary_care',
                      'umbral_actual_km':2, 'nuevo_umbral_km':3})]
    assert '| Dentro del umbral | 63 | 82 |' in answer


def test_portal_factory_needs_no_middleware(coordinator, monkeypatch):
    seen = {}
    def create_agent(**kwargs):
        seen.update(kwargs)
        return 'portal-agent'
    monkeypatch.setitem(sys.modules, 'langchain.agents', SimpleNamespace(create_agent=create_agent))
    model = object()
    assert coordinator.build_agent(model) == 'portal-agent'
    assert seen['model'] is model
    assert len(seen['tools']) == 10
    assert set(seen) == {'model', 'tools', 'system_prompt'}
