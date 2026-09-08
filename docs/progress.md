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

Feature 006, T001-T009 (Setup+Foundational+US1): `evaluar_subconjunto()`
(`analytics/metrica_deteccion_notas.py`) vía `mir_eval.transcription`,
guard manual de subconjunto vacío (FR-008) y caso de respuesta conocida
(estimada == referencia -> P=R=F1=1.0 exacto) como test. `just gauntlet`
verde: 190 tests, 98.85%. **T002 bloqueada**: `basic-pitch` irresoluble
en Python 3.12 -- su dependencia base arrastra `tensorflow<2.15.1`, sin
rueda `cp312`, verificado contra su `pyproject.toml` real. `mir_eval`/
`mirdata` sí se agregaron. Detalle en tasks.md (T002)/ATRIBUCIONES.md.
Hallazgo aparte, ya en AGENTS.md#Deuda conocida: `gauntlet-fast` no ve
archivos nunca trackeados -- sin defecto real esta vez (verificado a mano).

## Qué sigue

Decidir cómo destrabar T010+ (US2, `BasicPitchTranscriptor`): esperar
`basic-pitch` compatible con cp312, un entorno aparte, o reabrir
research.md #1. T010-T013 (Protocol, fixture, `leer_grabacion`) no
dependen de `basic-pitch` y podrían avanzar solos.

## Bloqueado / pendiente de decisión

**Nuevo**: instalación de `basic-pitch` (arriba) -- bloquea User Story 2.
`tests/holdout/guitarset_reservado_hito2.json` no existe -- se crea en
T028. Feature 001: dtype en `_decodificar_audio` -- diferido. Licencia de
pesos de Demucs: no verificada independientemente.
