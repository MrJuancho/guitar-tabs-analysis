---

description: "Task list template for feature implementation"
---

# Tasks: Métrica de separación de guitarra

**Input**: Design documents from `/specs/002-metrica-separacion-guitarra/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/metrica_separacion.md](./contracts/metrica_separacion.md), [quickstart.md](./quickstart.md)

**Tests**: Incluidas explícitamente — el guantelete del proyecto (`just gauntlet`, ver `AGENTS.md`) exige cobertura ≥90% sobre `tests/unit`+`tests/integration`+`tests/property`, y la constitución (Principio X) pide test rojo antes que fix.

**Organization**: Tareas agrupadas por user story (P1/P2 de `spec.md`) para poder implementar y validar cada una de forma independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede correr en paralelo con las demás tareas marcadas [P] de la misma fase (archivo distinto, sin dependencia pendiente)
- **[Story]**: A qué user story pertenece (US1/US2)

## Path Conventions

Proyecto único (`src/`, `tests/` en la raíz), tal como fija `plan.md#Project Structure`:
- `src/guitar_tabs_analysis/analytics/metrica_separacion.py` — módulo nuevo de esta feature (capa `analytics`, importa de `ingestion.slakh2100`, nunca al revés)
- `tests/fixtures/metrica_separacion_fixture.py` — helper de fixtures sintéticas
- `tests/unit/test_metrica_separacion.py`, `tests/integration/test_metrica_separacion_integracion.py`, `tests/property/test_metrica_separacion_property.py`

**Nota**: `src/guitar_tabs_analysis/analytics/resumen.py` (el ejemplo del template) **NO se elimina** en esta feature — `tests/holdout/conftest.py` todavía lo importa (`contar_valores_unicos`), y ese directorio es zona de retención no editable (`AGENTS.md`). El plan había dejado esto como una decisión pendiente de `/speckit-tasks`; queda resuelta aquí: se mantiene tal cual, sin tocarlo.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar dependencias antes de escribir código de dominio.

