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

T025-T027 (Polish), cierra la Feature 006/hito 2. Mutación acotada a la
capa nueva, alcance ampliado (research.md #20): `metrica_deteccion_notas`,
`deteccion.orquestador`/`cli`, `ingestion.guitarset`, `transcripcion.transcriptor`.
Hallazgo de config, corregido antes de mutar: `scripts/` faltaba en
`also_copy` de mutmut (mismo defecto que `docs/`, Feature 003) --
bloqueaba TODA corrida, no solo el módulo mutado. Resultado: 633/643
killed; los 10 restantes son equivalentes ya documentados (T009). Triage
completo en tasks.md: 8 aserciones débiles corregidas con evidencia real
(rojo a mano antes de cada fix, incluido un `in`/`==` que el propio test
nuevo escondía -- "2.5s" es substring de "202.5s"). T027: `modelo_real`
corrió de verdad, 6/6 pasaron. `just gauntlet` verde: 268 tests, 99.07%.

## Qué sigue

Feature 006 cerrada. Decidir si el hito 2 necesita una compuerta
automática sobre el presupuesto `0.70` (Principio VII), o si el reporte
del artefacto alcanza -- mismo criterio que el hito 1 diferenció medir de
aprobar.

## Bloqueado / pendiente de decisión

Ninguno nuevo. `.copier-answers.yml`/`AGENTS.md` tienen un `copier
update` pendiente sin commitear, fuera de alcance. Licencia de pesos de
Demucs: sin verificar.
