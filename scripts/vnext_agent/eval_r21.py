"""R21 development corpus/protocol frozen before observing model responses."""
import json
from scripts.vnext_agent import eval_r20
from scripts.vnext_agent.build_r21 import ROOT, sha

FAMILIES = eval_r20.FAMILIES

def convert(row):
    row = dict(row)
    if row['tool'] == 'comparar_municipios':
        row['composition'] = [{'tool': 'obtener_resumen_territorial', 'arguments': {'municipio': town}} for town in row['arguments']['municipios']]
        row['comparison_age'] = row['arguments']['grupo_edad']
        row['tool'] = 'obtener_resumen_territorial'; row['arguments'] = row['composition'][0]['arguments']
    elif row['tool'] == 'consultar_fuente':
        row['tool'] = 'consultar_capacidades'; row['arguments'] = {}
    elif row['family'] == 'scenario_remove':
        # No prompt grants an unobserved technical identity. The first call
        # must observe it; the offline companion uses that actual output ID.
        category = row['arguments']['categoria_servicio']; threshold = row['arguments']['umbral_km']
        human = {'primary_care':'atención primaria', 'hospital':'hospitales', 'mental_health':'salud mental'}[category]
        row['prompt'] = f'Observa el registro de {human} más cercano al punto municipal de Aduna y simula retirarlo, solo como hipótesis, con límite de {threshold} km. ¿Qué cambia y qué no demuestra?'
        row['tool'] = 'analizar_acceso_municipios'; row['arguments'] = {'categoria_servicio':category, 'umbral_km':threshold, 'municipios':['Aduna']}
        row['then_remove_observed'] = True
    elif row['family'] == 'multitool':
        row['composition'] = [{'tool':row['tool'], 'arguments':row['arguments']}, {'tool':'consultar_capacidades','arguments':{}}]
    return row

def generate():
    rows, sample = eval_r20.generate()
    return [convert(r) for r in rows], [convert(r) for r in sample]

def expand(rows):
    result = []
    for row in rows:
        steps = row.get('composition') or [{'tool':row['tool'], 'arguments':row['arguments']}]
        for index, step in enumerate(steps): result.append({'id':row['id'] + ':' + str(index), **step})
    return result

def build():
    rows, sample = generate(); out = ROOT / 'outputs/r21'; out.mkdir(parents=True, exist_ok=True)
    corpus = (json.dumps({'seed':eval_r20.SEED, 'classification':'DEVELOPMENT_NOT_HOLDOUT_OR_LLM_PROOF', 'cases':rows}, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    (out / 'generated-corpus.json').write_bytes(corpus)
    gates = [
        ('01', 'Todavía no tengo una pregunta concreta. ¿Qué podríamos estudiar sobre Gipuzkoa y qué no sabes?', 'catalog first; exact ten tools; human scope'),
        ('02', '¿Qué cinco municipios tienen mayor porcentaje de personas de 65 años o más? Explica la fuente y cómo se obtiene ese grupo.', 'ranking65 and isolated age metadata'),
        ('03', 'Explícamelo para una persona no técnica: En Getaria, ¿qué distancia geométrica hay al registro de salud mental más cercano y queda dentro de 1 km?', 'selected access;2913.3m;point not residents'),
        ('04', 'Analiza para todos los municipios de Gipuzkoa la distancia geométrica a atención primaria con un límite de 2 km. ¿Qué significa y qué no mide?', 'general access without selector;88rows'),
        ('05', 'Compara Legorreta y Alegia en personas de 65 años o más y su porcentaje. Explica las diferencias.', 'two fresh municipality summaries; exact derived differences in compatible measures'),
        ('06', '¿De dónde salen esos datos y de qué fecha son?', 'follow-up to05; observed provenance; catalog if detail needed; no technical ID request'),
        ('07', 'Estoy preparando un estudio. Simula cambiar el umbral de distancia municipal a salud mental de 1 a 6 km. ¿Qué cambia y qué no demuestra?', 'threshold tool3required fields; no coordinates/identity/placeholders'),
        ('08', 'Como hipótesis, añade un punto de atención primaria en latitud 43, longitud -2, WGS84, con umbral de 2 km. Compara las distancias municipales y explica lo que no demuestra.', 'add4required fields; no id'),
        ('09', 'Localiza el registro de atención primaria más cercano al punto municipal de Aduna y, usando su identificador real, simula retirarlo con límite de 2 km. ¿Qué cambiaría y qué no podemos afirmar?', 'observed accessID then removal; no invented identity'),
        ('10', 'Desde Zegama quiero ir al Ambulatorio de Beasain el 29/09/2026, con cita a las 09:30 y consulta de 20 minutos, y volver a las paradas. ¿Cuánto tiempo completo ocupa y qué límites tiene?', 'plan_visit;10691s;2h58m11;scheduled/modeled'),
        ('11', '¿Y si la cita fuese a las 09:45?', 'follow-up to10;fresh calculation8591s;2h23m11;2100s/35min lower modeled total conditional not saving/recommendation'),
    ]
    protocol = {'selected_before_any_response':True, 'corpus_sha256':sha(corpus), 'gates':[{'id':i,'prompt':p,'expectation':e,'new_empty_session':i not in ('06','11')} for i,p,e in gates], 'general_sample':sample, 'followups':[{'after_family':'comparison','prompt':'Mantén los municipios y cambia al otro grupo de edad disponible. Recalcula y explica las diferencias en puntos porcentuales.'},{'after_family':'health_visit','prompt':'Mantén origen, destino, fecha y duración. Cambia solo la cita al otro cuarto de hora entre 09:30 y 09:45, recalcula y compárala.'}], 'targeted_user_messages':11, 'general_user_messages':24, 'scoring':['intent','tool','arguments','output','claims','subject','entity','unit','period','source','derivation','context','recalculation','recovery','honesty','natural_language'], 'material_claim_labels':['SUPPORTED_BY_TOOL','EXACT_DERIVATION','NOT_AVAILABLE'], 'stop':'First real Critical/High/Medium: STOP, preserve exact trace, no R22 or auto-patch.', 'latencies':'Record observed first tool/output/final; unobserved timestamps stay NOT_OBSERVED.', 'holdout':'SEALED_NOT_EXECUTED', 'offline_model_calls':0}
    path = out / 'real-protocol.json'; path.write_text(json.dumps(protocol, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')
    return {'cases':len(rows),'families':len(FAMILIES),'corpus_sha256':sha(corpus),'protocol_sha256':sha(path.read_bytes())}

if __name__ == '__main__': print(json.dumps(build(), sort_keys=True))