- [X] T001 Añadir `scipy` a `[project].dependencies` en `pyproject.toml` (research.md #2); correr `uv sync`.
- [X] T002 [P] Correr `mypy --strict` sobre un import mínimo de `scipy.optimize.linear_sum_assignment`; si reporta stubs faltantes, añadir un `[[tool.mypy.overrides]]` (`ignore_missing_imports = true`) para ese módulo en `pyproject.toml`, igual que ya existe para `soundfile`. **Resuelto con `scipy-stubs` (dev dependency), no un override** — probado directamente: sin stubs, `linear_sum_assignment` resuelve a `Any` (no-any-return downstream); con `scipy-stubs`, tipado limpio. Mejor que `ignore_missing_imports` porque acá sí existen stubs reales.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Tipos, excepciones y la función `si_sdr()` que ambas user stories necesitan.

**⚠️ CRITICAL**: Ninguna user story empieza hasta que esta fase esté completa.

- [X] T003 Crear los tipos de dominio inmutables `Estimacion`, `ReferenciaEmparejada`, `ReferenciaSinPareja`, `ReporteTema`, `EntradaConjunto`, `Exclusion`, `ResultadoAgregado` (dataclasses `frozen=True`), los alias `MotivoSinPareja`/`MotivoExclusion`, y las excepciones `EstimacionIncompatibleError`, `ReferenciaEnergiaNulaError`, en `src/guitar_tabs_analysis/analytics/metrica_separacion.py`, según los campos de `data-model.md` y los mensajes de `contracts/metrica_separacion.md`. Reutiliza `PistaAudio`/`PistaGuitarra` de `guitar_tabs_analysis.ingestion.slakh2100` (import permitido: `analytics` → `ingestion`). Sin lógica de cálculo todavía.
- [X] T004 [P] Crear `tests/fixtures/metrica_separacion_fixture.py`: funciones que construyen `PistaGuitarra`/`Estimacion` sintéticas a partir de arrays `numpy` (senoidales con frecuencia/fase/ganancia parametrizables, ruido gaussiano, y una variante de energía nula/silencio total) — nunca audio real del dataset (constitución Principio IV).
- [X] T005 Implementar `si_sdr(referencia: PistaGuitarra, estimacion: Estimacion) -> float` en `src/guitar_tabs_analysis/analytics/metrica_separacion.py` — toma `PistaGuitarra`/`Estimacion`, no `PistaAudio` desnudo, porque las excepciones necesitan `identificador_origen`/`identificador` (hallazgo 2026-09-04, corregido antes de implementar): valida compatibilidad de forma y frecuencia de muestreo (research.md #7 → `EstimacionIncompatibleError`), valida energía nula de la referencia (research.md #4 → `ReferenciaEnergiaNulaError`), valida energía nula de la estimación y devuelve `-inf` por convención sin calcular la fórmula (research.md #5), castea a `float64` (research.md #3), calcula `α = ⟨ŝ,s⟩/⟨s,s⟩`, `s_target`, `e_noise` y el cociente en dB dentro de `numpy.errstate(divide="ignore", invalid="ignore")` para el caso `+inf` (research.md #5) (depende de T003; mismo archivo, después de T003).

**Checkpoint**: Tipos, excepciones y `si_sdr()` listos — las user stories pueden empezar.

---

## Phase 3: User Story 1 - Medir un tema individual (Priority: P1) 🎯 MVP

**Goal**: Dada la colección de referencias y estimaciones de un tema, calcular el SI-SDR de cada referencia contra la estimación que mejor la aproxima (asignación óptima, sin compartir estimaciones), y reportar el resultado completo — incluidas las referencias sin pareja, nunca omitidas.

**Independent Test**: Con fixtures sintéticas (vía T004), invocar `emparejar_tema` sobre distintas combinaciones de referencias/estimaciones y verificar el `ReporteTema` devuelto contra cada Acceptance Scenario de `spec.md` User Story 1.

### Tests for User Story 1 ⚠️

> Escribir estos tests primero, confirmarlos en rojo contra `si_sdr`/`emparejar_tema` aún no implementados (o parcialmente).

- [X] T006 [P] [US1] Unit test: para una estimación no trivial (no proporcional a la referencia, para no caer en el caso exacto +∞/-∞ de T007/T014), `si_sdr(referencia, c1 · estimación)` y `si_sdr(referencia, c2 · estimación)` dan el mismo valor **dentro de tolerancia numérica** (no igualdad exacta — research.md #6, son valores calculados, no exactos por construcción) para dos ganancias `c1 ≠ c2` conocidas — confirma la invarianza a escala sin depender de la implementación interna, en `tests/unit/test_metrica_separacion.py` (research.md #1/#3).
- [X] T007 [US1] Unit test: `si_sdr(referencia, estimación = vector cero)` da `float("-inf")` **por convención, no por cálculo** — la fórmula da `0/0` en este caso, corregido en research.md #5 (hallazgo 2026-09-04: la afirmación original era incorrecta), en `tests/unit/test_metrica_separacion.py` (mismo archivo que T006, después de T006).
- [X] T008 [US1] Unit test: `si_sdr(referencia con energía nula, cualquier estimación)` levanta `ReferenciaEnergiaNulaError`, sin `RuntimeWarning` sin capturar, en `tests/unit/test_metrica_separacion.py` (research.md #4; contracts/metrica_separacion.md, "Modos de fallo" de `si_sdr`) (mismo archivo, después de T007).
- [X] T009 [US1] Unit test: `si_sdr(referencia, estimación)` con distinta longitud, y por separado con distinta frecuencia de muestreo, levanta `EstimacionIncompatibleError` en ambos casos, en `tests/unit/test_metrica_separacion.py` (research.md #7) (mismo archivo, después de T008).
- [X] T010 [P] [US1] Integration test: una referencia, una estimación que la aproxima → `ReporteTema` con una `ReferenciaEmparejada`, `sin_pareja == []`, `num_referencias == 1`, `num_estimaciones_recibidas == 1`, en `tests/integration/test_metrica_separacion_integracion.py` (spec.md AS US1.1).
- [X] T011 [US1] Integration test: varias referencias con igual o más estimaciones → cada referencia emparejada con una estimación distinta, ningún `identificador_estimacion` repetido, en `tests/integration/test_metrica_separacion_integracion.py` (AS US1.2, FR-002) (mismo archivo que T010, después de T010).
- [X] T012 [US1] Integration test: más referencias que estimaciones recibidas → las referencias sobrantes en `sin_pareja` con `motivo == "sin_estimacion_disponible"`, sin excepción, en `tests/integration/test_metrica_separacion_integracion.py` (AS US1.3, FR-003) (mismo archivo, después de T011).
- [X] T013 [US1] Integration test: cero estimaciones recibidas → todas las referencias en `sin_pareja`, `num_estimaciones_recibidas == 0`, en `tests/integration/test_metrica_separacion_integracion.py` (AS US1.4) (mismo archivo, después de T012).
- [X] T014 [US1] Integration test — verificación de respuesta conocida completa: pasar cada referencia de un tema con varias guitarras como su propia estimación (a través de `emparejar_tema`, no llamando `si_sdr` directamente) → todas terminan en `emparejadas` con `si_sdr == float("inf")` exacto, en `tests/integration/test_metrica_separacion_integracion.py` (AS US1.5, FR-011, SC-001) (mismo archivo, después de T013).
- [X] T015 [US1] Integration tests (dos funciones, mismo tema del reporte — distinguir motivos, no colapsarlos): (a) tema con una referencia de energía nula entre otras con energía → esa referencia en `sin_pareja` con `motivo == "energia_nula"`, el resto del tema se calcula con normalidad, sin excepción no controlada (AS US1.6, FR-006, SC-006); (b) tema donde la asignación óptima le daría a una referencia una estimación de energía nula (estimación silenciosa, no ausente) → esa referencia en `sin_pareja` con `motivo == "estimacion_silenciosa"`, **no** en `emparejadas` (AS US1.7, FR-016, SC-009) — en `tests/integration/test_metrica_separacion_integracion.py` (mismo archivo que T014, después de T014).
- [X] T016 [P] [US1] Property test (Hypothesis): para cualquier tema generado con N referencias y M estimaciones aleatorias (senoidales con parámetros muestreados, incluyendo N=0 o M=0, y ocasionalmente una estimación silenciosa entre las generadas), `len(emparejadas) + len(sin_pareja) == N`, ningún `identificador_estimacion` se repite entre dos `ReferenciaEmparejada`, y ninguna `ReferenciaEmparejada` tiene una estimación asociada de energía nula (SC-009 — si la tuviera, debería estar en `sin_pareja`, no aquí), en `tests/property/test_metrica_separacion_property.py` (data-model.md invariantes de `ReporteTema`, SC-003).

### Implementation for User Story 1

- [X] T017 [US1] Implementar `emparejar_tema(tema_id: str, referencias: list[PistaGuitarra], estimaciones: list[Estimacion]) -> ReporteTema` en `src/guitar_tabs_analysis/analytics/metrica_separacion.py`: separa primero las referencias de energía nula (van directo a `sin_pareja` con `motivo == "energia_nula"`, sin llamar `si_sdr`, research.md #4); construye la matriz de costos `-si_sdr(...)` para el resto contra **todas** las estimaciones (las silenciosas incluidas como candidatas normales, research.md #11), sustituyendo `±inf` por un sentinel finito grande solo para la matriz (research.md #5); resuelve `scipy.optimize.linear_sum_assignment` (research.md #2); para cada par asignado, si la estimación tiene energía nula, la referencia va a `sin_pareja` con `motivo == "estimacion_silenciosa"` (FR-016, research.md #11) — si no, a `emparejadas` con el valor de `si_sdr` exacto original (nunca el sentinel); las referencias que quedaron sin asignación por escasez de estimaciones van a `sin_pareja` con `motivo == "sin_estimacion_disponible"` (depende de T003, T005; mismo archivo, después de T005).

**Checkpoint**: User Story 1 funciona y se puede validar de forma independiente -- ✅ hecho (T006-T017 en verde, `just gauntlet` completo, 100% cobertura en `metrica_separacion.py`).

---

## Phase 4: User Story 2 - Agregar la métrica sobre un conjunto de temas (Priority: P2)

**Goal**: Sobre un conjunto de `EntradaConjunto`, excluir los temas sin referencias o del directorio `omitted` (con conteo y motivo), calcular la mediana de todos los valores por referencia del resto (tratando cada referencia sin pareja como `-∞`), y reportar la distribución de referencias por tema.

**Independent Test**: Con un conjunto pequeño de `EntradaConjunto` construido a mano (algunas con referencias y estimaciones, alguna sin referencias, alguna con `es_directorio_omitido=True`), invocar `agregar_conjunto` y verificar `ResultadoAgregado` contra cada Acceptance Scenario de `spec.md` User Story 2.

### Tests for User Story 2 ⚠️

> Escribir estos tests primero, confirmarlos en rojo contra `agregar_conjunto` aún no implementado.

- [X] T018 [US2] Integration test: conjunto con un tema sin ninguna pista de referencia → excluido con `motivo == "sin_guitarra_referencia"`, ausente de `reportes_por_tema`, en `tests/integration/test_metrica_separacion_integracion.py` (AS US2.2, FR-009) (mismo archivo que T010-T015, después de T015).
- [X] T019 [US2] Integration test: conjunto con un tema `es_directorio_omitido=True` (con o sin referencias) → excluido con `motivo == "directorio_omitido"`, en `tests/integration/test_metrica_separacion_integracion.py` (AS US2.3, FR-010, research.md #10 para el caso donde ambos motivos aplicarían) (mismo archivo, después de T018).
- [X] T020 [US2] Integration test: tema con referencias pero `estimaciones == []` → permanece en el conjunto evaluado (no excluido), sus referencias entran al cálculo de la mediana como `-inf`, en `tests/integration/test_metrica_separacion_integracion.py` (AS US2.4, FR-008) (mismo archivo, después de T019).
- [X] T021 [US2] Integration test: mismo conjunto con temas de 1, 2 y 3 referencias → `distribucion_referencias_por_tema == {1: n1, 2: n2, 3: n3}` exacto, y la mediana calculada coincide con la mediana esperada calculada a mano sobre el pool de referencias individuales (no una mediana de medianas por tema), en `tests/integration/test_metrica_separacion_integracion.py` (AS US2.6/7, FR-007, FR-015) (mismo archivo, después de T020).
- [X] T022 [US2] Integration test: `agregar_conjunto([])` y un conjunto donde todas las entradas quedan excluidas → `mediana is None`, `num_temas_evaluados == 0`, sin excepción, en `tests/integration/test_metrica_separacion_integracion.py` (FR-014) (mismo archivo, después de T021).
- [X] T023 [P] [US2] Property test (Hypothesis): para cualquier conjunto de `EntradaConjunto` generado, `sum(distribucion_referencias_por_tema.values()) == num_temas_evaluados`, `len(reportes_por_tema) == num_temas_evaluados`, y ningún `tema_id` aparece a la vez en `exclusiones` y en `reportes_por_tema`, en `tests/property/test_metrica_separacion_property.py` (data-model.md invariantes de `ResultadoAgregado`, SC-005) (mismo archivo que T016, después de T016).
- [X] T024 [US2] Property test (Hypothesis): para cualquier par de conjuntos que solo difieren en que uno incluye un tema adicional donde **ninguna** referencia queda emparejada (no "al menos una sin pareja" — acotado en research.md #12 tras un contraejemplo verificado: un tema mixto puede subir la mediana), `agregar_conjunto(conjunto_con_ese_tema).mediana` nunca es mayor que `agregar_conjunto(conjunto_sin_ese_tema).mediana` (comparando `None` como "sin datos", no como peor valor), en `tests/property/test_metrica_separacion_property.py` (AS US2.5, SC-004) (mismo archivo, después de T023).

### Implementation for User Story 2

- [X] T025 [US2] Implementar `agregar_conjunto(entradas: list[EntradaConjunto]) -> ResultadoAgregado` en `src/guitar_tabs_analysis/analytics/metrica_separacion.py`: particiona `entradas` en excluidas (primero `es_directorio_omitido`, luego `referencias == []`, research.md #10) y evaluadas; llama `emparejar_tema` sobre cada evaluada; agrupa en un solo pool todos los valores por referencia (`si_sdr` de cada `emparejada`, `-inf` por cada `sin_pareja`) y calcula la mediana con `statistics.median`, o `None` si el pool está vacío (FR-014); calcula `distribucion_referencias_por_tema` como `Counter(len(e.referencias) for e in evaluadas)` (depende de T003, T017; mismo archivo, después de T017).

**Checkpoint**: Ambas user stories funcionan de forma independiente -- ✅ hecho (T018-T025 en verde, `just gauntlet` completo, 89 tests, 100% cobertura en `metrica_separacion.py`). El reporte agregado completo (mediana, exclusiones, distribución) está cubierto.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T026 [P] Correr `just gauntlet` (ruff format --check + lint-imports + mypy --strict + tests/unit+integration+property con cobertura ≥90%) y corregir cualquier hallazgo.
- [ ] T027 [P] Correr `just mutation analytics.metrica_separacion` sobre el módulo y resolver mutantes sobrevivientes (AGENTS.md; constitución Principio X) — prestar atención particular a los mensajes de las dos excepciones nuevas (`EstimacionIncompatibleError`, `ReferenciaEnergiaNulaError`): afirmar el mensaje completo, no solo que los identificadores aparezcan (AGENTS.md, "Tests de excepciones").
- [ ] T028 Ejecutar el ejemplo end-to-end de `quickstart.md` manualmente y confirmar que la salida coincide con lo esperado (`SI-SDR (referencia == estimación): inf`, exclusión de `Track00002`, distribución `{1: 1}`).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup — bloquea ambas user stories.
- **User Story 1 (Phase 3)**: depende de Foundational.
- **User Story 2 (Phase 4)**: depende de Foundational y, en la práctica, de que `emparejar_tema` (T017) ya exista — `agregar_conjunto` lo llama internamente. Los *tests* de US2 (T018-T024) solo requieren los tipos de T003, así que técnicamente podrían escribirse en paralelo con la Fase 3, pero se listan después por orden de prioridad P1 → P2.
- **Polish (Phase 5)**: depende de que ambas user stories estén completas.

### Dentro de cada Story

- Tests antes que implementación; confirmarlos en rojo antes de tocar `metrica_separacion.py`.
- T005 (Foundational) y T017/T025 (implementación) tocan el mismo archivo — se ejecutan en el orden indicado, no en paralelo entre sí.
- T006-T009 (unit), T010-T015+T018-T022 (integration) y T016+T023-T024 (property) tocan cada uno un único archivo de test — dentro de cada archivo, secuencial; entre archivos distintos, en paralelo.

### Parallel Opportunities

- T001 y T002 (Setup) — archivos distintos.
- T003 y T004 (Foundational) — archivos distintos.
- T006, T010, T016 — primeras tareas de cada uno de los tres archivos de test de US1 (unit/integration/property respectivamente).
- T023 (property, US2) — mismo archivo que T016, pero puede escribirse en paralelo con las tareas de integración de US2 (T018-T022) al vivir en un archivo distinto.

---

## Parallel Example: User Story 1

```bash
# Estas tres tareas escriben en archivos distintos y no dependen entre sí:
Task: "Unit test: invarianza a escala de si_sdr en tests/unit/test_metrica_separacion.py"
Task: "Integration test: una referencia, una estimación en tests/integration/test_metrica_separacion_integracion.py"
Task: "Property test: ninguna estimación compartida en tests/property/test_metrica_separacion_property.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 solamente)

1. Fase 1: Setup.
2. Fase 2: Foundational (bloqueante).
3. Fase 3: User Story 1.
4. **Parar y validar**: `emparejar_tema` calcula y reporta correctamente sobre un tema individual, incluida la verificación de respuesta conocida (+∞) — suficiente para validar la implementación de SI-SDR sin necesidad de un separador real ni de una agregación sobre un conjunto.

### Incremental Delivery

1. Setup + Foundational → base lista (`si_sdr` verificado de forma aislada).
2. User Story 1 → validar independientemente → MVP (medición por tema completa).
3. User Story 2 → validar independientemente (reutiliza `emparejar_tema` de US1, agrega la agregación, las exclusiones y la distribución).
4. Polish → gauntlet completo, mutation testing, validación manual de `quickstart.md`.

---

## Notes

- Ningún test usa audio real del dataset — todos construyen arrays sintéticos vía `tests/fixtures/metrica_separacion_fixture.py` (constitución Principio IV); esta feature no lee nada de disco, así que no hay una fixture `TrackXXXXX/` como en 001, solo arrays `numpy` en memoria.
- `[P]` se aplica solo entre tareas de archivos distintos sin dependencia pendiente; varias tareas de esta lista comparten archivo a propósito y se listan en orden de ejecución en lugar de marcarse `[P]`.
- Cada tarea de test cita el Acceptance Scenario o FR de `spec.md` que verifica, para que quede trazable sin tener que releer el spec completo.
- La verificación de respuesta conocida (T014) es, a propósito, un test de `emparejar_tema` y no solo de `si_sdr` — el criterio de aceptación (FR-011) pide verificar "la implementación completa sin necesidad de un separador", no solo la fórmula aislada.
- **Hallazgo 2026-09-04 (durante T005)**: research.md #5 afirmaba, sin verificarlo, que una estimación de energía nula daba `SI-SDR = -∞` *por cálculo*. Es falso — da `0/0` (NaN), porque `s_target` se anula junto con el denominador, no solo el denominador (verificado numéricamente, no solo razonado). El límite tampoco existe de forma general (depende de la dirección de aproximación). Se decidió con el usuario definir `-∞` **por convención** para este caso (mismo patrón que el sentinel de FR-008), no por cálculo — research.md #5 y `contracts/metrica_separacion.md` quedaron corregidos antes de implementar T005. Ver research.md #5 para el detalle completo, incluida la alternativa descartada (excepción simétrica a `ReferenciaEnergiaNulaError`).
- **Alcance de la sesión 2026-09-04**: se pidió explícitamente T001-T005 ("Setup más Foundational: tipos, excepciones y si_sdr()"). T006-T009 (tests unitarios de `si_sdr`) se marcaron `[X]` también porque terminaron siendo, literalmente, los tests que T005 necesitaba para construirse con TDD (no alcance añadido) — la implementación de `emparejar_tema` (T017) y todo lo de `agregar_conjunto` (Fase 4) sigue sin tocar, tal como se pidió. T010-T028 quedan para una sesión futura.
- **Diseño nuevo, sesión posterior 2026-09-04 (antes de T010-T017)**: FR-016 (spec.md) formaliza un tercer motivo, `"estimacion_silenciosa"`, para cuando la asignación óptima le da a una referencia una estimación de energía nula — se reclasifica a `sin_pareja` en vez de quedar en `emparejadas` con `si_sdr == -inf` (research.md #11 explica por qué se reclasifica *después* de optimizar, no se excluye *antes*). T015 se expandió para cubrir este caso junto al de energía nula de la referencia (mismo tema de "distinguir motivos", mismo archivo) en vez de crear un nuevo ID de tarea y renumerar toda la Fase 4/5. También se hizo explícita en `si_sdr()` (research.md #5) la prioridad del caso ambos-cero (referencia y estimación con energía nula a la vez): gana `ReferenciaEnergiaNulaError`, ya no por accidente de orden de los `if`.
- **Hallazgo E1 de `/speckit-analyze` (2026-09-05), cerrado sin agregar tarea**: SC-007 ("ningún reporte incluye un umbral de aprobación ni un veredicto de pase/falla") y FR-012/FR-013 (los dos `MUST NOT` de alcance) no tienen ninguna tarea que los verifique directamente. Decisión: **no la necesitan** — son restricciones de alcance, no comportamiento a ejercitar (no hay ninguna entrada que produzca un veredicto para verificar su ausencia). La parte mecánica ya la cubre el sistema de tipos: `ReporteTema`/`ResultadoAgregado` (data-model.md) no declaran ningún campo de umbral o veredicto, y `mypy --strict` (T026) rechazaría cualquier adición no tipada — introducir uno por accidente no es un modo de fallo real de este código. Igual que FR-012 (esta feature no separa audio: no existe ninguna llamada a un modelo que probar su ausencia), verificar una ausencia estructural con un test dedicado sería un test que nunca puede fallar de forma significativa.
