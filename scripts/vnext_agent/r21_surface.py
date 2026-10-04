"""Catalog projection only. The complete R20 analytical implementation precedes it."""
_R21_PUBLIC_TOOLS = ['obtener_resumen_territorial', 'analizar_envejecimiento', 'analizar_acceso_general', 'analizar_acceso_municipios', 'analizar_coincidencia', 'simular_anadir_servicio', 'simular_retirar_servicio', 'simular_cambiar_umbral', 'consultar_capacidades', 'plan_visit']
_r21_prior_public_call = public_call

def public_call(name, arguments, request_id, *, root=None):
    if name not in _R21_PUBLIC_TOOLS:
        return canonical(_r20_error_view(name, request_id, 'public_operation_unavailable', [], allowed={'tools': _R21_PUBLIC_TOOLS}))
    rendered = _r21_prior_public_call(name, arguments, request_id, root=root)
    if name != 'consultar_capacidades': return rendered
    try:
        view = strict_loads(rendered)
        if view['status'] != 'valid': return rendered
        caps = {c['id']: c for c in view['capabilities']}
        view['capabilities'] = [caps[name] for name in _R21_PUBLIC_TOOLS]
        view['public_tool_count'] = 10
        view['composed_capabilities'] = [
            {'id': 'municipal_comparison', 'callable_tool': False, 'steps': ['obtener_resumen_territorial for each municipality', 'compare observed compatible claims'], 'meaning': 'Comparación municipal por composición de consultas nuevas, no herramienta adicional.', 'limits': 'Misma métrica, sujeto, unidad y periodos compatibles; diferencias porcentuales en puntos porcentuales.'},
            {'id': 'source_explanation', 'callable_tool': False, 'steps': ['provenance in observed analytic output', 'consultar_capacidades for source cards if needed'], 'meaning': 'Explicar institución, fecha, método y límites de la fuente utilizada, sin pedir códigos al usuario.'},
        ]
        # The prior catalog exposed titles/dates but omitted methods/limitations.
        # Project the same locally validated source cards, not new source facts.
        view['sources_catalog'] = [dict(source) for source in _catalog(_workspace_root(root)).values()]
        view['age_group_derivations'] = {group: _r19_derivation(group, _workspace_root(root)) for group in ('65', '75')}
        view['capabilities'][8]['description'] = 'Catálogo de diez herramientas públicas, fuentes completas y capacidades compuestas; sin argumentos. No ejecuta análisis.'
        encoded = canonical(view)
        if len(encoded.encode('utf-8')) > MAX_PUBLIC_BYTES: raise ContractViolation('public:payload_too_large')
        return encoded
    except Exception:
        return canonical(_r20_error_view(name, request_id, 'catalog_unverified', [], message='No se ha podido verificar el catálogo. No hay cifras verificadas.'))
