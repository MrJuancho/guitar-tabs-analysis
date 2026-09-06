---

description: "Task list template for feature implementation"
---

# Tasks: Medición de la línea base

**Input**: Design documents from `/specs/004-medicion-linea-base/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/medicion.md](./contracts/medicion.md), [quickstart.md](./quickstart.md)

**Tests**: Incluidas explícitamente — mismo criterio que Features 002/003 (`just gauntlet` exige cobertura ≥90%, constitución Principio X pide test rojo antes que fix).

**Organization**: Tareas agrupadas por user story (P1/P2/P3 de `spec.md`), con una fase Foundational que incluye dos tareas pedidas explícitamente para esta sesión: la extracción reutilizable de la Feature 002 (T004) y su test de equivalencia (T005), ambas antes de cualquier tarea que las use.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede correr en paralelo con las demás tareas marcadas [P] de la misma fase (archivo distinto, sin dependencia pendiente)
- **[Story]**: A qué user story pertenece (US1/US2/US3) — ausente en Setup, Foundational y Polish, igual que en Features 001/002/003

## Path Conventions

Proyecto único (`src/`, `tests/` en la raíz), capa nueva `medicion` por encima de `separacion`/`analytics`/`ingestion`, excluida a propósito del contrato `layers` de import-linter (plan.md#Project Structure, research.md #6):
- `src/guitar_tabs_analysis/medicion/orquestador.py` — tipos, lógica de orquestación y persistencia, sin `torch`/`demucs`
- `src/guitar_tabs_analysis/medicion/cli.py` — único módulo que importa `separacion.demucs_separador`
- `src/guitar_tabs_analysis/analytics/metrica_separacion.py` — **tocado** por T004 (extracción, Feature 002 ya cerrada)
- `mediciones/` — artefactos finales versionados (nuevo, nivel superior)
- `tests/fixtures/dataset_sintetico_fixture.py`, `tests/unit/test_orquestador*.py`, `tests/unit/test_metrica_separacion_agregacion_equivalencia.py`, `tests/unit/test_cli.py`, `tests/integration/test_orquestador_integracion.py`, `tests/integration/test_medicion_modelo_real_integracion.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar la capa nueva antes de escribir código de dominio.

