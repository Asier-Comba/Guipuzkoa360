"""Focused flat boundary tests; producer math remains in its frozen suite."""
import inspect
import pytest
from agentes.gipuzkoa360_vnext import main

BASE = dict(origin_id='origin', destination_id='destination', date='date', appointment_time='time', duration_minutes=20)

def test_required_flat_fields():
    sig = inspect.signature(main.plan_visit)
    assert list(sig.parameters) == [*BASE, 'arrival_margin_minutes', 'boarding_margin_minutes', 'walking_profile_id', 'snapshot_id', 'return_deadline']
    assert [k for k,v in sig.parameters.items() if v.default is inspect.Parameter.empty] == list(BASE)

@pytest.mark.parametrize('optional', [{}, {'arrival_margin_minutes':None}, {'arrival_margin_minutes':0}, {'boarding_margin_minutes':8}, {'duration_minutes':'20'}, {'snapshot_id':'legacy'}, {'walking_profile_id':[]}, {'return_deadline':'12:00'}])
def test_exact_mapping_and_same_return(monkeypatch, optional):
    observed = []
    marker = object()
    def capture(name, arguments):
        observed.append((name, arguments))
        return marker
    monkeypatch.setattr(main, '_run', capture)
    kwargs = {**BASE, **optional}
    assert main.plan_visit(**kwargs) is marker
    assert observed == [('plan_visit', {'request':{k:v for k,v in kwargs.items() if k in BASE or v is not None}})]

def test_old_nested_argument_rejected_at_python_signature():
    with pytest.raises(TypeError):
        main.plan_visit(request='prose')

def test_prompt_two_generic_additions_only():
    import ast
    import subprocess
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    old = subprocess.check_output(['git','show','8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243:agentes/gipuzkoa360_vnext/main.py'],cwd=root)
    old_prompt = next(ast.literal_eval(n.value) for n in ast.parse(old).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SYSTEM_PROMPT' for t in n.targets))
    assert main.SYSTEM_PROMPT.startswith(old_prompt+'\n\n')
    added = main.SYSTEM_PROMPT[len(old_prompt):]
    assert len(added.strip().splitlines()) == 2
    assert all(gold not in added for gold in ['09:30','09:45','Zegama','10691','8591','-35'])
