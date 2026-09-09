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

Feature 006, Fase 7 (CLI, T028-T035) completa. `construir_lista_grabaciones`
deriva la reserva de GuitarSet EN VIVO de la semilla `20260908`
(`random.Random(...).sample(track_ids ordenados, 72)`) en cada
invocación -- SIN manifiesto persistido (corrección sobre `research.md`
#14, que preveía uno en `tests/holdout/`); medibles/reservado derivan del
mismo cálculo, complementarios por construcción. `artefacto_a_dict`
serializa `ArtefactoDeteccion` (FR-011). `ejecutar_deteccion` imprime
progreso por grabación. `deteccion/cli.py` (nuevo): `--modo`/`--root-dir`
required, escritura atómica + verificación releyendo el archivo final,
mismo mecanismo que `medicion/cli.py`. Recipe `just detectar`. `just
gauntlet` verde: 240 tests, 98.38% (`orquestador.py` 100%, `cli.py` 84%).

## Qué sigue

Feature 006 completa (35 tareas de `tasks.md`). Pendiente antes de cerrar
el hito 2: correr `just detectar medibles <root_dir>` contra GuitarSet
real para la cifra real -- nunca `--modo reservado` hasta el cierre
formal (Principio VI). Considerar mutation testing acotado sobre
`deteccion/cli.py`/`deteccion/orquestador.py` antes de cerrar del todo.

## Bloqueado / pendiente de decisión

Ninguno nuevo. Sin manifiesto de reservados -- se deriva en vivo, nunca
se persiste. Licencia de pesos de Demucs: no verificada independientemente.
