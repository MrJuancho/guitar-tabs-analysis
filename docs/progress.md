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

Feature 002 (métrica SI-SDR): spec/clarify/plan/tasks completos;
constitución cerrada a v1.2.0 (Principios VII-métrica, VIII-determinismo).
Implementado T001-T009 de tasks.md (Setup+Foundational): scipy +
scipy-stubs (uv.lock committeado junto con pyproject.toml -- `just doctor`
ahora lo verifica), tipos/excepciones, y `si_sdr()` con su suite de tests.
`just gauntlet` en verde (99% cobertura). Dos hallazgos corregidos ANTES
de implementar: research.md #5 afirmaba sin verificar que estimación
silenciosa daba `-inf` por cálculo -- es NaN (0/0), `-inf` quedó definido
por convención (confirmado con el usuario). `si_sdr()` cambió de firma
(`PistaAudio` -> `PistaGuitarra`/`Estimacion`, necesita identificadores).

## Qué sigue

Fase 3 de tasks.md (User Story 1, P1/MVP): T010-T016 (tests de
`emparejar_tema`) y T017 (implementación, con
`scipy.optimize.linear_sum_assignment` -- research.md #2). Después, Fase
4 (`agregar_conjunto`, US2) y Polish (T026-T028: mutation testing,
validación de `quickstart.md`).

## Bloqueado / pendiente de decisión

Nada bloqueado en feature 002. Sigue abierto de feature 001 (no tocado
esta sesión): `_SUBTYPE_A_DTYPE.get(..., "float64")` en
`_decodificar_audio` -- decisión diferida al `/plan` de hito 2.
