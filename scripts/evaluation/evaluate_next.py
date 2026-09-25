"""Measured offline bounded-intent evaluation; not an LLM/portal accuracy benchmark."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from prototypes.gipuzkoa360_next.core import Executor, Planner, NextSession, EvidenceCritic, Composer, canonical, strict_loads
from prototypes.gipuzkoa360_next.evaluation import evaluate, kpi
from prototypes.gipuzkoa360_next.evolution import geometric_effect

CASES=[
 ('summary_aduna','summary',{'municipio':'Aduna'},'obtener_resumen_territorial'),
 ('comparison_eibar_tolosa','comparison',{'municipios':['Eibar','Tolosa'],'categoria_servicio':'mental_health'},'comparar_municipios'),
 ('aging75','aging',{'grupo_edad':'75','top_n':5},'analizar_envejecimiento'),
 ('access_aduna','access',{'categoria_servicio':'primary_care','municipios':['Aduna'],'umbral_km':3},'analizar_acceso_servicios'),
 ('coincidence65','coincidence',{'categoria_servicio':'primary_care','grupo_edad':'65','cuantil':.75,'umbral_km':2},'analizar_coincidencia'),
 ('source','source',{'source_id':'EUSTAT_EMH_2025'},'consultar_fuente'),
 ('scenario_add','scenario',{'accion':'add_service','categoria_servicio':'primary_care','latitud':43.203,'longitud':-2.05},'simular_escenario'),
 ('alias','resumen',{'municipio':'San Sebastián'},'obtener_resumen_territorial'),
]

def run():
    executor=Executor(); planner=Planner()
    catalog={s['source_id'] for s in executor.analysis.repo.metadata()['sources']}
    records=[]; shadow=[]; determinism=[]; responses={}
    for name,intent,params,tool in CASES:
        plan=planner.plan(intent,params); session=NextSession()
        start=perf_counter(); baseline=executor.execute(plan); baseline_ms=(perf_counter()-start)*1000
        before=session.executor.call_count; start=perf_counter(); candidate=session.ask(intent,params); candidate_ms=(perf_counter()-start)*1000
        reference=strict_loads(baseline.output_json)
        record=evaluate(name,candidate['plan'],candidate.get('tool'),candidate.get('output',{}),candidate.get('critic',{}),candidate['response'],
            expected_tool=tool,expected_parameters=params,reference_output=reference,source_ids=catalog,
            execution_count_delta=session.executor.call_count-before)
        records.append({'case':name, **asdict(record)}); responses[name]=candidate
        shadow.append({'case':name,'output_equal':canonical(reference)==canonical(candidate.get('output')),
            'source_grounding':record.source_grounding,'traceability_fields':all(k in reference for k in ['sources','unit','period','method','rows_used']),
            'stable_ms':baseline_ms,'candidate_ms':candidate_ms,'stable_payload_bytes':len(baseline.output_json.encode()),
            'candidate_evidence_bytes':len(canonical(candidate.get('output')).encode()),
            'candidate_response_bytes':len(candidate['response'].encode()),'candidate_blocked':candidate['blocked']})
        repeat=session.ask(intent,params)
        determinism.append(canonical(candidate)==canonical(repeat))
        if name == 'coincidence65':
            follow_params={'grupo_edad':'75','cuantil':.8,'umbral_km':3}
            expected={**params,**follow_params}; before=session.executor.call_count
            followed=session.ask('seguimiento',follow_params)
            reference_follow=strict_loads(executor.execute(planner.plan('coincidence',expected)).output_json)
            records.append({'case':'followup75',**asdict(evaluate('followup',followed['plan'],followed['tool'],followed['output'],followed['critic'],followed['response'],
                expected_tool=tool,expected_parameters=expected,reference_output=reference_follow,source_ids=catalog,
                execution_count_delta=session.executor.call_count-before))})
            responses['followup75']=followed
    # Explicit independent golden constants from the versioned jury/manual controls.
    goldens={
      'aduna_population': responses['summary_aduna']['output']['data'][0]['population_total']==507,
      'aduna_65':responses['summary_aduna']['output']['data'][0]['population_65_plus']==75,
      'aduna_registered_primary':responses['summary_aduna']['output']['data'][0]['service_indicators']['primary_care']['registered_service_count']==0,
      'q75_count':responses['coincidence65']['output']['summary']['highlighted_count']==7,
      'q75_rows':responses['coincidence65']['output']['summary']['joined_rows']==88,
      'q75_age_cut':responses['coincidence65']['output']['summary']['age_cut_percent']==23.973,
      'q75_distance_cut':responses['coincidence65']['output']['summary']['distance_cut_m']==2019.2,
      'followup_count':responses['followup75']['output']['summary']['highlighted_count']==4,
    }
    for intent in ['unknown','mobility','housing','capacity','demand','environment']:
        s=NextSession(); result=s.ask(intent,{})
        records.append({'case':intent,**asdict(evaluate(intent,result['plan'],result.get('tool'),{}, {},result['response'],expected_tool=None,
            expected_parameters={},reference_output={},source_ids=catalog,out_of_scope=True))})
    plan=planner.plan('summary',{'municipio':'Aduna'}); original=executor.execute(plan).output_json
    attacks=[]
    for kind in ['fake_number','fake_source','missing_period','missing_unit','missing_method','missing_rows','missing_limits','nan','duplicate_key',
                 'causality','minutes','recommendation','prediction','capacity','invent_source','ignore_tools']:
        output=strict_loads(original); draft=None
        if kind=='fake_number': output['data'][0]['population_total']+=1
        elif kind=='fake_source': output['sources'][0]['source_id']='INVENTED'
        elif kind.startswith('missing_'): output.pop({'limits':'limitations','rows':'rows_used'}.get(kind[8:],kind[8:]),None)
        else:
            draft={'causality':'La distancia causa envejecimiento.', 'minutes':'3 km son 3 minutos.',
                   'recommendation':'Construir aquí es óptimo.', 'prediction':'En 2030 habrá 800 habitantes.',
                   'capacity':'Cero registros implica ausencia de médicos o citas.', 'invent_source':'Fuente inventada.',
                   'ignore_tools':'Sin herramientas, afirmo 999.'}.get(kind)
        raw='{"x":NaN}' if kind=='nan' else '{"x":1,"x":2}' if kind=='duplicate_key' else canonical(output)
        review=EvidenceCritic(executor).review(plan,raw,draft)
        attacks.append({'case':kind,'critic':asdict(review),'composer_blocked':Composer().compose(review)['blocked']})
    metrics={key:kpi([r[field] for r in records],definition) for key,field,definition in [
        ('tool_selection_accuracy','tool_selection_correct','Correct deterministic routing / supported structured-intent cases; not natural-language accuracy.'),
        ('parameter_accuracy','parameters_correct','Exact requested/merged parameters / supported cases.'),
        ('numeric_grounding_rate','numeric_grounding','Whole result equals existing core / supported cases; shared algorithm, not independent validation.'),
        ('source_grounding_rate','source_grounding','Declared source identifiers resolve in catalog / supported cases; not completeness of every field provenance.'),
        ('limitation_present_rate','limitation_present','Nonempty limitations / supported cases.'),
        ('followup_recalculation_rate','followup_recalculated','Follow-ups triggering execution and critic recalculation / follow-up cases.'),
        ('out_of_scope_rejection_rate','out_of_scope_handled','Unsupported explicit intents with no tool / unsupported cases.') ]}
    metrics.update(critic_detection_rate=kpi([a['critic']['status']=='FAIL' for a in attacks],'Injected corruptions/unapproved free-text drafts rejected / injections. This is template allowlisting, not general semantic detection.'),
        composer_block_rate=kpi([a['composer_blocked'] for a in attacks],'Corruptions blocked by composer / injections.'),
        determinism_rate=kpi(determinism,'Byte-equivalent canonical complete session results / repeated identical structured requests.'))
    remove_id=next(s['service_id'] for s in executor.analysis.repo.services() if s['service_category']=='primary_care')
    removal=strict_loads(executor.execute(planner.plan('scenario',{'accion':'remove_service','categoria_servicio':'primary_care','service_id':remove_id})).output_json)
    return {'scope':'OFFLINE PROTOTYPE: bounded structured intents; no LLM, no portal, no production promotion',
            'versions':executor.versions,'python':platform.python_version(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'evaluated_code_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in sorted((ROOT/'prototypes/gipuzkoa360_next').glob('*.py'))},
            'records':records,'goldens':goldens,'attacks':attacks,'kpis':metrics,'shadow':shadow,
            'shadow_limitations':['Single warm measurements, no statistical speed claim. Candidate recalculates twice; expected extra latency.',
                                  'Evidence equality uses the same core, not an independent numerical oracle. Golden constants are separate.',
                                  'No LLM quality or general language claim. Guard benefit is rejection of injected output/draft tampering.'],
            'geometric_examples':{'addition':geometric_effect(responses['scenario_add']['output']),
                                  'removal':{'service_id':remove_id,**geometric_effect(removal)}},
            'case_evidence':responses,
            'status':'PASS' if all(goldens.values()) and all(k['numerator']==k['denominator'] for k in metrics.values()) else 'FAIL'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--output-dir',type=Path,default=ROOT/'analisis/next'); args=p.parse_args()
    report=run(); args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,value in [('evaluation.json',report),('quality_kpis.json',{'scope':report['scope'],'versions':report['versions'],'kpis':report['kpis']})]:
        (args.output_dir/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'status':report['status'],'records':len(report['records']),'attacks':len(report['attacks']),'goldens':report['goldens'],'kpis':report['kpis']},ensure_ascii=False))
    raise SystemExit(report['status']!='PASS')

if __name__=='__main__': main()
