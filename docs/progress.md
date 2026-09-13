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

Feature 008 completa, T001-T011: agrega `peso_altura_traste` al modelo
de coste de digitación (hallazgo 4 de ADR-0002) -- un cambio por
medición, `peso_desplazamiento`/`peso_cruce_cuerdas` intactos en `1.0`.
Barrida real de diez valores sobre las 288 medibles
(`mediciones/barrido_altura_traste.json`): pico INTERIOR en `peso=0.1`
(`fraccion_coincidencia=0.652589`, +0.034 sobre la línea base `0.6186`)
-- confirma el hallazgo 4 también en GuitarSet. Pesos `>=1.0` empeoran
POR DEBAJO de la línea base (research.md #8). Mutation testing limpio
(solo equivalentes, `tasks.md` T011). `just gauntlet` verde (397
tests, 99.20%).

## Qué sigue

Elegir el valor final de `peso_altura_traste` (candidato `0.1`, o
recalibrar junto con `peso_desplazamiento`/`peso_cruce_cuerdas`,
research.md #15 de la Feature 007) es sesión aparte -- esta feature
mide, no elige (FR-007/FR-009). Hallazgos 1/2/3/5 de ADR-0002 sin
abordar.

## Bloqueado / pendiente de decisión

Valor final de `peso_altura_traste` (ver arriba). Hallazgos 1/2/3/5 de
ADR-0002. Antes: compuerta automática del `0.70` del hito 2; `copier
update` sin commitear; licencia de Demucs sin verificar.
