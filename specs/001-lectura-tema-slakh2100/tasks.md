---

description: "Task list template for feature implementation"
---

# Tasks: Lectura de un tema de Slakh2100

**Input**: Design documents from `/specs/001-lectura-tema-slakh2100/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/leer_tema.md](./contracts/leer_tema.md), [quickstart.md](./quickstart.md)

**Tests**: Incluidas explícitamente — el guantelete del proyecto (`just gauntlet`, ver `AGENTS.md`) exige cobertura ≥90% sobre `tests/unit`+`tests/integration`+`tests/property`, y la constitución (Principio X) pide test rojo antes que fix.

**Organization**: Tareas agrupadas por user story (P1/P2/P3 de `spec.md`) para poder implementar y validar cada una de forma independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede correr en paralelo con las demás tareas marcadas [P] de la misma fase (archivo distinto, sin dependencia pendiente)
- **[Story]**: A qué user story pertenece (US1/US2/US3)

## Path Conventions

Proyecto único (`src/`, `tests/` en la raíz), tal como fija `plan.md#Project Structure`:
- `src/guitar_tabs_analysis/ingestion/slakh2100.py` — módulo nuevo de esta feature
- `tests/fixtures/slakh2100_fixture.py` — helper de fixtures sintéticas
- `tests/unit/test_slakh2100_lectura.py`, `tests/integration/test_slakh2100_lectura_integracion.py`, `tests/property/test_slakh2100_lectura_property.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar dependencias antes de escribir código de dominio.

- [X] T001 Añadir `soundfile`, `pyyaml` y `numpy` a `[project].dependencies`, y `types-PyYAML` a `dependency-groups.dev`, en `pyproject.toml`; correr `uv sync` (research.md #1, #2).
- [X] T002 [P] Añadir un `[[tool.mypy.overrides]]` para el módulo `soundfile` (`ignore_missing_imports = true`) en `pyproject.toml` — la biblioteca no trae stubs y el proyecto corre `mypy --strict`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Tipos, excepciones y helpers que TODAS las user stories necesitan.

**⚠️ CRITICAL**: Ninguna user story empieza hasta que esta fase esté completa.

- [X] T003 Crear los tipos de dominio inmutables `PistaAudio`, `PistaGuitarra`, `LecturaTema` (dataclasses `frozen=True`) y las excepciones `TemaNoExisteError`, `ArchivoAudioNoLegibleError`, `LongitudInconsistenteError` en `src/guitar_tabs_analysis/ingestion/slakh2100.py`, según los campos y mensajes de `data-model.md` y `contracts/leer_tema.md`. Sin lógica de lectura todavía.
- [X] T004 [P] Crear `tests/fixtures/slakh2100_fixture.py`: una función que construye, en un `tmp_path`, un directorio `TrackXXXXX/` sintético (`metadata.yaml` + `mix.flac` + `stems/*.flac`) con formas de onda cortas generadas (no audio real), parametrizable en instrumentos por stem (`inst_class`, `audio_rendered`, `midi_program_name`) — research.md #6.
- [X] T005 Implementar `_leer_metadata(tema_dir: Path) -> dict` en `src/guitar_tabs_analysis/ingestion/slakh2100.py`: parsea `metadata.yaml` con PyYAML (depende de T003; mismo archivo, después de T003).
- [X] T006 Implementar `_decodificar_audio(path: Path) -> PistaAudio` en `src/guitar_tabs_analysis/ingestion/slakh2100.py`: usa `soundfile` para leer con el `dtype` que coincide con el `subtype` real del archivo, sin reescalado (research.md #1) (depende de T003; mismo archivo, después de T005).

**Checkpoint**: Tipos, excepciones y helpers de E/S listos — las user stories pueden empezar.

---

## Phase 3: User Story 1 - Leer un tema con pistas de guitarra (Priority: P1) 🎯 MVP

**Goal**: Dado un tema con una o más pistas de guitarra, devolver la mezcla y esas pistas correctamente clasificadas, sin transformar el audio.

**Independent Test**: Con un tema sintético (vía T004) que tiene al menos una pista de guitarra, invocar `leer_tema` y verificar mezcla + colección de guitarras esperada, con contenido idéntico al de origen.

### Tests for User Story 1 ⚠️

> Escribir estos tests primero, confirmarlos en rojo contra el `leer_tema` aún no implementado.

- [X] T007 [P] [US1] Integration test: tema con una única pista de guitarra → mezcla + exactamente esa pista con su identificador de origen correcto, en `tests/integration/test_slakh2100_lectura_integracion.py` (spec.md Acceptance Scenario US1.1).
- [X] T008 [US1] Integration test: tema con varias guitarras (limpia/distorsionada/acústica) → todas presentes, sin fusionar, en `tests/integration/test_slakh2100_lectura_integracion.py` (Acceptance Scenario US1.2) (mismo archivo que T007, después de T007).
- [X] T009 [US1] Integration test: tema con bajo eléctrico junto a guitarras → el bajo no aparece en la colección devuelta, en `tests/integration/test_slakh2100_lectura_integracion.py` (Acceptance Scenario US1.3) (mismo archivo, después de T008).
- [X] T010 [P] [US1] Unit test: una pista con `inst_class == "Guitar"` pero `audio_rendered == false` se excluye de la colección, sin lanzar excepción, en `tests/unit/test_slakh2100_lectura.py` (spec.md Acceptance Scenario US1.6, **FR-013**).
- [X] T011 [P] [US1] Property test (Hypothesis): para cualquier tema sintético generado, la mezcla y cada guitarra devuelta comparten longitud y frecuencia de muestreo, y esa frecuencia coincide con la declarada en `metadata.yaml`, en `tests/property/test_slakh2100_lectura_property.py` (Acceptance Scenario US1.4, FR-006/FR-007).
- [X] T012 [US1] Property test (Hypothesis): las muestras devueltas (mezcla y cada guitarra) son idénticas, entero a entero, a las muestras usadas para generar el `.flac` sintético — sin resampleo/normalización (Acceptance Scenario US1.5, SC-005) — **y además** son finitas y están dentro del rango representable por su `dtype` de origen (`np.isfinite(...).all()` más un chequeo de rango; FR-008), en `tests/property/test_slakh2100_lectura_property.py` (mismo archivo que T011, después de T011).

### Implementation for User Story 1

- [X] T013 [US1] Implementar `leer_tema(tema_id: str, root_dir: Path) -> LecturaTema` en `src/guitar_tabs_analysis/ingestion/slakh2100.py`: leer metadata (T005), decodificar la mezcla (T006), filtrar stems con `inst_class == "Guitar"` y `audio_rendered == true` (excluye bajo por FR-004 y no renderizados por **FR-013**), decodificar cada uno, construir `LecturaTema` — camino feliz únicamente, sin los modos de fallo de US3 todavía (depende de T003, T005, T006).

**Checkpoint**: User Story 1 funciona y se puede validar de forma independiente (T007-T012 en verde) -- ✅ hecho.

---

## Phase 4: User Story 2 - Leer un tema sin pistas de guitarra (Priority: P2)

**Goal**: Un tema sin guitarras en sus metadatos devuelve la mezcla y una colección vacía, sin error.

**Independent Test**: Con un tema sintético sin ninguna pista `inst_class == "Guitar"`, invocar `leer_tema` y verificar que no lanza excepción y `guitarras == []`.

### Tests for User Story 2

- [X] T014 [P] [US2] Integration test: tema sin ninguna pista etiquetada como guitarra en sus metadatos → mezcla + colección vacía, sin excepción, en `tests/integration/test_slakh2100_lectura_integracion.py` (Acceptance Scenario US2.1, FR-009/SC-002).

### Implementation for User Story 2

Sin tareas de implementación adicionales: el filtro de `leer_tema` construido en T013 ya devuelve `[]` cuando ningún stem cumple la condición de guitarra — esta fase solo agrega la prueba que lo confirma de forma independiente.

**Checkpoint**: User Stories 1 y 2 funcionan de forma independiente.

---

## Phase 5: User Story 3 - Manejar identificadores inválidos y datos inconsistentes (Priority: P3)

**Goal**: Fallar explícita y precisamente ante un `tema_id` inexistente, un archivo de audio ausente/no legible, o una discrepancia de longitud — nunca devolver datos parciales o silenciosamente ajustados.

**Independent Test**: Invocar `leer_tema` con un id inexistente, con un tema cuya guitarra tiene longitud distinta a la mezcla, y con un tema cuyo archivo referenciado no está en disco; verificar en cada caso la excepción específica y su mensaje.

### Tests for User Story 3

- [X] T015 [P] [US3] Unit test: `tema_id` inexistente → `TemaNoExisteError` cuyo mensaje incluye el identificador, en `tests/unit/test_slakh2100_lectura.py` (Acceptance Scenario US3.1, FR-010).
- [X] T016 [P] [US3] Integration test: mezcla y una pista de guitarra del mismo tema con distinta longitud → `LongitudInconsistenteError` con tema + pista, sin recortar ni rellenar ninguno de los dos audios, en `tests/integration/test_slakh2100_lectura_integracion.py` (Acceptance Scenario US3.2, FR-011).
- [X] T017 [US3] Integration test: guitarra con `audio_rendered: true` en metadata pero cuyo archivo `.flac` está ausente en disco → `ArchivoAudioNoLegibleError` con tema + archivo, en `tests/integration/test_slakh2100_lectura_integracion.py` (Clarification 2026-09-01, FR-012) (mismo archivo que T016, después de T016).
- [X] T018 [US3] Integration test: `mix.flac` ausente en disco para un tema cuyo directorio sí existe → `ArchivoAudioNoLegibleError` con tema + archivo, en `tests/integration/test_slakh2100_lectura_integracion.py` (FR-012) (mismo archivo, después de T017).

### Implementation for User Story 3

- [X] T019 [US3] En `leer_tema`, verificar la existencia de `root_dir/tema_id` antes de leer nada y lanzar `TemaNoExisteError(tema_id)` si no existe, en `src/guitar_tabs_analysis/ingestion/slakh2100.py` (FR-010) (depende de T013).
- [X] T020 [US3] En `_decodificar_audio`/`leer_tema`, capturar los errores de `soundfile` o de archivo ausente al leer la mezcla o cualquier guitarra, y relanzar como `ArchivoAudioNoLegibleError(tema_id, archivo)`, en `src/guitar_tabs_analysis/ingestion/slakh2100.py` (FR-012) (depende de T013; mismo archivo, después de T019).
- [X] T021 [US3] En `leer_tema`, comparar la longitud de cada `PistaGuitarra` contra la mezcla y lanzar `LongitudInconsistenteError(tema_id, identificador_origen)` ante cualquier discrepancia, sin mutar ninguno de los dos arrays, en `src/guitar_tabs_analysis/ingestion/slakh2100.py` (FR-011) (depende de T013; mismo archivo, después de T020).

**Checkpoint**: Las tres user stories funcionan de forma independiente; los tres modos de fallo del contrato están cubiertos.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T022 [P] Correr `just gauntlet` (ruff format --check + lint-imports + mypy --strict + tests/unit+integration+property con cobertura ≥90%) y corregir cualquier hallazgo.
- [ ] T023 [P] Correr `just mutation ingestion.slakh2100` (el `module` de la
      recipe ya antepone `guitar_tabs_analysis.` -- pasarlo completo
      duplica el prefijo y falla) sobre el módulo y resolver mutantes
      sobrevivientes (AGENTS.md; constitución Principio X).

      **Triage ya hecho sobre T007-T013** (sesión 2026-09-01, 19
      sobrevivientes de esa corrida — la corrida de T023 puede dar un
      número distinto si el módulo cambió desde entonces, pero la
      categorización sigue aplicando):
      - 1 equivalente confirmado (`_leer_metadata`, `encoding="UTF-8"` vs
        `"utf-8"` -- mismo patrón que `.encode("UTF-8")` ya documentado en
        AGENTS.md). Anotar con `# pragma: no mutate`.
      - 2 eran defecto de aserción real, ya corregido fuera de este slice
        (mensajes de excepción sin afirmar completos -- ver AGENTS.md
        "Tests de excepciones: afirma el mensaje completo").
      - 16 son generalidad no ejercitada por Slakh2100 (mono, 16-bit
        siempre -- research.md): fallback `metadata.get("audio_dir",
        "stems")`/`.get("stems", {})`, fallback `"float64"` para subtype
        no mapeado, y `always_2d`. **No cerrarlos escribiendo tests para
        casos que Slakh no puede producir** -- eso es fabricar evidencia
        de mutation score (AGENTS.md, "Mutation score: 90%, nunca 100%").
        La opción real es simplificar (borrar la generalidad no
        ejercitada). Antes de decidir: **¿este lector es específico de
        Slakh2100, o es el lector de audio del proyecto en general?** El
        hito 2 usa GuitarSet/EGFxSet y la verificación cualitativa usa
        música propia -- si alguno de esos formatos no es mono/16-bit,
        simplificar ahora borra generalidad que hará falta después. Decidir
        viendo qué formatos exige el separador (hito 2), no antes.
- [ ] T024 Ejecutar la validación manual de `quickstart.md` contra una copia local real de Slakh2100 (fuera de CI) y confirmar que el resultado coincide con lo esperado.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup — bloquea todas las user stories.
- **User Stories (Phase 3-5)**: cada una depende de Foundational; en orden de prioridad P1 → P2 → P3 (US2 y US3 reutilizan el `leer_tema` que US1 construye, así que en la práctica conviene implementarlas en ese orden aunque sus *tests* sean independientes).
- **Polish (Phase 6)**: depende de que las user stories que se vayan a entregar estén completas.

### Dentro de cada Story

- Tests antes que implementación; confirmarlos en rojo antes de tocar `slakh2100.py`.
- T005/T006 (Foundational) y T013/T019/T020/T021 (implementación) tocan el mismo archivo — se ejecutan en el orden indicado, no en paralelo entre sí.

### Parallel Opportunities

- T001 y T002 (Setup) — archivos distintos.
- T003 y T004 (Foundational) — archivos distintos.
- T007, T010, T011 (US1) — tres archivos de test distintos.
- T014 (US2) — único test de la fase.
- T015 y T016 (US3) — dos archivos de test distintos.

---

## Parallel Example: User Story 1

```bash
# Estas tres tareas escriben en archivos distintos y no dependen entre sí:
Task: "Integration test: tema con una única pista de guitarra en tests/integration/test_slakh2100_lectura_integracion.py"
Task: "Unit test: audio_rendered=false excluido en tests/unit/test_slakh2100_lectura.py"
Task: "Property test: longitud/frecuencia compartida en tests/property/test_slakh2100_lectura_property.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 solamente)

1. Fase 1: Setup.
2. Fase 2: Foundational (bloqueante).
3. Fase 3: User Story 1.
4. **Parar y validar**: `leer_tema` funciona para temas con guitarra, con contenido fiel al origen — este es el mínimo indispensable para que cualquier feature posterior (métrica, separación) tenga con qué trabajar.

### Incremental Delivery

1. Setup + Foundational → base lista.
2. User Story 1 → validar independientemente → MVP.
3. User Story 2 → validar independientemente (reutiliza la implementación de US1, agrega solo su test).
4. User Story 3 → validar independientemente → los tres modos de fallo del contrato quedan cubiertos.
5. Polish → gauntlet completo, mutation testing, validación manual con dataset real.

---

## Notes

- Ningún test usa audio real de Slakh2100 — todos construyen su propio `TrackXXXXX/` sintético vía `tests/fixtures/slakh2100_fixture.py` (constitución Principio IV).
- `[P]` se aplica solo entre tareas de archivos distintos sin dependencia pendiente; varias tareas de esta lista comparten archivo a propósito y se listan en orden de ejecución en lugar de marcarse `[P]`.
- Cada tarea de test cita el Acceptance Scenario o FR de `spec.md` que verifica, para que quede trazable sin tener que releer el spec completo.
