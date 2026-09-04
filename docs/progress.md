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

Feature 002 (métrica SI-SDR): **User Story 1 (P1/MVP) completa**.
Implementado T010-T017: `emparejar_tema()` con asignación óptima
(`scipy.optimize.linear_sum_assignment`), tres motivos de `sin_pareja`
distinguibles (`sin_estimacion_disponible`, `energia_nula`, y el nuevo
`estimacion_silenciosa` -- FR-016: una estimación asignada silenciosa se
reclasifica a `sin_pareja`, no queda en `emparejadas` con `-inf`).
`just gauntlet` en verde (99% cobertura, 100% en `metrica_separacion.py`,
82 tests). Dos brechas de contrato corregidas ANTES de implementar:
`emparejar_tema` no declaraba `tema_id` pese a que `ReporteTema` lo
requiere; `MotivoSinPareja` en código se quedó con dos valores tras
declarar tres en el spec (mypy lo atrapó, no los tests).

## Qué sigue

Fase 4 de tasks.md (User Story 2, P2): T018-T024 (tests de
`agregar_conjunto` -- exclusiones, mediana ponderada, distribución) y
T025 (implementación). Después, Polish (T026-T028: mutation testing,
validación manual de `quickstart.md`).

## Bloqueado / pendiente de decisión

Nada bloqueado en feature 002. Sigue abierto de feature 001 (no tocado
esta sesión): `_SUBTYPE_A_DTYPE.get(..., "float64")` en
`_decodificar_audio` -- decisión diferida al `/plan` de hito 2.
