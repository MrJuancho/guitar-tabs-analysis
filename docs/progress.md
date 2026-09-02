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
gauntlet`): T007-T013, `leer_tema()` construida con rojo confirmado por
escenario (T007/T009/T010), el resto en verde por generalización.

Además, fuera de `tasks.md`: triage de mutation testing sobre el módulo
(19→17 sobrevivientes) -- 1 equivalente confirmado, 2 corregidos
(mensajes de excepción sin afirmar completos; nueva regla en AGENTS.md
"Tests de excepciones..."), 16 son generalidad no ejercitada por Slakh
(mono/16-bit) que T023 no debe cerrar con tests fabricados.

## Qué sigue

`tasks.md` T014+: T014 (US2, ya la da el filtro de T013); T015-T021
(US3, test rojo primero cada uno); T022-T024 (Polish -- T023 ya trae el
triage precargado en `tasks.md`, no arranca en blanco).

## Bloqueado / pendiente de decisión

Nada bloqueado. T023 tiene una decisión de diseño pendiente y explícita
(no una duda abierta): si `_decodificar_audio`/`_leer_metadata` deben
simplificarse a lo que Slakh2100 usa (mono/16-bit) depende de qué
formatos exija el separador de hito 2 (GuitarSet/EGFxSet) -- se decide
viendo eso, no antes. Detalle completo en `tasks.md` T023.
