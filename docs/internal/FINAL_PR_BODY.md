## Decisión: integración preparada, con advertencias

FINAL_RELEASE_GO=YES conforme al gate autorizado. No publicar ni fusionar automáticamente.
Esta PR sustituye como cierre final a #8, conservada como historia.

Base de trabajo: 70c0e06e9858a64043088ed6510c68e857869f46.
Runtime congelado: 195b4980fa5998b096c308296a55e452380b0371.
Candidato del benchmark: 84e95167bfb9718ebb5f26b533f12cd885901e20.
Los commits posteriores registran evidencia y corrigen el texto de un diagnóstico; no cambian runtime.

### Qué incorpora

- Benchmark original de Asier (bf5c6cc y a1b0ecb) y ejecución final separada.
- ZIP canónico: causa exacta del byte distinto demostrada, requirements.txt LF/CRLF.
- Corrección High exclusivamente visual: eliminar corte fijo del 25 % y mostrar cuantiles reales.
- Hero autocontenida sobre 88 municipios: listas 7/4/2, fuentes, mapa y escenario.
- Rescate selectivo de Oier, seis documentos canónicos, guiones, 24 preguntas de defensa y pack.
- Evidencia adversarial, gate final y límites de la evidencia privada.

### Verificación

- Python 152/152, datos 18/18 incluidos; Node 17/17; golden contractual 3/3 incluidos.
- Contrastes fijos de fuente 4/4, A–H 8/8, QA de datos 41/41.
- Benchmark único: 72.673/72.673, 0 Critical, 0 High; trazabilidad 31.545/31.545.
- Fault injection 20/20, soak 1.000 sin deriva/excepciones.
- Nueve corrupciones visuales rechazadas; comparación completa HTML/JSON contra recálculo.
- 12 archivos de runtime/contexto idénticos al runtime congelado; manifiesto 7/7.
- ZIP 48.338 bytes, SHA-256 2808110d14e0bc30a53018cab1ec39b926e1e6ca1f1be19f0b2c9cf21106680a.
- 3 worktrees limpios con autocrlf false/true/input idénticos; misma versión Python/zlib.

### Advertencias que NO se ocultan

1. Medium abierto: extremo de simular_escenario de 20.155 caracteres, 66 afectados de 88 analizados.
   No se trunca. Aduna: 3.581 caracteres/2 afectados. El extremo no se ejecutó en portal.
2. Smoke actual INFRASTRUCTURE_BLOCKED: dos preparaciones runner ocupado y un Connection Error.
   Principal sin output; seguimiento no ejecutado. Se detuvo al tercer intento.
3. La historia conversacional se reparte entre v2/v3/v4; no toda la batería fue v4.
   Se conserva el core y la regresión histórica de escenario v4. No se presenta como smoke actual PASS.
4. La inspección visual real cubre escritorio, no una matriz exhaustiva móvil/navegadores.

### Límites de integración

No nuevas fuentes ni tools. No cambios de runtime ni contexto del portal.
No otro agente/version privada. No se abrió Entrega ni se publicó.
main y default se conservan. Tras autorización de merge, verificar main antes de cambiar default.

Referencias: docs/FINAL_RELEASE_GATE.md, docs/VALIDATION.md, analisis/final/README.md,
docs/internal/PORTAL_SMOKE_FINAL.md y docs/internal/FINAL_INTEGRATION_DECISIONS.md.
