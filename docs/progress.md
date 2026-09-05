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

**Feature 003, T001-T016 completas** (Setup, Foundational, US1, US2,
medición de presupuesto). `DemucsSeparador` real funciona -- pesos de
`htdemucs_6s` ya cacheados, carga en ~0,4s sin red.
`docs/ATRIBUCIONES.md` declara licencias. **T016 (medición real)**:
53,40s de inferencia sobre un tema de 241,56s (`train/Track00001`, nunca
`test` -- Principio VI); pico de memoria 2,3 GB. Extrapolación al
conjunto evaluable (1710 temas): ~25,4h -- cruza "días", así que se
declaró submuestra para el hito 1: primeros 40 temas de `validation`
alfabéticos (~35,6 min), detalle en research.md #9. `just gauntlet`
verde (105 tests, 97,80% cobertura total; `demucs_separador.py` al 74%
a propósito, `DemucsSeparador` en sí queda para la Fase 6).

## Qué sigue

Fase 6 (T017-T018): hook de visibilidad en `tests/conftest.py` para que
un salto del test `modelo_real` nunca sea silencioso, más el test real.
Fase 7 (US3, solo tests). Polish: T021-T023. Recomendado:
`/speckit-constitution` para registrar en Principio VII research.md #9.

## Bloqueado / pendiente de decisión

Feature 001: dtype por defecto en `_decodificar_audio` -- diferido a
hito 2. Licencia de pesos de Demucs (research.md #3 de 003): cita del
usuario, no verificada de forma independiente (`github.com` bloqueado).