- [X] T001 Crear `src/guitar_tabs_analysis/medicion/__init__.py` (paquete vacío, capa nueva).
- [X] T002 [P] Crear el directorio `mediciones/` en la raíz del repositorio con un archivo `mediciones/.gitkeep` (artefactos finales versionados, research.md #4) — no requiere cambios en `.gitignore`: `data/silver/*` ya cubre el progreso persistido efímero (`data/silver/mediciones/`).
- [X] T003 [P] En `pyproject.toml::[tool.importlinter]`, agregar un comentario junto al contrato `type = "layers"` existente documentando que `guitar_tabs_analysis.medicion` es el orquestador de esta feature y se deja **fuera a propósito** de la lista `layers` (research.md #6, AGENTS.md "Arquitectura") — sin modificar la lista `layers` en sí. Correr `uv run lint-imports` y confirmar que el contrato sigue pasando (el paquete `medicion` de T001 todavía no importa nada).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lo que las tres user stories necesitan: la extracción reutilizable de la Feature 002 (pedida explícitamente, con su criterio de corte), los tipos de dominio, y las piezas de bajo nivel (`procesar_tema`, persistencia atómica, listado de temas, manifiesto) sobre las que `ejecutar_corrida` se construye en User Story 1.

**⚠️ CRITICAL**: Ninguna user story empieza hasta que esta fase esté completa.

- [X] T004 **(Indicación 1 del usuario — antes que cualquier tarea que la use).** En `src/guitar_tabs_analysis/analytics/metrica_separacion.py`, extraer de `agregar_conjunto` dos funciones públicas nuevas, **sin cambiar su comportamiento observable**: `calcular_mediana_agregada(reportes: list[ReporteTema]) -> float | None` (la misma aritmética de pool plano + `-inf` para sin pareja + el caso NaN de la mediana entre `+inf`/`-inf`, ya implementada inline hoy) y `calcular_distribucion_referencias(reportes: list[ReporteTema]) -> dict[int, int]`. `agregar_conjunto` pasa a **llamarlas** en vez de repetir la lógica; su firma pública y su comportamiento externo no cambian (research.md #1/#2, data-model.md de esta feature).
      **Criterio de corte explícito (indicación del usuario, no negociable)**: correr la suite completa de la Feature 002 sin modificar ni un solo test existente — `uv run pytest tests/unit tests/integration tests/property --cov=src/guitar_tabs_analysis/analytics -k "metrica_separacion or agregar_conjunto or emparejar_tema"` (o, más simple, `just gauntlet` completo) — todos deben seguir en verde tal cual están. **Si algún test de la Feature 002 necesita cambiarse para que pase, la extracción alteró el comportamiento observable: DETENERSE y reportarlo, no adaptar el test.**
- [X] T005 **(Indicación 2 del usuario, depende de T004).** Test de equivalencia entre agregación en bloque e incremental, en `tests/unit/test_metrica_separacion_agregacion_equivalencia.py` (nuevo). Sobre el mismo `list[EntradaConjunto]` (temas con `referencias`/`estimaciones` no vacías — la exclusión por `sin_guitarra_referencia`/`directorio_omitido` ya la prueba la Feature 002 por separado, no es lo que este test fija), comparar dos caminos que deben producir **el mismo resultado exacto** (no aproximado):
      (a) **bloque**: `resultado = agregar_conjunto(entradas)`, tomar `resultado.mediana` y `resultado.distribucion_referencias_por_tema`;
      (b) **incremental**: `reportes = [emparejar_tema(e.tema_id, e.referencias, e.estimaciones) for e in entradas]` acumulados uno a la vez (simulando que cada `ReporteTema` se calculó y se guardó por separado, como hace esta feature), y **solo al final** `calcular_mediana_agregada(reportes)` / `calcular_distribucion_referencias(reportes)`.
      Assert de igualdad exacta entre (a) y (b) en ambos valores. Incluir un caso concreto con referencias `+inf` (estimación idéntica a la referencia) y `-inf` (sin pareja) en el mismo conjunto, para ejercitar el caso NaN de la mediana (research.md de la Feature 002, `_mediana_orden`). Agregar además un property test (Hypothesis) que genere `list[EntradaConjunto]` arbitrarias (varios temas, varias referencias/estimaciones por tema) y verifique la misma igualdad exacta en cada caso generado — fija que "incremental" en esta feature significa **acumular todos los reportes y calcular al final**, nunca un estadístico corriente/aproximado (la mediana necesita el conjunto completo de valores, no admite una aproximación por partes).
- [X] T006 [P] Crear los tipos de dominio en `src/guitar_tabs_analysis/medicion/orquestador.py` (data-model.md): `ModoEjecucion`, `MotivoExclusionMedicion`, `ExclusionMedicion`, `ResultadoProcesamientoTema`, `ManifiestoCorrida`, `ModeloCambiadoError` (dataclasses `frozen=True` donde aplique). Reutiliza `ReporteTema`/`emparejar_tema` de `analytics.metrica_separacion` (T004), `PistaAudio`/`LecturaTema`/`leer_tema`/`TemaNoExisteError`/`ArchivoAudioNoLegibleError`/`LongitudInconsistenteError` de `ingestion.slakh2100`, `Separador`/`separar_guitarra`/`SeparacionFallidaError`/`ModeloDeclarado` de `separacion.separador`. Este módulo **no importa `torch`, `demucs` ni `separacion.demucs_separador`**.
- [X] T007 [P] Crear `tests/fixtures/dataset_sintetico_fixture.py`: una función `construir_varios_temas_sinteticos(tmp_path: Path, split: str, cantidad: int, guitarras_por_tema: int | list[int] = 1) -> Path` (`guitarras_por_tema` como `int` aplica el mismo número de `EspecificacionStem` de guitarra a los `cantidad` temas; como `list[int]` de longitud `cantidad` fija un número distinto por tema — necesario para T013, que verifica reproducibilidad de muestreo sin que la composición de guitarras importe, y para el caso de fallo duro de T016, que necesita un tema distinguible del resto) que llama a `construir_tema_sintetico` (fixture de la Feature 001, `tests/fixtures/slakh2100_fixture.py`, **sin modificarla**) repetidamente sobre el mismo `tmp_path` con `tema_id=f"{split}/Track{i:05d}"` (research.md #3, #8), permitiendo poblar `validation/`, `train/`, `test/` y `omitted/` del mismo dataset sintético en un solo `tmp_path` — necesaria para que los tests de `construir_lista_temas` (T013) y de `ejecutar_corrida` (US1/US3) puedan verificar que `test/`/`omitted/` nunca se tocan aunque existan.
- [X] T008 Implementar `procesar_tema(tema_id: str, root_dir: Path, separador: Separador) -> ResultadoProcesamientoTema` en `orquestador.py` (contracts/medicion.md): llama `leer_tema(tema_id, root_dir)`; si levanta `TemaNoExisteError`/`ArchivoAudioNoLegibleError`/`LongitudInconsistenteError`, devuelve `exclusion=ExclusionMedicion(tema_id, "fallo_procesamiento", str(causa))` y `transformaciones=[]`; si `lectura.guitarras == []`, devuelve `exclusion=ExclusionMedicion(tema_id, "sin_guitarra_referencia", "")` y `transformaciones=[]` sin llamar a `separar_guitarra`; si no, llama `resultado_separacion = separar_guitarra(tema_id, lectura.mezcla, separador)`, capturando `SeparacionFallidaError` de la misma forma que la lectura fallida (`transformaciones=[]` en ese caso también — la separación no llegó a completarse); en el camino feliz, devuelve `reporte=emparejar_tema(tema_id, lectura.guitarras, resultado_separacion.estimaciones)` **y** `transformaciones=resultado_separacion.transformaciones` (data-model.md, `ResultadoProcesamientoTema.transformaciones`; FR-010, SC-007 — el campo que G1 de `/speckit-analyze` encontró sin capturar en ningún lado). Ningún reintento en ningún camino. Depende de T006.
- [X] T009 [P] Tests unitarios de `procesar_tema` con `SeparadorFalso` (Feature 003, `tests/fixtures/separador_fixture.py`) y `construir_tema_sintetico`/`dataset_sintetico_fixture`: los 4 casos de contracts/medicion.md — lectura fallida (tema inexistente, `transformaciones == []`), sin guitarra de referencia (sin llamar a `separar()`, verificable con un `SeparadorFalso` que cuenta invocaciones, `transformaciones == []`), separación fallida (`SeparadorFalso` que levanta una excepción, `transformaciones == []`), camino feliz (`resultado.transformaciones` no vacía y coincide, entrada por entrada, con las `TransformacionDeclarada` que `separar_guitarra` produjo para esa mezcla y ese `SeparadorFalso` — verificable llamando `separar_guitarra` por separado en el propio test y comparando, sin duplicar su lógica; G1 de `/speckit-analyze`, contracts/medicion.md postcondición 4) —, en `tests/unit/test_orquestador.py` (nuevo). Depende de T007, T008.
- [X] T010 Implementar persistencia atómica por tema en `orquestador.py`: `escribir_progreso_tema(directorio: Path, resultado: ResultadoProcesamientoTema) -> None` (serializa `resultado` —incluye `ReporteTema`/`ReferenciaEmparejada`/`ReferenciaSinPareja` de la Feature 002 o `ExclusionMedicion`— a un archivo temporal en el mismo directorio y lo renombra con `os.replace()` al nombre final `<tema_id_saneado>.json`, research.md #5) y `leer_progreso_tema(directorio: Path, tema_id: str) -> ResultadoProcesamientoTema | None` (reconstruye las dataclasses, o `None` si el archivo final no existe). Depende de T006.
- [X] T011 [P] Tests unitarios de persistencia en `tests/unit/test_orquestador_persistencia.py` (nuevo): escribir y releer un `ResultadoProcesamientoTema` exitoso y uno de exclusión recupera exactamente los mismos valores; un archivo temporal presente sin que exista el archivo final (interrupción simulada a mitad de escritura) hace que `leer_progreso_tema` devuelva `None` — nunca confunde un archivo a medias con uno completo. Depende de T010.
- [X] T012 Implementar `construir_lista_temas(modo: ModoEjecucion, root_dir: Path, *, tamano_submuestra: int = 40, semilla_submuestra: int = 20260904) -> list[str]` en `orquestador.py` (contracts/medicion.md, ambos modos completos): `"submuestra_hito1"` → `[f"validation/{t}" for t in random.Random(semilla_submuestra).sample(sorted(os.listdir(root_dir / "validation")), tamano_submuestra)]`; `"conjunto_completo"` → `[f"train/{t}" for t in sorted(os.listdir(root_dir / "train"))] + [f"validation/{t}" for t in sorted(os.listdir(root_dir / "validation"))]`, **sin enumerar jamás** `root_dir / "test"` ni `root_dir / "omitted"` (FR-014, research.md #7). Depende de T006.
- [X] T013 [P] Tests unitarios de `construir_lista_temas` en `tests/unit/test_orquestador_temas.py` (nuevo), sobre un dataset sintético con temas en los cuatro splits (`dataset_sintetico_fixture`): dos invocaciones con la misma `root_dir` y semilla devuelven la misma lista de 40 (o del tamaño de prueba) identificadores (reproducibilidad); `"conjunto_completo"` incluye todos los de `train`/`validation` del dataset sintético y **ninguno** de `test`/`omitted` aunque existan; cada identificador devuelto, pasado a `leer_tema(id, root_dir)` (Feature 001, real, sin mock), lee el tema correcto (research.md #3, verificación de que el prefijo de split funciona con `leer_tema` sin cambios). Depende de T007, T012.
- [X] T014 Implementar `leer_manifiesto(directorio: Path) -> ManifiestoCorrida | None` y `escribir_manifiesto(directorio: Path, manifiesto: ManifiestoCorrida) -> None` en `orquestador.py` — lectura/escritura simple, **sin validación de firma todavía** (eso es User Story 2, T023). Depende de T006.
- [X] T015 [P] Test unitario de manifiesto en `tests/unit/test_orquestador_manifiesto.py` (nuevo): escribir y releer un `ManifiestoCorrida` recupera los mismos campos (`modo`, `semilla`, `firma_modelo`, `temas`); un directorio sin manifiesto devuelve `None`. Depende de T014.

**Checkpoint**: Extracción de Feature 002 verificada con su propio criterio de corte (T004/T005), tipos y piezas de bajo nivel listas — User Story 1 puede empezar.

---

## Phase 3: User Story 1 - Medir la submuestra del hito 1 y obtener el artefacto (Priority: P1) 🎯 MVP

**Goal**: Un comando reproducible (`ejecutar_corrida`, invocado directamente en los tests — el CLI llega en User Story 3) que procesa los 40 temas de la submuestra del hito 1 de a uno, persiste cada reporte de inmediato, y al terminar produce un `ArtefactoMedicion` con todo lo necesario para interpretar la cifra.

**Independent Test**: Con `SeparadorFalso` (Feature 003) y un dataset sintético de 40 temas en `validation/` (`dataset_sintetico_fixture`), invocar `ejecutar_corrida("submuestra_hito1", ...)` y verificar el `ArtefactoMedicion` resultante contra cada Acceptance Scenario de `spec.md` User Story 1.

### Tests for User Story 1 ⚠️

> Escribir estos tests primero, confirmarlos en rojo contra `ejecutar_corrida` aún no implementado.

- [X] T016 [P] [US1] Dos tests de integración sobre el mismo mecanismo (`ejecutar_corrida`, mismo archivo — no dos tareas, Principio X: verifican la misma unidad desde dos escenarios), en `tests/integration/test_orquestador_integracion.py` (nuevo):
      (a) dataset sintético de 40 temas en `validation/` (distinto número de guitarras por tema, incluyendo alguno sin ninguna) → `ejecutar_corrida("submuestra_hito1", root_dir, SeparadorFalso(), tmp_path)` devuelve un `ArtefactoMedicion` con `temas` igual a `construir_lista_temas("submuestra_hito1", root_dir)` (AS1/AS4), `len(exclusiones) + len(reportes) == 40`, y dos invocaciones sucesivas sobre el mismo `root_dir` (sin progreso previo cada vez, `tmp_path` distinto) devuelven la misma lista de temas;
      (b) **(G2 de `/speckit-analyze` — garantía central para una corrida de 23 horas, no cubierta por ningún test existente: T022/T024 solo verifican no-reintento en una SEGUNDA invocación, no que la corrida siga avanzando DENTRO de la misma).** Dataset sintético de 5 temas en `validation/` con un `SeparadorFalso` configurado para levantar una excepción únicamente al procesar el tema 3 (identificable por su posición en la lista que devuelve `construir_lista_temas` — o, más simple, configurar el `SeparadorFalso` para fallar por `tema_id`, no por conteo de invocaciones, así el resultado no depende del orden de iteración interno) → tras una única invocación de `ejecutar_corrida`, el tema 3 queda con `exclusion.motivo == "fallo_procesamiento"` y los temas 4 y 5 tienen su `ReporteTema` persistido (`leer_progreso_tema` para cada uno de los cinco `tema_id`, no solo inspeccionar el `ArtefactoMedicion` final, para confirmar que de verdad siguieron procesándose y no que la corrida los alcanzó por casualidad) — SC-004 ("el 0% de los fallos... detiene la corrida antes de que se intenten todos los temas restantes") fijado dentro de una sola corrida, no entre dos.
      Depende de T007, T012.
- [X] T017 [P] [US1] Integration test: sobre el `ArtefactoMedicion` de T016, `mediana` y `distribucion_referencias_por_tema` coinciden exactamente con `calcular_mediana_agregada(artefacto.reportes)` / `calcular_distribucion_referencias(artefacto.reportes)` (T004) calculados de forma independiente en el propio test (AS3), en el mismo archivo que T016. Depende de T004.

### Implementation for User Story 1

- [X] T018 [US1] Implementar `ejecutar_corrida(modo: ModoEjecucion, root_dir: Path, separador: Separador, directorio_trabajo: Path) -> ArtefactoMedicion` en `orquestador.py` (contracts/medicion.md, postcondiciones 1, 2 y 4 — la mecánica de "saltar temas ya persistidos" queda incluida aquí porque una implementación correcta del bucle no puede evitarla, ver Notes): si `leer_manifiesto(directorio_trabajo)` es `None`, crea uno con `construir_lista_temas(modo, root_dir)` y lo persiste con `escribir_manifiesto`; para cada `tema_id` de `manifiesto.temas`, si `leer_progreso_tema(directorio_trabajo, tema_id)` ya existe lo salta, si no llama `procesar_tema` y `escribir_progreso_tema` de inmediato (nunca acumula el resultado de dos temas antes de persistir); cuando todos los temas tienen progreso, arma y **devuelve** (en memoria, sin escribir a `mediciones/`, ver contracts/medicion.md) el `ArtefactoMedicion` con `reportes`/`exclusiones` separados por tipo de `ResultadoProcesamientoTema`, `transformaciones_por_tema` recolectando `progreso.transformaciones` de cada tema cuyo `reporte` no es `None` (indexado por `tema_id` — G1 de `/speckit-analyze`, data-model.md y contracts/medicion.md postcondición 5), y `mediana`/`distribucion_referencias_por_tema` vía las funciones de T004 sobre `reportes`. Depende de T004, T008, T010, T012, T014.
- [X] T019 [US1] Implementar la serialización de `ArtefactoMedicion` a un `dict` JSON-compatible (incluye `ReporteTema`/`ReferenciaEmparejada`/`ReferenciaSinPareja` de la Feature 002, `ExclusionMedicion` y `ModeloDeclarado` de la Feature 003, y `transformaciones_por_tema` — cada `TransformacionDeclarada` de la Feature 003 con sus cuatro campos, `tipo`/`direccion`/`aplicada`/`detalle` — G1 de `/speckit-analyze`) en `orquestador.py` — función pura, sin tocar disco (quien escribe el archivo final es el CLI, User Story 3). Depende de T018.
- [X] T020 [P] [US1] Test unitario de la serialización de T019: el `dict` resultante contiene, como claves de nivel superior, exactamente lo que SC-007 exige — modelo y firma, semilla, lista de temas, valores por referencia, mediana, exclusiones con motivo, distribución de referencias por tema, **y las transformaciones declaradas por tema** (G1 de `/speckit-analyze`: `transformaciones_por_tema[tema_id]` presente y no vacía para cada `tema_id` de `reportes`, ausente para cada `tema_id` de `exclusiones`) —, y `json.dumps(...)` seguido de `json.loads(...)` no pierde ningún valor (round-trip), en `tests/unit/test_orquestador.py` (mismo archivo que T009). Depende de T019.

**Checkpoint**: User Story 1 funciona y se puede validar de forma independiente con `SeparadorFalso` — comando reproducible (`ejecutar_corrida`) que mide la submuestra del hito 1 y produce el artefacto en memoria, serializable.

---

## Phase 4: User Story 2 - Reanudar una corrida interrumpida sin perder el progreso (Priority: P2)

**Goal**: Verificar la firma del modelo antes de reanudar (única pieza de lógica nueva — la mecánica de "saltar lo ya persistido" ya la construyó User Story 1, ver Notes) y confirmar con tests dedicados que interrumpir y reanudar no pierde progreso ni mezcla resultados de dos modelos distintos.

**Independent Test**: Interrumpir deliberadamente una corrida sintética (con `SeparadorFalso`) tras procesar una parte de sus temas, reinvocar `ejecutar_corrida` sobre el mismo `directorio_trabajo`, y verificar contra cada Acceptance Scenario de `spec.md` User Story 2.

**Nota de alcance**: a diferencia de las demás fases, esta **no** necesita una tarea de implementación para "saltar temas ya persistidos" — `ejecutar_corrida` (T018, US1) ya lo hace porque no puede evitarlo: su bucle siempre consulta `leer_progreso_tema` antes de procesar cada tema, sea la primera invocación (nunca encuentra nada) o una reanudación (encuentra lo que ya se persistió). Mismo patrón que Feature 003, User Story 3 ("no tiene tareas de implementación nuevas... no hay una tercera rama posible"). La única implementación genuinamente nueva de esta historia es la validación de firma (T023).

### Tests for User Story 2 ⚠️

- [X] T021 [P] [US2] Integration test: corrida sintética de varios temas con `SeparadorFalso` que cuenta invocaciones por tema; tras procesar una parte (invocando `ejecutar_corrida` y luego truncando/inspeccionando el progreso persistido, o interrumpiendo el bucle de prueba a mitad — no matar un proceso real), reinvocar `ejecutar_corrida` con el mismo `directorio_trabajo` y el mismo `SeparadorFalso` (contador reseteado) → los temas ya persistidos no vuelven a invocar `separar()`, y el `ArtefactoMedicion` final es igual, campo a campo, al de una corrida equivalente sin interrupción sobre el mismo conjunto de temas (AS1/AS3, FR-008, FR-009), en `tests/integration/test_orquestador_integracion.py` (mismo archivo que T016). Depende de T018.
- [X] T022 [P] [US2] Integration test: un tema configurado para que `SeparadorFalso` levante una excepción (queda persistido con `motivo="fallo_procesamiento"`), reinvocar `ejecutar_corrida` → ese tema sigue excluido con el mismo motivo, y `separar()` no se vuelve a invocar para él (contador en 0 en la segunda invocación) — fija la aclaración de `/speckit-clarify` ("el fallo es terminal") (AS2), en el mismo archivo. Depende de T018.

### Implementation for User Story 2

- [X] T023 [US2] Extender el manejo de manifiesto dentro de `ejecutar_corrida` (`orquestador.py`, contracts/medicion.md postcondición 3, FR-008a): cuando `leer_manifiesto(directorio_trabajo)` devuelve un manifiesto existente, comparar `manifiesto.firma_modelo` contra `separador.modelo_declarado.firma` **antes** de procesar cualquier tema; si difieren, levantar `ModeloCambiadoError(firma_esperada=manifiesto.firma_modelo, firma_actual=separador.modelo_declarado.firma)` (T006) sin tocar ningún archivo de progreso. Depende de T006, T014, T018.
- [X] T024 [P] [US2] Test unitario/integración: manifiesto persistido con `firma_modelo="firma-vieja"`, reinvocar `ejecutar_corrida` con un `SeparadorFalso` de `firma="firma-nueva"` → `ModeloCambiadoError` con ambas firmas en el mensaje (`str(error)`), y el `SeparadorFalso` no recibe ninguna invocación de `separar()` (AS5, FR-008a), en `tests/unit/test_orquestador_manifiesto.py` (mismo archivo que T015). Depende de T023.

**Checkpoint**: User Stories 1 y 2 completas — reanudación segura, sin recomputar temas ya persistidos (éxito o fallo) y sin mezclar resultados de dos modelos distintos en el mismo artefacto.

---

## Phase 5: User Story 3 - Ejecutar la medición sobre el conjunto evaluable completo (Priority: P3)

**Goal**: El segundo modo de ejecución (`conjunto_completo`) verificado de punta a punta contra `ejecutar_corrida` (la función ya lo soporta desde que `construir_lista_temas`, T012, implementó ambas ramas — ver Notes), más el CLI real que hace ambos modos invocables sin que ninguno sea un efecto lateral del otro.

**Independent Test**: Dataset sintético con temas en los cuatro splits (`dataset_sintetico_fixture`); invocar `ejecutar_corrida("conjunto_completo", ...)` y el CLI con ambos modos, verificando contra `spec.md` User Story 3.

**Nota de alcance**: `construir_lista_temas` (T012, Foundational) ya implementó la rama `"conjunto_completo"` junto con `"submuestra_hito1"` porque ambas viven en la misma función pequeña y ninguna depende de la otra (research.md, contracts/medicion.md) — esta historia no repite esa implementación, la ejercita de punta a punta a través de `ejecutar_corrida` y construye lo único que sí es nuevo: el CLI.

### Tests for User Story 3 ⚠️

- [X] T025 [P] [US3] Integration test: dataset sintético con temas en `train/`, `validation/`, `test/` y `omitted/` → `ejecutar_corrida("conjunto_completo", root_dir, SeparadorFalso(), tmp_path)` produce un `ArtefactoMedicion.temas` que incluye exactamente los de `train`/`validation` del dataset sintético y **ninguno** con prefijo `test/` u `omitted/` (AS1, FR-014), en `tests/integration/test_orquestador_integracion.py` (mismo archivo que T016). Depende de T007, T012, T018.
- [X] T026 [P] [US3] Integration test: invocar `ejecutar_corrida` en modo `"submuestra_hito1"` y luego en modo `"conjunto_completo"` sobre el mismo `root_dir`, cada uno con su propio `directorio_trabajo` (como hará el CLI) → ambas corridas terminan con su propio `ArtefactoMedicion` correcto, sin que el progreso de una interfiera con el de la otra (AS3), en el mismo archivo. Depende de T018.
- [ ] T027 [P] [US3] Test de CLI: invocar `medicion.cli.main(["--root-dir", "/cualquier/ruta"])` (sin `--modo`) → `SystemExit` con código distinto de 0 antes de construir ningún `Separador` real (FR-004, AS2) — usar `monkeypatch` para reemplazar la construcción de `DemucsSeparador` por algo que falle la prueba si llega a invocarse, confirmando que el error de `argparse` ocurre antes. Invocar con `--modo` inválido (fuera de las dos opciones) → mismo resultado. En `tests/unit/test_cli.py` (nuevo).

### Implementation for User Story 3

- [ ] T028 [US3] Implementar `medicion/cli.py`: `argparse.ArgumentParser` con `--modo` (`choices=["submuestra_hito1", "conjunto_completo"]`, `required=True`, **sin** `default=`) y `--root-dir` (`type=Path`, `required=True`); `main(argv=None)` construye `separacion.demucs_separador.DemucsSeparador()` una sola vez, deriva `directorio_trabajo = Path("data/silver/mediciones") / modo`, llama `ejecutar_corrida(modo, root_dir, separador, directorio_trabajo)` (T018), serializa el resultado (T019) y lo escribe en `Path("mediciones") / f"{modo}.json"`; si `ejecutar_corrida` levanta `ModeloCambiadoError`, la deja propagar (mensaje a `stderr`, código de salida distinto de 0). Único módulo de esta capa que importa `separacion.demucs_separador`. Depende de T018, T019, T023.

**Checkpoint**: Las tres user stories completas. `uv run python -m guitar_tabs_analysis.medicion.cli --modo <modo> --root-dir <ruta>` es un comando real, invocable para ambos modos, ninguno por defecto.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T029 [P] Crear `tests/integration/test_medicion_modelo_real_integracion.py`: único test `@pytest.mark.modelo_real` de esta feature — `procesar_tema` con `DemucsSeparador` real (Feature 003) sobre un tema sintético corto (1-2s, `construir_tema_sintetico`); si `DemucsSeparador()` falla al construirse (sin red/pesos), el test se salta con `pytest.skip(f"...: {causa}")` (mismo patrón que `tests/integration/test_demucs_separador_integracion.py` de la Feature 003 — el mecanismo de aviso visible de `tests/conftest.py`, T017 de esa feature, ya cubre este marcador sin cambios); si carga, verifica que el resultado es un `ResultadoProcesamientoTema` con `reporte` o `exclusion` (nunca ambos ni ninguno) sin excepción no controlada. Depende de T008.
- [ ] T030 [P] Correr `just gauntlet` (ruff format --check + lint-imports + mypy --strict + tests unit/integration/property con cobertura ≥90%, excluyendo `-m modelo_real`) y corregir cualquier hallazgo.
- [ ] T031 [P] Correr `just mutation medicion.orquestador` (excluye `cli.py`, capa de invocación delgada — mismo criterio que la Feature 003 excluyó `demucs_separador.py`) y resolver mutantes sobrevivientes, prestando atención particular a los mensajes de `ModeloCambiadoError` y a los `motivo`/`detalle` de `ExclusionMedicion` (AGENTS.md, "Tests de excepciones": afirmar el mensaje completo).
- [ ] T032 [P] Agregar un recipe `medir modo root_dir` al `justfile` (mismo patrón que `just gates` para `quality.gates.main()`) que invoque `uv run python -m guitar_tabs_analysis.medicion.cli --modo {{modo}} --root-dir {{root_dir}}`.
- [ ] T033 Ejecutar manualmente la sección "Lo que corre en `just gauntlet`" de `quickstart.md` de punta a punta y confirmar que coincide con el comportamiento real; si hay red/pesos cacheados, correr también `uv run pytest -m modelo_real -v` y confirmar que el nuevo test (T029) pasa o se salta visiblemente.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup — bloquea las tres user stories. Dentro de esta fase, T004 (extracción) y T005 (test de equivalencia) van **antes** que cualquier otra tarea de la fase que las use (T018 en User Story 1 es la primera que las llama de verdad, pero T004/T005 se hacen aquí, no ahí, por la indicación explícita del usuario de que la extracción sea su propia tarea con su propio criterio de corte).
- **User Story 1 (Phase 3)**: depende de Foundational completa.
- **User Story 2 (Phase 4)**: depende de Foundational y de T018 (US1) — extiende `ejecutar_corrida`, no la reescribe.
- **User Story 3 (Phase 5)**: depende de Foundational y de T018 (US1); T028 (CLI) depende además de T023 (US2, validación de firma) porque el CLI real siempre pasa por esa ruta al reanudar.
- **Polish (Phase 6)**: depende de que las tres user stories estén completas.

### Dentro de cada Story

- Tests antes que implementación; confirmarlos en rojo antes de tocar `orquestador.py`/`cli.py`.
- T004 debe estar en verde (con el criterio de corte de Feature 002 cumplido) antes de T005; T005 debe estar en verde antes de que T018 dependa de esas funciones.
- T006 (tipos) antes que T008/T010/T012/T014 (todas escriben en el mismo archivo `orquestador.py`, secuenciales entre sí, no en paralelo).
- T018 (implementación de `ejecutar_corrida`) depende de T004, T008, T010, T012, T014 — todas las piezas de Foundational deben existir primero.
- T023 (US2) y T028 (US3) modifican/usan `ejecutar_corrida` después de T018 — secuenciales respecto a esa tarea, no en paralelo con ella.

### Parallel Opportunities

- T002 y T003 (Setup) — archivos distintos.
- T006 y T007 (Foundational, tipos vs. fixture de test) — archivos distintos, sin dependencia entre sí.
- T009, T011, T013, T015 (tests unitarios de Foundational, archivos distintos) — en paralelo entre sí una vez sus respectivas implementaciones (T008/T010/T012/T014) existen.
- T016 y T017 (US1, mismo archivo pero sin dependencia de escritura simultánea real — pueden escribirse como parte del mismo cambio) y T020 (US1, archivo distinto) — T020 en paralelo con T016/T017.
- T021 y T022 (US2, mismo archivo, escenarios distintos) — pueden escribirse en paralelo si se coordina el orden de inserción; T024 (archivo distinto) en paralelo con ambas.
- T025, T026 y T027 (US3) — T027 (archivo de CLI, distinto) en paralelo con T025/T026 (mismo archivo de integración que T016).
- T029, T030, T031, T032 (Polish) — archivos y comandos independientes entre sí.

---

## Parallel Example: Foundational

```bash
# Estas dos tareas son independientes entre sí una vez completado T004:
Task: "Test de equivalencia agregación en bloque vs. incremental en tests/unit/test_metrica_separacion_agregacion_equivalencia.py"
Task: "Tipos de dominio en src/guitar_tabs_analysis/medicion/orquestador.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 solamente)

1. Fase 1: Setup.
2. Fase 2: Foundational — incluye la extracción de Feature 002 (T004) verificada con su propio criterio de corte, y el test de equivalencia (T005) antes de construir nada que dependa de ellas.
3. Fase 3: User Story 1.
4. **Parar y validar**: `ejecutar_corrida("submuestra_hito1", ...)` con `SeparadorFalso` procesa 40 temas sintéticos de a uno, persiste cada reporte de inmediato, y produce un `ArtefactoMedicion` serializable con la mediana y la distribución correctas — sin CLI todavía, sin modelo real.

### Incremental Delivery

1. Setup + Foundational → extracción de Feature 002 verificada, tipos y piezas de bajo nivel listas.
2. User Story 1 → `ejecutar_corrida` funcional para un modo, validable con `SeparadorFalso` → MVP.
3. User Story 2 → validación de firma del modelo (única pieza nueva) + tests que fijan que interrumpir y reanudar no pierde ni duplica trabajo.
4. User Story 3 → segundo modo ejercitado de punta a punta (ya soportado desde Foundational) + CLI real, ambos modos invocables sin default.
5. Polish → test `modelo_real`, `just gauntlet`, mutation testing sobre `orquestador.py`, recipe de `just`, validación manual de `quickstart.md`.

---

## Notes

- **Por qué T004/T005 van en Foundational y no en User Story 1**: son la indicación explícita del usuario para esta sesión — la extracción debe ser su propia tarea, con su propio criterio de corte, ejecutada antes de cualquier tarea que la use. `ejecutar_corrida` (T018, US1) es la primera que realmente *usa* `calcular_mediana_agregada`/`calcular_distribucion_referencias`, pero la extracción y su verificación de equivalencia son trabajo de infraestructura compartida por las tres historias, no de una historia en particular — mismo criterio que ya separa Setup/Foundational de las historias en Features 001-003.
- **Criterio de corte de T004, repetido para que no se pierda al ejecutar la tarea**: los tests existentes de la Feature 002 se corren sin modificarlos. Si alguno falla y la única forma de arreglarlo es cambiar el test, la extracción no fue un refactor puro — DETENERSE, no editar el test para que pase.
- **Por qué el test de T005 no es "aproximado"**: la indicación del usuario es explícita — la mediana necesita el conjunto completo de valores para calcularse, así que "incremental" en esta feature significa acumular cada `ReporteTema` a medida que se calcula y aplicar `calcular_mediana_agregada`/`calcular_distribucion_referencias` **una sola vez, al final**, sobre la lista completa acumulada — nunca un estadístico corriente (online) que actualice un valor aproximado tema a tema. T005 fija esto comparando ese camino contra `agregar_conjunto` en bloque sobre el mismo input exacto, con igualdad exacta (no con una tolerancia).
- **Corrección respecto a `contracts/medicion.md` original**: la primera versión de esa postcondición decía que `ejecutar_corrida` escribía directamente `mediciones/<modo>.json`. Se corrigió (antes de escribir tasks.md, ver el archivo actual) para que `ejecutar_corrida` solo **devuelva** el `ArtefactoMedicion` en memoria — escribir el archivo final es responsabilidad del CLI (T028, US3). Esto es lo que permite que T016-T026 prueben `ejecutar_corrida` enteramente contra `tmp_path`, sin tocar ninguna ruta real del repositorio.
- **Por qué User Story 2 no tiene tarea de implementación para "saltar temas ya persistidos"**: ver la Nota de alcance de la Fase 4 — mismo patrón que Feature 003, User Story 3 (un comportamiento que una implementación correcta de la historia anterior no puede evitar no necesita una tarea de implementación separada, solo los tests que lo fijan).
- **Por qué User Story 3 no repite la implementación de `construir_lista_temas`**: ver la Nota de alcance de la Fase 5 — la función se implementó completa (ambos modos) en Foundational (T012) porque las dos ramas son pequeñas, no dependen una de la otra, y las dos historias (US1 y US3) la necesitan; lo que sí es nuevo en User Story 3 es el CLI, que antes de esta historia no existía.
- Ningún test de las Fases 1-5 usa `torch`/`demucs` real ni red — todos construyen `SeparadorFalso` (Feature 003) y datasets sintéticos (`dataset_sintetico_fixture`, sobre `construir_tema_sintetico` de la Feature 001), siguiendo el mismo principio que las tres features anteriores.
- **G1 de `/speckit-analyze` (transformaciones declaradas, CRITICAL)**: `spec.md` exige seis veces (ENTREGABLE, US1 AS3, FR-010, ambas Key Entities, SC-007) que el artefacto incluya las transformaciones declaradas de la Feature 003, y ningún artefacto de diseño las capturaba — `procesar_tema` descartaba `resultado_separacion.transformaciones` al construir solo `reporte`. Cerrado agregando `transformaciones` a `ResultadoProcesamientoTema` (data-model.md) y `transformaciones_por_tema` a `ArtefactoMedicion`, poblados en T008/T018 y serializados en T019/T020 (ver también contracts/medicion.md, `procesar_tema` postcondiciones 4-5 y `ejecutar_corrida` postcondiciones 5-6, ya actualizadas).
- **G2 de `/speckit-analyze` (continuación tras un fallo, MEDIUM)**: ningún test cubría que un fallo duro a mitad de una corrida no detiene los temas posteriores DENTRO de la misma invocación (SC-004) — T022/T024 solo verifican que un tema ya excluido no se reintenta en una SEGUNDA invocación, un caso distinto. Cerrado como un segundo escenario de T016 (mismo mecanismo, `ejecutar_corrida`, Principio X: no es una tarea nueva) en vez de una tarea aparte, para no forzar una renumeración de T018 en adelante solo para insertar un test que verifica lo mismo que T016 ya ejercita (el bucle de `ejecutar_corrida` sobre una lista de temas).
- **G3 de `/speckit-analyze` (SC-005, memoria, NO se implementa como test dedicado)**: SC-005 ("en ningún momento de la corrida el sistema mantiene en memoria el audio de más de un tema a la vez") se cumple por el diseño del bucle de `ejecutar_corrida` (T018): `procesar_tema` devuelve un `ResultadoProcesamientoTema` sin ningún array de audio (ni `ReporteTema`, ni `ExclusionMedicion`, ni `TransformacionDeclarada` retienen `PistaAudio`/`Estimacion` — son metadatos y números), así que el audio del tema anterior queda sin ninguna referencia viva tan pronto termina esa iteración del `for`, antes de empezar la siguiente. Deliberadamente **sin** test dedicado: un test que intentara verificar "coexistencia de arreglos" con `weakref` dependería del recolector de basura de CPython (cuándo decide recolectar un objeto sin referencias, no si lo recolectará eventualmente) — sería frágil e intermitente, fallando o pasando según el momento exacto del GC, no según si el diseño es correcto. La garantía real es estructural (ningún tipo de esta feature retiene audio, verificable por inspección de `data-model.md` y por `mypy --strict`), no algo que un test de runtime deba re-verificar.
