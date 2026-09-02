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

Feature 001 completa hasta Fase 5: US1(P1)+US2(P2)+US3(P3) en verde
(`just gauntlet`, 48 tests). T014-T021 con rojo confirmado por
escenario, commits separados test/fix. T014 (colección vacía) no
necesitaba fix -- se verificó rompiendo el filtro temporalmente y
confirmando fallo, luego se revirtió. T019 (`TemaNoExisteError`), T020
(`ArchivoAudioNoLegibleError` vía `_decodificar_o_fallar`, cubre mezcla
y guitarras) y T021 (`LongitudInconsistenteError`), en ese orden. Los
tres tests de excepción afirman `str(error) == "..."` completo.

## Qué sigue

`tasks.md` T022-T024 (Polish, sin empezar): T022 `just gauntlet` ya
verde; T023 mutation testing sobre `ingestion.slakh2100` -- triage
precargado (sesión previa, 17 sobrevivientes: 1 equivalente confirmado,
16 generalidad no ejercitada por Slakh mono/16-bit), pero T019-T021
agregaron código nuevo no retriageado aún; T024 validación manual con
dataset real.

## Bloqueado / pendiente de decisión

Nada bloqueado. Pendiente heredada de T023: si `_decodificar_audio`/
`_leer_metadata` deben simplificarse a mono/16-bit depende de qué
formatos exija el separador de hito 2 (GuitarSet/EGFxSet) -- se decide
viendo eso, no antes.
