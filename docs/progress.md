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

Feature 004 cerrada, constitución en v1.5.0 (Principio VII: `-8.0 dB`
sobre mediana de emparejadas). Feature 005 (compuerta de la métrica) con
spec/plan/research/data-model/contracts/quickstart/tasks completos.
`/speckit-analyze` corrido y sus 5 hallazgos cerrados a nivel de
documentos (sin código todavía): C1 HIGH (validación de
`modelo`/`modo`/`semilla` agregada a T005/T007), F1 (`leer_artefacto`
documentado en contracts/compuerta.md), C2 (test de firma arbitraria en
T002), C3 (T009 reescrito, independencia real entre modos), F2 (spec.md
corregido: la compuerta nunca tiene default). C4/C5 anotados como
no-implementados con su razón, no como tareas.

## Qué sigue

Implementar Feature 005 (`/speckit-implement`, T001-T015 de
`specs/005-compuerta-metrica/tasks.md`): módulo nuevo
`medicion/compuerta.py`, solo `stdlib`, TDD por user story (US1 juicio
básico, US2 fallo cerrado, US3 CLI con `--modo`), Polish con
integración a `just gauntlet` y triage de mutación.

## Bloqueado / pendiente de decisión

Ninguno. Feature 001: dtype en `_decodificar_audio` -- diferido a hito 2.
Licencia de pesos de Demucs (research.md #3 de 003): cita del usuario, no
verificada de forma independiente (`github.com` bloqueado).
