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
- `tests/fixtures/transcriptor_fixture.py`, `tests/unit/test_metrica_deteccion_notas.py`, `tests/unit/test_guitarset.py`, `tests/integration/test_deteccion_orquestador_integracion.py`, `tests/integration/test_basic_pitch_modelo_real_integracion.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar las dos capas nuevas y las dependencias antes de escribir código de dominio.

- [ ] T001 [P] Crear `src/guitar_tabs_analysis/transcripcion/__init__.py` y `src/guitar_tabs_analysis/deteccion/__init__.py` (paquetes vacíos, dos capas nuevas, plan.md#Project Structure).
- [ ] T002 En `pyproject.toml`, agregar `basic-pitch[onnx]` (Apache-2.0, research.md #1), `mir_eval` (MIT, research.md #3/#4/#5) y `mirdata` (BSD-3-Clause, research.md #7) como dependencias directas -- **nunca** el extra `[tf]` de `basic-pitch` (research.md #2). Correr `uv lock` y confirmar en `/implement` que `onnxruntime` queda como único backend de inferencia disponible para `basic_pitch` (ningún paquete instalado arrastra `tensorflow` de forma transitiva).
- [ ] T003 En `pyproject.toml::[tool.importlinter]`, agregar `"guitar_tabs_analysis.transcripcion"` al contrato `layers` existente, en la misma posición relativa que `guitar_tabs_analysis.separacion` (puede importar de `analytics`/`ingestion`, ninguna de las dos importa de vuelta, research.md #11) -- `guitar_tabs_analysis.deteccion` **NO** se agrega, con un comentario junto al contrato documentando la exclusión a propósito (mismo criterio que `medicion`, Feature 004). Depende de T002 (mismo archivo, secuencial). Correr `uv run lint-imports` y confirmar que el contrato sigue pasando (los paquetes de T001 todavía no importan nada).
- [ ] T004 [P] Extender `docs/ATRIBUCIONES.md` con una sección nueva para Basic Pitch (Apache-2.0, código y pesos, sin asimetría -- research.md #1), GuitarSet (CC BY 4.0, ya admitida por Principio IV), `mir_eval` (MIT, research.md #3/#4/#5) y `mirdata` (BSD-3-Clause, research.md #7) -- mismo archivo que documenta Demucs/Slakh2100 desde la Feature 003 (research.md #13).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Los tipos que `NotaReferencia`/`NotaEstimada` -- únicos que User Story 1 necesita para escribirse por completo con notas sintéticas, sin GuitarSet ni ningún modelo.

**⚠️ CRITICAL**: Ninguna user story empieza hasta que esta fase esté completa.

- [ ] T005 [P] Tipos de dominio en `src/guitar_tabs_analysis/ingestion/guitarset.py` (nuevo, data-model.md): `NotaReferencia` (`frozen=True`: `tono_midi: float`, `inicio_s: float`, `fin_s: float`), `LecturaGrabacion` (`frozen=True`: `grabacion_id: str`, `ruta_audio: Path`, `notas_referencia: list[NotaReferencia]`), y `GrabacionNoExisteError` (mismo patrón que `TemaNoExisteError` de `ingestion.slakh2100`, contracts/deteccion.md postcondición 2 de `leer_grabacion`). Este módulo no importa `transcripcion` ni `analytics` (capa base, research.md #11) -- todavía sin la función `leer_grabacion()` en sí (User Story 2, T012).
- [ ] T006 [P] Tipos de dominio en `src/guitar_tabs_analysis/analytics/metrica_deteccion_notas.py` (nuevo, data-model.md): `NotaEstimada` (`frozen=True`: `tono_midi: float`, `inicio_s: float`, `fin_s: float` -- `velocity`/`pitch_bend` de Basic Pitch no se conservan, research.md #1, ningún requisito de esta feature los necesita), `ClasificacionPolifonia = Literal["monofonica", "polifonica"]`, `ResultadoSubconjunto` (`frozen=True`: `precision: float | None`, `exhaustividad: float | None`, `balance_f1: float | None`, `num_notas_referencia: int`, `num_notas_estimadas: int`). Puede importar `NotaReferencia` de `ingestion.guitarset` (T005), nunca de `transcripcion` (research.md #11, contracts/deteccion.md).

**Checkpoint**: Tipos base listos -- User Story 1 puede empezar sin GuitarSet ni ningún modelo.

---

## Phase 3: User Story 1 - Juzgar si una nota estimada acierta contra una de referencia (Priority: P1) 🎯 MVP

**Goal**: Una función que, dado un conjunto de `NotaReferencia` y `NotaEstimada` de una misma grabación, calcula acierto vía `mir_eval.transcription` (tolerancia de tono 50 cents, ventana de inicio 50 ms, duración ignorada con `offset_ratio=None` -- research.md #3/#4/#5) y produce un `ResultadoSubconjunto`, con el denominador-cero de FR-008 resuelto explícitamente (`None`, nunca una cifra sobre cero casos).

**Independent Test**: Construir pares de notas a mano (dentro/fuera de tolerancia de tono, dentro/fuera de ventana de inicio, en el borde exacto de cada una, con duraciones distintas que no afectan el acierto) y varios conjuntos con múltiples notas, verificando el veredicto contra cada Acceptance Scenario de `spec.md` User Story 1 -- sin GuitarSet ni ningún modelo.

### Tests for User Story 1 ⚠️

> Escribir estos tests primero, confirmarlos en rojo contra la función aún no implementada.

- [ ] T007 [P] [US1] Tests unitarios de los Acceptance Scenarios 1-5 de `spec.md` User Story 1 en `tests/unit/test_metrica_deteccion_notas.py` (nuevo): mismo tono e inicios dentro de la ventana -> acierto (AS1); tono fuera de tolerancia (inicio cercano) -> desacierto (AS2); inicio fuera de ventana (mismo tono) -> desacierto (AS3); duración muy distinta con tono e inicio dentro de tolerancia -> acierto, la duración no participa (AS4); varias referencias y varias estimadas sobre la misma grabación -> cada estimada se acredita a lo sumo a una referencia y viceversa, nunca doble crédito (AS5, FR-005). Depende de T005, T006.
- [ ] T008 [P] [US1] Tests unitarios de subconjunto vacío en el mismo archivo (`tests/unit/test_metrica_deteccion_notas.py`, FR-008, data-model.md `ResultadoSubconjunto`): ambas listas vacías -> `precision`/`exhaustividad`/`balance_f1` en `None`; solo `notas_referencia` vacía (hay estimadas) -> `exhaustividad=None`, `precision` calculada (0.0, ninguna estimada tiene con qué acertar -- Edge Cases de spec.md); solo `notas_estimadas` vacía (hay referencias) -> `precision=None`, `exhaustividad` calculada (0.0, nada acertó). Depende de T005, T006.

### Implementation for User Story 1

- [ ] T009 [US1] Implementar `evaluar_subconjunto(notas_referencia: list[NotaReferencia], notas_estimadas: list[NotaEstimada]) -> ResultadoSubconjunto` en `analytics/metrica_deteccion_notas.py`: convierte tono MIDI e intervalos al formato que `mir_eval.transcription.precision_recall_f1_overlap` espera (`mir_eval.util.midi_to_hz`), la invoca con `onset_tolerance=0.05`, `pitch_tolerance=50.0`, `offset_ratio=None` (research.md #3/#4/#5) -- **guard explícito de listas vacías ANTES de invocar `mir_eval`**, sin depender de qué haga la librería con entrada vacía (verificar contra su código fuente real en `/implement`, no supuesto aquí), para producir los `None` de FR-008/data-model.md de forma controlada en los tres casos de T008. Depende de T007, T008.

**Checkpoint**: Acierto/emparejamiento correcto, verificable con notas sintéticas, sin ningún modelo ni GuitarSet -- MVP de la feature.

---

## Phase 4: User Story 2 - Obtener las notas que un modelo preentrenado estima sobre una grabación (Priority: P2)

**Goal**: `leer_grabacion()` real contra GuitarSet (vía `mirdata`, señal `audio_mic`) y `BasicPitchTranscriptor` real (Basic Pitch, backend ONNX), ambos verificados de punta a punta -- único camino de esta feature que toca red/disco/modelo real.

**Independent Test**: Invocar `BasicPitchTranscriptor.transcribir()` sobre una grabación corta real de GuitarSet y verificar que el resultado es una lista de `NotaEstimada` sin ninguna excepción no controlada (spec.md User Story 2, análogo al test `modelo_real` que el hito 1 ya estableció para `DemucsSeparador`).

- [ ] T010 [US2] `Transcriptor` (Protocol), `ModeloTranscripcionDeclarado` (`frozen=True`: `nombre: str`, `variante: str`, `firma: str`, `backend: str`, `licencia: str`, data-model.md) y `TranscripcionFallidaError` en `src/guitar_tabs_analysis/transcripcion/transcriptor.py` (nuevo) -- mismo patrón que `separacion/separador.py` (`Separador`/`ModeloDeclarado`/`SeparacionFallidaError`). `transcribir(self, ruta_audio: Path) -> list[NotaEstimada]` recibe una **ruta de archivo**, no muestras en memoria (contracts/deteccion.md: `basic_pitch.inference.predict()` solo acepta ruta, verificado contra su código fuente real, research.md #1). Importa `NotaEstimada` de `analytics.metrica_deteccion_notas` (T006). Este módulo no importa `basic_pitch`. Depende de T006.
- [ ] T011 [P] [US2] `TranscriptorFalso` en `tests/fixtures/transcriptor_fixture.py` (nuevo): implementa el protocolo `Transcriptor` de forma configurable (`notas: list[NotaEstimada] | None`, `excepcion: Exception | None`), mismo patrón que `SeparadorFalso` (`tests/fixtures/separador_fixture.py`) -- por defecto devuelve `[]` o la lista `notas` inyectada; si `excepcion` no es `None`, la levanta al invocar `transcribir()`. Cuenta invocaciones (`self.llamadas`), igual que `SeparadorFalso`. Depende de T010.
- [ ] T012 [US2] Implementar `leer_grabacion(grabacion_id: str, root_dir: Path) -> LecturaGrabacion` en `ingestion/guitarset.py` vía `mirdata`: `ruta_audio` apuntando al archivo real de `audio_mic` (research.md #6 -- **nunca** `audio_mix` ni ninguna señal hexafónica), `notas_referencia` derivadas de `Track.notes_all` (`intervals`/`values`, research.md #7) mapeadas a `NotaReferencia`. Si `grabacion_id` no existe en el índice de `mirdata` (o el índice está corrupto), levanta `GrabacionNoExisteError` -- nunca una excepción cruda de `mirdata` sin envolver (contracts/deteccion.md postcondición 2). Depende de T005.
- [ ] T013 [P] [US2] Tests unitarios de `leer_grabacion` en `tests/unit/test_guitarset.py` (nuevo), con el índice/`Track` de `mirdata` reemplazado por `monkeypatch` (sin descargar GuitarSet real, Principio IV): una grabación existente devuelve `LecturaGrabacion` con `ruta_audio` de `audio_mic` y `notas_referencia` que coinciden con `Track.notes_all` (contracts/deteccion.md postcondición 1); una `grabacion_id` inexistente levanta `GrabacionNoExisteError` (postcondición 2). Depende de T012.
- [ ] T014 [US2] Implementar `BasicPitchTranscriptor` en `transcripcion/basic_pitch_transcriptor.py` (nuevo) -- único módulo de esta feature que importa `basic_pitch`: construye el modelo ONNX declarado una sola vez (reutilizable entre llamadas, research.md #1/#2), `transcribir(ruta_audio)` invoca `basic_pitch.inference.predict()` y mapea cada tupla `(start_time_s, end_time_s, pitch_midi, velocity, pitch_bend)` a `NotaEstimada` (descartando `velocity`/`pitch_bend`), backend `onnx` forzado (research.md #2). Envuelve cualquier excepción real de `basic_pitch`/`onnxruntime` en `TranscripcionFallidaError` -- **nunca** la deja propagar cruda (contracts/deteccion.md postcondición 2). Depende de T010.
- [ ] T015 [P] [US2] `tests/integration/test_basic_pitch_modelo_real_integracion.py` (nuevo) -- único test `@pytest.mark.modelo_real` de esta feature, mismo mecanismo de aviso visible que el hito 1 (`tests/conftest.py`, nunca corre como parte de `just gauntlet`): `BasicPitchTranscriptor.transcribir()` sobre una grabación corta real de GuitarSet produce una lista de `NotaEstimada` (o vacía, si el clip no tiene nada que Basic Pitch reconozca -- spec.md US2 AS3) sin lanzar ninguna excepción no controlada (AS1). Si `BasicPitchTranscriptor()` falla al construirse (sin red/pesos), el test se salta con `pytest.skip(f"...: {causa}")`, mismo patrón que `test_demucs_separador_integracion.py` de la Feature 003. Depende de T014.

**Checkpoint**: User Story 2 completa -- lectura real de GuitarSet y modelo real ambos verificados de punta a punta; `TranscripcionFallidaError` se levanta correctamente ante un fallo real (la conversión de ese fallo en una exclusión que no aborta la corrida es responsabilidad de `deteccion.orquestador`, User Story 3, T023/T024 -- ver Notes).

---

## Phase 5: User Story 3 - Medir el sistema sobre un conjunto de grabaciones y reportar por polifonía (Priority: P3)

**Goal**: Clasificación de polifonía a partir exclusivamente de la anotación de referencia (research.md #8), agregación sobre un conjunto de grabaciones -- pool plano, nunca promedio de resultados por grabación (contracts/deteccion.md postcondición 4) -- y el orquestador (`ejecutar_deteccion`) que ata User Story 1 y User Story 2 sobre un conjunto real, con exclusión terminal por grabación ante un fallo de inferencia (FR-012).

**Independent Test**: Con `TranscriptorFalso` (T011) y notas de referencia/estimadas construidas a mano sobre varias grabaciones sintéticas (algunas monofónicas, otras con acordes, alguna configurada para fallar), verificar `ejecutar_deteccion()` contra cada Acceptance Scenario de `spec.md` User Story 3 y el AS4 de User Story 2.

- [ ] T016 [US3] Agregar `ExclusionDeteccion` (`frozen=True`: `grabacion_id: str`, `detalle: str`) y `ResultadoDeteccionGrabacion` (`frozen=True`: `grabacion_id: str`, `notas_referencia: list[NotaReferencia] | None`, `notas_estimadas: list[NotaEstimada] | None`, `exclusion: ExclusionDeteccion | None`) a `analytics/metrica_deteccion_notas.py` (data-model.md) -- **corrección de ubicación respecto a research.md #11** (que las situaba en `deteccion/orquestador.py`, ver Notes): `agregar_conjunto` (T021, misma fase) las necesita en su propia firma, y `analytics` no puede importar de `deteccion` sin crear una dependencia circular (`deteccion` importa de las tres capas, nunca al revés, research.md #11). `deteccion/orquestador.py` las importa desde aquí. Depende de T006.
- [ ] T017 [P] [US3] Implementar `clasificar_polifonia_en_instante(instante_s: float, notas_referencia: list[NotaReferencia]) -> ClasificacionPolifonia` en `analytics/metrica_deteccion_notas.py` (research.md #8): cuenta cuántos intervalos `[inicio_s, fin_s]` de `notas_referencia` solapan `instante_s` (solape parcial cuenta) -- `"polifonica"` si dos o más solapan, `"monofonica"` en cualquier otro caso, incluido el caso degenerado de cero referencias solapando (FR-006). Depende de T005, T006.
- [ ] T018 [P] [US3] Tests unitarios de `clasificar_polifonia_en_instante` en `tests/unit/test_metrica_deteccion_notas.py` (mismo archivo que T007/T008): un acorde (dos o más referencias solapando el instante) -> `"polifonica"`; una nota suelta (cero o una referencia solapando) -> `"monofonica"`; solape justo en el borde de un intervalo; caso degenerado de cero referencias -> `"monofonica"`. Depende de T017.
- [ ] T019 [US3] Implementar `evaluar_grabacion(notas_referencia: list[NotaReferencia], notas_estimadas: list[NotaEstimada]) -> tuple[ResultadoSubconjunto, ResultadoSubconjunto, ResultadoSubconjunto]` (global, monofónico, polifónico) en `analytics/metrica_deteccion_notas.py`: clasifica cada `NotaReferencia` en su propio inicio y cada `NotaEstimada` en el suyo, ambas contra `notas_referencia` de la misma grabación (T017, research.md #8) -- la fuente de la clasificación es siempre la referencia, nunca la propia predicción (FR-006). Arma los tres pares de listas (global = todo sin partir, monofónico, polifónico) y llama `evaluar_subconjunto` (T009) **una vez por subconjunto** -- nunca calcula un emparejamiento global y lo divide después (contracts/deteccion.md postcondición 2, research.md #9). Depende de T009, T017.
- [ ] T020 [P] [US3] Tests de `evaluar_grabacion` en el mismo archivo: una grabación con pasajes monofónicos y polifónicos mezclados -> las tres cifras (global/mono/poli) coinciden con el cálculo esperado a mano; una grabación 100% monofónica -> el subconjunto polifónico se reporta como `None`, nunca como cero (FR-008); una nota estimada sin ninguna nota de referencia en la grabación (referencia vacía) -> clasificada monofónica por el caso degenerado y cuenta en contra de la precisión global (Edge Cases de spec.md). Depende de T019.
- [ ] T021 [US3] Implementar `agregar_conjunto(resultados: list[ResultadoDeteccionGrabacion]) -> tuple[ResultadoSubconjunto, ResultadoSubconjunto, ResultadoSubconjunto]` en `analytics/metrica_deteccion_notas.py`: filtra los `resultados` con `exclusion is not None`; para cada grabación no excluida, clasifica sus notas contra las referencias de **esa misma grabación** (nunca cruzando grabaciones -- la simultaneidad solo tiene sentido dentro de una misma grabación), y acumula en tres *pools* (global/mono/poli) a través de **todas** las grabaciones no excluidas; llama `evaluar_subconjunto` **una vez por pool**, sobre el conjunto combinado -- nunca promedia los `ResultadoSubconjunto` calculados por grabación (contracts/deteccion.md postcondición 4: una grabación con muchas notas debe pesar más que una con pocas). Depende de T016, T019.
- [ ] T022 [P] [US3] Tests de `agregar_conjunto` en el mismo archivo: varias grabaciones, alguna con `exclusion` (queda fuera del pool); un caso construido para que la cifra combinada sea observablemente distinta de promediar las cifras por grabación (fija que se pooleó, no se promedió); un conjunto cuyas referencias son todas monofónicas -> el subconjunto polifónico agregado se reporta como `None` (US3 AS3, FR-008). Depende de T021.
- [ ] T023 [US3] Implementar `ArtefactoDeteccion` (`frozen=True`, data-model.md: `modelo`, `tolerancia_tono_cents=50.0`, `ventana_inicio_s=0.05`, `grabaciones`, `exclusiones`, `resultados_por_grabacion`, `global_`, `monofonico`, `polifonico`) y `ejecutar_deteccion(grabaciones: list[str], root_dir: Path, transcriptor: Transcriptor) -> ArtefactoDeteccion` en `deteccion/orquestador.py` (nuevo, paquete excluido del contrato `layers`, research.md #11): para cada `grabacion_id`, llama `leer_grabacion` (T012) y `transcriptor.transcribir` (T010/T014); si cualquiera de los dos levanta una excepción real (`GrabacionNoExisteError` o `TranscripcionFallidaError`), registra `ExclusionDeteccion(grabacion_id, detalle=str(causa))` y **continúa** con la siguiente grabación -- nunca aborta la corrida completa (FR-012, research.md #10, contracts/deteccion.md postcondición 1). Al completar todas las grabaciones, arma y devuelve el `ArtefactoDeteccion` con el modelo declarado, la tolerancia y ventana fijas, la lista de grabaciones, las exclusiones con su motivo, los resultados crudos por grabación, y las tres cifras vía `agregar_conjunto` (T021) sobre las grabaciones no excluidas -- **nunca** compara ninguna cifra contra ningún umbral (FR-009, contracts/deteccion.md postcondición 3). Depende de T012, T014, T016, T021.
- [ ] T024 [P] [US3] Tests de integración en `tests/integration/test_deteccion_orquestador_integracion.py` (nuevo), con `TranscriptorFalso` (T011) y `leer_grabacion` real o con `monkeypatch` sobre el índice de `mirdata` (mismo mecanismo que T013): una grabación cuyo `TranscriptorFalso` está configurado para levantar una excepción -> queda excluida con un motivo distinguible, y la corrida sigue con el resto del conjunto (spec.md US2 AS4, FR-012, Clarifications 2026-09-07); agregación sobre varias grabaciones con notas construidas a mano produce un `ArtefactoDeteccion` con las tres cifras correctas (US3 AS1); una grabación cuya anotación de referencia no tiene ninguna nota -> se mide igual (no es una exclusión), su exhaustividad queda sin denominador (Edge Cases de spec.md, distinto del caso de fallo de inferencia). Depende de T023.

**Checkpoint**: Las tres user stories completas -- `ejecutar_deteccion()` mide un conjunto de grabaciones de punta a punta, reporta global/monofónico/polifónico, ningún fallo individual detiene la corrida, sin ningún umbral de aprobación.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T025 [P] Correr `just gauntlet` (ruff format --check + lint-imports + mypy --strict + tests unit/integration/property con cobertura ≥90%, excluyendo `-m modelo_real`) y corregir cualquier hallazgo.
- [ ] T026 [P] Correr `just mutation analytics.metrica_deteccion_notas` y `just mutation deteccion.orquestador` (excluye `transcripcion.basic_pitch_transcriptor.py` y `transcripcion.transcriptor.py` del alcance de mutación -- capa de invocación delgada, mismo criterio que `separacion.demucs_separador` en el hito 1) y resolver mutantes sobrevivientes, prestando atención particular a los mensajes de `TranscripcionFallidaError`/`GrabacionNoExisteError` y al `detalle` de `ExclusionDeteccion` (AGENTS.md, "Tests de excepciones").
- [ ] T027 Ejecutar manualmente la sección "Lo que corre en `just gauntlet`" de `quickstart.md` de punta a punta y confirmar que coincide con el comportamiento real; si hay red/pesos cacheados, correr también `uv run pytest -m modelo_real -v` y confirmar que T015 pasa o se salta visiblemente.

---

## Phase 7: CLI (desbloqueada -- la reserva de GuitarSet ya está fijada)

**Purpose**: Con el tamaño y la semilla de la reserva ya cerrados (72/360, semilla `20260908` -- Principio VI v1.8.0, research.md #14), la CLI puede construirse sin riesgo de reescritura. Mismo criterio que el hito 1 diferenció "orquestador puro" (Fase 5) de "CLI real" (aquí), Feature 004.

- [ ] T028 [US3] Implementar `construir_lista_grabaciones(root_dir: Path, manifiesto_reservados: Path) -> list[str]` en `deteccion/orquestador.py`: enumera los 360 identificadores de grabación de GuitarSet vía el índice de `mirdata`, ordenados; lee `manifiesto_reservados` (formato del manifiesto: research.md #14 -- `tests/holdout/guitarset_reservado_hito2.json`, lista de `grabacion_id`) y excluye esos 72 del resultado -- **nunca** los enumera. Si `manifiesto_reservados` no existe, MUST fallar con un mensaje claro (Principio IV: "el pipeline falla con mensaje claro si no lo encuentra, nunca en silencio") -- nunca asumir "sin reservados" por defecto, que dejaría medir sobre las 360 sin darse cuenta. Depende de T005, T012.
- [ ] T029 [P] [US3] Tests unitarios de `construir_lista_grabaciones` en `tests/unit/test_orquestador_deteccion.py` (nuevo): con un índice de `mirdata` sintético/monkeypatcheado y un manifiesto de reservados de prueba, el resultado excluye exactamente los `grabacion_id` del manifiesto y es reproducible (misma lista en dos invocaciones); manifiesto ausente -> excepción clara, sin devolver la lista completa por defecto. Depende de T028.
- [ ] T030 [US3] Implementar la serialización de `ArtefactoDeteccion` a un `dict` JSON-compatible en `deteccion/orquestador.py` -- función pura, sin tocar disco (mismo patrón que `artefacto_a_dict` de `medicion/orquestador.py`, Feature 004 T019). Depende de T023.
- [ ] T031 [P] [US3] Test unitario de la serialización de T030 en `tests/unit/test_orquestador_deteccion.py` (mismo archivo que T029): el `dict` contiene, como claves de nivel superior, exactamente lo que FR-011 exige (modelo, tolerancia, ventana, grabaciones, exclusiones con motivo, resultados por grabación, y el desglose global/monofónico/polifónico), y `json.dumps(...)`/`json.loads(...)` no pierde ningún valor (round-trip). Depende de T030.
- [ ] T032 [US3] Implementar `deteccion/cli.py`: `argparse.ArgumentParser` con `--root-dir` (`type=Path`, `required=True`) y `--manifiesto-reservados` (`type=Path`, `required=True` -- **sin** valor por defecto, mismo criterio que `medicion/cli.py` con `--modo`, FR-004 de Feature 004: un default silencioso sobre qué se mide es exactamente el riesgo que ese patrón evita); `main(argv=None)` construye `BasicPitchTranscriptor()` una sola vez, obtiene la lista con `construir_lista_grabaciones` (T028), llama `ejecutar_deteccion` (T023), serializa el resultado (T030) y lo escribe en `mediciones/deteccion_hito2.json` con escritura atómica (archivo temporal + `os.replace()`, mismo mecanismo que `medicion` ya usa). Único módulo de esta feature que importa `deteccion.orquestador` desde un punto de entrada de proceso. Depende de T023, T028, T030.
- [ ] T033 [P] [US3] Test de CLI en `tests/unit/test_deteccion_cli.py` (nuevo): invocar `deteccion.cli.main([])` (sin `--root-dir` ni `--manifiesto-reservados`) -> `SystemExit` con código distinto de 0 antes de construir ningún `BasicPitchTranscriptor` real (`monkeypatch` para confirmar que no se invoca), mismo patrón que `test_cli.py` del hito 1 (Feature 004, T027). Depende de T032.
- [ ] T034 [P] Agregar un recipe `detectar root_dir manifiesto_reservados` al `justfile` (mismo patrón que `medir modo root_dir`) que invoque `uv run python -m guitar_tabs_analysis.deteccion.cli --root-dir {{root_dir}} --manifiesto-reservados {{manifiesto_reservados}}`.
- [ ] T035 [P] Correr `just gauntlet` de nuevo (ahora con `deteccion/cli.py`/`orquestador.py` completos) y confirmar que la cobertura ≥90% sigue en verde -- T025 corrió antes de que esta fase existiera.

**Checkpoint**: `uv run python -m guitar_tabs_analysis.deteccion.cli --root-dir <ruta> --manifiesto-reservados <ruta>` es un comando real, que nunca mide sobre las 72 grabaciones reservadas del hito 2.

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
