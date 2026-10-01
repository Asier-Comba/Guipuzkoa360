"""R16 public presentation delta; appended to the immutable R15 tools module.

No provider execution, data, argument validation or arithmetic is replaced.
Names supplied by that module are intentionally resolved only in the bundle.
"""


def _duration_hms(seconds):
    if type(seconds) is not int or not 0 <= seconds < 86400:
        raise ContractViolation("presentation:invalid_duration")
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours} h {minutes} min {seconds} s"


def _civil_clock(seconds):
    if type(seconds) is not int or not 0 <= seconds < 86400:
        raise ContractViolation("presentation:invalid_civil_clock")
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _time_summary(result):
    itinerary = result["itinerary"]
    start, end, total = (itinerary[key] for key in ("start_s", "end_s", "total_s"))
    components = result["components_s"]
    if any(type(value) is not int for value in (start, end, total)):
        raise ContractViolation("presentation:non_integer_scope")
    if type(components) is not dict or not components or any(
        type(value) is not int or value < 0 for value in components.values()
    ):
        raise ContractViolation("presentation:invalid_components")
    if end - start != total or sum(components.values()) != total:
        raise ContractViolation("presentation:inconsistent_total")
    initial = components.get("initial_wait_s")
    if type(initial) is not int or initial < 0:
        raise ContractViolation("presentation:invalid_initial_wait")
    # The provider's departure string is retained, never used to derive scope.
    departure = itinerary["outbound"]["departure_time"]
    if _civil_clock(start + initial) != departure:
        raise ContractViolation("presentation:initial_wait_scope_mismatch")
    return {
        "scope": result["scope"], "scope_start_s": start, "scope_end_s": end,
        "scope_start_clock": _civil_clock(start), "scope_end_clock": _civil_clock(end),
        "total_s": total, "total_hms": _duration_hms(total), "initial_wait_s": initial,
    }


def _mobility_view(raw, root, arguments):
    view = _r15_mobility_view(raw, root, arguments)
    scenarios = raw["results"] if "results" in raw else [raw]
    for result, projected in zip(scenarios, view["scenarios"], strict=True):
        if result["status"] == "ok":
            projected["time_summary"] = _time_summary(result)
    return view


def _mobility_catalog_view(root):
    view = _r15_mobility_catalog_view(root)
    if view is None:
        return None
    defaults = view.pop("provider_defaults")
    for key in ("contract_scope", "public_contract_version", "contract_version", "engine_contract", "defaults_policy"):
        view.pop(key, None)
    view["modelling_assumptions"] = {
        "arrival_margin_minutes": defaults["arrival_margin_minutes"],
        "boarding_margin_minutes": defaults["boarding_margin_minutes"],
        "walking_profile": view["walking_profile"]["label"],
        "meaning": "Supuestos de cálculo; no son decisiones observadas del usuario ni argumentos públicos.",
    }
    return view


def _human_metadata(value):
    """Hide internal identities, not source IDs, real periods or numeric claims.

The original envelope/raw and manifest retain all technical lineage. A model
version label is not an observed source period; label it honestly as such.
"""
    if type(value) is dict:
        hidden = {"versions", "snapshot_id", "contracts", "contract_version", "engine_contract", "contract_scope", "public_contract_version"}
        return {key: _human_metadata(child) for key, child in value.items()
                if key not in hidden and "sha256" not in key}
    if type(value) is list:
        return [_human_metadata(child) for child in value
                if not (type(child) is dict and child.get("field") == "snapshot_id")]
    if type(value) is str:
        for old, new in (
            ("R5.1", "supuesto del modelo de paseo, no periodo observado"),
            ("Defaults applied by provider_r6; not observed human choices.", "Márgenes y perfil aplicados como supuestos del cálculo, no elecciones humanas observadas."),
            ("Only fields explicitly supplied by the caller; no provider defaults.", "Campos recibidos en la consulta; no incluye los supuestos aplicados por el cálculo."),
        ):
            value = value.replace(old, new)
    return value


def _public_result(evidence, root):
    return canonical(_human_metadata(strict_loads(_r15_public_result(evidence, root))))
