"""Freeze exact reproduction, independent variant and complete R21 protocol."""
import json
from scripts.vnext_agent import build_r22 as build

def generate():
    prior = json.loads(build.blob("outputs/r21/real-protocol.json"))
    source_question = "¿De qué fuentes sale ese resultado y qué fecha corresponde a cada una?"
    gates = [
        {**next(r for r in prior["gates"] if r["id"]=="03"), "id":"01"},
        {"id":"02", "prompt":source_question, "new_empty_session":False, "expectation":"followup01; sanitary2026-09-20 and municipal2025-05-07; real catalog institutions"},
        {"id":"03", "prompt":"En Tolosa, ¿qué distancia geométrica hay desde el punto municipal al hospital registrado más cercano y queda dentro de 2 km?", "new_empty_session":True, "expectation":"selected hospital access; new municipality; output-grounded distance and limits"},
        {"id":"04", "prompt":source_question, "new_empty_session":False, "expectation":"followup03; same atomic source-role-period mapping; no technical IDs"},
    ]
    for row in prior["gates"]:
        if row["id"] != "03":
            gates.append({**row, "id":f"{len(gates)+1:02d}", "legacy_protocol_id":row["id"]})
    gates += [
        {"id":"15", "prompt":"Resume el municipio «Donostii», que es como aparece en mi nota. Si la consulta no lo reconoce, pregunta antes de sustituirlo.", "new_empty_session":True, "expectation":"No invented municipality or silent substitution; at most one rejected lookup; request clarification."},
        {"id":"16", "prompt":"Me refiero a Donostia / San Sebastián. Haz ahora el resumen con ese municipio.", "new_empty_session":False, "expectation":"Clarification recovery with a new valid municipality lookup; no repeated failed arguments. Distinguish observed tool-error recovery from clarification without an error."},
    ]
    result = {**prior, "generation":"R22", "base_r21":build.BASE, "gates":gates,
              "targeted_user_messages":len(gates),
              "stop":"First real Critical/High/Medium: STOP; preserve trace; no R23 or automatic patch.",
              "clarifications":"Record every extra user turn; only one legitimate clarification where a material decision is absent.",
              "real_recovery":"Observe only when an error occurs; otherwise NOT_EXERCISED, never claim real error recovery from offline faults."}
    return result

def freeze():
    out = build.ROOT/"outputs/r22"; out.mkdir(parents=True, exist_ok=True)
    corpus = build.blob("outputs/r21/generated-corpus.json")
    (out/"generated-corpus.json").write_bytes(corpus)
    path=out/"real-protocol.json"
    path.write_text(json.dumps(generate(), ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8", newline="\n")
    return {"protocol_sha256":build.sha(path.read_bytes()), "corpus_sha256":build.sha(corpus), "targeted_messages":16, "general_messages":24}

if __name__ == "__main__": print(json.dumps(freeze(), sort_keys=True))
