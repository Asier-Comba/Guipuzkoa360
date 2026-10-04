"""Public-only cleanup. No argument coercion, provider or data changes."""


def _presentation_metadata(value, key=None):
    if type(value) is dict:
        hidden = {"schema_version", "catalog_source_id", "validation_status", "contract_scope", "contract_version", "engine_contract", "public_contract_version"}
        renamed = {"provider_origin": "parameter_origin", "w2_attribution": "attribution"}
        return {renamed.get(k, k): _presentation_metadata(v, k) for k, v in value.items()
                if k not in hidden and "sha256" not in k}
    if type(value) is list:
        return [_presentation_metadata(child, key) for child in value]
    # Historic source identifiers are keys for real traceability, not labels.
    if key in {"source_id", "source_ids", "source_refs", "upstream_source_ids", "input_source_ids"}:
        return value
    if type(value) is str:
        replacements = (
            ("Los argumentos del agente no acreditan autoría humana aunque W1 los marque human_explicit.", "Los argumentos presentes en la llamada no acreditan por sí solos autoría humana."),
            ("W1 0.3.1: pares GO01 programados y paseo modelado hasta punto oficial del centro; validación W2 de identidad, parámetros y componentes.", "Combinación de servicios GO01 programados y paseo modelado hasta el punto oficial del centro; comprobación de identidad, parámetros y componentes."),
            ("W1 0.2.0: búsqueda completa de pares directos programados entre paradas; tiempos modelados y parámetros aplicados diferenciados, sin acreditar autoría humana.", "Búsqueda completa de pares directos programados entre paradas; tiempos modelados y parámetros aplicados diferenciados, sin acreditar autoría humana."),
            ("Registro de operaciones W2 habilitadas y pendientes", "Registro de operaciones disponibles y no disponibles"),
            ("Ficha W2 cotejada con referencias y hashes W1 publicados.", "Ficha de procedencia cotejada con las referencias de las fuentes del cálculo."),
            ("R4 normalized GO01 rows, unchanged; approximate stop times, no realtime", "Filas normalizadas del horario GO01; horas aproximadas, no tiempo real"),
            ("R4 public derivative removes editor/contact metadata; R5 canonicalizes XML line endings to LF for hashing, no geometry change; ODbL 1.0", "Derivado de red peatonal sin datos personales de edición ni cambios de geometría; ODbL 1.0"),
            ("R4", "servicio entre paradas"),
            ("R5", "modelo de paseo"),
            ("human_explicit en W1 significa presente en la llamada; W2 no acredita por sí solo autoría humana.", "Un parámetro presente en la llamada no acredita por sí solo autoría humana."),
            ("Proveedor W1 0.3.1", "GIPUZKOA 360, cálculo de visita sanitaria"),
            ("Proveedor W1 0.2.0", "GIPUZKOA 360, cálculo entre paradas"),
            ("W1 stop_only 0.2.0", "GIPUZKOA 360, cálculo entre paradas"),
            ("W1 deterministic provider 0.2.0", "GIPUZKOA 360, cálculo entre paradas"),
            ("Perfil de paseo W1 supuesto del modelo de paseo, no periodo observado", "Perfil de paseo modelado"),
            ("Defaults aplicados por W1", "Supuestos aplicados al cálculo"),
            ("Supuestos y defaults de W1 stop_only", "Supuestos del cálculo entre paradas"),
            ("petición a W1", "petición"),
            ("componentes de W1", "componentes calculados"),
            ("provider_r6", "cálculo de visita sanitaria"),
            ("provider_default", "calculation_assumption"),
            ("legacy_calculation_assumption", "stop_only_calculation_assumption"),
            ("not_provided_by_legacy_contract", "not_provided_in_stop_only_calculation"),
            ("Lectura del registro validado contra handlers, fuentes y hashes de datos.", "Consulta de las operaciones disponibles, sus fuentes y límites."),
        )
        for before, after in replacements:
            value = value.replace(before, after)
    return value


def _age_group_derivation(root):
    source = _catalog(root)["EUSTAT_EMH_2025"]
    # Validate the existing transformation metadata; never infer a new cutoff.
    if source["reference_period"] != "2025-01-01" or "1949" not in source.get("method", "") or "<=1949" not in " ".join(source.get("limitations", [])):
        raise ContractViolation("presentation:unverified_age_derivation")
    return {
        "source_id": source["source_id"], "institution": source["institution"],
        "reference_period": source["reference_period"], "output_field": "population_75_plus",
        "source_field": "año de nacimiento", "condition": "año de nacimiento <= 1949, incluido el grupo de años anteriores",
        "method": "Suma de los recuentos por municipio y sexo total de los nacidos hasta 1949; porcentaje = recuento / población total × 100, redondeado a tres decimales.",
        "meaning": "A 1 de enero de 2025, quienes nacieron hasta 1949 ya habían cumplido al menos 75 años. La agrupación se basa en el año de nacimiento; no permite identificar cumpleaños individuales de quienes nacieron en 1950.",
        "limitation": "Son recuentos municipales agregados, no edades exactas ni circunstancias individuales; el límite por año no identifica a los nacidos el propio 1 de enero de 1950.",
    }


def _public_result(evidence, root):
    view = strict_loads(_r16_public_result(evidence, root))
    if view["status"] == "valid":
        for cap in view.get("capabilities", []):
            if cap["id"] == "obtener_resumen_territorial":
                periods = territorial.DataRepository(root / "datos_preparados").available_periods()
                if len(periods) != 1:
                    raise ContractViolation("presentation:summary_requires_single_period")
                cap["input_fields"] = [field for field in cap["input_fields"] if field["name"] != "periodo"]
                cap.pop("period_policy", None)
                cap["periodo_demografico_actual"] = periods[0]
                cap["periodo_demografico_explicacion"] = "La versión actual incorpora una única referencia demográfica disponible. Las fuentes sanitarias conservan sus propias fechas."
        source_ids = {s for claim in view.get("claims", []) for s in claim["source_ids"]}
        source_ids.update(row["source_id"] for row in view.get("source_metadata", []))
        if "EUSTAT_EMH_2025" in source_ids:
            view["age_group_derivation"] = _age_group_derivation(root)
    return canonical(_presentation_metadata(view))
