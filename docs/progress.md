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

Arnés de hooks verificado con evidencia real del transcript (Stop hook:
331ms corriendo `gauntlet-fast`, contra 21ms de un falso positivo
anterior). `gauntlet-template` actualizado a v1.5.0 (pathspec `**/*.py` y
diff-vacío-en-CI corregidos, recipe `gauntlet-ci` nuevo). Spec Kit
instalado (`specify init --here --integration claude`) y trackeado
(`.specify/`, `.claude/skills/`) sin tocar `.claude/settings.json`.

## Qué sigue

Correr `/speckit-constitution`, pasándole explícitamente que `SECTION_3`
(workflow/quality gates) debe remitir a `AGENTS.md` por referencia en vez
de repetirlo -- la plantilla infiere de "README, docs" si no se le da
input, y el detalle operativo (4 capas, roles, fail-open/fail-closed) ya
vive en AGENTS.md. Después: branch protection con los checks que este PR
registre.

## Bloqueado / pendiente de decisión

`uv.lock` sigue sin trackear (untracked) en el repo -- no evaluado
todavía si debería commitearse o si falta una entrada en `.gitignore`.
