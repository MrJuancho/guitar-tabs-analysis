# Progress -- handoff entre sesiones

<!--
Este archivo se SOBRESCRIBE, no se acumula -- no es un diario ni un
changelog (eso ya vive en los ADRs y en git). Cada sesión reemplaza el
contenido de las tres secciones de abajo con el estado actual; no agrega
al final ni conserva versiones previas.

Límite duro: 40 líneas en todo el archivo, este comentario incluido. Si no
entra, resume más -- el punto es que sea barato de leer al empezar una
sesión nueva, no que sea completo.

Generado una sola vez por Copier al crear el proyecto (`_skip_if_exists`)
-- `copier update` nunca vuelve a tocarlo después: para entonces contiene
estado real de este proyecto, no la plantilla.
-->

## En qué quedó la última sesión

`/speckit-constitution` corrido desde `docs/constitucion-fuente.md` v2
(contenido acordado, no un borrador) → `.specify/memory/constitution.md`
v1.1.0. `SECTION_3` remite a `AGENTS.md` en vez de duplicar proceso; los 3
`ABIERTO` (VII métrica, VII presupuesto, VIII determinismo) quedaron sin
rellenar, cada uno con su criterio de cierre (dos en `/plan`, presupuesto
tras medir). Corregida la Governance de v1.0.0: decía que bloqueaban
`/specify`, pero la fuente v2 fija el cierre en `/plan`, no antes.

## Qué sigue

Por instrucción explícita, NO se corrió `/speckit-specify` -- sesión
aparte. Pendiente sin resolver: confirmar si `plan-template.md`/
`spec-template.md`/`tasks-template.md` asumen algún Core Principle por
nombre o número, antes del primer `/plan`.

## Bloqueado / pendiente de decisión

`uv.lock` sigue sin trackear (untracked) en el repo -- no evaluado
todavía si debería commitearse o si falta una entrada en `.gitignore`.
