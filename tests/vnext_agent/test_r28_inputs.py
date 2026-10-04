import copy
import hashlib
import importlib.util
import itertools
import json
import random
import subprocess
import sys
import zipfile

import pytest
from scripts.vnext_agent import build_r28 as build


@pytest.fixture(scope='module')
def observed(tmp_path_factory):
    build.build()
    root=tmp_path_factory.mktemp('r28')
    with zipfile.ZipFile(build.ZIP) as z:
        z.extractall(root)
    catalog=json.loads((root/'datos_preparados/vnext/operational_catalog_r6.json').read_bytes())
    destination=catalog['destination']
    cases=[]
    for origin in catalog['origins']:
        for times in [['09:30'],['09:30','09:45'],['10:00','10:15']]:
            base=dict(origin_id=origin['origin_id'],destination_id=destination['destination_id'],date=catalog['validated_date'],appointment_times=times,duration_minutes=30 if times[0]=='10:00' else 20)
            for label in [origin['origin_id'],origin['municipality_name'],origin['name']]:
                for transform in [lambda s:s,lambda s:'  '+s.upper().replace(' ','   ')+'  ',lambda s:s.casefold()]:
                    human={**base,'origin_id':transform(label),'destination_id':transform(destination['name']),'date':'29/09/2026'}
                    key=str(len(cases))
                    cases.extend([dict(id=key,tool='plan_visit',arguments=base,keep_raw=True),dict(id=key+'human',tool='plan_visit',arguments=human,keep_raw=True)])
    base=cases[0]['arguments']
    for field,values in {
        'origin_id':['unknown','',None,False,{'x':1}],
        'destination_id':['unknown','',None,False],
        'date':['31/02/2026','29/02/2025','09/29/2026','2026/09/29','29/09/26','mañana','2026-02-30',None,False],
        'appointment_times':[[],['09:30','09:30'],['09:30','10:00','11:00'],None],
    }.items():
        for value in values:
            cases.append(dict(id='invalid'+str(len(cases)),tool='plan_visit',arguments={**base,field:value}))
    for cat,a,b in itertools.product(['primary_care','hospital','mental_health','other_health'],[1,2,3],[1,2,3]):
        cases.append(dict(id=f'threshold-{cat}-{a}-{b}',tool='simular_cambiar_umbral',arguments=dict(categoria_servicio=cat,umbral_actual_km=a,nuevo_umbral_km=b),keep_raw=True))
    def worker(path):
        result=subprocess.run([sys.executable,'-X','utf8','-m','scripts.vnext_agent.worker_r20',str(path)],input=json.dumps({'cases':cases}),cwd=build.ROOT,capture_output=True,text=True,encoding='utf-8',timeout=240)
        assert result.returncode==0,result.stderr
        return json.loads(result.stdout)
    data=worker(root)
    old=tmp_path_factory.mktemp('r27')
    with zipfile.ZipFile(build.prior.ZIP) as z:z.extractall(old)
    prior=worker(old)
    spec=importlib.util.spec_from_file_location('r28_test_tools',root/'tools.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return data,prior,module,cases


def test_all_canonical_bytes_and_thresholds_unchanged(observed):
    data,prior,_,cases=observed
    for case in cases:
        key=case['id']
        if key.endswith('human') or key.startswith('invalid'):continue
        left,right=copy.deepcopy(prior['records'][key]),copy.deepcopy(data['records'][key])
        if key.startswith('threshold'):
            # The ledger intentionally fingerprints the current tools.py. Verify
            # each fingerprint, then compare every other byte/field unchanged.
            for record,archive in [(left,build.prior.ZIP),(right,build.ZIP)]:
                versions=record['view']['threshold_transition_ledger']['evidence_versions']
                with zipfile.ZipFile(archive) as z:
                    assert versions.pop('code_sha256')==hashlib.sha256(z.read('tools.py')).hexdigest()
        assert right==left,key
    assert len(data['signatures'])==10
    assert data['signatures']==prior['signatures']


def test_natural_alias_properties(observed):
    data,_,_,cases=observed
    for case in cases:
        if not case['id'].endswith('human'):continue
        row=data['records'][case['id']];base=data['records'][case['id'][:-5]]
        assert row['status']=='valid',row
        for key in ['raw','raw_sha256','claims','effective_request','engine_input']:
            assert row[key]==base[key],(case,key)
        assert row['view']['public_input']['arguments']==case['arguments']
        assert row['view']['mobility']==base['view']['mobility']
        assert row['view'].get('comparison_ledger')==base['view'].get('comparison_ledger')


def test_invalid_closed(observed):
    for key,row in observed[0]['records'].items():
        if key.startswith('invalid'):
            assert row['status']=='error' and row['claims']==[] and row['execute_calls']==0,row
            assert row['view']['error']['invalid_fields']
            assert row['view']['error']['allowed_values']


def test_historical_cases_and_legazpi(observed):
    records=observed[0]['records'];seen=set()
    for row in records.values():
        ledger=row.get('view',{}).get('comparison_ledger')
        if ledger:
            seen.add((ledger['left']['total_seconds'],ledger['right']['total_seconds'],ledger['total_delta_seconds']))
    assert (10691,8591,-2100) in seen and (9323,11123,1800) in seen
    ledger=records['threshold-primary_care-2-3']['view']['threshold_transition_ledger']
    assert ledger['verified'] is True
    assert ledger['counts']==dict(outside_to_inside=19,inside_to_outside=0,stays_inside=63,stays_outside=6,total=88)


def test_date_calendar_and_ambiguous_formats(observed):
    module=observed[2]
    assert module._r28_normalize_date('29/02/2024')=='2024-02-29'
    assert module._r28_normalize_date('01/02/2026')=='2026-02-01'  # Explicit D/M/Y grammar, not guessing locale.
    for value in ['1/2/2026','02-01-2026','20260102','29/02/2025','2026-13-01']:
        with pytest.raises(ValueError):module._r28_normalize_date(value)


def test_unique_accent_normalization_and_collisions(observed):
    module=observed[2]
    rows=[dict(origin_id='one',name='Punto Ámbito',municipality_name='Municipio Uno')]
    assert module._r28_resolve('  PUNTO   ambito ',rows,'origin_id',('name',))=='one'
    rows.append(dict(origin_id='two',name='Punto Ambito'))
    with pytest.raises(ValueError):module._r28_resolve('punto ambito',rows,'origin_id',('name',))
    assert module._r28_resolve('one',rows,'origin_id',('name',))=='one'


def test_malformed_normalization_fuzz(observed):
    module=observed[2];rng=random.Random(28)
    for _ in range(5000):
        value=''.join(rng.choices('abc /-0123456789',k=rng.randrange(40)))
        try:result=module._r28_normalize_date(value)
        except ValueError:continue
        assert module._r28_normalize_date(result)==result


def test_no_runtime_fixture_literals_and_only_tools_changed():
    source=(build.ROOT/'scripts/vnext_agent/r28_inputs.py').read_text(encoding='utf-8')
    assert not any(value in source for value in ['Segura','Zegama','Idiazabal','Beasain','10691','8591','9323','11123'])
    with zipfile.ZipFile(build.prior.ZIP) as old,zipfile.ZipFile(build.ZIP) as new:
        assert old.namelist()==new.namelist()
        assert [n for n in old.namelist() if old.read(n)!=new.read(n)]==['tools.py']
        assert new.read('tools.py').startswith(old.read('tools.py'))
