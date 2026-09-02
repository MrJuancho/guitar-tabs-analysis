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

Feature 001, Fase 3 (User Story 1/P1/MVP) completa y en verde (`just
gauntlet`): T007-T013. `leer_tema()` construida incrementalmente --
T007/T009/T010 confirmados en rojo antes de extender el filtro
(`inst_class`, luego `audio_rendered`); T008/T011/T012 pasaron en verde
de inmediato por generalización del bucle/construcción. Property tests
muestrean `subtype` de la intersección real entre `_SUBTYPE_A_DTYPE` y
lo que admite el contenedor FLAC (PCM_16/PCM_24; PCM_32/FLOAT/DOUBLE
rompen `sf.write(".flac")`).

## Qué sigue

`tasks.md` T014+: T014 (US2, colección vacía, ya la da el filtro de
T013); T015-T021 (US3: `TemaNoExisteError`/`ArchivoAudioNoLegibleError`/
`LongitudInconsistenteError`, test rojo primero cada uno); T022-T024
(Polish: gauntlet completo, mutation testing, validación manual).

## Bloqueado / pendiente de decisión

Nada bloqueado. Para T023: `just mutation ingestion.slakh2100` (sin el
prefijo `guitar_tabs_analysis.` -- con él, duplica y falla) deja 19
mutantes vivos sobre el módulo -- brecha real, sin equivalentes
evidentes, pendiente de inspección en T023.
