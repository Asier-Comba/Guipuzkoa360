"""Build the deterministic, versioned 1,000-prompt Spanish gold corpus."""

from __future__ import annotations

import json
from pathlib import Path

from oracle_v2 import IndependentOracle, ROOT, SERVICE_CATEGORIES


OUT = ROOT / "analisis" / "research_grade" / "nl_gold_corpus.jsonl"
SOURCES = ["EUSTAT_EMH_2025", "ODE_HEALTH_CENTRES_2026", "GEOEUSKADI_MUNICIPIOS_2025"]
DISTANCE_LIMIT = "La distancia es geométrica; no equivale a tiempo de viaje ni accesibilidad real."
SCENARIO_LIMIT = "El escenario es hipotético; no es predicción ni recomendación."


def row(
    case_id: str,
    stratum: str,
    prompt: str,
    context: list[dict[str, str]],
    intent: str,
    tool: str | None,
    parameters: dict,
    abstention: bool,
    oracle_ref: str | None,
    sources: list[str],
    limitations: list[str],
) -> dict:
    return {
        "id": case_id,
        "stratum": stratum,
        "prompt": prompt,
        "conversation_context": context,
        "expected_intent": intent,
        "expected_tool": tool,
        "expected_parameters": parameters,
        "expected_abstention": abstention,
        "expected_numeric_oracle_ref": oracle_ref,
        "expected_sources": sources,
        "expected_required_limitations": limitations,
    }


