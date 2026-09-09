---

description: "Task list template for feature implementation"
---

# Tasks: Detección de notas sobre guitarra limpia

**Input**: Design documents from `/specs/006-deteccion-notas-guitarra-limpia/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/deteccion.md](./contracts/deteccion.md), [quickstart.md](./quickstart.md)

**Tests**: Incluidas explícitamente -- mismo criterio que Features 002-005 (`just gauntlet` exige cobertura ≥90%, constitución Principio X pide test rojo antes que fix).

**Organization**: Tareas agrupadas por user story (P1/P2/P3 de `spec.md`), con una fase Foundational mínima -- solo los tipos que `NotaReferencia`/`NotaEstimada` necesitan para que User Story 1 pueda escribirse sin ningún modelo ni GuitarSet real (ver Notes, "Por qué Foundational es más chica que en Feature 004").

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede correr en paralelo con las demás tareas marcadas [P] de la misma fase (archivo distinto, sin dependencia pendiente)
- **[Story]**: A qué user story pertenece (US1/US2/US3) -- ausente en Setup, Foundational y Polish

## Path Conventions

Proyecto único (`src/`, `tests/` en la raíz), dos capas nuevas paralelas a las del hito 1 (plan.md#Project Structure, research.md #11):

- `src/guitar_tabs_analysis/ingestion/guitarset.py` (nuevo) -- paralelo a `ingestion/slakh2100.py`
- `src/guitar_tabs_analysis/transcripcion/` (capa nueva, paralela a `separacion/`) -- `transcriptor.py` (protocolo) y `basic_pitch_transcriptor.py` (único módulo que importa `basic_pitch`)
- `src/guitar_tabs_analysis/analytics/metrica_deteccion_notas.py` (nuevo) -- paralelo a `analytics/metrica_separacion.py`
- `src/guitar_tabs_analysis/deteccion/orquestador.py` (paquete nuevo, paralelo a `medicion/`) -- excluido a propósito del contrato `layers`
- `envs/basic_pitch_py310/` (nuevo, research.md #15) -- segundo proyecto `uv`, Python 3.10, fuera de `src/guitar_tabs_analysis` y del contrato `layers` por completo: `pyproject.toml`, `uv.lock`, `transcribir_subproceso.py`
- `tests/fixtures/transcriptor_fixture.py`, `tests/unit/test_metrica_deteccion_notas.py`, `tests/unit/test_guitarset.py`, `tests/unit/test_basic_pitch_transcriptor.py`, `tests/integration/test_deteccion_orquestador_integracion.py`, `tests/integration/test_basic_pitch_modelo_real_integracion.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar las dos capas nuevas y las dependencias antes de escribir código de dominio.

