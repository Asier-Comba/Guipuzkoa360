"""Atomic source/role/period projection. No data, provider or arithmetic changes."""

_PUBLIC_SOURCE_ROLES = {
    "service_location": "registro sanitario",
    "municipal_reference_point": "punto municipal/cartografía",
    "demographic_observation": "demografía municipal",
    "denominator": "demografía usada como denominador",
    "numerator": "registro sanitario usado como numerador",
    "official_schedule": "horario programado",
    "official_health_registry": "registro sanitario",
    "official_health_page": "ficha sanitaria",
    "open_network": "red peatonal",
    "model_parameter": "supuesto del cálculo",
    "agent_or_user_parameter": "parámetro recibido en la consulta",
    "user_parameter": "parámetro recibido en la consulta",
    "modelling_assumption": "supuesto del cálculo",
    "derived_network": "componente calculado",
    "derived_metric": "magnitud calculada",
    "observed_input": "dato observado",
}


def source_attributions(claim, catalog):
    """Join three independently ordered sets by ID; reject every partial join."""
    ids = claim.get("source_ids")
    if type(ids) is not list or not ids or any(type(s) is not str or not s for s in ids):
        raise ContractViolation("attribution:invalid_source_ids")
    if len(ids) != len(set(ids)):
        raise ContractViolation("attribution:duplicate_source_id")

    def indexed(field):
        rows = claim.get(field)
        if type(rows) is not list or any(type(r) is not dict for r in rows):
            raise ContractViolation("attribution:invalid_" + field)
        result = {}
        for row in rows:
            sid = row.get("source_id")
            if type(sid) is not str or not sid or sid in result:
                raise ContractViolation("attribution:duplicate_or_invalid_" + field)
            result[sid] = row
        if set(result) != set(ids):
            raise ContractViolation("attribution:incomplete_" + field)
        return result

    refs, periods = indexed("source_refs"), indexed("reference_periods")
    expected = {r["source_id"]: r["role"] for r in _source_roles(claim.get("metric_id", ""), ids)}
    joined = []
    for sid in sorted(ids):
        role, period = refs[sid].get("role"), periods[sid].get("period")
        if role not in _PUBLIC_SOURCE_ROLES or role != expected[sid]:
            raise ContractViolation("attribution:unverified_role")
        metadata = catalog.get(sid)
        if type(metadata) is not dict or metadata.get("source_id") != sid:
            raise ContractViolation("attribution:source_not_in_catalog")
        # The public projection already labels model versions as assumptions,
        # not observed dates. Use the same established presentation transform.
        known = _presentation_metadata(_human_metadata(metadata))
        if type(period) is not str or not period or period != known.get("reference_period"):
            raise ContractViolation("attribution:unverified_period")
        institution = known.get("institution")
        if institution is not None and (type(institution) is not str or not institution.strip()):
            raise ContractViolation("attribution:invalid_institution")
        joined.append({"source_id": sid, "role": role,
                       "public_role": _PUBLIC_SOURCE_ROLES[role],
                       "period": period, "institution": institution})
    return joined


def _source_attributed_view(view, catalog):
    if view.get("status") != "valid":
        return view
    claims = view.get("claims")
    if type(claims) is not list:
        raise ContractViolation("attribution:invalid_claims")
    # Build everything before returning anything: a later invalid claim cannot
    # leave earlier claims exposed with a partial or inconsistent attribution.
    attributed = [{**claim, "source_attributions": source_attributions(claim, catalog)}
                  for claim in claims]
    return {**view, "claims": attributed}


_r21_public_call = public_call


def public_call(name, arguments, request_id, *, root=None):
    view = strict_loads(_r21_public_call(name, arguments, request_id, root=root))
    if view.get("status") != "valid" or not view.get("claims"):
        return canonical(view)
    try:
        projected = _source_attributed_view(view, _catalog(_workspace_root(root)))
        encoded = canonical(projected)
        if len(encoded.encode("utf-8")) > MAX_PUBLIC_BYTES:
            raise ContractViolation("attribution:payload_too_large")
        return encoded
    except (ContractViolation, ValueError, TypeError, KeyError, OSError):
        error = _r20_error_view(name, request_id, "source_attribution_failure", [],
                              message="No se ha podido verificar la asociación completa entre fuentes, funciones y fechas; no se proporcionan cifras.")
        error["error"]["error_class"] = "contract_or_data_failure"
        return canonical(error)
