"""Historical R14 contract, loaded from its immutable accepted Git source.

These tests preserve what R14 promised; current public-interface regressions
belong in test_r15_public_contract.py. No engine call is needed here.
"""
import ast
import inspect
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
R14_SHA = "094745b26bc57aee5cc1a5e003401743d96a914f"
SOURCE_PATH = "agentes/gipuzkoa360_vnext/main.py"


@pytest.fixture(scope="module")
def main():
    source = subprocess.check_output(
        ["git", "show", f"{R14_SHA}:{SOURCE_PATH}"], cwd=ROOT
    )
    module = ModuleType("agentes.gipuzkoa360_vnext._historical_r14_main")
    module.__package__ = "agentes.gipuzkoa360_vnext"
    module.__file__ = f"{R14_SHA}:{SOURCE_PATH}"
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module

BASE = dict(origin_id='origin', destination_id='destination', date='date', appointment_time='time', duration_minutes=20)

def test_required_flat_fields(main):
    sig = inspect.signature(main.plan_visit)
    assert list(sig.parameters) == [*BASE, 'arrival_margin_minutes', 'boarding_margin_minutes', 'walking_profile_id', 'snapshot_id', 'return_deadline']
    assert [k for k,v in sig.parameters.items() if v.default is inspect.Parameter.empty] == list(BASE)

@pytest.mark.parametrize('optional', [{}, {'arrival_margin_minutes':None}, {'arrival_margin_minutes':0}, {'boarding_margin_minutes':8}, {'duration_minutes':'20'}, {'snapshot_id':'legacy'}, {'walking_profile_id':[]}, {'return_deadline':'12:00'}])
def test_exact_mapping_and_same_return(main, monkeypatch, optional):
    observed = []
    marker = object()
    def capture(name, arguments):
        observed.append((name, arguments))
        return marker
    monkeypatch.setattr(main, '_run', capture)
    kwargs = {**BASE, **optional}
    assert main.plan_visit(**kwargs) is marker
    assert observed == [('plan_visit', {'request':{k:v for k,v in kwargs.items() if k in BASE or v is not None}})]

def test_old_nested_argument_rejected_at_python_signature(main):
    with pytest.raises(TypeError):
        main.plan_visit(request='prose')

def test_prompt_two_generic_additions_only(main):
    old = subprocess.check_output(['git','show','8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243:agentes/gipuzkoa360_vnext/main.py'],cwd=ROOT)
    old_prompt = next(ast.literal_eval(n.value) for n in ast.parse(old).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SYSTEM_PROMPT' for t in n.targets))
    assert main.SYSTEM_PROMPT.startswith(old_prompt+'\n\n')
    added = main.SYSTEM_PROMPT[len(old_prompt):]
    assert len(added.strip().splitlines()) == 2
    assert all(gold not in added for gold in ['09:30','09:45','Zegama','10691','8591','-35'])
