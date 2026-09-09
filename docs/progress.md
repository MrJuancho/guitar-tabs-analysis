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

Feature 006, T010-T015 (US2 completa): `leer_grabacion()` real
(`mirdata`, `audio_mic`, `.pitches` no `.values` -- corrección de
research.md #7) y `BasicPitchTranscriptor` real, invoca Basic Pitch por
subproceso en `envs/basic_pitch_py310/` (proyecto `uv` nuevo, Python
3.10, TFLite -- nunca importa `basic_pitch` desde el principal). `just
gauntlet` verde: 203 tests, 98.94%. `just doctor` extendido. `-m
modelo_real` verde de verdad (8/8, seno 440 Hz -> tono MIDI 69).

## Qué sigue

User Story 3 (T016-T024): `ExclusionDeteccion`/`ResultadoDeteccionGrabacion`,
clasificación de polifonía, `evaluar_grabacion`/`agregar_conjunto`, y
`deteccion/orquestador.py` (`ejecutar_deteccion`) atando US1+US2 sobre un
conjunto. Después: Polish (T025-T027) y CLI (T028-T035).

## Bloqueado / pendiente de decisión

Nada bloqueado en US2 -- resuelto con el entorno Python 3.10 aparte.
Manifiesto de reservados de GuitarSet: se crea en T028. Licencia de
pesos de Demucs: no verificada independientemente.
