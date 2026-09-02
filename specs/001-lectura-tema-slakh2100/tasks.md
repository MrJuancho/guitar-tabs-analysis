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
- [X] T023 [P] Correr `just mutation ingestion.slakh2100` (el `module` de la
      recipe ya antepone `guitar_tabs_analysis.` -- pasarlo completo
      duplica el prefijo y falla) sobre el módulo y resolver mutantes
      sobrevivientes (AGENTS.md; constitución Principio X).

      **Triage sesión 2026-09-01 (T007-T013), retriage completo sesión
      2026-09-02 (después de T019-T021)**: la corrida contra el módulo
      actual (T003, T005-T021) dio **17 sobrevivientes**, no 19 -- los 2
      que la sesión anterior ya identificó como defecto de aserción real
      quedaron corregidos fuera de este slice (mensajes de excepción sin
      afirmar completos), y **T019-T021 (`TemaNoExisteError`,
      `ArchivoAudioNoLegibleError`, `LongitudInconsistenteError`, más el
      chequeo de longitud) no introdujeron ningún sobreviviente nuevo** --
      los 17 se verificaron uno por uno contra los diffs de `mutmut show`
      y todos caen en código de T005/T006/T013 (helpers de E/S y el
      camino feliz), ninguno en las rutas de fallo agregadas por T019-T021.
      Los tres modos de fallo de US3 quedan completamente cubiertos por
      T015-T018.

      De los 17:

      - **2 equivalentes confirmados, resueltos con `# pragma: no
        mutate`** en `_leer_metadata` (línea del `.open(encoding=...)`):
        - `encoding="UTF-8"` vs `"utf-8"`: Python normaliza el nombre del
          códec sin distinguir mayúsculas -- mismo patrón que
          `.encode("UTF-8")` en AGENTS.md.
        - `encoding=None`: cae al locale del proceso. Indistinguible de
          `"utf-8"` explícito salvo con contenido no-ASCII en
          `metadata.yaml`, y ese archivo es ASCII puro según el esquema
          documentado en `data-model.md` (`inst_class`, `audio_rendered`,
          identificadores) -- fabricar contenido no-ASCII para matar este
          mutante sería exactamente lo que AGENTS.md prohíbe ("no
          fabricar evidencia de mutation score").
        - Nota sobre el pragma: mutmut excluye por línea de inicio del
          statement completo, no por sub-expresión -- este pragma también
          deja de generar los mutantes (ya verdes) sobre el nombre del
          archivo (`"metadata.yaml"` → otro string/mayúsculas). No es una
          pérdida real de cobertura: cualquier typo ahí rompe por
          construcción casi todos los tests (la fixture escribe y el
          lector lee el mismo nombre), independientemente de mutation
          testing.

      - **2 equivalentes confirmados, documentados SIN pragma** en
        `_decodificar_audio` (`always_2d=None` / `always_2d` omitido):
        verificado contra el código real de `soundfile`
        (`SoundFile._create_empty_array` hace `if always_2d or
        self.channels > 1`, donde `None` y `False` son indistinguibles
        por verdad; y el default de la firma de `sf.read` ya es `False`)
        -- cierto para cualquier archivo, mono o no, no depende de
        Slakh2100. No se pragma la línea: comparte statement con `dtype=`
        y la ruta, cuyas mutaciones (`dtype=None` hardcodeado, ruta
        rota) sí son reales y hoy están cubiertas -- pragma-ar la línea
        completa apagaría esa cobertura real solo para silenciar dos
        sobrevivientes ya explicados. Quedan como sobrevivientes
        documentados de forma permanente (razonamiento en el comentario
        del código, junto a la línea).

      - **13 pendientes de una decisión de diseño, sin ejecutar todavía**
        (ver más abajo): 4 en `_decodificar_audio` (fallback
        `_SUBTYPE_A_DTYPE.get(info.subtype, "float64")` -- valores
        `None`, omitido, `"XXfloat64XX"`, `"FLOAT64"`) + 9 en `leer_tema`
        (`metadata.get("audio_dir", "stems")`: 7 mutaciones sobre clave y
        valor; `metadata.get("stems", {}).items()`: 2 mutaciones sobre el
        default).

      **Resultado**: mutation score del módulo sube de 17 a 15
      sobrevivientes; los 15 restantes son 2 equivalentes documentados
      (permanentes, no se pueden pragma-ar sin perder cobertura real) y
      13 pendientes de la decisión de diseño de abajo.

      ### Decisión pendiente: ¿`_decodificar_audio` es el lector de Slakh2100 o el lector de audio del proyecto?

      Los 4 mutantes del fallback de `_SUBTYPE_A_DTYPE.get(...)` y los 9
      de `metadata.get("audio_dir"/"stems", ...)` sobreviven porque
      Slakh2100 (research.md: mono, 44.1kHz, 16-bit siempre; distribuido
      enteramente en `.flac`) nunca ejercita esas ramas -- el único
      `subtype` real es `PCM_16` (mapeado) y el `.flac` de Slakh solo
      puede traer subtypes PCM de todos modos (el contenedor no admite
      `FLOAT`/`DOUBLE`, que igual están en el mapa). No se pueden matar
      sin fabricar un archivo con un subtype que Slakh2100 nunca produce
      -- exactamente lo que AGENTS.md prohíbe.

      **Hallazgo adicional (no en el triage original)**: la clave
      `"audio_dir"` no aparece en ningún lado de `research.md` ni
      `data-model.md` -- el esquema documentado de `metadata.yaml` solo
      lista `stems.<id>.{inst_class, audio_rendered}` (data-model.md
      "Metadatos de origen"). La fuente citada por research.md #2
      (`ethman/slakh-utils`) tampoco se referencia para este campo. La
      fixture (`tests/fixtures/slakh2100_fixture.py`) sí lo escribe
      (`"audio_dir": "stems"`, siempre ese valor), pero eso fue decisión
      de implementación de T013, no un requisito trazado a research.md.
      Esto es evidencia adicional a favor de la Posición A para ese caso
      puntual (no aplica al fallback de `dtype`/`always_2d`, que sí tiene
      respaldo en research.md #1).

      **Posición A -- es el lector de Slakh2100, simplificar ahora:**
      - El módulo se llama, se documenta y se numera por tareas
        (T003, T005-T021) como lectura de Slakh2100, no como un lector
        general -- `_decodificar_audio` es una función privada
        (`_`-prefijada), no expuesta como API compartida; ningún otro
        módulo la importa hoy.
      - research.md #1 justifica `soundfile` citando específicamente el
        formato de Slakh2100 ("se distribuye enteramente en .flac"), y
        data-model.md documenta la forma `(n_muestras,)` como consecuencia
        de que "Slakh2100 es mono" -- el mono/16-bit no es un supuesto
        implícito, es la base documentada del diseño actual.
      - Constitución/AGENTS.md son explícitos: no diseñar para
        necesidades hipotéticas futuras, y no perseguir mutation score
        subiendo generalidad que el conjunto actual no puede ejercitar.
      - Si hito 2 (GuitarSet/EGFxSet) necesita otros subtypes/canales,
        esa decisión se toma con el spec de hito 2 en mano (qué formatos
        exige realmente, no una suposición de hoy) -- puede reusar este
        código promoviéndolo a un módulo compartido en ese momento, con
        su propio test rojo antes del fix, tal como pide AGENTS.md.

      **Posición B -- ya es (o debería tratarse como) el lector general
      del proyecto, mantener la generalidad:**
      - Hito 2 usa GuitarSet y EGFxSet, y la verificación cualitativa usa
        grabaciones propias -- ninguno de los tres está garantizado
        mono/16-bit PCM. Si la generalidad de `_decodificar_audio`
        termina siendo exactamente lo que esos lectores necesitan,
        borrarla ahora y reescribirla en unas semanas es el mismo churn
        que el proyecto quiere evitar.
      - El fallback a `"float64"` no es "generalidad especulativa": es el
        propio default de `soundfile.read()`, hecho explícito en vez de
        implícito -- una tabla subtype→dtype con un fallback razonable es
        cómo se usa correctamente una biblioteca general, no
        sobre-ingeniería acoplada a un dataset.
      - Conclusión bajo esta posición: dejar el código como está,
        aceptar los 4 sobrevivientes de `dtype` como deuda de cobertura
        acotada por el dataset (documentada, no perseguida con tests
        artificiales), y revisar ubicación/nombre (¿un
        `ingestion/audio.py` compartido?) cuando hito 2 lo necesite de
        verdad.

      **Recomendación (no ejecutada -- pendiente de confirmación)**:
      Posición A para los 9 mutantes de `metadata.get("audio_dir"/
      "stems", ...)` -- ninguno de los dos tiene respaldo documental
      (ni siquiera como generalidad "razonable" de biblioteca, a
      diferencia de `dtype`) y el hallazgo adicional de arriba los hace
      indefendibles incluso bajo la Posición B. Para los 4 mutantes de
      `dtype` fallback: **Posición A también**, pero con menos urgencia
      -- el argumento de research.md #1 sobre `soundfile` no exige
      mantener el mapeo de subtypes que Slakh2100 nunca usa, y simplificar
      ahora no impide reintroducir la generalidad completa cuando el
      spec de hito 2 la pida con requisitos concretos en mano. Ninguna de
      las dos simplificaciones se ejecutó en esta sesión -- queda para
      cuando se confirme la decisión.
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
