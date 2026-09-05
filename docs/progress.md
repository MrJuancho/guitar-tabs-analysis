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

**Feature 003 (separación con Demucs), T001-T011 completas** (Setup,
Foundational, User Story 1). `separar_guitarra()` verifica sample
rate/canales contra un `Separador` inyectado (protocolo, sin `torch`),
declara cada transformación, colapsa salida a mono por promedio, y
envuelve fallos reales en `SeparacionFallidaError` sin reintento -- todo
probado con `SeparadorFalso`, ningún test importa `torch`/`demucs`.
`just gauntlet` verde (98 tests, 100% cobertura en `separador.py`). Capa
`separacion` nueva en import-linter. `demucs`+`torch` (`+cpu`, ~187 MB)
en `pyproject.toml` -- `tool.uv.sources` no enruta una transitiva;
`torch` se declaró directa también (ver comentario en el archivo).

## Qué sigue

Fase 4 (US2, T012-T015): `DemucsSeparador` real + `docs/ATRIBUCIONES.md`.
Fase 5 (T016): medición real de cómputo sobre un tema completo (dataset
en `/home/mrjuancho/datos/slakh2100_flac_redux`). Fase 6 (T017-T018):
visibilidad del `modelo_real`. Fase 7 (US3, solo tests). Polish: T021-023.

## Bloqueado / pendiente de decisión

Feature 001: dtype por defecto en `_decodificar_audio` -- diferido al
`/plan` de hito 2. Licencia de pesos de Demucs (research.md #3 de 003):
cita del usuario, no verificada de forma independiente (`github.com`
bloqueado en el sandbox).