def build() -> list[dict]:
    oracle = IndependentOracle()
    municipalities = [item["municipality_name"] for item in oracle.data.municipalities]
    thresholds = [0.25, 0.5, 1, 1.5, 2, 2.5, 3, 5, 10, 50]
    quantiles = [round(0.50 + 0.01 * index, 2) for index in range(46)]
    cases: list[dict] = []

    direct_templates = [
        "¿Dónde coinciden más población de {age}+ y mayor distancia a {cat}, con cuantil {q:.2f} y umbral {t:g} km?",
        "Busca municipios con envejecimiento {age}+ y lejanía geométrica a {cat}; q={q:.2f}, {t:g} km.",
        "En Gipuzkoa, cruza {age}+ con distancia a {cat} usando cuantil {q:.2f} y umbral {t:g} km.",
        "oye, ¿qué pueblos salen para {age}+ / {cat} / q {q:.2f} / {t:g} km?",
        "Coincidencia territorial {age}+ y {cat}: cuantil {q:.2f}, corte informativo {t:g} km.",
    ]
    for index in range(300):
        category = SERVICE_CATEGORIES[index % len(SERVICE_CATEGORIES)]
        age = ("65", "75")[index % 2]
        q = quantiles[index % len(quantiles)]
        threshold = thresholds[index % len(thresholds)]
        prompt = direct_templates[index % len(direct_templates)].format(
            age=age, cat=category, q=q, t=threshold
        )
        params = {
            "categoria_servicio": category,
            "grupo_edad": age,
            "umbral_km": threshold,
            "periodo": "2025-01-01",
            "cuantil": q,
        }
        cases.append(
            row(
                f"direct-{index:04d}", "supported_direct", prompt, [], "coincidence",
                "analizar_coincidencia", params, False,
                f"coincidence:{category}:{age}:{q:.2f}:{threshold:g}",
                SOURCES, [DISTANCE_LIMIT, "La coincidencia no demuestra causalidad."],
            )
        )

    followups = [
        "Ahora usa 75+.", "Sube el cuantil a {q:.2f}.", "Cambia solo a {cat}.",
        "Pon el umbral en {t:g} km; no cambies el cuantil.", "¿Y para {municipality}?",
    ]
    for index in range(150):
        category = SERVICE_CATEGORIES[index % len(SERVICE_CATEGORIES)]
        age = ("65", "75")[index % 2]
        q = quantiles[index % len(quantiles)]
        threshold = thresholds[index % len(thresholds)]
        municipality = municipalities[index % len(municipalities)]
        prompt = followups[index % len(followups)].format(q=q, cat=category, t=threshold, municipality=municipality)
        context = [{"role": "user", "content": "Analiza 65+, atención primaria, q 0,75 y 2 km."}]
        params = {"categoria_servicio": category, "grupo_edad": age, "umbral_km": threshold, "periodo": "2025-01-01", "cuantil": q}
        cases.append(row(f"followup-{index:04d}", "short_followup", prompt, context, "coincidence", "analizar_coincidencia", params, False, f"coincidence:{category}:{age}:{q:.2f}:{threshold:g}", SOURCES, [DISTANCE_LIMIT]))

    for index in range(100):
        source_id = SOURCES[index % len(SOURCES)]
        prompt = ("¿De dónde sale esta cifra? Muéstrame la ficha " if index % 2 else "Fuente, periodo, unidad y método de ") + source_id
        cases.append(row(f"source-{index:04d}", "source_query", prompt, [], "source", "consultar_fuente", {"source_id": source_id}, False, None, [source_id], ["La ficha de fuente no valida por sí sola la calidad del dato."]))

    scenario_prompts = [
        "Añade hipotéticamente atención primaria en el punto representativo de {municipality}.",
        "Quita de forma hipotética el servicio {service_id} y recalcula.",
        "Cambia el umbral de 1 a {t:g} km sin tocar los centros.",
    ]
    service_ids = [item["service_id"] for item in oracle.data.services]
    for index in range(150):
        action = ("add_service", "remove_service", "change_threshold")[index % 3]
        municipality = municipalities[index % len(municipalities)]
        service_id = service_ids[index % len(service_ids)]
        threshold = thresholds[(index + 2) % len(thresholds)] or 0.25
        prompt = scenario_prompts[index % 3].format(municipality=municipality, service_id=service_id, t=threshold)
        params = {"accion": action, "categoria_servicio": "primary_care", "umbral_km": 1, "periodo": "2025-01-01"}
        if action == "remove_service":
            params["service_id"] = service_id
        elif action == "change_threshold":
            params["nuevo_umbral_km"] = threshold
        else:
            point = oracle.municipality(municipality)
            params.update({"latitud": point["latitude"], "longitud": point["longitude"]})
        cases.append(row(f"scenario-{index:04d}", "scenario", prompt, [], "scenario", "simular_escenario", params, False, f"scenario:{action}:{index:04d}", SOURCES, [DISTANCE_LIMIT, SCENARIO_LIMIT]))

    unsupported = [
        "Predice cuántos médicos habrá en {municipality} en 2030.",
        "Dime el tiempo andando al centro más cercano en {municipality}.",
        "¿Cuántas citas libres hay mañana en {municipality}?",
        "Ordena inversiones sanitarias óptimas para toda Gipuzkoa.",
        "¿Qué centro ofrece mayor calidad asistencial?",
        "Calcula las listas de espera futuras por paciente.",
        "Demuestra que el envejecimiento causa peor salud.",
        "Elige el solar óptimo y recomienda construir ya.",
        "¿Es accesible en silla de ruedas el centro de {municipality}?",
        "Diagnostica a una persona usando estos datos municipales.",
    ]
    for index in range(200):
        municipality = municipalities[index % len(municipalities)]
        prompt = unsupported[index % len(unsupported)].format(municipality=municipality)
        cases.append(row(f"unsupported-{index:04d}", "out_of_scope", prompt, [], "unsupported", None, {}, True, None, [], ["La información solicitada no está cargada y no deben inventarse cifras ni recomendaciones."]))

    ambiguous = [
        "¿Cuál está peor?", "Dame la accesibilidad.", "¿Dónde hacen falta más médicos?",
        "Compara esto con aquello.", "Usa un umbral alto.", "Haz una predicción.",
        "¿Qué municipio gana?", "Pon el criterio más estricto.", "Cuéntame lo importante.",
        "¿Hay suficientes centros?",
    ]
    for index in range(100):
        prompt = ambiguous[index % len(ambiguous)] + f" (consulta ambigua {index + 1})"
        cases.append(row(f"ambiguous-{index:04d}", "ambiguous", prompt, [], "clarification_or_abstention", None, {}, True, None, [], ["Debe pedir precisión o explicar el límite sin inventar parámetros."]))

    if len(cases) != 1000 or len({item["id"] for item in cases}) != 1000:
        raise AssertionError("gold corpus must contain 1,000 unique cases")
    return cases


def main() -> None:
    cases = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in cases), encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "cases": len(cases), "path": OUT.relative_to(ROOT).as_posix()}))


if __name__ == "__main__":
    main()
