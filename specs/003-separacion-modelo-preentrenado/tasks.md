---

description: "Task list template for feature implementation"
---

# Tasks: Separación de guitarra con modelo preentrenado

**Input**: Design documents from `/specs/003-separacion-modelo-preentrenado/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/separacion.md](./contracts/separacion.md), [quickstart.md](./quickstart.md)

**Tests**: Incluidas explícitamente — mismo criterio que Feature 002 (`just gauntlet` exige cobertura ≥90%, constitución Principio X pide test rojo antes que fix).

**Organization**: Tareas agrupadas por user story (P1/P2/P3 de `spec.md`), más dos fases sin user story que el usuario pidió explícitamente para esta sesión: medición de presupuesto de cómputo (Fase 5) y visibilidad del único test que ejercita el sistema completo (Fase 6).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede correr en paralelo con las demás tareas marcadas [P] de la misma fase (archivo distinto, sin dependencia pendiente)
- **[Story]**: A qué user story pertenece (US1/US2/US3) — ausente en Setup, Foundational, la fase de medición de presupuesto, la fase de visibilidad, y Polish, igual que en Features 001/002

## Path Conventions

Proyecto único (`src/`, `tests/` en la raíz), capa nueva `separacion` por encima de `analytics` (plan.md#Project Structure, research.md #8):
- `src/guitar_tabs_analysis/separacion/separador.py` — lógica de orquestación pura, sin `torch`/`demucs`
- `src/guitar_tabs_analysis/separacion/demucs_separador.py` — único módulo que importa `torch`/`demucs`
- `docs/ATRIBUCIONES.md` — declaración de licencias (FR-003/004)
- `tests/fixtures/separador_fixture.py`, `tests/unit/test_separador.py`, `tests/unit/test_demucs_separador.py`, `tests/unit/test_atribuciones.py`, `tests/integration/test_demucs_separador_integracion.py`, `tests/conftest.py` (nuevo)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar dependencias antes de escribir código de dominio.

- [X] T001 Añadir `demucs` a `[project].dependencies` en `pyproject.toml` (research.md #2, licencia MIT). Configurar `torch` para instalarse desde el índice CPU-only de PyTorch, no desde PyPI por defecto (research.md #7: ~187 MB contra ~555 MB con CUDA sin uso, "sin GPU declarada" del hardware descrito) — en `pyproject.toml`: `[[tool.uv.index]]` con `name = "pytorch-cpu"`, `url = "https://download.pytorch.org/whl/cpu"`, `explicit = true`; `[tool.uv.sources]` con `torch = { index = "pytorch-cpu" }`. Correr `uv lock` + `uv sync` y confirmar en `uv.lock` que la rueda resuelta de `torch` es la variante `+cpu` (`grep torch uv.lock` o inspeccionar la URL resuelta), no la de CUDA.
- [X] T002 [P] Dos cambios de configuración, mismo `pyproject.toml`, sin dependencia entre sí: (a) agregar `"guitar_tabs_analysis.separacion"` al **inicio** de `layers` en `[[tool.importlinter.contracts]]` (por encima de `analytics`, research.md #8) — correr `uv run lint-imports` para confirmar que el contrato sigue siendo válido aunque el paquete `separacion` todavía no exista (import-linter no falla por un paquete de una capa sin módulos, solo por una importación que lo viole); (b) agregar `"modelo_real: el único test que ejercita el sistema completo con el modelo real; se salta sin red o sin pesos cacheados (research.md #7)"` a `markers` en `[tool.pytest.ini_options]`, junto al `holdout` ya existente.
- [X] T003 [P] Crear `src/guitar_tabs_analysis/separacion/__init__.py` (paquete vacío, capa nueva).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Tipos y protocolo que las tres user stories necesitan.

**⚠️ CRITICAL**: Ninguna user story empieza hasta que esta fase esté completa.

- [X] T004 Crear en `src/guitar_tabs_analysis/separacion/separador.py` los tipos inmutables `ModeloDeclarado`, `TransformacionDeclarada`, `ResultadoSeparacionTema` (dataclasses `frozen=True`), el protocolo `Separador` (`typing.Protocol`: `modelo_declarado`, `samplerate`, `audio_channels`, `separar(muestras) -> dict[str, NDArray]`), y la excepción `SeparacionFallidaError(tema_id, causa)` según data-model.md y contracts/separacion.md. Reutiliza `PistaAudio` de `guitar_tabs_analysis.ingestion.slakh2100` y `Estimacion` de `guitar_tabs_analysis.analytics.metrica_separacion` (import permitido: `separacion` → `analytics` → `ingestion`, T002). Sin lógica de cálculo todavía — este módulo no importa `torch` ni `demucs`.
- [X] T005 [P] Crear `tests/fixtures/separador_fixture.py`: `SeparadorFalso` (implementa el protocolo `Separador`, configurable en `samplerate`, `audio_channels`, el diccionario que devuelve `separar()` — incluida la posibilidad de omitir `"guitar"` o de levantar una excepción arbitraria en vez de devolver algo) y un helper de mezcla mono sintética (senoidal, duración parametrizable). Nunca importa `torch`/`demucs`.

**Checkpoint**: Tipos, protocolo y fixtures listos — las user stories pueden empezar.

---

## Phase 3: User Story 1 - Producir estimaciones de guitarra para un tema (Priority: P1) 🎯 MVP

**Goal**: Dada la mezcla de un tema y un `Separador`, verificar (no asumir) formato de entrada/salida contra lo que el separador espera, aplicar y declarar cualquier transformación, y devolver la colección de estimaciones que produjo, sin inventar nada ni fallar en silencio ante un error real del modelo.

**Independent Test**: Con `SeparadorFalso` (T005), invocar `separar_guitarra` sobre distintas combinaciones de formato/salida/fallo y verificar `ResultadoSeparacionTema` contra cada Acceptance Scenario de `spec.md` User Story 1.

### Tests for User Story 1 ⚠️

> Escribir estos tests primero, confirmarlos en rojo contra `separar_guitarra` aún no implementado.

- [X] T006 [P] [US1] Unit test: mezcla con `frecuencia_muestreo` igual a `separador.samplerate` → `resultado.transformaciones` incluye `TransformacionDeclarada(tipo="frecuencia_muestreo", direccion="entrada", aplicada=False)`, y el array que recibe `separador.separar()` no fue remuestreado, en `tests/unit/test_separador.py` (AS1, FR-005).
- [X] T007 [US1] Unit test: mezcla con `frecuencia_muestreo` distinta a `separador.samplerate` → `aplicada=True`, y el array que recibe `separador.separar()` está efectivamente remuestreado a `separador.samplerate` (verificar longitud esperada, `len ≈ len_original * samplerate_modelo / samplerate_original`), en `tests/unit/test_separador.py` (AS2, FR-005) (mismo archivo que T006, después de T006).
- [X] T008 [US1] Unit test: mezcla mono contra `separador.audio_channels == 2` → el array que recibe `separador.separar()` tiene forma `(2, N)` con ambos canales idénticos (duplicado, no rellenado); la salida `"guitar"` (simulada de 2 canales, con valores distintos por canal en el `SeparadorFalso` para que el test no pase por accidente) se colapsa en el resultado a un array de una sola dimensión igual al promedio `(L + R) / 2`; `resultado.transformaciones` declara **ambas** transformaciones de canal por separado (entrada y salida), en `tests/unit/test_separador.py` (AS3, FR-006, FR-007) (mismo archivo, después de T007).
- [X] T009 [US1] Unit test: `SeparadorFalso.separar()` configurado para levantar una excepción arbitraria (`RuntimeError("forma no soportada")`) → `separar_guitarra` levanta `SeparacionFallidaError` con `tema_id` y `str(causa)` en el mensaje, `error.__cause__` es la excepción original, y `separador.separar()` se llamó exactamente una vez (sin reintento — usar un `SeparadorFalso` que cuenta invocaciones), en `tests/unit/test_separador.py` (AS6, FR-014) (mismo archivo, después de T008).
- [X] T010 [P] [US1] Property test (Hypothesis): para `SeparadorFalso` generados con `samplerate`/`audio_channels`/duración de mezcla arbitrarios (incluyendo el caso sin transformación real y el caso con ambas), `resultado.transformaciones` siempre tiene exactamente 2 entradas de `direccion="entrada"` (frecuencia y canales) más 1 de `direccion="salida"` cuando hay una estimación producida; ninguna transformación reescala amplitud fuera de la duplicación/promedio esperados (la energía total de la mezcla original, ajustada por el factor de canales, se conserva dentro de tolerancia); y dos invocaciones sucesivas con el mismo `SeparadorFalso` determinista producen `Estimacion.audio.muestras` idénticas (FR-015, caso trivial — el no trivial lo cubre la Fase 6 con el modelo real), en `tests/property/test_separador_property.py`.

### Implementation for User Story 1

- [X] T011 [US1] Implementar `separar_guitarra(tema_id: str, mezcla: PistaAudio, separador: Separador) -> ResultadoSeparacionTema` en `src/guitar_tabs_analysis/separacion/separador.py`: compara `mezcla.frecuencia_muestreo` contra `separador.samplerate` (remuestrea con `scipy.signal.resample` si difieren, ya declarando la transformación; `scipy` ya es dependencia del proyecto desde Feature 002); compara el número de canales de `mezcla` (1, siempre mono) contra `separador.audio_channels` (duplica con `numpy.tile`/`broadcast_to` si el modelo espera más de 1); envuelve la llamada a `separador.separar()` en un `try/except Exception as causa: raise SeparacionFallidaError(tema_id, causa) from causa`; si el diccionario resultante no tiene `"guitar"`, `estimaciones = []` (FR-009); si la tiene, colapsa sus canales a mono promediando (`.mean(axis=0)`), construye una `Estimacion(identificador="guitar", audio=PistaAudio(...))` (FR-010, sin evaluar su energía) y declara la transformación de salida; construye y devuelve `ResultadoSeparacionTema` con `modelo=separador.modelo_declarado` (depende de T004, T005; mismo archivo que T004, después de T004).

**Checkpoint**: User Story 1 funciona y se puede validar de forma independiente con `SeparadorFalso` — ✅ hecho (T006-T011 en verde, `just gauntlet` completo, 98 tests, 100% cobertura en `separador.py`, sin cargar el modelo real todavía).

---

## Phase 4: User Story 2 - Declarar el modelo y sus licencias de forma fija y verificable (Priority: P2)

**Goal**: El modelo (nombre, variante, firma, checksum) y la licencia de sus pesos quedan declarados en un lugar consultable sin ejecutar ninguna inferencia.

**Independent Test**: Importar la declaración del modelo y leer `docs/ATRIBUCIONES.md` sin invocar `separar_guitarra` ni cargar ningún peso real.

### Tests for User Story 2 ⚠️

- [X] T012 [P] [US2] Unit test: `demucs_separador.MODELO_DECLARADO` tiene `nombre="Demucs"`, `variante="htdemucs_6s"`, `firma="5c90dfd2"`, `checksum_sha256_prefijo="d2a1745f0744"` (research.md #1/#2, corrección post-`/plan`: hash real del archivo `.safetensors` efectivamente cargado, no el del `.th` legacy), y dos importaciones sucesivas del módulo devuelven el mismo valor (consulta idempotente, sin instanciar `DemucsSeparador` ni tocar la red), en `tests/unit/test_demucs_separador.py` (AS1, FR-002).
- [X] T013 [P] [US2] Test: `docs/ATRIBUCIONES.md` existe y contiene, como texto plano verificable con `assert ... in contenido`: la licencia MIT del código de Demucs, el nombre `"htdemucs_6s"`, la declaración de uso personal y educativo de los pesos, y la cita de la fuente de la restricción de los pesos (el issue `facebookresearch/demucs#327`, research.md #3 — citada como aportada por el usuario, no verificada de forma independiente por este proyecto), en `tests/unit/test_atribuciones.py` (AS2, FR-003, FR-004).

