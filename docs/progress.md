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

Feature 007 (hito 3), T001-T012: MVP completo (US1+US2).
`analytics/metrica_digitacion.py` nuevo: `generar_candidatas`/
`asignar_instante` (US1, tres motivos de exclusión distinguibles) y
`agrupar_en_instantes`/`asignar_secuencia` (US2, DP sobre un enrejado
por instantes, research.md #1) verificados contra fuerza bruta escrita
en el propio test (FR-006). Dos decisiones de arquitectura resueltas al
implementar, documentadas en el código: helper privado compartido
`_generar_combinaciones_validas` (asignar_instante usa una asignación,
la DP necesita el conjunto por instante); centroide de traste/cuerda
como posición de mano, con la alternativa de traste-mínimo dejada
escrita para T025. `just gauntlet` verde: 294 tests, 99.20% (`metrica_digitacion` 100%).

## Qué sigue

T013-T025 (US3, P3): posición real de GuitarSet, `evaluar_coincidencia`/
`agregar_conjunto`, `digitacion.orquestador`/`cli`, medición real sobre
las 288 medibles (Principio VII), T025 (calibración de pesos). Luego
T026-T027 (Polish).

## Bloqueado / pendiente de decisión

Ninguno nuevo. Mismos pendientes: compuerta automática del presupuesto
`0.70` del hito 2; `copier update` de `.copier-answers.yml`/`AGENTS.md`
sin commitear; licencia de pesos de Demucs sin verificar.
