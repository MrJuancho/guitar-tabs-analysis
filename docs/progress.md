# Progress -- handoff entre sesiones

<!--
Este archivo se SOBRESCRIBE, no se acumula -- no es un diario ni un
changelog (eso ya vive en los ADRs y en git). Cada sesión reemplaza el
contenido de las tres secciones de abajo con el estado actual; no agrega
al final ni conserva versiones previas.

Límite duro: 40 líneas, este comentario incluido. Si no entra, resume más.

Generado una sola vez por Copier (`_skip_if_exists`) -- `copier update`
nunca vuelve a tocarlo después.
-->

## En qué quedó la última sesión

Feature 002 (métrica SI-SDR): **T026 y T027 cerrados** (Fase 5, Polish).
`just gauntlet` en verde (93 tests, 99.26% cobertura). T027 encontró,
antes de poder correr mutation testing siquiera, un defecto real: el
clean-run de `mutmut` hizo que Hypothesis diera con un contraejemplo
donde `agregar_conjunto` devolvía NaN (`statistics.median` promediando
+∞ y −∞, `inf + -inf` en IEEE754) — corregido con test-rojo-primero y
una `_mediana_orden()` nueva. Con la línea base sana, mutation testing
sobre `metrica_separacion.py` corrió 246 mutantes, 24 sobrevivientes;
triage completo en `tasks.md` ("Triage T027"): brechas reales
corregidas (aserciones débiles, justo donde se esperaba -- las dos
ramas de `sin_estimacion_disponible` no comprobaban a qué referencia
pertenecía cada `sin_pareja`, más otras 4) y 6 equivalentes
documentados con `# pragma: no mutate` o comentario. Cierre: 226/228
mutantes matados (99.1%).

## Qué sigue

Solo falta T028 (validación manual end-to-end de `quickstart.md`).

## Bloqueado / pendiente de decisión

Nada bloqueado en feature 002. Sigue abierto de feature 001 (no tocado
esta sesión): `_SUBTYPE_A_DTYPE.get(..., "float64")` en
`_decodificar_audio` -- decisión diferida al `/plan` de hito 2.
