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


def turn(payload, name='simular_cambiar_umbral'):
    return [SimpleNamespace(type='human', content='change threshold'),
            SimpleNamespace(type='tool', name=name, content=json.dumps(payload))]


def test_observed_total_includes_newly_inside(coordinator):
    payload = json.loads(FIXTURE.read_bytes())
    answer = coordinator._threshold_answer(turn(payload))
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
    answer = coordinator._threshold_answer(turn(payload))
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
    messages = turn(payload)
    if kind == 'invalid_json': messages[-1].content = 'not JSON'
    assert coordinator._threshold_answer(messages) is None


def test_historical_threshold_never_answers_new_question(coordinator):
    messages = turn(json.loads(FIXTURE.read_bytes()))
    messages.append(SimpleNamespace(type='human', content='different question'))
    assert coordinator._threshold_answer(messages) is None


def test_other_tools_and_multiple_analyses_keep_reasoning(coordinator):
    payload = json.loads(FIXTURE.read_bytes())
    assert coordinator._threshold_answer(turn(payload, 'plan_visit')) is None
    messages = turn(payload)
    messages.append(copy.deepcopy(messages[-1]))
    assert coordinator._threshold_answer(messages) is None


def test_real_graph_finishes_from_tool_without_second_model_call(coordinator, monkeypatch):
    pytest.importorskip('langchain')
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import AIMessage, HumanMessage
    from langchain_core.outputs import ChatGeneration, ChatResult

    class OneCallModel(BaseChatModel):
        calls: int = 0

        @property
        def _llm_type(self): return 'threshold-regression-test'

        def bind_tools(self, tools, **kwargs): return self

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            self.calls += 1
            assert self.calls == 1, 'The final threshold answer must bypass model arithmetic'
            message = AIMessage(content='', tool_calls=[{'name':'simular_cambiar_umbral', 'args':{
                'categoria_servicio':'primary_care', 'umbral_actual_km':2, 'nuevo_umbral_km':3}, 'id':'test-1'}])
            return ChatResult(generations=[ChatGeneration(message=message)])

    monkeypatch.setattr(coordinator, '_run', lambda name, args: FIXTURE.read_text(encoding='utf-8'))
    model = OneCallModel()
    result = coordinator.build_agent(model).invoke({'messages':[HumanMessage(content='Cambia 2 a 3 km')]})
    assert model.calls == 1
    assert '| Dentro del umbral | 63 | 82 |' in result['messages'][-1].content
