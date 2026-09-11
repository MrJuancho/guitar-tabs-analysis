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

Incidente real: el F1 global medido (0.7394) era mayor que AMBAS
particiones (mono 0.6094, poli 0.5835) -- imposible si mono+poli cubren
el global sin resto (ref/est ya sumaban exacto). Diagnóstico medido: de
36995 pares del match global, 7329 clasificaban distinto entre su lado
de referencia y su lado estimado (research.md #17) --
`evaluar_grabacion` reclasificaba y reemparejaba cada lado por separado
dentro de cada subconjunto (research.md #9, superado), en vez de
heredar del emparejamiento único. Mismo defecto de forma que FR-013,
fijado ahora como FR-014. Arreglo: un solo emparejamiento por
grabación, cada par hereda la clase de su referencia; una estimada sin
pareja se clasifica por su propio instante. Invariante permanente
agregado (SC-007). Recalculado sobre el artefacto existente: global sin
cambio (0.7394), mono sube a 0.7710, poli sube a 0.7242 -- ya
consistente. `just gauntlet` verde: 244 tests, 98.40%.

## Qué sigue

Mutation testing acotado (T026) antes de cerrar la Feature 006. Después:
fijar el presupuesto de aprobación del hito 2 (Principio VII).

## Bloqueado / pendiente de decisión

Ninguno nuevo. `mediciones/deteccion_medibles.json` corregido y
commiteado esta sesión. Licencia de pesos de Demucs: sin verificar.
