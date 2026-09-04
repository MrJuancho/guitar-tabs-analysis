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

T024 completada: validación manual de `quickstart.md` contra una copia
local real de Slakh2100 (fuera de CI), revisada a mano -- sin hallazgos,
el resultado coincide con lo esperado. Con T024 cerrada, la **feature
001 (lectura de un tema de Slakh2100) termina aquí**: US1/US2/US3
implementadas y probadas, mutation testing de T023 triageado.

## Qué sigue

Nada pendiente de esta feature para arrancar de cero. Antes de tocar
`ingestion/slakh2100.py` de nuevo, revisar dos items que quedaron
abiertos a propósito (no bloquean el cierre de 001, ver tasks.md):

- T022 (`just gauntlet`) no se marcó explícitamente aunque corre en
  verde como efecto colateral de T023 -- confirmar antes de reusar.
- Próxima feature: hito 2 (separación de guitarra), spec/plan sin
  iniciar.

## Bloqueado / pendiente de decisión

`_SUBTYPE_A_DTYPE.get(info.subtype, "float64")` en `_decodificar_audio`
(4 sobrevivientes de mutation testing, tasks.md#T023): decisión sobre
si el módulo es lector de Slakh2100 o lector general del proyecto
queda abierta hasta que el `/plan` de hito 2 (GuitarSet/EGFxSet,
grabaciones propias) fije qué formatos/subtypes exige leer.