- [X] T001 [P] Crear `src/guitar_tabs_analysis/transcripcion/__init__.py` y `src/guitar_tabs_analysis/deteccion/__init__.py` (paquetes vacíos, dos capas nuevas, plan.md#Project Structure).
- [ ] T002 (BLOQUEADO -- parcial) En `pyproject.toml`, agregar `basic-pitch[onnx]` (Apache-2.0, research.md #1), `mir_eval` (MIT, research.md #3/#4/#5) y `mirdata` (BSD-3-Clause, research.md #7) como dependencias directas -- **nunca** el extra `[tf]` de `basic-pitch` (research.md #2). Correr `uv lock` y confirmar en `/implement` que `onnxruntime` queda como único backend de inferencia disponible para `basic_pitch` (ningún paquete instalado arrastra `tensorflow` de forma transitiva).
  **Hallazgo de la sesión de `/speckit-implement` (T001-T009): `basic-pitch` NO se pudo agregar al proyecto principal.** Verificado contra su `pyproject.toml` real: su dependencia BASE -- fuera de cualquier extra, incondicional para `python_version >= '3.11'` -- incluye `tensorflow>=2.4.1,<2.15.1`, sin rueda `cp312`. `mir_eval` y `mirdata` SÍ se agregaron aquí y resuelven limpio (T005-T009 solo los necesitan a ellos). **T002 se cierra así, intencionalmente incompleta para `basic-pitch`: esta tarea NUNCA debe agregar `basic-pitch` a `pyproject.toml` del proyecto principal** -- es irresoluble ahí sin importar la versión futura de `basic-pitch`, porque la restricción es de Python (`>=3.12`), no de una versión concreta del paquete.
  **Resuelto (sesión de T010-T015): arquitectura de subproceso, research.md #15.** `basic-pitch` vive en `envs/basic_pitch_py310/`, un segundo proyecto `uv` fijado a Python 3.10 -- ver T010 para su scaffolding. El backend real en 3.10 es TFLite, no ONNX (`onnxruntime` tampoco publica rueda `cp310` -- verificado, research.md #2 corregido).
- [X] T003 En `pyproject.toml::[tool.importlinter]`, agregar `"guitar_tabs_analysis.transcripcion"` al contrato `layers` existente, en la misma posición relativa que `guitar_tabs_analysis.separacion` (puede importar de `analytics`/`ingestion`, ninguna de las dos importa de vuelta, research.md #11) -- `guitar_tabs_analysis.deteccion` **NO** se agrega, con un comentario junto al contrato documentando la exclusión a propósito (mismo criterio que `medicion`, Feature 004). Depende de T002 (mismo archivo, secuencial -- completada pese al bloqueo de T002: no requiere que `basic-pitch` esté instalado, solo que el paquete `transcripcion` exista, T001). Correr `uv run lint-imports` y confirmar que el contrato sigue pasando (los paquetes de T001 todavía no importan nada).
- [X] T004 [P] Extender `docs/ATRIBUCIONES.md` con una sección nueva para Basic Pitch (Apache-2.0, código y pesos, sin asimetría -- research.md #1), GuitarSet (CC BY 4.0, ya admitida por Principio IV), `mir_eval` (MIT, research.md #3/#4/#5) y `mirdata` (BSD-3-Clause, research.md #7) -- mismo archivo que documenta Demucs/Slakh2100 desde la Feature 003 (research.md #13).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Los tipos que `NotaReferencia`/`NotaEstimada` -- únicos que User Story 1 necesita para escribirse por completo con notas sintéticas, sin GuitarSet ni ningún modelo.

**⚠️ CRITICAL**: Ninguna user story empieza hasta que esta fase esté completa.

- [X] T005 [P] Tipos de dominio en `src/guitar_tabs_analysis/ingestion/guitarset.py` (nuevo, data-model.md): `NotaReferencia` (`frozen=True`: `tono_midi: float`, `inicio_s: float`, `fin_s: float`), `LecturaGrabacion` (`frozen=True`: `grabacion_id: str`, `ruta_audio: Path`, `notas_referencia: list[NotaReferencia]`), y `GrabacionNoExisteError` (mismo patrón que `TemaNoExisteError` de `ingestion.slakh2100`, contracts/deteccion.md postcondición 2 de `leer_grabacion`). Este módulo no importa `transcripcion` ni `analytics` (capa base, research.md #11) -- todavía sin la función `leer_grabacion()` en sí (User Story 2, T012).
- [X] T006 [P] Tipos de dominio en `src/guitar_tabs_analysis/analytics/metrica_deteccion_notas.py` (nuevo, data-model.md): `NotaEstimada` (`frozen=True`: `tono_midi: float`, `inicio_s: float`, `fin_s: float` -- `velocity`/`pitch_bend` de Basic Pitch no se conservan, research.md #1, ningún requisito de esta feature los necesita), `ClasificacionPolifonia = Literal["monofonica", "polifonica"]`, `ResultadoSubconjunto` (`frozen=True`: `precision: float | None`, `exhaustividad: float | None`, `balance_f1: float | None`, `num_notas_referencia: int`, `num_notas_estimadas: int`). Puede importar `NotaReferencia` de `ingestion.guitarset` (T005), nunca de `transcripcion` (research.md #11, contracts/deteccion.md).

**Checkpoint**: Tipos base listos -- User Story 1 puede empezar sin GuitarSet ni ningún modelo.

---

## Phase 3: User Story 1 - Juzgar si una nota estimada acierta contra una de referencia (Priority: P1) 🎯 MVP

**Goal**: Una función que, dado un conjunto de `NotaReferencia` y `NotaEstimada` de una misma grabación, calcula acierto vía `mir_eval.transcription` (tolerancia de tono 50 cents, ventana de inicio 50 ms, duración ignorada con `offset_ratio=None` -- research.md #3/#4/#5) y produce un `ResultadoSubconjunto`, con el denominador-cero de FR-008 resuelto explícitamente (`None`, nunca una cifra sobre cero casos).

**Independent Test**: Construir pares de notas a mano (dentro/fuera de tolerancia de tono, dentro/fuera de ventana de inicio, en el borde exacto de cada una, con duraciones distintas que no afectan el acierto) y varios conjuntos con múltiples notas, verificando el veredicto contra cada Acceptance Scenario de `spec.md` User Story 1 -- sin GuitarSet ni ningún modelo.

### Tests for User Story 1 ⚠️

> Escribir estos tests primero, confirmarlos en rojo contra la función aún no implementada.

- [X] T007 [P] [US1] Tests unitarios de los Acceptance Scenarios 1-5 de `spec.md` User Story 1 en `tests/unit/test_metrica_deteccion_notas.py` (nuevo): mismo tono e inicios dentro de la ventana -> acierto (AS1); tono fuera de tolerancia (inicio cercano) -> desacierto (AS2); inicio fuera de ventana (mismo tono) -> desacierto (AS3); duración muy distinta con tono e inicio dentro de tolerancia -> acierto, la duración no participa (AS4); varias referencias y varias estimadas sobre la misma grabación -> cada estimada se acredita a lo sumo a una referencia y viceversa, nunca doble crédito (AS5, FR-005). Depende de T005, T006. También incluye el caso de respuesta conocida pedido en esta sesión (estimada == referencia -> precisión/exhaustividad/balance == 1.0 exacto).
- [X] T008 [P] [US1] Tests unitarios de subconjunto vacío en el mismo archivo (`tests/unit/test_metrica_deteccion_notas.py`, FR-008, data-model.md `ResultadoSubconjunto`): ambas listas vacías -> `precision`/`exhaustividad`/`balance_f1` en `None`; solo `notas_referencia` vacía (hay estimadas) -> `exhaustividad=None`, `precision` calculada (0.0, ninguna estimada tiene con qué acertar -- Edge Cases de spec.md); solo `notas_estimadas` vacía (hay referencias) -> `precision=None`, `exhaustividad` calculada (0.0, nada acertó). Depende de T005, T006.

### Implementation for User Story 1

- [X] T009 [US1] Implementar `evaluar_subconjunto(notas_referencia: list[NotaReferencia], notas_estimadas: list[NotaEstimada]) -> ResultadoSubconjunto` en `analytics/metrica_deteccion_notas.py`: convierte tono MIDI e intervalos al formato que `mir_eval.transcription.precision_recall_f1_overlap` espera (`mir_eval.util.midi_to_hz`), la invoca con `onset_tolerance=0.05`, `pitch_tolerance=50.0`, `offset_ratio=None` (research.md #3/#4/#5) -- **guard explícito de listas vacías ANTES de invocar `mir_eval`**, sin depender de qué haga la librería con entrada vacía (verificar contra su código fuente real en `/implement`, no supuesto aquí), para producir los `None` de FR-008/data-model.md de forma controlada en los tres casos de T008. Depende de T007, T008.
  Verificado contra el código fuente real de `mir_eval/transcription.py`: `precision_recall_f1_overlap` devuelve `(0.0, 0.0, 0.0, 0.0)` para AMBAS métricas (no solo una) cuando `ref_pitches` O `est_pitches` está vacío, sin distinguir cuál -- ese comportamiento crudo no sirve para los tres casos de T008 (que exigen distinguir cuál lista está vacía), así que el guard de esta función nunca delega en él, tal como pedía la tarea.

**Checkpoint**: Acierto/emparejamiento correcto, verificable con notas sintéticas, sin ningún modelo ni GuitarSet -- MVP de la feature.

---

## Phase 4: User Story 2 - Obtener las notas que un modelo preentrenado estima sobre una grabación (Priority: P2)

**Goal**: `leer_grabacion()` real contra GuitarSet (vía `mirdata`, señal `audio_mic`) y `BasicPitchTranscriptor` real (Basic Pitch vía subproceso en un entorno Python 3.10 aparte, research.md #15), ambos verificados de punta a punta -- único camino de esta feature que toca red/disco/modelo real.

**Independent Test**: Invocar `BasicPitchTranscriptor.transcribir()` sobre una grabación corta real de GuitarSet y verificar que el resultado es una lista de `NotaEstimada` sin ninguna excepción no controlada (spec.md User Story 2, análogo al test `modelo_real` que el hito 1 ya estableció para `DemucsSeparador`).

**Arquitectura de esta fase (research.md #15, pedido explícito de esta sesión)**: `basic-pitch` es irresoluble en Python 3.12 (T002). El transcriptor real corre en un entorno Python 3.10 aparte (`envs/basic_pitch_py310/`), invocado por subproceso desde el adaptador -- comunicación por archivos (JSON de salida), nunca por stdout (los avisos de `basic_pitch`/sus dependencias se mezclarían). El protocolo `Transcriptor` y `TranscriptorFalso` **no cambian** -- siguen siendo la misma interfaz que User Story 1 ya no toca.

- [X] T010 [US2] Dos piezas, mismo commit lógico (scaffolding antes que la implementación real, ninguna prueba propia todavía -- las pruebas llegan en T011/T013/T014(c) más abajo):
  **(a)** `Transcriptor` (Protocol), `ModeloTranscripcionDeclarado` (`frozen=True`: `nombre: str`, `variante: str`, `firma: str`, `backend: str`, `licencia: str`, data-model.md) y `TranscripcionFallidaError(ruta_audio: Path, causa: Exception)` en `src/guitar_tabs_analysis/transcripcion/transcriptor.py` (nuevo) -- mismo patrón que `separacion/separador.py` (`Separador`/`ModeloDeclarado`/`SeparacionFallidaError`), mensaje completo con `ruta_audio` (identifica la grabación) y `causa` encadenada (`raise ... from causa`). `transcribir(self, ruta_audio: Path) -> list[NotaEstimada]` recibe una **ruta de archivo**, no muestras en memoria (contracts/deteccion.md). Importa `NotaEstimada` de `analytics.metrica_deteccion_notas` (T006). Este módulo no importa `basic_pitch`.
  **(b)** Scaffolding de `envs/basic_pitch_py310/` (research.md #15): `uv init --python 3.10` (o equivalente) en ese directorio; `pyproject.toml` con dependencias `basic-pitch` (sin extra), `numpy<2` (pin ABI, tflite-runtime), `setuptools<81` (pin `pkg_resources`, resampy) -- las tres verificadas necesarias en research.md #15, no solo la primera; `uv lock` versionado. Extender `doctor:` en `justfile`: **en este orden** (chequeo de estado antes que cualquier `uv run` que pueda sincronizar, mismo criterio que el `uv lock --check` ya existente) -- primero `uv lock --check` dentro de `envs/basic_pitch_py310/`, luego (solo si lo anterior pasó) `uv run --project envs/basic_pitch_py310 python -c "import basic_pitch"` para confirmar intérprete 3.10 + import real. Fallo cerrado en cualquiera de los dos pasos, mismo criterio que el resto de `doctor`.
  Depende de T006.
  **Hecho (sesión de T010-T015)**: `envs/basic_pitch_py310/` creado con `uv init --python 3.10 --app --no-package` (no `--lib`, sin `src/` layout -- no hay ningún paquete Python que compilar, solo un script standalone). `requires-python = "==3.10.*"` (más estricto que `>=3.10`, evita que el proyecto resuelva accidentalmente contra un 3.11+ donde `basic-pitch` vuelve a arrastrar tensorflow). El chequeo de `doctor:` invoca el intérprete del venv directamente (`envs/basic_pitch_py310/.venv/bin/python -c "import basic_pitch"`), no `uv run --project` -- research.md #15 pide exactamente esto para no enmascarar un desincronizado; el texto original de esta tarea decía `uv run --project` por error, corregido en la implementación.
- [X] T011 [P] [US2] `TranscriptorFalso` en `tests/fixtures/transcriptor_fixture.py` (nuevo): implementa el protocolo `Transcriptor` de forma configurable (`notas: list[NotaEstimada] | None`, `excepcion: Exception | None`), mismo patrón que `SeparadorFalso` (`tests/fixtures/separador_fixture.py`) -- por defecto devuelve `[]` o la lista `notas` inyectada; si `excepcion` no es `None`, la levanta al invocar `transcribir()`. Cuenta invocaciones (`self.llamadas`), igual que `SeparadorFalso`. Depende de T010.
- [X] T012 [US2] Implementar `leer_grabacion(grabacion_id: str, root_dir: Path) -> LecturaGrabacion` en `ingestion/guitarset.py` vía `mirdata`: `ruta_audio` apuntando al archivo real de `audio_mic` (research.md #6 -- **nunca** `audio_mix` ni ninguna señal hexafónica), `notas_referencia` derivadas de `Track.notes_all` (`intervals`/`values`, research.md #7) mapeadas a `NotaReferencia`. Si `grabacion_id` no existe en el índice de `mirdata` (o el índice está corrupto), levanta `GrabacionNoExisteError` -- nunca una excepción cruda de `mirdata` sin envolver (contracts/deteccion.md postcondición 2). Depende de T005.
  **Corrección de research.md #7 (verificado contra `mirdata` 1.0.0 instalado, no supuesto)**: `NoteData` expone `.pitches`, no `.values` -- `mirdata.annotations.NoteData` nunca tuvo un atributo `values` en la versión que `mirdata>=0.3` resuelve. `intervals` sí coincide con lo documentado. Corregido en `ingestion/guitarset.py` con un comentario explicando la discrepancia.
- [X] T013 [P] [US2] Tests unitarios de `leer_grabacion` en `tests/unit/test_guitarset.py` (nuevo), con el índice/`Track` de `mirdata` reemplazado por `monkeypatch` (sin descargar GuitarSet real, Principio IV): una grabación existente devuelve `LecturaGrabacion` con `ruta_audio` de `audio_mic` y `notas_referencia` que coinciden con `Track.notes_all` (contracts/deteccion.md postcondición 1); una `grabacion_id` inexistente levanta `GrabacionNoExisteError` (postcondición 2). Depende de T012.
- [X] T014 [US2] Dos piezas (contracts/deteccion.md, secciones `BasicPitchTranscriptor` y `transcribir_subproceso.py`):
  **(a)** `envs/basic_pitch_py310/transcribir_subproceso.py`: CLI (`argparse` o `sys.argv` simple) `<ruta_audio> <ruta_salida_json>` -- invoca `basic_pitch.inference.predict(ruta_audio)`, mapea cada tupla `(start_time_s, end_time_s, pitch_midi, velocity, pitch_bend)` a `{"tono_midi": pitch_midi, "inicio_s": start_time_s, "fin_s": end_time_s}` (descarta `velocity`/`pitch_bend`, igual que `NotaEstimada`), escribe el array JSON en `ruta_salida_json`, sale `0`. Ante cualquier excepción: imprime el detalle a stderr, sale distinto de `0`, **no** escribe `ruta_salida_json` (ni lo deja a medias -- escribir a un temporal y `os.replace()` al final si hace falta esa garantía).
  **(b)** `BasicPitchTranscriptor` en `transcripcion/basic_pitch_transcriptor.py` (nuevo) -- **no importa `basic_pitch`**: `transcribir(ruta_audio)` crea un archivo de salida temporal, invoca el intérprete de `envs/basic_pitch_py310/.venv/bin/python` (ruta directa, **nunca** `uv run` en tiempo de llamada -- research.md #15) sobre `transcribir_subproceso.py` con `[ruta_audio, ruta_salida_temporal]`, espera el resultado (`subprocess.run(..., capture_output=True)`). Si el código de salida es distinto de `0`, o el archivo de salida no existe, o el JSON es inválido -- los tres casos, cualquiera de ellos -- levanta `TranscripcionFallidaError(ruta_audio, causa)` con el `stderr` capturado como parte de la causa; **nunca** devuelve `[]` por defecto ante un fallo. En el camino feliz, parsea el JSON a `list[NotaEstimada]` y borra el archivo temporal. `modelo_declarado.firma` se determina en vivo (no inventada) -- verificar en el propio código un identificador corto y estable del modelo real (p.ej. hash corto del `.tflite` bundleado, o versión de `basic-pitch` pineada en `envs/basic_pitch_py310/pyproject.toml`) y documentar en un comentario cuál se usó y por qué. `backend="tflite"` (research.md #2/#15, no `"onnx"`).
  **(c)** Tests unitarios de `BasicPitchTranscriptor.transcribir()` con `subprocess.run` reemplazado por `monkeypatch` (rápidos, sin el entorno 3.10 real, corren en `just gauntlet`) en `tests/unit/test_basic_pitch_transcriptor.py` (nuevo): código de salida distinto de cero -> `TranscripcionFallidaError` con `ruta_audio` en el mensaje; archivo de salida ausente pese a código `0` (simula una falla a medio escribir) -> mismo error; JSON malformado en el archivo de salida -> mismo error; camino feliz simulado (el mock escribe un JSON válido de 2 notas) -> `list[NotaEstimada]` correcta, archivo temporal limpiado.
  Depende de T010, T012 (comparte el patrón de resolución de rutas del entorno, aunque no lo importa).
  **Hecho (sesión de T010-T015)**: `firma="3db297d5"` -- primeros 8 hex de `sha256(nmp.tflite)`, el archivo de pesos real bundleado en el paquete instalado, verificado en vivo con `sha256sum` sobre ese archivo exacto (mismo criterio que `firma="5c90dfd2"` de `DemucsSeparador` en el hito 1: identificador corto y estable de los PESOS concretos, no de la versión del paquete). `PYTHON_ENV`/`SCRIPT_SUBPROCESO` (antes `_PYTHON_ENV`/`_SCRIPT_SUBPROCESO`) quedaron públicos, sin guion bajo, a propósito: T015 los usa para decidir si el entorno secundario está materializado antes de invocarlo.
- [X] T015 [P] [US2] `tests/integration/test_basic_pitch_modelo_real_integracion.py` (nuevo) -- único test `@pytest.mark.modelo_real` de esta feature, mismo mecanismo de aviso visible que el hito 1 (`tests/conftest.py`, nunca corre como parte de `just gauntlet`): `BasicPitchTranscriptor.transcribir()` sobre una grabación corta real de GuitarSet produce una lista de `NotaEstimada` (o vacía, si el clip no tiene nada que Basic Pitch reconozca -- spec.md US2 AS3) sin lanzar ninguna excepción no controlada (AS1) -- subproceso real incluido, no mockeado. Si el entorno `envs/basic_pitch_py310/` no existe o no está sincronizado (sin `just doctor` corrido antes, o sin red la primera vez), el test se salta con `pytest.skip(f"...: {causa}")`, mismo patrón que `test_demucs_separador_integracion.py` de la Feature 003. Depende de T014.
  **Desviación pedida explícitamente para esta sesión**: usa un seno sintético (`soundfile`/`numpy`), no una grabación real de GuitarSet -- GuitarSet no está descargado en este entorno y no hace falta para este test puntual (mismo patrón que `mezcla_sintetica` del hito 1). Corrido de verdad (no saltado): `uv run pytest -m modelo_real -v` produce 2/2 tests en verde sobre este archivo, incluyendo el caso de respuesta conocida (seno de 440 Hz -> tono MIDI cercano a 69).

**Checkpoint**: User Story 2 completa -- lectura real de GuitarSet y modelo real ambos verificados de punta a punta; `TranscripcionFallidaError` se levanta correctamente ante un fallo real (la conversión de ese fallo en una exclusión que no aborta la corrida es responsabilidad de `deteccion.orquestador`, User Story 3, T023/T024 -- ver Notes).

---

## Phase 5: User Story 3 - Medir el sistema sobre un conjunto de grabaciones y reportar por polifonía (Priority: P3)

**Goal**: Clasificación de polifonía a partir exclusivamente de la anotación de referencia (research.md #8), agregación sobre un conjunto de grabaciones -- pool plano, nunca promedio de resultados por grabación (contracts/deteccion.md postcondición 4) -- y el orquestador (`ejecutar_deteccion`) que ata User Story 1 y User Story 2 sobre un conjunto real, con exclusión terminal por grabación ante un fallo de inferencia (FR-012).

**Independent Test**: Con `TranscriptorFalso` (T011) y notas de referencia/estimadas construidas a mano sobre varias grabaciones sintéticas (algunas monofónicas, otras con acordes, alguna configurada para fallar), verificar `ejecutar_deteccion()` contra cada Acceptance Scenario de `spec.md` User Story 3 y el AS4 de User Story 2.

- [X] T016 [US3] Agregar `ExclusionDeteccion` (`frozen=True`: `grabacion_id: str`, `detalle: str`) y `ResultadoDeteccionGrabacion` (`frozen=True`: `grabacion_id: str`, `notas_referencia: list[NotaReferencia] | None`, `notas_estimadas: list[NotaEstimada] | None`, `exclusion: ExclusionDeteccion | None`) a `analytics/metrica_deteccion_notas.py` (data-model.md) -- **corrección de ubicación respecto a research.md #11** (que las situaba en `deteccion/orquestador.py`, ver Notes): `agregar_conjunto` (T021, misma fase) las necesita en su propia firma, y `analytics` no puede importar de `deteccion` sin crear una dependencia circular (`deteccion` importa de las tres capas, nunca al revés, research.md #11). `deteccion/orquestador.py` las importa desde aquí. Depende de T006.
- [X] T017 [P] [US3] Implementar `clasificar_polifonia_en_instante(instante_s: float, notas_referencia: list[NotaReferencia]) -> ClasificacionPolifonia` en `analytics/metrica_deteccion_notas.py` (research.md #8): cuenta cuántos intervalos `[inicio_s, fin_s]` de `notas_referencia` solapan `instante_s` (solape parcial cuenta) -- `"polifonica"` si dos o más solapan, `"monofonica"` en cualquier otro caso, incluido el caso degenerado de cero referencias solapando (FR-006). Depende de T005, T006.
- [X] T018 [P] [US3] Tests unitarios de `clasificar_polifonia_en_instante` en `tests/unit/test_metrica_deteccion_notas.py` (mismo archivo que T007/T008): un acorde (dos o más referencias solapando el instante) -> `"polifonica"`; una nota suelta (cero o una referencia solapando) -> `"monofonica"`; solape justo en el borde de un intervalo; caso degenerado de cero referencias -> `"monofonica"`. Depende de T017.
- [X] T019 [US3] Implementar `evaluar_grabacion(notas_referencia: list[NotaReferencia], notas_estimadas: list[NotaEstimada]) -> tuple[ResultadoSubconjunto, ResultadoSubconjunto, ResultadoSubconjunto]` (global, monofónico, polifónico) en `analytics/metrica_deteccion_notas.py`: clasifica cada `NotaReferencia` en su propio inicio y cada `NotaEstimada` en el suyo, ambas contra `notas_referencia` de la misma grabación (T017, research.md #8) -- la fuente de la clasificación es siempre la referencia, nunca la propia predicción (FR-006). Arma los tres pares de listas (global = todo sin partir, monofónico, polifónico) y llama `evaluar_subconjunto` (T009) **una vez por subconjunto** -- nunca calcula un emparejamiento global y lo divide después (contracts/deteccion.md postcondición 2, research.md #9). Depende de T009, T017.
- [X] T020 [P] [US3] Tests de `evaluar_grabacion` en el mismo archivo: una grabación con pasajes monofónicos y polifónicos mezclados -> las tres cifras (global/mono/poli) coinciden con el cálculo esperado a mano; una grabación 100% monofónica -> el subconjunto polifónico se reporta como `None`, nunca como cero (FR-008); una nota estimada sin ninguna nota de referencia en la grabación (referencia vacía) -> clasificada monofónica por el caso degenerado y cuenta en contra de la precisión global (Edge Cases de spec.md). Depende de T019.
- [X] T021 [US3] Implementar `agregar_conjunto(resultados: list[ResultadoDeteccionGrabacion]) -> tuple[ResultadoSubconjunto, ResultadoSubconjunto, ResultadoSubconjunto]` en `analytics/metrica_deteccion_notas.py`: filtra los `resultados` con `exclusion is not None`; para cada grabación no excluida, clasifica sus notas contra las referencias de **esa misma grabación** (nunca cruzando grabaciones -- la simultaneidad solo tiene sentido dentro de una misma grabación), y acumula en tres *pools* (global/mono/poli) a través de **todas** las grabaciones no excluidas; llama `evaluar_subconjunto` **una vez por pool**, sobre el conjunto combinado -- nunca promedia los `ResultadoSubconjunto` calculados por grabación (contracts/deteccion.md postcondición 4: una grabación con muchas notas debe pesar más que una con pocas). Depende de T016, T019.
- [X] T022 [P] [US3] Tests de `agregar_conjunto` en el mismo archivo: varias grabaciones, alguna con `exclusion` (queda fuera del pool); un caso construido para que la cifra combinada sea observablemente distinta de promediar las cifras por grabación (fija que se pooleó, no se promedió); un conjunto cuyas referencias son todas monofónicas -> el subconjunto polifónico agregado se reporta como `None` (US3 AS3, FR-008). Depende de T021.
- [X] T023 [US3] Implementar `ArtefactoDeteccion` (`frozen=True`, data-model.md: `modelo`, `tolerancia_tono_cents=50.0`, `ventana_inicio_s=0.05`, `grabaciones`, `exclusiones`, `resultados_por_grabacion`, `global_`, `monofonico`, `polifonico`) y `ejecutar_deteccion(grabaciones: list[str], root_dir: Path, transcriptor: Transcriptor) -> ArtefactoDeteccion` en `deteccion/orquestador.py` (nuevo, paquete excluido del contrato `layers`, research.md #11): para cada `grabacion_id`, llama `leer_grabacion` (T012) y `transcriptor.transcribir` (T010/T014); si cualquiera de los dos levanta una excepción real (`GrabacionNoExisteError` o `TranscripcionFallidaError`), registra `ExclusionDeteccion(grabacion_id, detalle=str(causa))` y **continúa** con la siguiente grabación -- nunca aborta la corrida completa (FR-012, research.md #10, contracts/deteccion.md postcondición 1). Al completar todas las grabaciones, arma y devuelve el `ArtefactoDeteccion` con el modelo declarado, la tolerancia y ventana fijas, la lista de grabaciones, las exclusiones con su motivo, los resultados crudos por grabación, y las tres cifras vía `agregar_conjunto` (T021) sobre las grabaciones no excluidas -- **nunca** compara ninguna cifra contra ningún umbral (FR-009, contracts/deteccion.md postcondición 3). Depende de T012, T014, T016, T021.
- [X] T024 [P] [US3] Tests de integración en `tests/integration/test_deteccion_orquestador_integracion.py` (nuevo), con `TranscriptorFalso` (T011) y `leer_grabacion` real o con `monkeypatch` sobre el índice de `mirdata` (mismo mecanismo que T013): una grabación cuyo `TranscriptorFalso` está configurado para levantar una excepción -> queda excluida con un motivo distinguible, y la corrida sigue con el resto del conjunto (spec.md US2 AS4, FR-012, Clarifications 2026-09-07); agregación sobre varias grabaciones con notas construidas a mano produce un `ArtefactoDeteccion` con las tres cifras correctas (US3 AS1); una grabación cuya anotación de referencia no tiene ninguna nota -> se mide igual (no es una exclusión), su exhaustividad queda sin denominador (Edge Cases de spec.md, distinto del caso de fallo de inferencia). Depende de T023.

**Checkpoint**: Las tres user stories completas -- `ejecutar_deteccion()` mide un conjunto de grabaciones de punta a punta, reporta global/monofónico/polifónico, ningún fallo individual detiene la corrida, sin ningún umbral de aprobación.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T025 [P] Correr `just gauntlet` (ruff format --check + lint-imports + mypy --strict + tests unit/integration/property con cobertura ≥90%, excluyendo `-m modelo_real`) y corregir cualquier hallazgo.
- [ ] T026 [P] Correr `just mutation analytics.metrica_deteccion_notas` y `just mutation deteccion.orquestador` (excluye `transcripcion.basic_pitch_transcriptor.py` y `transcripcion.transcriptor.py` del alcance de mutación -- capa de invocación delgada, mismo criterio que `separacion.demucs_separador` en el hito 1) y resolver mutantes sobrevivientes, prestando atención particular a los mensajes de `TranscripcionFallidaError`/`GrabacionNoExisteError` y al `detalle` de `ExclusionDeteccion` (AGENTS.md, "Tests de excepciones").
- [ ] T027 Ejecutar manualmente la sección "Lo que corre en `just gauntlet`" de `quickstart.md` de punta a punta y confirmar que coincide con el comportamiento real; si hay red/pesos cacheados, correr también `uv run pytest -m modelo_real -v` y confirmar que T015 pasa o se salta visiblemente.

---

## Phase 7: CLI (desbloqueada -- la reserva de GuitarSet ya está fijada)

**Purpose**: Con el tamaño y la semilla de la reserva ya cerrados (72/360, semilla `20260908` -- Principio VI v1.8.0, research.md #14), la CLI puede construirse sin riesgo de reescritura. Mismo criterio que el hito 1 diferenció "orquestador puro" (Fase 5) de "CLI real" (aquí), Feature 004.

**Corrección de diseño (sesión de T028-T035, research.md #14)**: la reserva de GuitarSet **no** se lee de un manifiesto persistido -- se deriva en vivo de la semilla `20260908` en cada invocación (`random.Random(semilla_reserva).sample(...)`). Si alguien cambia la semilla en el código, la partición completa cambia automáticamente y de forma visible en el diff -- un manifiesto cacheado en disco no tendría esa propiedad. Sin archivo, sin hook de protección adicional para esto.

- [X] T028 [US3] Implementar `construir_lista_grabaciones(modo: Literal["medibles", "reservado"], root_dir: Path, *, tamano_reserva: int = 72, semilla_reserva: int = 20260908) -> list[str]` en `deteccion/orquestador.py`: enumera todos los identificadores de grabación de GuitarSet vía el índice de `mirdata`, **ordenados** (mismo criterio de reproducibilidad que `construir_lista_temas` del hito 1, Feature 004 T012 -- el orden de `mirdata` no tiene garantía propia de estabilidad); calcula `random.Random(semilla_reserva).sample(todos, tamano_reserva)` -- con `modo="reservado"` devuelve esa lista (ordenada); con `modo="medibles"` devuelve el complemento (`todos` menos esas, en el mismo orden). Ambos modos derivan del mismo cálculo, así que son complementarios por construcción (unión = `todos`, intersección = vacía) -- nunca dos cálculos independientes que podrían divergir. Depende de T005, T012.
- [X] T029 [P] [US3] Tests unitarios de `construir_lista_grabaciones` en `tests/unit/test_orquestador_deteccion.py` (nuevo), con el índice de `mirdata` reemplazado por `monkeypatch` (una lista sintética de identificadores, del mismo orden de magnitud que las 360 reales -- no hace falta GuitarSet real): **el test que más importa de esta fase (pedido explícito de esta sesión)** -- con los parámetros por defecto (`tamano_reserva=72`, `semilla_reserva=20260908`), recalcular de forma independiente en el propio test (no llamando a ninguna función de producción) el conjunto esperado de 72 reservados vía `random.Random(20260908).sample(sorted(ids_sinteticos), 72)`, y afirmar que **ninguno** de esos 72 aparece en el resultado de `modo="medibles"` (`set(reservados_esperados) & set(construir_lista_grabaciones("medibles", ...)) == set()`) -- nunca solo `len(resultado) == 288`, que un filtro que excluyera 72 arbitrarias distintas también daría. Además: `modo="reservado"` devuelve exactamente esos 72 recalculados; la unión de `medibles` + `reservado` cubre todos los sintéticos sin overlap; dos invocaciones con los mismos parámetros dan la misma lista (reproducibilidad); **con una `semilla_reserva` distinta (parámetro explícito, sobre un dominio sintético más chico para que el test sea legible) el conjunto reservado cambia por completo** -- fija en un test, no solo en la documentación, que la partición depende de la semilla. Depende de T028.
- [X] T030 [US3] Implementar la serialización de `ArtefactoDeteccion` a un `dict` JSON-compatible en `deteccion/orquestador.py` -- función pura, sin tocar disco (mismo patrón que `artefacto_a_dict` de `medicion/orquestador.py`, Feature 004 T019). Depende de T023.
- [X] T031 [P] [US3] Test unitario de la serialización de T030 en `tests/unit/test_orquestador_deteccion.py` (mismo archivo que T029): el `dict` contiene, como claves de nivel superior, exactamente lo que FR-011 exige (modelo, tolerancia, ventana, grabaciones, exclusiones con motivo, resultados por grabación, y el desglose global/monofónico/polifónico), y `json.dumps(...)`/`json.loads(...)` no pierde ningún valor (round-trip). Depende de T030.
- [X] T032 [US3] Dos piezas:
  **(a)** Agregar salida de progreso a `ejecutar_deteccion` (T023, `deteccion/orquestador.py`) -- mismo patrón exacto que `ejecutar_corrida` del hito 1 (`medicion/orquestador.py`, commit "salida de progreso en ejecutar_corrida"): una línea por grabación procesada (`[i/N] grabacion_id  ok  Xs  N notas` o `[i/N] grabacion_id  excluido: motivo`), y un aviso al entrar a la agregación (`agregando N grabaciones`). A diferencia de `ejecutar_corrida`, `ejecutar_deteccion` no tiene persistencia por grabación ni reanudación -- omití esa parte del patrón (no hay "ya procesados, se omiten" que reportar).
  **(b)** Implementar `deteccion/cli.py`: `argparse.ArgumentParser` con `--modo` (`choices=["medibles", "reservado"]`, `required=True`, **sin** `default=` -- mismo criterio que `medicion/cli.py` con su `--modo`, FR-004 de Feature 004: un default silencioso sobre qué se mide es el riesgo que este patrón evita, y acá es más grave todavía -- un default que apuntara a `"reservado"` mediría el conjunto que Principio VI prohíbe tocar) y `--root-dir` (`type=Path`, `required=True`); `main(argv=None)` construye `BasicPitchTranscriptor()` una sola vez, obtiene la lista con `construir_lista_grabaciones(args.modo, args.root_dir)` (T028), llama `ejecutar_deteccion` (T023), serializa el resultado (T030) y lo escribe en `mediciones/deteccion_{modo}.json` (mismo patrón de nombre que `mediciones/{modo}.json` del hito 1) con escritura atómica (archivo temporal + `os.replace()`) **y verificación releyendo el archivo final** -- mismo mecanismo exacto que `medicion/cli.py::escribir_artefacto`/`EscrituraIncompletaError` (no confiar en que `os.replace()` no haya lanzado como prueba de que el artefacto quedó bien escrito, ver el propio comentario de esa función en el hito 1). Único módulo de esta feature que importa `deteccion.orquestador` desde un punto de entrada de proceso. Depende de T023, T028, T030.
- [X] T033 [P] [US3] Test de CLI en `tests/unit/test_deteccion_cli.py` (nuevo): invocar `deteccion.cli.main([])` (sin `--modo` ni `--root-dir`) -> `SystemExit` con código distinto de 0 antes de construir ningún `BasicPitchTranscriptor` real (`monkeypatch` para confirmar que no se invoca); mismo tratamiento con `--modo` fuera de las dos opciones válidas. Mismo patrón que `test_cli.py` del hito 1 (Feature 004, T027). Depende de T032.
- [X] T034 [P] Agregar un recipe `detectar modo root_dir` al `justfile` (mismo patrón que `medir modo root_dir`) que invoque `uv run python -m guitar_tabs_analysis.deteccion.cli --modo {{modo}} --root-dir {{root_dir}}`.
- [X] T035 [P] Correr `just gauntlet` de nuevo (ahora con `deteccion/cli.py`/`orquestador.py` completos) y confirmar que la cobertura ≥90% sigue en verde -- T025 corrió antes de que esta fase existiera.

**Checkpoint**: `uv run python -m guitar_tabs_analysis.deteccion.cli --modo medibles --root-dir <ruta>` es un comando real, que nunca mide sobre las 72 grabaciones reservadas del hito 2 (`--modo reservado` existe para cuando el hito 2 cierre, no se invoca en desarrollo).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias, salvo T003 depende de T002 (mismo archivo `pyproject.toml`).
- **Foundational (Phase 2)**: depende de Setup -- bloquea las tres user stories.
- **User Story 1 (Phase 3)**: depende de Foundational completa. No depende de User Story 2 ni 3.
- **User Story 2 (Phase 4)**: depende de Foundational. No depende de User Story 1 -- ambas podrían implementarse en paralelo por personas distintas, aunque `deteccion` (User Story 3) necesita las dos.
- **User Story 3 (Phase 5)**: depende de Foundational, de T009 (US1, `evaluar_subconjunto`) y de T012/T014 (US2, lectura real y modelo real) -- es la que ata las dos historias anteriores sobre un conjunto.
- **Polish (Phase 6)**: depende de que las tres user stories estén completas.
- **CLI (Phase 7)**: depende de User Story 3 completa (T023, T012, T028 en adelante) -- no depende de Polish (Phase 6), pero T035 (re-correr `just gauntlet`) sí depende de que T025 ya haya corrido una vez antes.

### Dentro de cada Story

- Tests antes que implementación; confirmarlos en rojo antes de tocar `analytics/metrica_deteccion_notas.py`/`ingestion/guitarset.py`/`transcripcion/`/`deteccion/orquestador.py`.
- User Story 2: T010 (tipos) antes que T011 (fixture que los implementa) y T014 (implementación real que los usa); T012 (lectura real) es independiente de T010/T011/T014 -- mismo archivo que T005, capa `ingestion`.
- User Story 3: T016 (tipos) antes que T021 (`agregar_conjunto`, que los necesita en su firma); T017 (clasificación) antes que T019 (`evaluar_grabacion`, que la usa); T019 antes que T021 (`agregar_conjunto` reutiliza la misma lógica de clasificación+partición que `evaluar_grabacion` ya estableció); T023 (orquestador) depende de que T012/T014 (US2) y T021 (US3) existan.

### Parallel Opportunities

- T001 y T004 (Setup, archivos distintos) -- en paralelo entre sí y con T002/T003 (secuenciales entre sí, mismo archivo `pyproject.toml`).
- T005 y T006 (Foundational, archivos distintos) -- en paralelo.
- T007 y T008 (US1, mismo archivo, escenarios independientes) -- en paralelo.
- T011 (US2, fixture) en paralelo con T012 (implementación real de `ingestion.guitarset`, archivo distinto); T013 y T015 (tests, archivos distintos de sus implementaciones) en paralelo entre sí una vez sus dependencias existen.
- T017, T018 (US3, clasificación) en paralelo con el trabajo de T016 una vez completo; T020, T022, T024 (tests, mismo archivo entre sí donde aplica) en paralelo una vez sus implementaciones respectivas existen.
- T025, T026 (Polish) -- comandos independientes entre sí; T027 depende de que T025/T026 ya hayan dejado el árbol en verde.
- T029 (US3, CLI) en paralelo con T030/T031 (archivo distinto) una vez T028 existe; T033, T034, T035 (Fase 7) -- comandos/archivos independientes entre sí una vez T032 existe.

---

## Parallel Example: User Story 1

```bash
# Estas dos tareas son independientes entre sí (mismo archivo, escenarios distintos):
Task: "Acceptance Scenarios 1-5 en tests/unit/test_metrica_deteccion_notas.py"
Task: "Subconjunto vacío (FR-008) en tests/unit/test_metrica_deteccion_notas.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 solamente)

1. Fase 1: Setup.
2. Fase 2: Foundational -- tipos de `NotaReferencia`/`NotaEstimada`.
3. Fase 3: User Story 1.
4. **Parar y validar**: `evaluar_subconjunto()` juzga acierto (tono + inicio, duración ignorada) sobre notas construidas a mano, con el denominador-cero de FR-008 resuelto -- sin GuitarSet ni ningún modelo todavía.

### Incremental Delivery

1. Setup + Foundational -> tipos base listos.
2. User Story 1 -> mecanismo de juicio verificable con notas sintéticas -> MVP.
3. User Story 2 -> lectura real de GuitarSet + modelo real (Basic Pitch, ONNX) verificados de punta a punta, en paralelo con (o después de) User Story 1.
4. User Story 3 -> clasificación de polifonía + agregación sobre un conjunto + orquestador (`ejecutar_deteccion`) que ata todo, con exclusión terminal por grabación.
5. Polish -> `just gauntlet`, mutation testing, validación manual de `quickstart.md`.
6. CLI (Fase 7) -> comando real que nunca mide sobre la reserva de GuitarSet, con `just gauntlet` re-corrido para cubrirlo.

---

## Notes

- **Por qué Foundational es más chica que en Feature 004**: a diferencia del hito 1 (donde `medicion` reutilizaba tipos ya cerrados de tres features previas), aquí solo `NotaReferencia`/`NotaEstimada`/`ResultadoSubconjunto`/`ClasificacionPolifonia` son necesarios para que **las tres** historias puedan empezar -- `Transcriptor`/`ModeloTranscripcionDeclarado` (T010) solo los necesita User Story 2 en adelante, y `ExclusionDeteccion`/`ResultadoDeteccionGrabacion` (T016) solo User Story 3, así que viven en la fase de la historia que primero los necesita, no en Foundational (mismo criterio general que ya aplicó Feature 004 al T006 de esa feature, aplicado aquí con un corte más fino porque esta feature tiene una historia P1 genuinamente independiente del modelo).
- **Corrección de ubicación respecto a research.md #11 (T016, CRITICAL)**: ese documento describía `ExclusionDeteccion` como parte de `deteccion/orquestador.py`. No puede vivir ahí: `agregar_conjunto` (`analytics.metrica_deteccion_notas`) recibe `list[ResultadoDeteccionGrabacion]` en su propia firma pública (contracts/deteccion.md), y `analytics` no puede importar de `deteccion` sin crear una dependencia circular -- `deteccion` es, por diseño, el paquete que importa de las tres capas de abajo (`ingestion`, `transcripcion`, `analytics`), nunca al revés (research.md #11 mismo). Ambos tipos se definen en `analytics/metrica_deteccion_notas.py`; `deteccion/orquestador.py` los importa desde ahí, igual que importa `NotaReferencia`/`NotaEstimada`.
- **`evaluar_subconjunto` (T009) no aparece en `contracts/deteccion.md`**: el contrato solo nombra `clasificar_polifonia_en_instante`, `evaluar_grabacion` y `agregar_conjunto` como funciones públicas. `evaluar_subconjunto` es un helper extraído para que las tres invocaciones de `mir_eval` que `evaluar_grabacion` necesita hacer (global, monofónico, polifónico -- data-model.md, docstring de `ResultadoSubconjunto`: "sobre un subconjunto de notas (global, monofónico, o polifónico)") no dupliquen la misma lógica de guard-de-vacío + llamada a `mir_eval` tres veces -- mismo patrón de extracción que `calcular_mediana_agregada`/`calcular_distribucion_referencias` en Feature 004 (T004 de esa feature). No es una desviación del contrato, es la pieza interna que lo hace implementable sin repetición.
- **US2 AS4 (fallo de inferencia -> exclusión terminal) se verifica en User Story 3, no en User Story 2**: `spec.md` lista ese escenario bajo User Story 2, pero el comportamiento real ("se registra como excluida, la corrida sigue") es responsabilidad de `deteccion.orquestador.ejecutar_deteccion` (T023/T024, US3) -- `Transcriptor`/`BasicPitchTranscriptor` (US2) solo levantan `TranscripcionFallidaError` (T010/T014); no les corresponde decidir si la corrida continúa. Mismo patrón que Feature 003 separó "la separación falla" (excepción) de "el orquestador la convierte en exclusión y sigue" (orquestador de Feature 004).
- **GAP entre `plan.md` y la constitución v1.7.0 -- RESUELTO (sesión de cierre de huecos, constitución v1.8.0)**: la reserva de GuitarSet quedó fijada por documentación (sin re-correr `/speckit-plan` completo, para no arriesgar las decisiones ya verificadas de Basic Pitch/`mir_eval`/`onnxruntime`): **72 de 360 grabaciones (20%) reservadas, semilla `20260908`** (constitución Principio VI v1.8.0, `research.md` #14, `plan.md#Scale/Scope`, `spec.md` Assumptions actualizado). Las tareas de CLI, antes bloqueadas por esta laguna, se agregan en la Fase 7 más abajo.
