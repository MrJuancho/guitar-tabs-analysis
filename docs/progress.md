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

Feature 007, T015-T025: User Story 3 completa (segunda mitad).
`agregar_conjunto`, `digitacion.orquestador`/`cli` (mismo patrón que
`deteccion.cli`: modo sin default, escritura atómica, progreso por
grabación). T024: primera corrida real sobre las 288 medibles -- 11.1s
de reloj (lineal confirmado), 0 excluidas, `fraccion_coincidencia=0.6186`
(research.md #14). T025: calibración medida, no aplicada -- hallazgo
estructural (un desacuerdo nunca aísla cuerda o traste, mecánico) más
una asimetría real (Δcuerda acotado ~1-2, Δtraste disperso hasta 19)
documentada como hipótesis para recalibrar después (research.md #15) --
pesos sin tocar. `just gauntlet` verde: 331 tests, 99.23%.

## Qué sigue

T026-T027 (Polish): `just gauntlet` ya verde; falta mutation testing
acotado a la capa nueva (`metrica_digitacion`, `digitacion.orquestador`/
`cli`, extensión de `ingestion.guitarset`) con triage real. Después:
cerrar Principio VII del hito 3 (`/speckit-constitution`) con la cifra
de T024/T025 como evidencia.

## Bloqueado / pendiente de decisión

Ninguno nuevo. Mismos pendientes: compuerta automática del presupuesto
`0.70` del hito 2; `copier update` de `.copier-answers.yml`/`AGENTS.md`
sin commitear; licencia de pesos de Demucs sin verificar.
