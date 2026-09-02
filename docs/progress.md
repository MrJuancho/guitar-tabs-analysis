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

Feature 001 (lectura-tema-slakh2100), T001-T006 en verde (`just
gauntlet`): deps soundfile/pyyaml/numpy + override de mypy; tipos
`PistaAudio`/`PistaGuitarra`/`LecturaTema` (frozen; `PistaAudio` con
`eq=False` por el `ndarray`) y las 3 excepciones del contrato;
`tests/fixtures/slakh2100_fixture.py` parametrizable por stem (longitud
distinta, `audio_rendered=true` sin archivo, `audio_rendered=false`
coherente); `_leer_metadata`/`_decodificar_audio` en `slakh2100.py`. Cada
pieza: test rojo → commit → implementación → commit, por separado.
`leer_tema()` NO existe todavía (T013, fuera de este slice).

## Qué sigue

`tasks.md` T007+: tests rojos de `leer_tema()` (T007-T012 US1, T014 US2,
T015-T018 US3), luego su implementación (T013, T019-T021), P1→P2→P3.
Después Fase 6 (T022-T024): gauntlet completo, mutation testing, y
validación manual con dataset real.

## Bloqueado / pendiente de decisión

Nada bloqueado. Para T023: `just mutation ingestion.slakh2100` deja
10/41 mutantes vivos -- 2 equivalentes (mayúsculas en literal, como el
`.encode("UTF-8")` ya en AGENTS.md), el resto brecha real de cobertura
en `_decodificar_audio` (fallback `"float64"`, `always_2d`) y en
`_leer_metadata` (`encoding=None`).
