"""Offline generated-frontdoor parity and deterministic fuzz; no LLM claims."""
import argparse
import ast
import hashlib
import inspect
import json
import random
import socket
import subprocess
import sys
import tempfile
import time
import typing
from pathlib import Path
import zipfile
from scripts.vnext_agent.build_r14_binding import ROOT, ZIP, MANIFEST, build

def emit(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8', newline='\n')

def run(oracle, output, count=5000):
    started = time.monotonic()
    first = build()
    assert build() == first, 'double-build drift'
    original = subprocess.check_output(['git','show','8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243:scripts/vnext_agent/dist/gipuzkoa360-vnext-w2.zip'], cwd=ROOT)
    import io
    with tempfile.TemporaryDirectory(prefix='g360-r14-') as directory, zipfile.ZipFile(ZIP) as z, zipfile.ZipFile(io.BytesIO(original)) as old:
        changed = [n for n in z.namelist() if z.read(n) != old.read(n)]
        assert changed == ['main.py']
        z.extractall(directory)
        sys.path.insert(0, directory)
        # No model/framework installed: studio fallback is the identity decorator.
        import main
        import tools
        main.uuid4 = lambda: type('FixedID', (), {'hex':'R14_PARITY'})()
        socket.socket = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('network denied'))
        sig = inspect.signature(main.plan_visit)
        hints = typing.get_type_hints(main.plan_visit)
        required = [k for k,p in sig.parameters.items() if p.default is inspect.Parameter.empty]
        assert required == ['origin_id','destination_id','date','appointment_time','duration_minutes']
        assert 'request' not in sig.parameters and len(sig.parameters) == 10
        assert [hints[k] for k in required] == [str,str,str,str,int]
        assert all(p.default is None for k,p in sig.parameters.items() if k not in required)
        schema = {'type':'object','properties':{k:{'type':(['integer' if k.endswith('_minutes') else 'string','null'] if k not in required else 'integer' if k.endswith('_minutes') else 'string')} for k in sig.parameters},'required':required,'additionalProperties':False}
        emit(output/'SERVED_INTERFACE_R14.json', {'status':'EXPECTED_LOCAL_SIGNATURE_NOT_STUDIO_SERVED','signature':str(sig),'expected_schema':schema,'decorator':'identity fallback; platform schema NOT_OBSERVED','tools':len(main.TOOLS)})
        original_run = main._run
        mapping = []
        def spy(name, arguments):
            mapping.append((name, arguments))
            return original_run(name, arguments)
        main._run = spy
        truth = json.loads(oracle.read_bytes())
        assert hashlib.sha256(oracle.read_bytes()).hexdigest() == '2f57634fcab245a63c95b2a4e833895f664b8a43b52592214470b913b6b1ba53'
        base = truth['cases'][0]['structured_request']
        fixtures = [(c['case_id'], c['structured_request']) for c in truth['cases']]
        fixtures += [('origin_'+origin,{**base,'origin_id':origin}) for origin in ['zegama_center_stops','segura_center_stops','idiazabal_center_stops']]
        fixtures += [('explicit_defaults',{**base,'arrival_margin_minutes':10,'boarding_margin_minutes':3}),('nondefault_margins',{**base,'arrival_margin_minutes':15,'boarding_margin_minutes':8}),('duration',{**base,'duration_minutes':90}),('invalid_date',{**base,'date':'not-a-date'}),('unsupported_origin',{**base,'origin_id':'不存在'}),('legacy',{**base,'destination_id':'beasain_station','snapshot_id':'official-goierrialdea-go01-r4-20260929'})]
        # Obtain the exact supported legacy request from frozen W1 conformance.
        conformance = json.loads(z.read('datos_preparados/vnext/w1_conformance_r7.json'))
        legacy = next(c['request'] for c in conformance['cases'] if c['case_id']=='legacy_r4_explicit')
        fixtures[-1] = ('legacy', legacy)
        records = []
        def parity(case, kwargs):
            request = {k:v for k,v in kwargs.items() if k in required or v is not None}
            direct = json.loads(original_run('plan_visit', {'request':request}))
            flat = json.loads(main.plan_visit(**kwargs))
            assert mapping[-1] == ('plan_visit', {'request':request}), case
            assert direct == flat, (case, 'full public_result mismatch')
            if flat['status'] == 'error':
                assert not flat['claims'], case
                assert all(item.get('status') != 'ok' for item in flat['outcomes']), case
            assert 'raw_result_json' not in flat
            return flat
        for case, request in fixtures:
            flat = parity(case, request)
            records.append({'case':case,'request':request,'public_result':flat})
        # None is omitted, preserving full default attribution and raw hash.
        omitted = parity('omitted', base)
        assert parity('optional_none',{**base, **{k:None for k in sig.parameters if k not in required}}) == omitted
        # The two real historical prose arguments remain rejected by the frozen engine.
        historical = []
        observed = json.loads(subprocess.check_output(['git','show','46657c9fc966052dce8b5de75959f8c68282cfb4:resultados/vnext/r13/request_binding_reproduction.json'],cwd=ROOT))
        for call in observed['results']:
            value = json.loads(original_run('plan_visit',call['arguments']))
            assert value['error']['message'] == 'arguments:request:invalid_value'
            historical.append(value)
        emit(output/'parity.json',{'classification':'OFFLINE_GENERATED_FRONTDOOR_NOT_LLM','full_public_result_equality':True,'records':records,'optional_none_omitted':'PASS','historical_prose_still_rejected':historical})
        rng = random.Random(360014)
        domains = {
            'origin_id':['zegama_center_stops','segura_center_stops','idiazabal_center_stops','',None,42,[],{},'不存在'],
            'destination_id':['beasain_official_centre_anchor','',None,False,[],{},'⚠️'],
            'date':['2026-09-29','2026-09-30','2026-02-30','',None,20260929,{},'mañana'],
            'appointment_time':['09:30','09:45','00:30','23:59','24:60','',None,930,[], '٩:٣٠'],
            'duration_minutes':[20,90,0,-1,1441,'20',None,True,1.5,[],{}],
            'arrival_margin_minutes':[None,0,10,15,-1,1441,'10',True,[],{}],
            'boarding_margin_minutes':[None,0,3,8,-1,1441,'3',False,[],{}],
            'walking_profile_id':[None,'', 'unknown','reference_50m_min',42,[],{}],
            'snapshot_id':[None,'','missing_snapshot','official-goierrialdea-go01-health-r5-20260929',42,[],{}],
            'return_deadline':[None,'12:00','00:00','25:00','',930,False,[],{}],
        }
        digest = hashlib.sha256()
        statuses = {}
        unique = set()
        for i in range(count):
            kwargs = {k:rng.choice(values) for k,values in domains.items()}
            data = json.dumps(kwargs,sort_keys=True,ensure_ascii=False).encode()
            unique.add(data); digest.update(data+b'\n')
            value = parity('FUZZ_'+str(i),kwargs)
            statuses[value['status']] = statuses.get(value['status'],0)+1
            if (i+1)%500 == 0: print(f'Frontdoor {i+1}/{count} PASS',flush=True)
        # Explicitly exercise valid inputs too; random-invalid coverage is not a valid-query benchmark.
        emit(output/'fuzz.json', {'classification':'GENERATED_OFFLINE_FRONTDOOR_NOT_LLM','seed':360014,'cases':count,'distinct_kwargs':len(unique),'executions':2*count,'input_sequence_sha256':digest.hexdigest(),'statuses':statuses,'crashes':0,'mapping_failures':0,'partial_authoritative_errors':0,'valid_inputs':'separate explicit parity fixtures','elapsed_s':round(time.monotonic()-started,3)})
        report = {**first,'status':'PASS_OFFLINE_NOT_PORTAL','changed_members':changed,'assets_byte_identical':len(json.loads(MANIFEST.read_bytes())['context_paths'])==15,'nested_w1_zip_byte_identical':True,'tools_byte_identical':True,'double_build':'PASS','parity_cases':len(fixtures)+2,'fuzz_cases':count,'seed':360014,'model_calls':0,'w1_independent_acceptance':'PENDING','portal_upload':'NOT_RUN'}
        emit(output/'PORTAL_BINDING_HOTFIX_R14.json',report)
        return report

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--oracle',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--count',type=int,default=5000)
    a=p.parse_args();print(json.dumps(run(a.oracle,a.output,a.count)))
