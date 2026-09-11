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

FR-015/FR-016 (research.md #19): precondiciones de arranque para
`deteccion.cli`, en vez de fallar a mitad de una corrida. Verificado
antes de tocar código: con `root_dir` apuntando al repositorio (el
incidente reportado), el fallo real es un `FileNotFoundError` sin
envolver en la primera grabación -- no 288 exclusiones idénticas como se
reportó de entrada; documentado así en research.md. Nuevas
`validar_raiz_guitarset`/`validar_indice_mirdata` en `ingestion.guitarset`,
invocadas al principio de `_ejecutar_y_escribir`, antes de tocar ninguna
grabación. Rojo primero confirmado con `git stash` sobre el código (rojo
contra el viejo, verde tras el fix). Caso 3 (el índice vive en
`site-packages/mirdata/`, `uv sync --reinstall` lo borra): verificado
contra el código fuente real que NO hay forma de reubicarlo --
documentado como limitación conocida. `just gauntlet` verde: 256 tests,
98.44%.

## Qué sigue

Mutation testing acotado (T026) antes de cerrar la Feature 006.

## Bloqueado / pendiente de decisión

Ninguno nuevo. `.copier-answers.yml`/`AGENTS.md` tienen un `copier
update` pendiente sin commitear, fuera de alcance. Licencia de pesos de
Demucs: sin verificar.
