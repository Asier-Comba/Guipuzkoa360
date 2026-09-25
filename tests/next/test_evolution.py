from dataclasses import asdict
import pytest
from prototypes.gipuzkoa360_next.core import Executor, NextSession, Planner, strict_loads
from prototypes.gipuzkoa360_next.evolution import QueryPatternRecord, ImprovementProposal, capability_gaps, geometric_effect
from prototypes.gipuzkoa360_next.providers import DemographyProvider, MobilityProvider
from prototypes.gipuzkoa360_next.evaluation import evaluate, kpi

def test_future_provider_fail_closed():
    with pytest.raises(ValueError): MobilityProvider().execute()

def test_provider_delegates():
    e = Executor()
    assert strict_loads(DemographyProvider(e).execute('aging',{}).output_json)['status'] == 'ok'
    with pytest.raises(ValueError): DemographyProvider(e).execute('housing',{})

def test_privacy_gap_has_no_raw_query_and_cannot_self_deploy():
    patterns = [QueryPatternRecord('unsupported','mobility',False,'requires_data','lt_1s','mobility')]*3
    assert 'query' not in asdict(patterns[0])
    assert capability_gaps(patterns) == [{'type':'CapabilityGapProposal','capability':'mobility','frequency':3,'status':'REQUIRES_DATA','automatic_implementation':False}]
    assert capability_gaps(patterns[:2]) == []

def test_invalid_improvement_type():
    with pytest.raises(ValueError): ImprovementProposal('AUTO_DEPLOY',(),1,'','',(),'')

@pytest.mark.parametrize('action',['add_service','remove_service'])
def test_actual_geometric_effect(action):
    e = Executor()
    params = {'accion':action, 'categoria_servicio':'primary_care','latitud':43.203,'longitud':-2.05}
    if action == 'remove_service': params['service_id']=next(s['service_id'] for s in e.analysis.repo.services() if s['service_category']=='primary_care')
    result = strict_loads(e.execute(Planner().plan('scenario',params)).output_json)
    effect = geometric_effect(result)
    assert effect['sum_distance_change_m'] >= 0
    assert effect['affected_municipalities'] == sum(r['difference_absolute_m']!=0 for r in result['data'])
    assert 'Not social benefit' in effect['limitations'][1]

def test_evaluator_detects_wrong_tool_arguments_and_numbers():
    r=NextSession().ask('summary',{'municipio':'Aduna'})
    fields = dict(query='summary',plan=r['plan'],tool='wrong',tool_output=r['output'],critic=r['critic'],response=r['response'],
        expected_tool=r['tool'],expected_parameters={'municipio':'Tolosa'},reference_output={},source_ids=set())
    score=evaluate(**fields)
    assert not score.tool_selection_correct and not score.parameters_correct
    assert not score.numeric_grounding and not score.source_grounding
    assert kpi([True,False,None],'test')['value'] == .5
    assert kpi([],'test')['value'] is None
    unsupported=evaluate('',{},None,{}, {},'',expected_tool=None,expected_parameters={},reference_output={},source_ids=set(),out_of_scope=True)
    assert unsupported.out_of_scope_handled is False
