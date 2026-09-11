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

Constitución v1.9.0: cierra el Principio VII para el hito 2 con la
primera medición real (Feature 006, `mediciones/deteccion_medibles.json`,
288 grabaciones, Basic Pitch icassp_2022 firma `3db297d5`). Métrica F1
(precisión/exhaustividad siempre por separado, desglosadas global/mono/
poli); presupuesto `0.70` sobre F1 global (`0.7394` observado, margen
`~5.3%`). Registrada la historia metodológica como evidencia sobre el
método: dos defectos de la misma familia (agrupar antes de emparejar,
FR-013; clasificar antes de emparejar, FR-014) corregidos antes de
cerrar el número, ninguno detectado por spec/plan/clarify/analyze. No se
tocó nada del hito 1 (pedido explícito). Con este cierre no queda ningún
`ABIERTO` pendiente en la constitución -- los cinco originales (3 hito 1,
2 hito 2) están cerrados. `just gauntlet` verde: 248 tests, 98.40% (doc
puro, sin cambios de código).

## Qué sigue

Mutation testing acotado (T026) antes de cerrar formalmente la Feature
006. Después: decidir si el hito 2 necesita una compuerta automática
sobre el presupuesto `0.70`, o si alcanza con el reporte del artefacto.

## Bloqueado / pendiente de decisión

Ninguno nuevo. Licencia de pesos de Demucs: sin verificar.
