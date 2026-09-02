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

T023 (mutation testing sobre `ingestion.slakh2100`) hecho. Retriage
completo: 17 sobrevivientes, T019-T021 no agregaron ninguno nuevo (los
tres modos de fallo de US3 quedan bien cubiertos). 2 resueltos con
`# pragma: no mutate` (equivalentes confirmados en `_leer_metadata`), 2
documentados como equivalentes sin pragma en `_decodificar_audio`
(pragma-arlos apagaría cobertura real de argumentos vecinos en la misma
línea). Quedan 13 sin tocar, sujetos a la decisión de abajo. `just
gauntlet` verde (48 tests, cobertura 98%).

## Qué sigue

`tasks.md` T024: validación manual de `quickstart.md` contra una copia
local real de Slakh2100 (fuera de CI). T022 viene en verde como efecto
colateral de T023, pero no se marcó -- fuera del alcance pedido.

## Bloqueado / pendiente de decisión

Sin ejecutar: tasks.md#T023 documenta dos posiciones sobre si
`_decodificar_audio`/`leer_tema` son el lector de Slakh2100 o el
general del proyecto. Recomendación escrita: simplificar (Posición A)
los 13 sobrevivientes restantes, con más urgencia en
`metadata.get("audio_dir"/"stems", ...)` (sin respaldo documental) que
en el fallback de `dtype` (research.md #1 sí lo justifica). Decidir
antes de tocar esas líneas.