### Implementation for User Story 2

- [X] T014 [P] [US2] Crear `docs/ATRIBUCIONES.md` con la declaración exigida por T013: licencia MIT del código de Demucs (con enlace/cita del archivo `LICENSE` real del repositorio, research.md #2), variante `htdemucs_6s`, y la nota de licencia de los pesos citando `facebookresearch/demucs#327` con la advertencia explícita de que este proyecto no verificó esa cita de forma independiente (bloqueo de red del entorno de planificación, research.md #3) — uso del proyecto declarado como personal y educativo.
- [X] T015 [US2] Implementar `MODELO_DECLARADO` (constante, valores de T012) y `DemucsSeparador` en `src/guitar_tabs_analysis/separacion/demucs_separador.py`: envuelve `demucs.api.Separator(model="htdemucs_6s", device="cpu")` (research.md #1/#2, `device="cpu"` fijo — hardware sin GPU utilizable, AMD sin ROCm probado); expone `modelo_declarado` (la constante), `samplerate`/`audio_channels` como propiedades que leen `self._separator.samplerate`/`.audio_channels` (nunca hardcodeadas — research.md #4); `separar(muestras)` llama `self._separator.separate_tensor(torch.from_numpy(muestras), sr=self.samplerate)` y convierte cada tensor de salida a `numpy` antes de devolver el diccionario (depende de T004 para la forma del protocolo `Separador`; T012 lo prueba).

**Checkpoint**: User Stories 1 y 2 funcionan de forma independiente — ✅ hecho (T012-T015 en verde, 105 tests, `just gauntlet` completo). Pesos de `htdemucs_6s` ya cacheados localmente en este entorno (HuggingFace Hub, no el fallback legacy) — `DemucsSeparador()` carga en ~1.9s con `HF_HUB_OFFLINE=1`, sin red. Corrección post-`/plan`: el checksum declarado se ajustó al hash real del archivo `.safetensors` efectivamente cargado (research.md #2).

---

## Phase 5: Medición de presupuesto de cómputo real (bloqueante para el alcance del hito 1)

**Por qué esta fase existe y por qué va aquí, no en Polish**: pedido explícito del usuario para esta sesión. El resultado de esta medición condiciona qué alcance es ejecutable para el hito 1 (¿corre el conjunto de prueba completo, o hace falta declarar una submuestra?) — es información de la que dependen decisiones de alcance posteriores, no una tarea de limpieza de cierre. Requiere que `DemucsSeparador` (T015) ya exista.

- [X] T016 Medir, con reloj real (`time.perf_counter()`, no una estimación), cuánto tarda `separar_guitarra` (vía `DemucsSeparador`) sobre **un tema completo real** de Slakh2100 — no un clip sintético. Dataset disponible localmente en `/home/mrjuancho/datos/slakh2100_flac_redux` (confirmado en esta sesión de planificación); usar `guitar_tabs_analysis.ingestion.slakh2100.leer_tema(tema_id, root_dir=Path("/home/mrjuancho/datos/slakh2100_flac_redux/train"))` (**train o validation, NUNCA `test`** — el split de prueba es el conjunto reservado del Principio VI de la constitución, y esta medición ni siquiera necesita examinar su contenido; corrección hecha antes de ejecutar, no descubierta a mitad de la medición) sobre un `tema_id` real, confirmando la duración real (`len(mezcla.muestras) / mezcla.frecuencia_muestreo`) antes de medir — no asumir que son exactamente ~4 minutos/~10.6M muestras, verificarlo del tema elegido. Medir también el pico de memoria residente del proceso durante la inferencia (`resource.getrusage(resource.RUSAGE_SELF).ru_maxrss`, o equivalente) — hay 64 GB disponibles, pero conviene saber cuánto pide un tema antes de planear corridas en paralelo. Correr en un script ad-hoc (`uv run python -c "..."` o un script temporal, no en `just gauntlet` — es una medición manual de una sola vez, igual que T028 de Feature 002). Registrar en `research.md` una entrada nueva (`## 9. Presupuesto de cómputo medido para inferencia real`) con: el tiempo real medido, el pico de memoria medido, la duración real del tema usado, el hardware (8 núcleos CPU, 64 GB RAM, sin GPU utilizable), la extrapolación aritmética simple al split de prueba (~150 temas) y al conjunto completo (~2100 temas). **Si la extrapolación al conjunto completo supera el orden de días**, declarar en esa misma entrada una submuestra explícita para el hito 1 (tamaño y criterio de selección reproducible, p. ej. N temas por orden alfabético o por semilla fija del split de prueba) con su justificación, y anotar explícitamente que este hallazgo debe registrarse en la constitución (Principio VII, presupuesto) vía `/speckit-constitution` en una sesión posterior — este task NO edita `constitution.md` directamente (Governance: los `ABIERTO` no se rellenan por adelantado ni fuera de ese comando).

**Checkpoint**: ✅ hecho (research.md #9). Medido sobre `Track00001` de `train`: 53,40 s de inferencia real (241,56 s de audio), pico de memoria 2,3 GB. Extrapolación al conjunto evaluable completo (1710 temas, sin `omitted`): ~25,4 horas (~1,06 días) — cruza el umbral de "orden de días" para una corrida secuencial repetible. **Submuestra declarada para el hito 1 (corregida 2026-09-05)**: 40 temas de `validation` por **muestreo aleatorio con semilla fija `20260904`** (no los primeros por orden alfabético — un orden así podía correlacionar con algo del proceso de generación del dataset sin que nadie lo hubiera verificado; corregido antes de que el número llegara a la constitución, más barato ahora que después de medir), nunca de `test`. Distribución de guitarras por tema de esa muestra, verificada contra `metadata.yaml`: `{1: 9, 2: 13, 3: 6, 4: 7, 5: 1, 6: 4}` — 31/40 (77,5%) polifónicos, así que sí ejercita el caso que más importa (Principio V). Queda anotado que el Principio VII de la constitución necesita actualizarse vía `/speckit-constitution` con esta evidencia — no editado aquí.

---

## Phase 6: Visibilidad del único test de punta a punta con el modelo real

**Por qué esta fase existe**: pedido explícito del usuario — `modelo_real` es el único test que ejercita el sistema completo (carga real del modelo, transformaciones reales, inferencia real). Saltarlo sin que el resumen lo muestre de forma visible reproduce el patrón de "compuerta que pasa sin haber examinado nada" que este proyecto ya encontró varias veces (`AGENTS.md`, sección "qué falla cerrado y qué falla abierto": el hook de `jq` ausente, y el hallazgo de `uv lock --check` mal ordenado, son dos hechos documentados de ese mismo patrón). `addopts = "-q --strict-markers"` en `pyproject.toml` no imprime motivos de salto por defecto — sin esta fase, un salto real sería indistinguible de "todo pasó".

- [ ] T017 [P] Crear `tests/conftest.py` (nuevo — no existe ninguno en el proyecto todavía) con un hook `pytest_terminal_summary` que, al final de cualquier corrida (con o sin `-q`), cuenta los tests con el marcador `modelo_real` que terminaron `skipped` y, si hay al menos uno, imprime un bloque separado y visible (`terminalreporter.write_sep("=", ...)`) con el conteo y el motivo de cada salto — nunca silencioso, nunca solo en el resumen de una línea que `-q` suprime. Escribir un test de regresión que demuestre que el mecanismo SÍ avisa cuando corresponde (no solo que no rompe nada): invocar `pytest` como subproceso (`subprocess.run` o el plugin `pytester` de pytest) sobre un archivo de test temporal con una única prueba marcada `modelo_real` que se salta a propósito (`pytest.skip("sin red, motivo de prueba")`), y verificar que la salida capturada contiene el bloque visible y el motivo — en `tests/unit/test_conftest_modelo_real.py` (AGENTS.md, "su test de regresión debe demostrar que el chequeo falla cuando debe fallar", aplicado aquí a "que el aviso aparece cuando debe aparecer").
- [ ] T018 Crear `tests/integration/test_demucs_separador_integracion.py`: el único test marcado `@pytest.mark.modelo_real` de esta feature. Construye un `DemucsSeparador` real y separa un clip sintético mono de 1-2 segundos (no un tema completo — eso ya lo mide la Fase 5 aparte); si la construcción del `DemucsSeparador` falla (sin red la primera vez que se descargan los pesos, o cualquier error de carga), el test se salta con `pytest.skip(f"DemucsSeparador no se pudo cargar: {causa}")` — motivo específico, no genérico — capturando la excepción real de carga, no un `except Exception: pass` silencioso. Si carga, verifica: `separador.samplerate == 44100`, `separador.audio_channels == 2` (research.md #4); `separar_guitarra` de punta a punta no lanza ninguna excepción no controlada; y dos corridas sucesivas sobre el mismo clip producen estimaciones cuyas muestras coinciden dentro de tolerancia numérica (FR-015, research.md #6 — el caso NO trivial de determinismo, con el modelo real). Depende de T015 (`DemucsSeparador`) y T017 (para que un salto de este test sea visible).

**Checkpoint**: Correr `uv run pytest -m modelo_real -v` con red disponible ejercita el sistema completo; correrlo sin red lo salta, pero el resumen de `just gauntlet`/CI lo dice explícitamente, no en silencio.

---

## Phase 7: User Story 3 - Tema sin ninguna estimación de guitarra producida (Priority: P3)

**Goal**: Distinguir, en el resultado, la ausencia total de estimación (colección vacía) de una estimación real que resulta silenciosa (se entrega igual, sin reclasificar).

**Independent Test**: Con `SeparadorFalso` configurado para cada uno de los dos casos, verificar `resultado.estimaciones` contra `spec.md` User Story 3.

**Nota de alcance**: esta fase **no tiene tareas de implementación nuevas** — `separar_guitarra` (T011, US1) ya construye estos dos caminos porque no puede evitarlos (el diccionario que devuelve `Separador.separar()` o tiene la clave `"guitar"` o no la tiene; no hay una tercera rama posible). Mismo patrón que Feature 001, User Story 2 (T014, "leer un tema sin guitarra" no necesitó una nueva tarea de implementación porque `leer_tema` de US1 ya la cubría). Ver también research.md #1: con el modelo real (`htdemucs_6s`), el camino de "ausencia total" (FR-009) no se dispara nunca en la práctica — solo es ejercitable con `SeparadorFalso`.

### Tests for User Story 3

- [ ] T019 [P] [US3] Integration test: `SeparadorFalso` configurado para devolver un diccionario sin la clave `"guitar"` → `resultado.estimaciones == []`, sin excepción, en `tests/integration/test_separador_integracion.py` (US3 AS1, FR-009).
- [ ] T020 [US3] Integration test: `SeparadorFalso` configurado para devolver `"guitar"` con energía nula (vector cero) → `resultado.estimaciones` tiene exactamente una `Estimacion`, con esas muestras exactas — no se omite ni se reclasifica en esta feature (esa clasificación es de Feature 002), en `tests/integration/test_separador_integracion.py` (US3 AS2, FR-010) (mismo archivo que T019, después de T019).

**Checkpoint**: Las tres user stories funcionan de forma independiente.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T021 [P] Correr `just gauntlet` (ruff format --check + lint-imports + mypy --strict + tests/unit+integration+property con cobertura ≥90%, excluyendo `-m modelo_real` de la corrida rápida) y corregir cualquier hallazgo.
- [ ] T022 [P] Correr `just mutation separacion.separador` (la lógica pura, no `demucs_separador` — mutar código que envuelve una librería externa pesada aporta poca señal) y resolver mutantes sobrevivientes, prestando atención particular al mensaje de `SeparacionFallidaError` (AGENTS.md, "Tests de excepciones": afirmar el mensaje completo).
- [ ] T023 Ejecutar el ejemplo end-to-end de `quickstart.md` manualmente (la sección sin modelo real) y confirmar que la salida coincide con lo esperado; luego, si hay red disponible, correr también `uv run pytest -m modelo_real -v` y confirmar que el bloque de la Fase 6 aparece si el test se salta, y que las aserciones pasan si carga.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup — bloquea las tres user stories.
- **User Story 1 (Phase 3)**: depende de Foundational.
- **User Story 2 (Phase 4)**: depende de Foundational. Independiente de US1 en el código (archivos distintos), aunque ambas viven en la misma capa nueva.
- **Medición de presupuesto (Phase 5)**: depende de que `DemucsSeparador` exista (T015, US2) — no de US1 en sí, aunque en la práctica usa `separar_guitarra` (T011) como punto de entrada.
- **Visibilidad + test real (Phase 6)**: depende de T015 (US2) y, para T018 en particular, también de T011 (US1) — el test real ejercita `separar_guitarra` completo.
- **User Story 3 (Phase 7)**: depende de T011 (US1) — sin tareas de implementación propias (ver nota de alcance arriba).
- **Polish (Phase 8)**: depende de que las tres user stories y las Fases 5-6 estén completas.

### Dentro de cada Story

- Tests antes que implementación; confirmarlos en rojo antes de tocar `separador.py`/`demucs_separador.py`.
- T004 (Foundational) y T011 (US1) tocan el mismo archivo (`separador.py`) — orden secuencial, no paralelo.
- T012 (test) y T015 (implementación) apuntan al mismo archivo nuevo (`demucs_separador.py`) — T012 primero (rojo: `ImportError` porque el módulo no existe), T015 después.
- T006-T009 (mismo archivo `tests/unit/test_separador.py`) son secuenciales entre sí; T010 vive en un archivo distinto y puede escribirse en paralelo.
- T019-T020 comparten archivo — secuenciales entre sí.

### Parallel Opportunities

- T002 y T003 (Setup) — archivos distintos, sin dependencia.
- T004 y T005 (Foundational) — archivos distintos.
- T006 (primer test de `test_separador.py`) y T010 (property test, archivo distinto) — en paralelo.
- T012 y T013 (US2, archivos de test distintos) — en paralelo.
- T014 (crear `ATRIBUCIONES.md`) y T012/T013 (tests) — en paralelo, archivos distintos, aunque T013 es quien verifica el contenido de T014 después.
- T017 (conftest) puede escribirse en paralelo con cualquier tarea de US1/US2 — no depende de `separador.py` ni de `demucs_separador.py`.
- T019 (primer test de US3, archivo nuevo) — en paralelo con Polish si US3 no tiene dependencia de Fase 5/6 más allá de T011.

---

## Parallel Example: User Story 1

```bash
# Estas dos tareas escriben en archivos distintos y no dependen entre sí:
Task: "Unit test: sin transformación de frecuencia en tests/unit/test_separador.py"
Task: "Property test: transformaciones e invariantes en tests/property/test_separador_property.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 solamente)

1. Fase 1: Setup.
2. Fase 2: Foundational (bloqueante).
3. Fase 3: User Story 1.
4. **Parar y validar**: `separar_guitarra` verifica y declara formato, produce o no una estimación según lo que el `Separador` inyectado devuelva, y nunca silencia un fallo real — todo esto validable con `SeparadorFalso`, sin cargar el modelo real ni tocar la red.

### Incremental Delivery

1. Setup + Foundational → protocolo y tipos listos.
2. User Story 1 → validar independientemente con `SeparadorFalso` → MVP de la lógica de orquestación.
3. User Story 2 → declaración del modelo y licencias, `DemucsSeparador` real construido (aunque su primera instanciación necesite red).
4. Medición de presupuesto (Fase 5) → hallazgo escrito que condiciona el alcance de una corrida completa, antes de seguir construyendo sobre un supuesto no verificado.
5. Visibilidad + test real (Fase 6) → el sistema completo queda ejercitado de punta a punta al menos una vez, y su ausencia (sin red) queda imposible de pasar por alto.
6. User Story 3 → tests que confirman la distinción ausencia-total vs. estimación-silenciosa, sin código nuevo.
7. Polish → gauntlet completo, mutation testing sobre la lógica pura, validación manual de `quickstart.md`.

---

## Notes

- Ningún test de las Fases 1-4 y 7 usa `torch`/`demucs` real ni red — todos construyen `SeparadorFalso` (`tests/fixtures/separador_fixture.py`), siguiendo el mismo principio que Feature 002 aplicó a audio sintético (constitución Principio IV, extendido aquí a "no depender de un modelo real para probar la lógica propia").
- **Por qué la medición de presupuesto (Fase 5) no es una `[US#]`**: no corresponde a ningún user story de `spec.md` — es un hallazgo operativo pedido explícitamente por el usuario para esta sesión de tasks, que condiciona decisiones de alcance de features posteriores (si Feature 002/004 corren sobre el conjunto completo o una submuestra declarada). Mismo criterio que Setup/Foundational/Polish: infraestructura y hallazgos transversales no llevan etiqueta de historia.
- **Por qué Fase 6 (visibilidad) tampoco lleva `[US#]`**: `modelo_real` ejercita transformaciones (US1), declaración del modelo (US2) y, potencialmente, ambos motivos de US3 según lo que el clip sintético produzca — es una validación cruzada de la feature completa, no de una sola historia.
- **US3 sin tarea de implementación (Fase 7)**: ver la nota de alcance dentro de esa fase — mismo patrón que Feature 001/US2 y Feature 002/E1 (`/speckit-analyze`): cuando el comportamiento ya lo produce una implementación anterior por construcción, agregar una tarea de implementación vacía sería ceremonia, no trabajo real.
- **FR-008 (no fabricar estimaciones para las referencias que falten) no tiene tarea dedicada**: `separar_guitarra()` nunca recibe `referencias` como parámetro (contracts/separacion.md) — no hay ningún dato con el que la función podría siquiera intentar fabricar una estimación adicional. Es una garantía estructural de la firma, verificable por inspección (mypy --strict, T021), no un comportamiento que un test deba ejercitar — mismo criterio que Feature 002 aplicó a SC-007/FR-012/FR-013 (hallazgo E1 de `/speckit-analyze`, cerrado sin tarea).
- La cita de licencia de los pesos (T013/T014) se declara con su fuente y con la advertencia explícita de que no se verificó de forma independiente (research.md #3) — no se presenta como un hecho confirmado por este proyecto cuando no lo es.
- El resultado de T016 (medición real) puede cambiar decisiones que todavía no se han tomado (alcance de una corrida completa del hito 1); no se anticipa aquí cuál será el resultado ni se prellena una submuestra "por si acaso" — la tarea decide sobre el dato medido, no antes.
