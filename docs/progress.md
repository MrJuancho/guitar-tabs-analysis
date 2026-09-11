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

Feature 007 (T026-T027), CERRADA -- hito 3 completo. Mutation testing
acotado a la capa nueva: 8 sobrevivientes en `metrica_digitacion` (335
mutantes), todos equivalentes verificados (zip estructuralmente
garantizado, valores iniciales nunca leídos); 0 en
`digitacion.orquestador`/`cli` e `ingestion.guitarset`. Supervivientes
reales NO aparecieron donde se predijo (motivos de exclusión, guard de
Δt, ya cubiertos) sino en el backtracking de la DP (6 mutantes del
rango del bucle, indetectables mirando solo `coste_total`) y el
desempate de costos iguales (Principio VIII). ~20 tests nuevos, todos
por hallazgo real. `just gauntlet` verde: 361 tests, 99.23%. tasks.md
27/27.

## Qué sigue

Cerrar el Principio VII del hito 3 (`/speckit-constitution`) con la
evidencia de T024/T025: `fraccion_coincidencia=0.6186` sobre las 288
medibles, y la asimetría Δcuerda/Δtraste como entrada para una futura
recalibración de pesos (research.md #15, sin aplicar todavía).

## Bloqueado / pendiente de decisión

Ninguno nuevo. Mismos pendientes: compuerta automática del presupuesto
`0.70` del hito 2; `copier update` de `.copier-answers.yml`/`AGENTS.md`
sin commitear; licencia de pesos de Demucs sin verificar.
