---

description: "Task list template for feature implementation"
---

# Tasks: Digitación con restricción de la mano

**Input**: Design documents from `/specs/007-digitacion-restriccion-mano/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/digitacion.md](./contracts/digitacion.md), [quickstart.md](./quickstart.md)

**Tests**: Incluidas explícitamente -- mismo criterio que las Features 002-006 (`just gauntlet` exige cobertura ≥90%, constitución Principio X pide test rojo antes que fix).

**Organization**: Tareas agrupadas por user story (`spec.md`: User Story 1 y User Story 2 son ambas P1, User Story 3 es P3), con una fase Foundational que solo contiene los tipos que las dos historias P1 necesitan -- ver Notes, "Por qué Foundational es chica otra vez".

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede correr en paralelo con las demás tareas marcadas [P] de la misma fase (archivo distinto, sin dependencia pendiente)
- **[Story]**: A qué user story pertenece (US1/US2/US3) -- ausente en Setup, Foundational y Polish

## Path Conventions

Proyecto único (`src/`, `tests/` en la raíz). Sin capa productora nueva (plan.md#Project Structure: no hay `digitacion.asignador` -- toda la lógica de dominio vive en `analytics.metrica_digitacion`, porque a diferencia del hito 2 no hay ningún modelo/subproceso externo que aislar):

- `src/guitar_tabs_analysis/ingestion/guitarset.py` (EXTENDIDO, no nuevo) -- `leer_grabacion()` del hito 2 no se toca, sigue usando `notes_all`
- `src/guitar_tabs_analysis/analytics/metrica_digitacion.py` (NUEVO) -- tipos de dominio, modelo de coste, generación de candidatas, asignación por instante, programación dinámica de la secuencia completa, métrica de coincidencia
- `src/guitar_tabs_analysis/digitacion/` (paquete NUEVO) -- `orquestador.py` (`ejecutar_digitacion`, reutiliza `deteccion.orquestador.construir_lista_grabaciones` tal cual) y `cli.py`, excluidos a propósito del contrato `layers`
- `tests/unit/test_metrica_digitacion.py`, `tests/unit/test_guitarset.py` (extendido), `tests/unit/test_digitacion_cli.py`, `tests/integration/test_digitacion_orquestador_integracion.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar el paquete orquestador nuevo antes de escribir código de dominio. Sin dependencia nueva de terceros (research.md #2: ninguna biblioteca evaluada implementa el modelo de coste declarado -- se implementa el algoritmo estándar de la literatura, no una dependencia nueva).

- [X] T001 [P] Crear `src/guitar_tabs_analysis/digitacion/__init__.py` (paquete vacío, mismo patrón que `deteccion/__init__.py` de la Feature 006 T001).
- [X] T002 En `pyproject.toml::[tool.importlinter]`, agregar un comentario junto al contrato `layers` documentando que `guitar_tabs_analysis.digitacion` **NO** se agrega a la lista -- mismo criterio y misma posición de comentario que `deteccion`/`medicion` (research.md #11 de la Feature 006, plan.md Constitution Check tabla, fila II): es el orquestador que ata `ingestion` y `analytics` a la vez. Depende de T001 (el paquete debe existir para que el comentario tenga contra qué referirse, aunque `lint-imports` no lo requiera). Correr `uv run lint-imports` y confirmar que el contrato sigue pasando.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Los tipos que las DOS historias P1 (User Story 1 y User Story 2) necesitan para escribirse por completo con notas construidas a mano, sin GuitarSet real.

**⚠️ CRITICAL**: Ninguna user story empieza hasta que esta fase esté completa.

- [X] T003 [P] Tipos de dominio en `src/guitar_tabs_analysis/analytics/metrica_digitacion.py` (nuevo, data-model.md), todos `frozen=True`: `Posicion` (`cuerda: str`, `traste: int`); `ModeloCoste` (`midi_cuerda_abierta: dict[str, int]`, `traste_minimo: int`, `traste_maximo: int`, `tolerancia_tono_cents: float`, `limite_estiramiento_trastes: int`, `ventana_instante_s: float`, `peso_desplazamiento: float`, `peso_cruce_cuerdas: float` -- valores por defecto exactos de research.md #3/#4/#6/#8/#9/#13, nunca constantes sin nombre dentro de otra función, FR-014); `Instante` (`notas: list[NotaEntrada]`, `inicio_representativo_s: float` -- `NotaEntrada` es un alias de tipo para `ingestion.guitarset.NotaReferencia`, reutilizada tal cual, spec.md Key Entities: "mismo dato que `NotaReferencia` del hito 2, sin cuerda ni traste todavía" -- **no se define ningún tipo `NotaEntrada` nuevo**, solo el alias para que las firmas de este módulo sean legibles); `PosicionAsignada` (`nota: NotaEntrada`, `posicion: Posicion`); `InstanteExcluido` (`inicio_representativo_s: float`, `motivo: str`). Este módulo importa `NotaReferencia` de `ingestion.guitarset`, nunca de `digitacion` (capa productora) -- mismo criterio de capas que `analytics.metrica_deteccion_notas` (research.md #11 del hito 2).

**Checkpoint**: Tipos base listos -- User Story 1 y User Story 2 pueden empezar, incluso en paralelo por personas distintas.

---

## Phase 3: User Story 1 - Asignar una posición válida a un instante de notas simultáneas (Priority: P1) 🎯 MVP

**Goal**: Dado un `Instante` ya formado (una nota sola, o un acorde), producir una asignación (cuerda, traste) por nota que reproduzca su tono dentro de tolerancia y respete el límite de estiramiento -- o excluir el instante con un motivo distinguible si ninguna combinación lo logra.

**Independent Test**: Instantes construidos a mano (spec.md US1 Independent Test) -- sin `agrupar_en_instantes` (User Story 2) ni ninguna secuencia de más de un instante.

### Tests for User Story 1 ⚠️

> Escribir estos tests primero, confirmarlos en rojo contra las funciones aún no implementadas.

- [X] T004 [P] [US1] Tests de `generar_candidatas` en `tests/unit/test_metrica_digitacion.py` (nuevo): un tono MIDI entero exacto devuelve, entre sus candidatas, al menos la posición entera esperada en la cuerda correspondiente (contracts/digitacion.md postcondición 1); un tono fraccionario dentro de `tolerancia_tono_cents` devuelve esa posición igual; el mismo tono fraccionario justo por encima de la tolerancia NO la devuelve; el rango `[traste_minimo, traste_maximo]` se respeta en ambos bordes (una candidata en `traste_maximo` es válida, ninguna en `traste_maximo + 1`); un tono fuera del rango físico del instrumento en cualquier cuerda (más grave que la sexta al aire, o más agudo que el traste más alto de la primera -- spec.md Edge Cases) devuelve una lista vacía, sin lanzar ninguna excepción (postcondición 1: "Puede devolver una lista vacía... MUST NOT fallar"). Depende de T003.
- [X] T005 [P] [US1] Tests de `asignar_instante` en el mismo archivo (spec.md US1 Acceptance Scenarios, contracts/digitacion.md postcondición 3): una nota sola -> una posición que reproduce su tono (AS1); un acorde alcanzable sin exceder el límite -> cada nota recibe una cuerda distinta, ningún traste usado excede `limite_estiramiento_trastes` (AS2); un acorde que excede el límite en TODA combinación posible (incluida la tolerancia de tono) -> `InstanteExcluido` con motivo `"excede el límite de estiramiento"`, nunca una posición en silencio (AS3, FR-013); dos notas simultáneas con el mismo tono exacto -> cuerdas distintas, ambas reproduciendo ese tono (AS4); un instante con más notas que cuerdas disponibles (7, sintético -- research.md #10: no ocurre en datos reales pero el código no debe asumirlo garantizado por el tipo) -> `InstanteExcluido` con motivo `"más notas simultáneas que cuerdas disponibles"`, **distinguible** del motivo de AS3 (data-model.md `InstanteExcluido.motivo`); una nota cuyo tono está fuera del rango físico incluso con tolerancia completa (cero candidatas, spec.md Edge Cases) -> `InstanteExcluido` con un TERCER motivo distinguible de los otros dos (por ejemplo `"nota inalcanzable dentro de tolerancia y rango"`) -- cierra el Edge Case de `spec.md` que ninguna FR nombraba explícitamente; `data-model.md` ya deja la puerta abierta ("distinguible entre, AL MENOS" los otros dos). Depende de T003.

### Implementation for User Story 1

- [X] T006 [US1] Implementar `generar_candidatas(tono_midi: float, modelo: ModeloCoste) -> list[Posicion]` en `analytics/metrica_digitacion.py` (contracts/digitacion.md postcondición 1): para cada `(cuerda, abierta)` de `modelo.midi_cuerda_abierta` (orden de inserción del dict, determinista -- Principio VIII), para cada `traste` en `[modelo.traste_minimo, modelo.traste_maximo]`, incluir `Posicion(cuerda, traste)` si `abs(tono_midi - (abierta + traste)) * 100 <= modelo.tolerancia_tono_cents` (conversión semitonos-cents). Nunca lanza excepción; lista vacía es un resultado válido. Depende de T003.
- [X] T007 [US1] Dos piezas, mismo archivo:
  **(a)** Helper privado `_generar_combinaciones_validas(instante: Instante, modelo: ModeloCoste) -> list[list[PosicionAsignada]] | InstanteExcluido` -- **decisión de arquitectura, no en el contrato público, necesaria para que User Story 2 sea correcta**: `asignar_instante` (pieza (b) de esta tarea) devuelve UNA sola asignación por contrato (contracts/digitacion.md), pero `asignar_secuencia` (User Story 2, research.md #1) necesita el CONJUNTO de asignaciones válidas de cada instante para que la programación dinámica tenga algo sobre lo cual buscar el óptimo global -- si solo existiera la asignación única de `asignar_instante`, la DP de User Story 2 degeneraría a encadenar decisiones puramente locales, sin ningún margen para que el coste de transición influya en qué combinación elegir por instante, contradiciendo la propia recurrencia de research.md #1 ("mín sobre p' candidata de instante(i-1)"). Este helper es la única fuente de verdad de validez (motivo de exclusión incluido, T005) -- **tanto `asignar_instante` como `asignar_secuencia` lo llaman**, nunca hay una segunda implementación paralela de la regla de validez. Genera las candidatas de cada nota (T006); si `len(instante.notas) > 6`, o si alguna nota tiene cero candidatas, o si ninguna combinación de posiciones con cuerdas todas distintas mantiene `max(traste) - min(traste)` sobre `traste ≥ 1` (research.md #7) dentro de `modelo.limite_estiramiento_trastes`, devuelve `InstanteExcluido` con el motivo correspondiente de entre los TRES de T005 (más notas que cuerdas / nota inalcanzable / excede estiramiento, en ese orden de precedencia -- una nota inalcanzable siempre impide cualquier combinación, así que se reporta antes que un posible exceso de estiramiento que nunca se llegaría a evaluar). En cualquier otro caso, devuelve TODAS las combinaciones válidas (búsqueda exhaustiva sobre permutaciones de cuerdas × candidatas por nota -- acotada por construcción a ≤6 notas y un puñado de candidatas por nota, research.md #1/#6/#10, nunca exponencial en el largo de la secuencia porque esto corre una vez POR INSTANTE, no sobre la secuencia completa).
  **(b)** `asignar_instante(instante: Instante, modelo: ModeloCoste) -> list[PosicionAsignada] | InstanteExcluido` (contracts/digitacion.md postcondición 3): llama a (a); si excluido, propaga la exclusión tal cual; si no, devuelve la PRIMERA combinación válida (orden determinista de (a) -- Principio VIII) -- User Story 1 no necesita la mínima en ningún sentido de coste, solo una válida (spec.md US1 no menciona minimización, eso es User Story 2). Depende de T006.

**Checkpoint**: Un instante aislado recibe una asignación correcta por construcción, o se excluye con un motivo distinguible -- verificable con instantes construidos a mano, sin ninguna secuencia ni GuitarSet real.

---

## Phase 4: User Story 2 - Asignar la digitación completa de una secuencia minimizando el coste total (Priority: P1)

**Goal**: Agrupar una secuencia completa de notas en instantes (research.md #6) y calcular, vía programación dinámica sobre las combinaciones válidas de cada instante (T007a), la digitación de coste mínimo sobre toda la secuencia.

**Independent Test**: Secuencias sintéticas cortas con óptimo calculable por fuerza bruta (spec.md US2 Independent Test) -- independiente de que User Story 3 exista.

### Tests for User Story 2 ⚠️

- [X] T008 [P] [US2] Tests de `agrupar_en_instantes` en `tests/unit/test_metrica_digitacion.py` (contracts/digitacion.md postcondición 2, research.md #6): notas cuyos `inicio_s` caen dentro de `ventana_instante_s` del PRIMER inicio del grupo (no del último agregado) se agrupan en un mismo `Instante` -- caso que distingue agrupación "sin arrastre" de "con arrastre" (una nota a `ventana_instante_s * 0.9` de la primera y otra a `ventana_instante_s * 1.8` de la primera pero solo `ventana_instante_s * 0.9` de la segunda -- con arrastre se agruparían las tres, sin arrastre la tercera abre un nuevo grupo, research.md #6 "Alternatives considered"); notas fuera de la ventana abren un nuevo `Instante`; una nota sola es un `Instante` de un elemento, no un caso especial distinto (data-model.md). Depende de T003.
- [X] T009 [P] [US2] Tests de `asignar_secuencia` en el mismo archivo (spec.md US2 Acceptance Scenarios, FR-006): sobre varias secuencias sintéticas cortas (pocas notas, acotadas para que una función de fuerza bruta ESCRITA EN EL PROPIO TEST -- nunca reutilizando la implementación de producción -- sea viable), el coste total que devuelve `asignar_secuencia` coincide EXACTAMENTE (tolerancia numérica, Principio VIII) con el óptimo de fuerza bruta (AS1, FR-006 -- test de corrección del algoritmo, nunca reportado como métrica); dos instantes consecutivos con el mismo desplazamiento en trastes pero separados por intervalos de tiempo distintos -> el intervalo más corto produce un coste de desplazamiento mayor o igual (AS2); dos notas consecutivas en cuerdas opuestas del mástil con desplazamiento en trastes igual a cero (traste 1 de la sexta, luego traste 1 de la primera) -> coste de cruce de cuerdas mayor que cero pese al desplazamiento nulo (AS3, el ejemplo literal de `spec.md`); el primer instante de una secuencia -> coste de transición cero, ningún término de desplazamiento ni cruce (AS4); una secuencia con un instante intermedio que se excluye (ninguna combinación válida) -> la secuencia sigue, el `Δt` de la transición siguiente se calcula contra el último instante NO excluido, no contra el excluido (contracts/digitacion.md postcondición 4). Depende de T003.

### Implementation for User Story 2

- [X] T010 [US2] Agregar `Digitacion` (`frozen=True`: `posiciones: list[PosicionAsignada]`, `exclusiones: list[InstanteExcluido]`, `coste_total: float`, data-model.md) a `analytics/metrica_digitacion.py`. Depende de T003.
- [X] T011 [US2] Implementar `agrupar_en_instantes(notas: list[NotaEntrada], modelo: ModeloCoste) -> list[Instante]` en `analytics/metrica_digitacion.py` (contracts/digitacion.md postcondición 2, research.md #6): ordena `notas` por `inicio_s` (no asume orden de entrada), agrupa de forma codiciosa SIN arrastre -- cada nota entra al grupo actual si `inicio_s - inicio_del_primer_elemento_del_grupo <= modelo.ventana_instante_s`, si no, cierra el grupo actual y abre uno nuevo con esa nota. NUNCA usa solape de intervalo `[inicio_s, fin_s]` (research.md #6: ese criterio es `clasificar_polifonia_en_instante` del hito 2, un concepto distinto que rompe el límite físico de 6 cuerdas sobre datos reales). Depende de T003, T008.
- [X] T012 [US2] Implementar `asignar_secuencia(notas: list[NotaEntrada], modelo: ModeloCoste) -> Digitacion` en `analytics/metrica_digitacion.py` -- la programación dinámica (contracts/digitacion.md postcondición 4, research.md #1):
  1. Agrupa en instantes (T011). Para cada instante, obtiene sus combinaciones válidas vía `_generar_combinaciones_validas` (T007a) -- si excluido, lo registra en `exclusiones` y lo salta del resto del cálculo (no participa de ningún nodo ni arista).
  2. **Decisión de arquitectura sobre desplazamiento/cruce entre instantes multi-nota, no resuelta explícitamente en `research.md`/`contracts/digitacion.md` -- necesaria para que esta tarea sea implementable, documentada aquí con la misma disciplina que research.md**: la "posición de la mano" de una combinación, para calcular desplazamiento y cruce de cuerdas contra el instante siguiente/anterior, es el CENTROIDE (promedio) de `traste` y de índice de cuerda (`"E"`=0 ... `"e"`=5, orden de `modelo.midi_cuerda_abierta`) sobre TODAS las notas de la combinación -- a diferencia del estiramiento (research.md #7, que excluye cuerdas al aire porque no exigen dedo), el desplazamiento mide dónde queda la mano en el mástil, y una cuerda al aire (`traste=0`) sí participa de esa ubicación con su valor real (una mano apoyada sobre cuerdas al aire tiende a estar cerca del clavijero, no en un lugar arbitrario) -- simplificación consciente y declarada, misma disciplina que research.md #12 (trastes en vez de mm), revisable con evidencia de User Story 3 (T025) si el sesgo resultante lo justifica.
  3. Recurrencia (research.md #1): `costeNodo(p) = peso_estiramiento(=1.0, research.md #13) × estiramiento(p)`; `costeArista(p', p, Δt) = modelo.peso_desplazamiento × |centroide_traste(p) - centroide_traste(p')| / Δt + modelo.peso_cruce_cuerdas × |centroide_cuerda(p) - centroide_cuerda(p')| / Δt` (`Δt` = diferencia entre `inicio_representativo_s` del instante actual y del último instante NO excluido -- contracts/digitacion.md postcondición 4; siempre estrictamente positivo por construcción de T011, con un `ε` de salvaguarda igual, research.md #13). `mínCoste(1, p) = costeNodo(p)` para el primer instante no excluido; `mínCoste(i, p) = costeNodo(p) + mín sobre p' de [mínCoste(i-1, p') + costeArista(p', p, Δt)]` en cualquier otro caso.
  4. Reconstruye el camino óptimo con backpointers, arma `Digitacion.posiciones` (aplanando las `PosicionAsignada` de la combinación elegida en cada instante, en el mismo orden que la entrada) y `Digitacion.exclusiones` (las registradas en el paso 1), con `coste_total` igual a `mínCoste` del último instante en el óptimo.
  Depende de T007, T010, T011.

**Checkpoint**: `asignar_secuencia` produce una digitación completa de coste mínimo verificable contra fuerza bruta sobre secuencias cortas -- MVP completo de la feature (User Story 1 + User Story 2), sin GuitarSet real todavía.

---

## Phase 5: User Story 3 - Medir la digitación producida contra la anotación real de GuitarSet (Priority: P3)

**Goal**: Leer la posición real anotada por GuitarSet (`track.notes` por cuerda, research.md #5), medir la fracción de coincidencia contra `asignar_secuencia`, agregar sobre un conjunto de grabaciones, y atar todo en un orquestador + CLI real -- sin tocar las 72 reservadas.

**Independent Test**: Notas de referencia y posiciones reales anotadas construidas a mano sobre grabaciones sintéticas (spec.md US3 Independent Test) -- depende de que User Story 1 y 2 ya funcionen (agrega su resultado, no redefine cómo se asigna una posición).

### Tests for User Story 3 ⚠️

- [X] T013 [P] [US3] Tests de `leer_grabacion_con_posicion_real` en `tests/unit/test_guitarset.py` (extendido, mismo mecanismo de `monkeypatch` sobre el índice/`Track` de `mirdata` que `leer_grabacion` ya usa -- Principio IV, nunca GuitarSet real descargado en un test): una grabación existente devuelve una lista de `NotaConPosicionReal`, una por nota anotada en CUALQUIERA de las seis cuerdas de `track.notes`, con `cuerda_real` igual a la clave del diccionario y `traste_real = round(tono_midi - MIDI_CUERDA_ABIERTA[cuerda_real])` (research.md #5, contracts/digitacion.md postcondición 1); la lista queda ordenada por `inicio_s` aunque las seis listas por cuerda no vengan ordenadas entre sí; una `grabacion_id` inexistente levanta `GrabacionNoExisteError` (el mismo tipo que `leer_grabacion`, postcondición 2). Depende de T003.
- [X] T014 [P] [US3] Tests de `evaluar_coincidencia` en `tests/unit/test_metrica_digitacion.py` (contracts/digitacion.md postcondición 5): una `Digitacion` cuyas posiciones coinciden exactamente (cuerda Y traste) con las `NotaConPosicionReal` correspondientes -> `fraccion_coincidencia == 1.0`; una que difiere en cuerda o en traste (cualquiera de los dos) -> no cuenta como coincidencia; las notas de instantes excluidos (`Digitacion.exclusiones`) NO participan del denominador; comparación por igualdad exacta, nunca tolerancia numérica (Principio VIII). Depende de T003, T010.
- [X] T015 [P] [US3] Tests de `agregar_conjunto` en el mismo archivo (contracts/digitacion.md postcondición 6, mismo patrón que `agregar_conjunto` del hito 2, research.md #16 de esa feature): varias grabaciones, alguna con `exclusion` (queda fuera); un caso construido para que la cifra combinada sea observablemente distinta de promediar las fracciones por grabación (fija que se sumaron conteos, no se promedió); `fraccion_coincidencia is None` si el total de notas medidas es cero. Depende de T003.
- [X] T016 [P] [US3] Tests de integración de `ejecutar_digitacion` en `tests/integration/test_digitacion_orquestador_integracion.py` (nuevo, mismo patrón que `test_deteccion_orquestador_integracion.py` del hito 2): una grabación cuya lectura falla (`GrabacionNoExisteError`, vía `monkeypatch` sobre el índice de `mirdata`) -> queda excluida con detalle, la corrida sigue con el resto (US3 AS1, mismo patrón FR-012 del hito 2 aplicado aquí); varias grabaciones sintéticas con posiciones reales construidas a mano -> `ArtefactoDigitacion.resultado_coincidencia` coincide con el cálculo esperado (US3 AS1); ninguna de las 72 reservadas participa cuando la lista de entrada se construye con `construir_lista_grabaciones("medibles", ...)` -- se reutiliza la función tal cual, nunca una segunda partición (US3 AS2, FR-008). Depende de T012, T013.
- [X] T017 [P] [US3] Tests de `digitacion/cli.py` en `tests/unit/test_digitacion_cli.py` (nuevo, mismo patrón que `test_deteccion_cli.py` del hito 2): invocar `main([])` (sin `--modo` ni `--root-dir`) -> `SystemExit` con código distinto de 0 antes de tocar disco; `--modo` fuera de `["medibles", "reservado"]` -> mismo tratamiento; escritura atómica del artefacto final verificada (archivo temporal + `os.replace()`, relectura de confirmación). Depende de T022 (ver abajo, el propio módulo).

**Nota de alcance (sesión T013-T020)**: T015, T016 y T017 se DEJARON SIN ESCRIBIR
en esta sesión, pese a estar numeradas dentro del rango pedido -- escribirlas
ahora las dejaría en rojo hasta que T021/T022/T023 (fuera de este rango) existan,
violando el cierre "just gauntlet verde" de cada sesión (ninguna tarea de este
proyecto queda en rojo entre sesiones, precedente de todas las features
anteriores). Se emparejan T013+T018, T014+T020 (test y su implementación en la
misma sesión); T015/T016/T017 quedan explícitamente para la sesión que también
implemente T021/T022/T023.

### Implementation for User Story 3

- [X] T018 [US3] Agregar `NotaConPosicionReal` (`frozen=True`: `tono_midi: float`, `inicio_s: float`, `fin_s: float`, `cuerda_real: str`, `traste_real: int`, data-model.md) y `leer_grabacion_con_posicion_real(grabacion_id: str, root_dir: Path) -> list[NotaConPosicionReal]` a `src/guitar_tabs_analysis/ingestion/guitarset.py` (extensión, `leer_grabacion()` no se toca -- research.md #5, contracts/digitacion.md): fusiona `track.notes` (`dict[str, NoteData]`, una entrada por cuerda) en una única lista, derivando `traste_real` con `MIDI_CUERDA_ABIERTA` (reexportar o reusar el mismo mapeo que `ModeloCoste.midi_cuerda_abierta` -- valor idéntico, research.md #3; evitar declarar dos fuentes de verdad del mismo dato -- `ingestion` no puede importar `analytics` sin invertir capas, así que el mapeo se declara como constante propia de este módulo, con un comentario que señala la coincidencia intencional de valor con `analytics.metrica_digitacion`), ordena por `inicio_s`. `grabacion_id` inexistente o índice corrupto -> `GrabacionNoExisteError` (el mismo tipo, nunca una excepción cruda de `mirdata`). Depende de T013.
- [X] T019 [US3] Agregar a `analytics/metrica_digitacion.py` (data-model.md, todos `frozen=True`): `PosicionReal` (`cuerda: str`, `traste: int`); `ResultadoCoincidencia` (`fraccion_coincidencia: float | None`, `num_notas_medidas: int`, `num_notas_coincidentes: int`); `ExclusionDigitacion` (`grabacion_id: str`, `detalle: str`); `ResultadoDigitacionGrabacion` (`grabacion_id: str`, `digitacion: Digitacion | None`, `notas_con_posicion_real: list[NotaConPosicionReal] | None`, `exclusion: ExclusionDigitacion | None`); `ArtefactoDigitacion` (`modelo_coste: ModeloCoste`, `grabaciones: list[str]`, `exclusiones_grabacion: list[ExclusionDigitacion]`, `resultados_por_grabacion: list[ResultadoDigitacionGrabacion]`, `resultado_coincidencia: ResultadoCoincidencia`). Importa `NotaConPosicionReal` de `ingestion.guitarset` (T018). Depende de T010, T018.
- [X] T020 [US3] Implementar `evaluar_coincidencia(digitacion: Digitacion, notas_con_posicion_real: list[NotaConPosicionReal]) -> ResultadoCoincidencia` en `analytics/metrica_digitacion.py` (contracts/digitacion.md postcondición 5): compara, nota por nota, cada `PosicionAsignada.posicion` de `digitacion.posiciones` contra la `PosicionReal` derivada de su `NotaConPosicionReal` correspondiente (misma nota) -- igualdad exacta de `(cuerda, traste)`. Notas de instantes excluidos no entran al denominador. **MUST leer exclusivamente `notas_con_posicion_real`, nunca derivar la fracción del `coste_total` de `digitacion`** (FR-007, sería circular). Depende de T014, T019.
- [X] T021 [US3] Implementar `agregar_conjunto(resultados: list[ResultadoDigitacionGrabacion]) -> ResultadoCoincidencia` en `analytics/metrica_digitacion.py` (contracts/digitacion.md postcondición 6): filtra `exclusion is not None`; SUMA `num_notas_medidas`/`num_notas_coincidentes` de cada grabación no excluida, deriva `fraccion_coincidencia` de esa suma -- nunca promedia fracciones por grabación, nunca poolea notas crudas entre grabaciones (la asignación ya corrió una vez por grabación, esta función solo suma conteos ya resueltos). Depende de T015, T019.
- [X] T022 [US3] Implementar `digitacion/orquestador.py` (nuevo, paquete excluido del contrato `layers`, T002): `ejecutar_digitacion(grabaciones: list[str], root_dir: Path) -> ArtefactoDigitacion` (contracts/digitacion.md): para cada `grabacion_id`, lee con `leer_grabacion_con_posicion_real` (T018); si falla con `GrabacionNoExisteError`, registra `ExclusionDigitacion` y continúa (nunca aborta la corrida completa); si tiene éxito, llama `asignar_secuencia` (T012, sobre las notas proyectadas a `NotaEntrada`, sin la posición real) y `evaluar_coincidencia` (T020) sobre el resultado más las `NotaConPosicionReal` originales. Al completar, arma el `ArtefactoDigitacion` con `agregar_conjunto` (T021) sobre las grabaciones no excluidas -- **MUST NOT comparar ninguna cifra contra ningún umbral** (FR-015). **Reutiliza `deteccion.orquestador.construir_lista_grabaciones` tal cual para cualquier necesidad de partición medibles/reservado -- MUST NOT definir una segunda función de partición** (Principio VI, contracts/digitacion.md). Salida de progreso por grabación, mismo patrón que `ejecutar_deteccion`/`ejecutar_corrida` (línea `[i/N] grabacion_id  ok  Xs  N notas` o `excluido: motivo`). Depende de T012, T018, T021.
- [X] T023 [US3] Implementar `digitacion/cli.py` (nuevo, mismo patrón exacto que `deteccion/cli.py` del hito 2): `--modo` (`choices=["medibles", "reservado"]`, `required=True`, sin `default=` -- FR-004/Principio VI, mismo criterio que `deteccion.cli`) y `--root-dir` (`type=Path`, `required=True`); `main()` obtiene la lista con `construir_lista_grabaciones(args.modo, args.root_dir)` (importada de `deteccion.orquestador`), llama `ejecutar_digitacion` (T022), serializa el `ArtefactoDigitacion` a JSON (función pura `artefacto_a_dict`, mismo patrón que `medicion`/`deteccion`) y escribe en `mediciones/digitacion_{modo}.json` con escritura atómica + relectura de verificación (mismo mecanismo que `deteccion.cli.escribir_artefacto`, `EscrituraIncompletaError`). Valida `root_dir`/índice de `mirdata` al arrancar, reutilizando `validar_raiz_guitarset`/`validar_indice_mirdata` de `ingestion.guitarset` (FR-015/FR-016 del hito 2, mismo criterio -- no se reinventa la validación). Agregar recipe `digitar modo root_dir` al `justfile` (mismo patrón que `detectar modo root_dir`). Depende de T017, T022.
- [X] T024 [US3] **Ejecución manual real, no un test** (quickstart.md, "Ejecución manual"): correr `ejecutar_digitacion` (vía `just digitar medibles <ruta-guitarset>`) sobre las 288 grabaciones medibles reales -- primera medición real del hito 3 (Principio VII: el presupuesto se fija DESPUÉS de esta medición, con evidencia -- esta tarea NO cierra el presupuesto, solo lo produce). Confirmar con evidencia de reloj real que la complejidad lineal proyectada en research.md #1/plan.md (Performance Goals) se sostiene en la práctica, antes de asumirlo cerrado (mismo criterio que toda afirmación cuantitativa de este proyecto, AGENTS.md) -- si el tiempo real diverge de forma significativa de la proyección, documentarlo en research.md como un hallazgo, no descartarlo en silencio. Registrar la cifra de `resultado_coincidencia` (con precisión/exhaustividad NO aplica aquí -- es una fracción de coincidencia única, FR-007 -- pero SÍ el desglose de exclusiones con motivo, FR-016) como la entrada real para el futuro cierre del Principio VII del hito 3 (`/speckit-constitution`, sesión posterior, fuera de alcance de esta tarea). Depende de T023.
- [X] T025 [US3] **Calibración de los pesos de movimiento -- tarea explícita con su propio criterio, no una nota (pedido explícito de esta sesión, research.md #13)**: sobre el resultado de T024, tomar las notas donde la posición asignada NO coincide con la real PERO el tono sí se reprodujo correctamente (es decir, desacuerdos de digitación, no fallos de corrección) y, para cada una, calcular por separado `Δcuerda = |índice_cuerda_asignada - índice_cuerda_real|` (0=E grave a 5=e agudo) y `Δtraste = |traste_asignado - traste_real|`. **Criterio de señal de calibración**: si la distribución de `Δcuerda` y la de `Δtraste` sobre esos desacuerdos muestran una asimetría sistemática identificable (por ejemplo, `Δcuerda` alto es mucho más común que `Δtraste` alto, o al revés) -- MUST documentarse en `research.md` como un hallazgo nuevo, con la evidencia real medida (nunca "parece razonable" sin medir, mismo criterio que el resto de `research.md` de esta feature). **MUST NOT ajustar `peso_desplazamiento`/`peso_cruce_cuerdas` a ciegas dentro de esta misma tarea** -- el hallazgo se registra como la entrada de una recalibración posterior, con su propia evidencia de que el nuevo valor mejora `fraccion_coincidencia` de verdad (Principio VII: el presupuesto/los parámetros se fijan CON evidencia, después de medir, nunca antes ni "para mejorar una cifra que todavía no existe" -- research.md #13 ya lo advierte). Si NO hay asimetría identificable, documentar igual esa ausencia de señal (evidencia negativa, también un resultado real). Depende de T024.

**Checkpoint**: Las tres user stories completas -- `ejecutar_digitacion()` mide un conjunto de grabaciones de punta a punta contra la anotación real de GuitarSet, ninguna de las 72 reservadas participa, la primera medición real queda registrada como entrada del futuro cierre del Principio VII, y la señal de calibración de pesos queda documentada con criterio explícito.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T026 [P] Correr `just gauntlet` (ruff format --check + lint-imports + mypy --strict + tests unit/integration/property con cobertura ≥90%) y corregir cualquier hallazgo. Verde: 361 tests, 99.23% cobertura (capa nueva de esta feature al 100%, salvo el guard `if __name__ == "__main__"` de `digitacion/cli.py`, mismo patrón ya aceptado en `deteccion/cli.py`).
- [X] T027 [P] Mutation testing acotado a la capa nueva de esta feature: `analytics.metrica_digitacion`, `digitacion.orquestador`, `digitacion.cli`, y la extensión de `ingestion.guitarset` (`leer_grabacion_con_posicion_real`, `NotaConPosicionReal`).

  **Verificación previa de `also_copy`** (pedido explícito de esta sesión, es la segunda vez que este hueco aparece -- Feature 006 T026 lo encontró con `scripts/`): confirmado que `also_copy = ["docs/", "scripts/"]` ya cubre todo lo que los tests de esta feature necesitan -- ninguno de los tests nuevos de la Feature 007 lee ningún archivo por ruta relativa fuera de `src/`/`tests/` (a diferencia de `test_verificar_entorno_basic_pitch.py` de la Feature 006, que invocaba `scripts/verificar_entorno_basic_pitch.sh`). Corrida limpia de mutmut confirmada sin ningún error 127 para ningún módulo.

  **Resultado por módulo** (triage, no conteo -- cada superviviente revisado con `mutmut show`, nunca solo contado):

  | Módulo | Mutantes | Killed | Sobrevivientes |
  |---|---|---|---|
  | `analytics.metrica_digitacion` | 335 | 327 | 8 (equivalentes, documentados abajo) |
  | `digitacion.orquestador` | 160 | 160 | 0 |
  | `digitacion.cli` | 116 | 116 | 0 |
  | `ingestion.guitarset` (módulo completo, extensión incluida) | 110 | 110 | 0 |

  **Hallazgos reales corregidos con tests nuevos (no solo los "esperados" por precedente -- las ramas de motivo de `InstanteExcluido` y el guard de `Δt`/`ε` que se anticipaban arriba resultaron YA cubiertas por los tests de T004-T012; los sobrevivientes reales aparecieron en otro lugar, verificado, no asumido por la predicción original):**

  - `generar_candidatas`: `traste_minimo` omitido del `range()`, el multiplicador de cents (`*100.0`→`*101.0`), y el límite de tolerancia como `<` en vez de `<=` -- los tres sobrevivían porque ningún test anterior tenía `traste_minimo≠0` ni caía justo en el borde exacto de la tolerancia o en la banda estrecha que distingue `*100` de `*101`. 3 tests nuevos, cada uno con el valor exacto en el borde.
  - `_generar_combinaciones_validas`/`_estiramiento` (código compartido, mismo defecto en los dos lugares -- research.md no documentaba esta duplicación intencional hasta ahora): `traste >= 1` mutado a `> 1`/`>= 2` (traste 1 dejaba de contar como pisada), `max - min` mutado a `max + min`, el caso base `else 0` mutado a `else 1`, `estiramiento > límite` mutado a `>=`, y `continue` mutado a `break` dentro del recorrido de combinaciones (cortaba la búsqueda en la primera combinación inválida, perdiendo combinaciones válidas posteriores). Todos sobrevivían porque los tests de T004-T007 nunca ejercitaban un traste exactamente en 1, un estiramiento exactamente en el límite, o una secuencia de candidatas donde la primera combinación fallara y una posterior no. 8 tests nuevos (algunos contra la función privada directamente, mismo criterio que probar `_emparejar` habría exigido en el hito 2 si no hubiera quedado cubierta por otra vía).
  - `agrupar_en_instantes`: la comparación `nota.inicio_s - inicio_grupo > ventana` mutada a `+` sobrevivía porque todos los tests anteriores agrupaban desde `inicio_grupo=0.0` (donde resta y suma coinciden); mutada a `>=` sobrevivía porque ningún test caía en el borde exacto de la ventana. 2 tests nuevos, uno con un grupo que no empieza en el origen, otro en el borde exacto.
  - `_centroide`: el promedio (`/len`) mutado a `*len` en ambas coordenadas (traste y cuerda) -- ningún test anterior invocaba `_centroide` directamente, solo a través de `asignar_secuencia`, donde el efecto quedaba mezclado con otros términos del coste. 2 tests nuevos, directos.
  - `asignar_secuencia` -- el hallazgo más significativo de este triage: el desempate `costo < mejor_costo` mutado a `<=` (cambia CUÁL de dos óptimos empatados se conserva -- Principio VIII, determinismo), `mejor_costo + _estiramiento(...)` mutado a `-` (ninguna de las secuencias de fuerza bruta de T009 tenía un acorde con estiramiento distinto de cero después del primer instante), y **seis mutantes distintos del rango del bucle de backtracking** (`range(0,-1)`, `range(len-1,-1)`, paso omitido, `range(len-2,0,-1)`, límite `1` en vez de `0`, paso `+1`, paso `-2`) -- todos indetectables mirando solo `coste_total`, porque ese valor se calcula ANTES de que el bucle de backtracking corra: los tests de fuerza bruta de T009 comparaban exclusivamente `coste_total` a propósito (múltiples óptimos son válidos), así que nunca habrían podido detectar un backtracking roto. 4 tests nuevos que verifican `digitacion.posiciones` completo, no solo el costo -- incluido un caso con la candidata ambigua en el instante DEL MEDIO de una secuencia de tres, necesario porque un mutante (`range(len-2,0,-1)`) sobrevivía al primer test (la candidata ambigua estaba en el primer instante, cuyo índice coincide con el valor por defecto sin importar si el bucle lo visita).
  - `evaluar_coincidencia`: `continue` mutado a `break` (una nota sin posición real al principio de la lista detenía la cuenta de las siguientes), `num_coincidentes += 1` mutado a `= 1` (el conteo no pasaba de 1 con más de una coincidencia), `/` mutado a `*` en el cálculo de la fracción. 3 tests nuevos.
  - `agregar_conjunto`: `num_medidas_total > 0` mutado a `> 1` (con exactamente una nota medida en todo el conjunto, la fracción quedaba en `None` en vez de calcularse). 1 test nuevo.
  - `ejecutar_digitacion` (orquestador): toda la salida de progreso (`total=None`, `prefijo=None`, `print(None)` en cada rama, `duracion` con `+` en vez de `-`, `continue` mutado a `break` tras una exclusión, y los campos `grabacion_id`/`detalle` de la exclusión mutados a `None`) -- mismo patrón exacto que la Feature 006 encontró en `ejecutar_deteccion`: ningún test anterior capturaba `stdout`, y los que sí probaban una exclusión la ponían siempre al FINAL de la lista, donde `break` y `continue` son indistinguibles. 5 tests nuevos con `capsys`, incluido uno con la exclusión al PRINCIPIO de la lista.
  - `leer_grabacion_con_posicion_real`: `zip(note_data.intervals, note_data.pitches, strict=True)` mutado a `strict=False`/omitido -- a diferencia de los `zip(strict=True)` de `metrica_digitacion` (ver equivalentes abajo), `intervals`/`pitches` aquí son dos arrays leídos de forma independiente desde `mirdata`, sin ninguna garantía estructural de igual longitud -- mismo patrón que `leer_grabacion` ya tenía cubierto para `notes_all`. 1 test nuevo, mismo mecanismo (arrays de longitud distinta).

  **Equivalentes documentados (no corregidos -- no hay nada que corregir, el código y el mutante producen el mismo resultado real, cada uno verificado por qué antes de descartarlo, nunca solo "no se me ocurre un test"):**

  - `_generar_combinaciones_validas`, 3 mutantes: `zip(instante.notas, combinacion, strict=True)` mutado a `strict=False`/omitido/`strict=None` -- `combinacion` proviene de `itertools.product(*candidatas_por_nota)`, que produce tuplas de EXACTAMENTE `len(instante.notas)` elementos por construcción; las dos secuencias no pueden divergir en longitud, nunca. Mismo tipo de equivalente que los 10 de `_emparejar` documentados en la Feature 006 (research.md #17 de esa feature).
  - `agrupar_en_instantes`, 1 mutante: `grupo_actual: list[NotaEntrada] = []` mutado a `= None` -- ese valor inicial solo se lee en `if grupo_actual:`, una comprobación de verdad donde `None` y `[]` son indistinguibles (ambos falsos); se reasigna sin condición inmediatamente después.
  - `asignar_secuencia`, 4 mutantes: `fila_bp_inicial: list[int | None] = [None] * len(primeras)` mutado a `= None`, y el `backptr.append(fila_bp_inicial)` correspondiente mutado a `backptr.append(None)` -- `backptr[0]` nunca se lee: el bucle de backtracking recorre `range(len(activos)-1, 0, -1)`, que por diseño nunca llega al índice `0` (no hay instante anterior al primero del que backtrackear). `camino = [0] * len(activos)` mutado a `[1] * len(activos)` -- cada posición de `camino` se sobreescribe sin condición antes de leerse (`camino[-1] = j_optimo`, y el bucle cubre el resto), así que el valor inicial nunca se observa. `mejor_k: int | None = None` mutado a `= ""` -- el bucle interno sobre `combos_prev` siempre tiene al menos una iteración (ningún instante activo llega con cero combinaciones válidas, por construcción de `_generar_combinaciones_validas`), así que `mejor_k` siempre se reasigna a un `int` real antes de leerse.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T002 depende de T001 (mismo paquete).
- **Foundational (Phase 2)**: depende de Setup -- bloquea las dos historias P1.
- **User Story 1 (Phase 3)**: depende de Foundational. No depende de User Story 2.
- **User Story 2 (Phase 4)**: depende de Foundational Y de T007 de User Story 1 (`_generar_combinaciones_validas`, el helper compartido) -- **no es independiente de User Story 1 pese a ser ambas P1**: la DP de User Story 2 reutiliza literalmente la regla de validez de User Story 1, nunca una segunda implementación paralela (T012, ver su propia descripción).
- **User Story 3 (Phase 5)**: depende de Foundational, de T007 (US1) y de T010/T012 (US2, `Digitacion`/`asignar_secuencia`) -- es la que ata las dos historias P1 sobre un conjunto real.
- **Polish (Phase 6)**: depende de que las tres user stories estén completas.

### Dentro de cada Story

- Tests antes que implementación; confirmarlos en rojo antes de tocar `analytics/metrica_digitacion.py`/`ingestion/guitarset.py`/`digitacion/`.
- User Story 1: T006 (`generar_candidatas`) antes que T007 (que la usa); T007a (helper) antes que T007b (`asignar_instante`, que lo envuelve) -- mismo commit lógico, T007.
- User Story 2: T010 (tipo `Digitacion`) y T011 (`agrupar_en_instantes`) antes que T012 (`asignar_secuencia`, que produce lo uno y consume lo otro); T012 depende también de T007 (US1).
- User Story 3: T018 (lectura real) antes que T019 (tipos que la importan); T019 antes que T020/T021 (que los usan en su firma); T020/T021 antes que T022 (orquestador, que llama a ambos); T022 antes que T023 (CLI, que lo invoca); T023 antes que T024 (medición real, que corre la CLI); T024 antes que T025 (calibración, que analiza el resultado de T024).

### Parallel Opportunities

- T001 y T002 son secuenciales (mismo paquete/mismo archivo de config) -- sin paralelismo real en Setup.
- T004 y T005 (US1, mismo archivo, escenarios independientes) -- en paralelo.
- T008 y T009 (US2, mismo archivo, funciones independientes) -- en paralelo; ambas en paralelo con T004/T005 de US1 si dos personas trabajan las dos historias P1 a la vez (aunque T012 después necesitará que T007 de US1 ya exista).
- T013, T014, T015, T016, T017 (US3, tests de piezas distintas) -- en paralelo entre sí una vez Foundational + US1 + US2 están completas.
- T026 y T027 (Polish) -- comandos independientes entre sí.

---

## Parallel Example: User Story 1

```bash
# Estas dos tareas son independientes entre sí (mismo archivo, escenarios distintos):
Task: "Tests de generar_candidatas en tests/unit/test_metrica_digitacion.py"
Task: "Tests de asignar_instante en tests/unit/test_metrica_digitacion.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2)

1. Fase 1: Setup.
2. Fase 2: Foundational -- tipos de `Posicion`/`ModeloCoste`/`Instante`/`PosicionAsignada`/`InstanteExcluido`.
3. Fase 3: User Story 1 -- asignación correcta por instante aislado.
4. Fase 4: User Story 2 -- digitación completa de coste mínimo, verificada contra fuerza bruta.
5. **Parar y validar**: `asignar_secuencia()` sobre secuencias sintéticas cortas, óptimo verificado -- sin GuitarSet real todavía. Esto es el MVP: ambas historias son P1 porque ninguna es útil sola (User Story 1 sin User Story 2 no produce una digitación tocable de punta a punta; User Story 2 depende del mecanismo de validez de User Story 1).

### Incremental Delivery

1. Setup + Foundational -> tipos base listos.
2. User Story 1 -> mecanismo de asignación/exclusión por instante, verificable con instantes sintéticos.
3. User Story 2 -> digitación completa de coste mínimo, verificada contra fuerza bruta -> MVP (junto con User Story 1).
4. User Story 3 -> medición real contra GuitarSet, orquestador + CLI, primera medición real (Principio VII) y señal de calibración de pesos.
5. Polish -> `just gauntlet`, mutation testing acotado a la capa nueva.

---

## Notes

- **Por qué Foundational es chica otra vez**: mismo criterio que la Feature 006 (`tasks.md` de esa feature, misma sección) -- solo los tipos que las historias P1 necesitan para EMPEZAR (`Posicion`/`ModeloCoste`/`Instante`/`PosicionAsignada`/`InstanteExcluido`) viven en Foundational; `Digitacion` (T010) solo lo necesita User Story 2 en adelante, y todos los tipos de User Story 3 (`NotaConPosicionReal`, `PosicionReal`, `ResultadoCoincidencia`, `ExclusionDigitacion`, `ResultadoDigitacionGrabacion`, `ArtefactoDigitacion`) solo esa historia -- viven en la fase de la historia que primero los necesita.
- **`_generar_combinaciones_validas` (T007a) no aparece en `contracts/digitacion.md`**: es un helper privado extraído porque `asignar_instante` (contrato público de User Story 1, devuelve UNA asignación) y `asignar_secuencia` (User Story 2, necesita el CONJUNTO de asignaciones válidas por instante para que la DP tenga margen de decisión) comparten exactamente la misma regla de validez y de motivo de exclusión -- sin este helper, cualquier cambio a esa regla (por ejemplo, un cuarto motivo de exclusión futuro) tendría que mantenerse sincronizado a mano en dos lugares. Mismo patrón de extracción que `_emparejar` en `analytics.metrica_deteccion_notas` del hito 2 (research.md #17 de esa feature) o `evaluar_subconjunto` (T009 de esa feature, Notes).
- **Tercer motivo de exclusión (T005/T007a)**: `spec.md` (Edge Cases) pregunta explícitamente qué pasa con una nota fuera del rango físico del instrumento incluso con tolerancia completa, pero ninguna FR lo resuelve con un motivo nombrado -- `data-model.md` (`InstanteExcluido.motivo`) ya deja la puerta abierta ("distinguible entre, AL MENOS" los otros dos), así que agregar un tercero es una extensión compatible, no una desviación del contrato ya committeado.
- **Centroide de traste/cuerda para desplazamiento y cruce entre instantes multi-nota (T012)**: ni `research.md` ni `contracts/digitacion.md` fijaban cómo representar la "posición de la mano" de un acorde completo para calcular movimiento contra el instante siguiente -- ambos documentos solo dan el ejemplo de dos notas sueltas consecutivas (spec.md, el caso de cruce de cuerdas). La decisión (centroide sobre TODAS las notas de la combinación, incluidas las al aire) queda documentada en la propia tarea T012 con su razón, siguiendo la misma disciplina que el resto de parámetros de `research.md` -- revisable con la evidencia de User Story 3 (T025) si el sesgo resultante lo justifica, nunca elegida a ciegas ahora.
- **User Story 1 y User Story 2 son ambas P1 pero no son independientes entre sí en la implementación** (a diferencia del patrón usual donde historias del mismo nivel de prioridad se pueden paralelizar sin acoplamiento): `spec.md` ya lo dice explícitamente ("User Story 2... depende de que User Story 1 ya produzca candidatos válidos por instante") -- el acoplamiento real, verificado al escribir estas tareas, es más fino que "candidatos": es la regla de validez/exclusión completa (T007a), no solo la generación de candidatas por nota (T006). Documentado aquí para que quede explícito, no implícito en el orden de las fases.
