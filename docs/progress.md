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

Feature 007, T013/T014/T018/T019/T020 (mitad de US3). `leer_grabacion_con_posicion_real`
(`ingestion/guitarset.py`, track.notes por cuerda, nunca notes_all) y
`evaluar_coincidencia` (compara SIEMPRE contra la posición real anotada,
nunca contra `coste_total` -- sería circular, FR-007). `ResultadoCoincidencia`
documenta explícitamente que mide PARECIDO con el uso humano, no
corrección -- una posición distinta puede ser igual de válida.
T015-T017 (tests de `agregar_conjunto`/orquestador/CLI) quedaron
DELIBERADAMENTE sin escribir -- sus implementaciones (T021-T023) caen
fuera de este rango, y escribirlas ahora las dejaría en rojo entre
sesiones (nota de alcance en tasks.md). `just gauntlet` verde: 302
tests, 100% en `metrica_digitacion.py`.

## Qué sigue

T015-T017 (tests) + T021-T023 (agregar_conjunto, digitacion.orquestador,
digitacion.cli) en la misma sesión. Después T024 (medición real sobre
las 288 medibles, Principio VII) y T025 (calibración de pesos). Luego
T026-T027 (Polish).

## Bloqueado / pendiente de decisión

Ninguno nuevo. Mismos pendientes: compuerta automática del presupuesto
`0.70` del hito 2; `copier update` de `.copier-answers.yml`/`AGENTS.md`
sin commitear; licencia de pesos de Demucs sin verificar.
