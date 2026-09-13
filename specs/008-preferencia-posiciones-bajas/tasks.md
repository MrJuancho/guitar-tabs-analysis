---

description: "Task list template for feature implementation"
---

# Tasks: Preferencia por posiciones bajas en el modelo de coste

**Input**: Design documents from `/specs/008-preferencia-posiciones-bajas/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/digitacion.md](./contracts/digitacion.md), [quickstart.md](./quickstart.md)

**Tests**: Incluidas explícitamente -- mismo criterio que las Features 002-007 (`just gauntlet` exige cobertura ≥90%, constitución Principio X pide test rojo antes que fix).

**Organization**: Tareas agrupadas por user story (`spec.md`: User Story 1 y User Story 2 son ambas P1, User Story 3 es P2), con una fase Foundational de una sola tarea -- el campo nuevo de `ModeloCoste` es lo único que las tres historias comparten antes de poder empezar.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede correr en paralelo con las demás tareas marcadas [P] de la misma fase (archivo distinto o escenario independiente, sin dependencia pendiente)
- **[Story]**: A qué user story pertenece (US1/US2/US3) -- ausente en Setup, Foundational y Polish

## Path Conventions

Proyecto único (`src/`, `tests/` en la raíz). Sin paquete ni capa nueva (plan.md#Project Structure) -- esta feature extiende dos módulos que la Feature 007 ya declaró dueños del modelo de coste y la orquestación:

- `src/guitar_tabs_analysis/analytics/metrica_digitacion.py` (EXTENDIDO) -- campo nuevo en `ModeloCoste`, coste de nodo extendido dentro de `asignar_secuencia`, tipos `PuntoBarrida`/`ResultadoBarrida`
- `src/guitar_tabs_analysis/digitacion/orquestador.py` (EXTENDIDO) -- `ejecutar_barrida_peso_altura`, serialización de `ResultadoBarrida`
- `src/guitar_tabs_analysis/digitacion/cli_barrido.py` (NUEVO) -- punto de entrada de proceso para la barrida
- `tests/unit/test_metrica_digitacion.py` (extendido), `tests/integration/test_digitacion_orquestador_integracion.py` (extendido), `tests/unit/test_digitacion_cli_barrido.py` (nuevo)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: N/A para esta feature -- declarado explícitamente, no omitido en silencio. `plan.md` (Primary Dependencies) ya confirma que no hay ninguna dependencia de terceros nueva ni ningún paquete nuevo que preparar (a diferencia de la Feature 007, que sí tuvo que crear el paquete `digitacion/` y extender el contrato `layers`, T001/T002 de esa feature): esta feature extiende dos módulos que ya existen. Sin tareas.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: El único cambio de tipo que las tres user stories necesitan antes de poder empezar.

**⚠️ CRITICAL**: Ninguna user story empieza hasta que esta fase esté completa.

- [X] T001 Agregar el campo `peso_altura_traste: float` a `ModeloCoste` en `src/guitar_tabs_analysis/analytics/metrica_digitacion.py` (data-model.md, contracts/digitacion.md postcondición 1 de `ModeloCoste`), y fijar `peso_altura_traste=0.0` en `MODELO_COSTE_POR_DEFECTO` (research.md #6 -- punto de control que reproduce exactamente el comportamiento de la Feature 007 hasta que la barrida de User Story 3 fije el valor final con evidencia). Actualizar `_modelo_coste_a_dict` en `src/guitar_tabs_analysis/digitacion/orquestador.py` para serializar el campo nuevo (mismo patrón que los demás campos de `ModeloCoste`).

**Checkpoint**: `ModeloCoste` tiene el campo nuevo con su valor de control -- User Story 1 puede empezar.

---

## Phase 3: User Story 1 - Agregar el término de altura al modelo de coste (Priority: P1) 🎯 MVP

**Goal**: Extender el coste de nodo que `asignar_secuencia` ya calcula (`_estiramiento`, un peso de nodo, research.md #1 de la Feature 007) con un segundo sumando proporcional a la altura de traste de cada posición del combo, ponderado por `peso_altura_traste`.

**Independent Test**: Posiciones e instantes construidos a mano (spec.md US1 Independent Test) -- sin GuitarSet real, sin la verificación de fuerza bruta de User Story 2.

### Tests for User Story 1 ⚠️

> Escribir estos tests primero, confirmarlos en rojo contra el coste de nodo aún sin extender.

- [X] T002 [US1] Tests del coste de nodo extendido en `tests/unit/test_metrica_digitacion.py` (spec.md US1 Acceptance Scenarios, contracts/digitacion.md postcondición 4' de `asignar_secuencia`): con `peso_altura_traste = 0.0` (`MODELO_COSTE_POR_DEFECTO`), el `coste_total` de `asignar_secuencia` sobre una secuencia sintética es IDÉNTICO al que produce hoy la Feature 007 sin este componente (AS3, Edge Case de `spec.md`: "debe reproducir exactamente" el valor de control); una posición al aire (`traste == 0`) aporta coste `0` de este componente para cualquier valor de `peso_altura_traste` (AS2, FR-003); dos posiciones candidatas para la misma nota con el mismo tono y el mismo coste de estiramiento/desplazamiento/cruce respecto del resto de la secuencia, una en traste bajo y otra en traste alto -- con `peso_altura_traste > 0`, la de traste más bajo produce un `coste_total` menor, en una cantidad exactamente `peso_altura_traste * (traste_alto - traste_bajo)` (AS1, FR-001); `peso_desplazamiento`/`peso_cruce_cuerdas` de `MODELO_COSTE_POR_DEFECTO` siguen en `1.0`, sin cambio (AS4, FR-002) -- assertion directa sobre la constante, no un test de comportamiento; **dos posiciones candidatas en el MISMO traste y distinta cuerda (spec.md Edge Cases, único caso límite sin cobertura señalado por `/speckit-analyze`) -- el componente de altura aporta EXACTAMENTE el mismo valor a ambas** (`peso_altura_traste * traste`, sin ninguna referencia a la cuerda en la fórmula, FR-001/FR-003) -- este componente nunca introduce un desempate implícito entre cuerdas distintas de igual traste; cualquier desempate observado sigue siendo responsabilidad exclusiva de los componentes ya existentes (estiramiento/desplazamiento/cruce). Depende de T001.

### Implementation for User Story 1

- [X] T003 [US1] Extraer `_coste_nodo(posiciones: list[Posicion], modelo: ModeloCoste) -> float` en `src/guitar_tabs_analysis/analytics/metrica_digitacion.py`, definido como `_estiramiento(posiciones) + modelo.peso_altura_traste * sum(p.traste for p in posiciones)` (research.md #1/#2 de esta feature, contracts/digitacion.md postcondición 4'). Reemplazar las dos invocaciones directas de `_estiramiento(...)` dentro de la recurrencia de `asignar_secuencia` (el caso base `dp[0][j]` y el término que se suma tras el mínimo sobre aristas en cada `dp[i][j]`, `i > 0`) por `_coste_nodo(posiciones, modelo)` -- **MUST NOT** tocar `_generar_combinaciones_validas`/`asignar_instante` ni el criterio de validez de una combinación (FR-004: agregar este componente al coste no altera qué posiciones se consideran válidas, solo cuánto cuestan las ya válidas), ni `_coste_arista`/`_centroide` (el nuevo término es de nodo, no de arista, research.md #1). Depende de T001, T002.

**Checkpoint**: `asignar_secuencia` prefiere posiciones bajas entre alternativas de igual coste de movimiento, con `peso_altura_traste = 0.0` reproduciendo exactamente la Feature 007 -- verificable con secuencias construidas a mano, sin GuitarSet real todavía.

---

## Phase 4: User Story 2 - Confirmar que la optimalidad se sigue verificando contra fuerza bruta (Priority: P1)

**Goal**: Repetir, con el coste de nodo extendido (T003) incluido, la misma verificación de optimalidad que la Feature 007 ya tiene contra fuerza bruta -- para varios valores de `peso_altura_traste`, incluido `0`. Esta historia no agrega ningún comportamiento observable nuevo (el mecanismo ya lo entrega User Story 1): es una verificación de corrección del algoritmo, no una funcionalidad -- mismo estatus que FR-006 de la Feature 007.

**Independent Test**: Las mismas secuencias sintéticas cortas (o una extensión de ellas) que la Feature 007 ya usa para su propia verificación de fuerza bruta, recalculando el óptimo con el término de altura incluido.

### Tests for User Story 2 ⚠️

- [X] T004 [US2] Extender los tests de fuerza bruta de `asignar_secuencia` en `tests/unit/test_metrica_digitacion.py` (spec.md US2 Acceptance Scenarios, FR-005). **Requisito de independencia de esta tarea (verificado contra el archivo real antes de escribir esta tarea, no asumido -- mismo defecto que ya se cerró en la Feature 002, donde el property test deriva su propia tabla de referencia en vez de importar la de producción)**: la fuerza bruta de la Feature 007 (`_fuerza_bruta_coste_minimo`/`_coste_nodo_bruteforce`/`_centroide_bruteforce`/`_coste_arista_bruteforce`, líneas 527-587 del archivo) ya está escrita de forma independiente -- ninguna de esas funciones llama a `_coste_nodo`/`_centroide`/`_coste_arista`/`_generar_combinaciones_validas` de producción, solo reutiliza `generar_candidatas` (mapeo tono→posición, un cálculo cerrado ajeno a la minimización bajo prueba) y `agrupar_en_instantes` (ya verificado aparte). **Esta tarea MUST preservar esa independencia al extenderla**: `_coste_nodo_bruteforce` MUST cambiar de firma a `_coste_nodo_bruteforce(combo: tuple[Posicion, ...], modelo: ModeloCoste) -> float` y sumar `peso_altura_traste * sum(p.traste for p in combo)` con aritmética escrita en el propio test -- MUST NOT invocar `_coste_nodo` de producción ni ningún otro helper de `analytics.metrica_digitacion` para calcular este término (si se comparte el cálculo entre ambos lados, un error en `_coste_nodo` de producción afectaría los dos lados de la comparación por igual y el test pasaría en verde sin detectarlo -- exactamente el defecto que esta independencia previene). Actualizar los dos call sites de `_coste_nodo_bruteforce` dentro de `_fuerza_bruta_coste_minimo` para pasar `modelo`. Con esa independencia preservada: para cada una de varias secuencias sintéticas cortas YA usadas por la Feature 007, y para los valores `0`, `1` y `100` del conjunto de candidatos ya declarado en research.md #3 (nunca "un valor intermedio"/"un valor grande" sin fijar -- mismo criterio de números concretos que el resto de esta feature, `/speckit-analyze` A1), el `coste_total` que devuelve `asignar_secuencia` coincide EXACTAMENTE (tolerancia numérica, Principio VIII) con el óptimo de fuerza bruta recalculado con ese mismo valor de peso -- confirma que agregar un peso de nodo adicional no rompe la subestructura óptima (research.md #1 de esta feature: mismo argumento estructural que research.md #1 de la Feature 007, ahora verificado con evidencia empírica también, y sin el riesgo de una comparación circular). Depende de T003.

**Checkpoint**: La verificación de optimalidad de la Feature 007 sigue pasando con el término de altura incluido, para varios valores del peso -- User Story 1 + User Story 2 son el MVP de esta feature (mecanismo verificado, sin GuitarSet real todavía).

---

## Phase 5: User Story 3 - Barrer el peso y medir contra GuitarSet (Priority: P2)

**Goal**: Medir `fraccion_coincidencia` sobre las 288 grabaciones medibles para los diez valores candidatos declarados en research.md #3/#5 (`0, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100`), leyendo GuitarSet una única vez (research.md #4), y documentar la curva completa con un criterio de mejora fijado antes de correrla.

**Independent Test**: `ejecutar_barrida_peso_altura` puede probarse por completo con grabaciones sintéticas construidas a mano (mismo patrón que `ejecutar_digitacion` de la Feature 007) -- depende de que User Story 1 ya exista (el peso debe tener efecto real sobre el coste para que la barrida mida algo).

### Tests for User Story 3 ⚠️

- [X] T005 [P] [US3] Tests de `ejecutar_barrida_peso_altura` en `tests/integration/test_digitacion_orquestador_integracion.py` (contracts/digitacion.md postcondiciones 1-5 de esta función, research.md #4): varias grabaciones sintéticas leídas -- verificar (con un `monkeypatch`/spy sobre `leer_grabacion_con_posicion_real` que cuenta invocaciones) que cada grabación se lee EXACTAMENTE UNA VEZ sin importar cuántos valores tenga `valores_candidatos` (postcondición 1); el `ResultadoBarrida` devuelto tiene un `PuntoBarrida` por cada valor de `valores_candidatos`, en el mismo orden, incluido el de menor `fraccion_coincidencia` (postcondiciones 2/3 -- nunca solo el máximo); una grabación cuya lectura falla (`GrabacionNoExisteError`) queda excluida de TODOS los puntos por igual, nunca solo de algunos (postcondición 1); el punto con `peso_altura_traste == 0.0` produce una `fraccion_coincidencia` idéntica a la de `ejecutar_digitacion` con `MODELO_COSTE_POR_DEFECTO` sobre las mismas grabaciones (postcondición 5, punto de control de research.md #6); ninguna de las 72 reservadas participa cuando la lista de entrada se construye con `construir_lista_grabaciones("medibles", ...)` (mismo criterio que `ejecutar_digitacion`, FR-011 de esta feature). Depende de T001, T003.
- [X] T006 [P] [US3] Tests de `digitacion/cli_barrido.py` en `tests/unit/test_digitacion_cli_barrido.py` (nuevo, mismo patrón que `test_digitacion_cli.py` de la Feature 007): invocar `main([])` sin `--root-dir` -> `SystemExit` con código distinto de 0 antes de tocar disco; el conjunto de valores candidatos NO es un argumento aceptado por el parser (research.md #5 -- MUST NOT poder pasarse por línea de comandos); escritura atómica del artefacto final en `mediciones/barrido_altura_traste.json` verificada (archivo temporal + `os.replace()`, relectura de confirmación, mismo mecanismo que `digitacion/cli.py`). Depende de T001.

### Implementation for User Story 3

- [X] T007 [US3] Agregar `PuntoBarrida` (`frozen=True`: `peso_altura_traste: float`, `resultado_coincidencia: ResultadoCoincidencia`) y `ResultadoBarrida` (`frozen=True`: `valores_candidatos: list[float]`, `puntos: list[PuntoBarrida]`) a `src/guitar_tabs_analysis/analytics/metrica_digitacion.py` (data-model.md). Implementar `ejecutar_barrida_peso_altura(valores_candidatos: list[float], grabaciones: list[str], root_dir: Path, modelo_base: ModeloCoste = MODELO_COSTE_POR_DEFECTO) -> ResultadoBarrida` en `src/guitar_tabs_analysis/digitacion/orquestador.py` (contracts/digitacion.md postcondiciones 1-5, research.md #4): lee `leer_grabacion_con_posicion_real` por cada `grabacion_id` de `grabaciones` UNA SOLA VEZ (mismo manejo de `GrabacionNoExisteError` que `ejecutar_digitacion`: exclusión que aplica a todos los puntos por igual, nunca una relectura por valor candidato); para cada valor de `valores_candidatos`, en orden, construye un `ModeloCoste` igual a `modelo_base` salvo `peso_altura_traste` en ese valor, corre `asignar_secuencia` + `evaluar_coincidencia` sobre los datos ya leídos para cada grabación no excluida, agrega con `agregar_conjunto`, y arma un `PuntoBarrida`; devuelve `ResultadoBarrida` con la lista completa. **MUST NOT** invocar `ejecutar_digitacion` en un bucle (relee disco innecesariamente, research.md #4) ni comparar puntos entre sí para elegir un "ganador" (FR-007/FR-009). Agregar `resultado_barrida_a_dict`/`_punto_barrida_a_dict` (serialización, mismo patrón que `artefacto_a_dict`). Depende de T003, T005.
- [X] T008 [US3] Implementar `src/guitar_tabs_analysis/digitacion/cli_barrido.py` (nuevo, mismo patrón que `digitacion/cli.py`: `--root-dir` `required=True`, sin ningún argumento para los valores candidatos -- research.md #5): declara `VALORES_CANDIDATOS_ALTURA_TRASTE = (0.0, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0)` como constante nombrada del módulo; `main()` construye la lista de grabaciones con `construir_lista_grabaciones("medibles", args.root_dir)` (importada de `deteccion.orquestador`, **MUST NOT** aceptar `"reservado"` -- a diferencia de `digitacion/cli.py`, esta CLI no tiene `--modo`: la barrida es exclusivamente sobre medibles, Principio VI), llama `ejecutar_barrida_peso_altura` (T007) y escribe `ResultadoBarrida` serializado en `mediciones/barrido_altura_traste.json` con escritura atómica + relectura de verificación (mismo mecanismo que `digitacion/cli.py`). Valida `root_dir`/índice de `mirdata` al arrancar, reutilizando `validar_raiz_guitarset`/`validar_indice_mirdata`. Agregar recipe `barrer-altura root_dir` al `justfile` (mismo patrón que `digitar modo root_dir`, sin el parámetro `modo`). Depende de T006, T007.
- [X] T009 [US3] **Ejecución manual real, no un test** (quickstart.md "Ejecución manual"): correr `ejecutar_barrida_peso_altura` (vía `just barrer-altura <ruta-guitarset>`) sobre las 288 grabaciones medibles reales con los diez valores candidatos declarados (research.md #3/#5).

  **Criterio de mejora, fijado AHORA -- antes de correr la barrida y de ver ningún resultado (pedido explícito de esta sesión)**: un valor candidato cuenta como mejora real sobre la línea base (`fraccion_coincidencia = 0.618633...`, T024 de la Feature 007) solo si se cumplen LAS DOS condiciones siguientes:
  1. Su `fraccion_coincidencia` supera la línea base por al menos `0.01` (un punto porcentual absoluto -- sobre 49535 notas medidas, equivale a al menos ~495 notas que pasan de no-coincidentes a coincidentes; una diferencia de ese tamaño no es explicable por el desempate arbitrario pero determinista de la DP entre óptimos de igual coste, Principio VIII).
  2. Ese margen se sostiene en al menos un valor candidato ADYACENTE de la escala logarítmica (no es un pico aislado de un solo punto) -- un único punto por encima del umbral, rodeado de vecinos por debajo, se trata como posible artefacto de la discretización de la barrida (un valor de peso que por casualidad cruza un umbral de desempate en varias posiciones a la vez), no como una tendencia real.

  Un valor candidato que no cumple ambas condiciones NO cuenta como mejora, sin importar cuánto más alto sea su número crudo que la línea base.

  **Casos explícitos a documentar en `research.md` -- NINGUNO de los tres es un fallo que evitar reportar (FR-010 de esta feature)**:
  - **Curva plana o el óptimo cae en `peso_altura_traste = 0`**: ningún valor candidato cumple el criterio de arriba. Refuta la hipótesis motivadora (ADR-0002 hallazgo 4) sobre GuitarSet como conjunto de evaluación -- se documenta como un hallazgo real: la preferencia por posiciones bajas no es lo que separa la digitación del modelo de la humana en este conjunto, aunque sí lo fuera en la canción real que motivó la feature (discrepancia entre evidencia anecdótica y evidencia de dataset, en sí misma un hallazgo sobre GuitarSet).
  - **Algún valor cumple el criterio de mejora**: se documenta como evidencia real de que la preferencia por posiciones bajas mejora el parecido con el uso humano sobre este conjunto -- la ELECCIÓN de qué valor adoptar como nuevo `peso_altura_traste` por defecto en `MODELO_COSTE_POR_DEFECTO` queda para una sesión posterior (con su propia decisión, potencialmente vía `/speckit-constitution` si también se documenta en la constitución) -- **fuera de alcance de esta tarea** (FR-007/FR-009: la curva completa se documenta, no se elige un ganador mirando el resultado).
  - **Tiempo real**: confirmar con evidencia de reloj que el costo proyectado (research.md #4, `~25s`: `~8.9s` de lectura única + `~1.6s` por cada uno de los diez valores) se sostiene en la práctica -- si diverge de forma significativa, documentarlo como hallazgo, mismo criterio que toda afirmación cuantitativa del proyecto (AGENTS.md).

  Registrar la curva completa (los diez pares `peso_altura_traste`/`fraccion_coincidencia`, con `num_notas_medidas`/`num_notas_coincidentes` de cada uno) en `research.md` como un hallazgo nuevo -- nunca solo el valor que "ganó". Depende de T008.

**Checkpoint**: Las tres user stories completas -- la curva completa de la barrida queda documentada con su criterio de mejora declarado por adelantado, sin importar si refuta o confirma la hipótesis motivadora, y ninguna de las 72 reservadas participó.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T010 [P] Correr `just gauntlet` (ruff format --check + lint-imports + mypy --strict + tests unit/integration/property con cobertura ≥90%) y corregir cualquier hallazgo.
- [X] T011 [P] Mutation testing acotado a la capa nueva/extendida de esta feature: el coste de nodo extendido y `PuntoBarrida`/`ResultadoBarrida` en `analytics.metrica_digitacion`, `ejecutar_barrida_peso_altura`/serialización en `digitacion.orquestador`, y `digitacion.cli_barrido` completo -- mismo criterio de triage que T027 de la Feature 007 (cada superviviente revisado con `mutmut show`, equivalentes documentados con su razón, nunca solo contados).

  **Resultado por módulo** (triage completo, no conteo):

  | Módulo | Mutantes | Killed | Sobrevivientes |
  |---|---|---|---|
  | `analytics.metrica_digitacion` (completo, extensión incluida) | 714 | 706 | 8 (equivalentes, heredados de la Feature 007 sin cambio -- ver abajo) |
  | `digitacion.orquestador` (completo, extensión incluida) | 785 | 784 | 1 (equivalente, nuevo de esta feature) |
  | `digitacion.cli_barrido` (nuevo) | -- | -- | 0 |

  **Hallazgos reales corregidos con tests nuevos, en `digitacion.orquestador`
  y `digitacion.cli_barrido`** (triage inicial: 16 y 21 sobrevivientes
  respectivamente, antes de las correcciones):
  - `ejecutar_barrida_peso_altura`: `root_dir` mutado a `None` en la
    lectura -- ningún test capturaba el argumento real recibido, solo el
    `grabacion_id`. `continue` mutado a `break` tras una lectura fallida
    -- el único test de exclusión tenía la grabación fallida al FINAL de
    la lista (mismo patrón exacto que T027 de la Feature 007 encontró en
    `ejecutar_digitacion`). `dataclasses.replace(modelo_base, )` sin el
    argumento `peso_altura_traste` -- **el hallazgo más significativo**:
    ningún test verificaba que el PESO REALMENTE USADO dentro de
    `asignar_secuencia` fuera el valor candidato -- `PuntoBarrida.
    peso_altura_traste` es una etiqueta que el código ya asignaba
    correctamente desde la variable de loop, independiente de si el
    `ModeloCoste` interno lo llevaba o no; un espía sobre `asignar_secuencia`
    capturando `modelo.peso_altura_traste` cierra el hueco. 3 tests nuevos.
  - `_punto_barrida_a_dict`: las cuatro claves del dict (`peso_altura_traste`,
    `resultado_coincidencia`, con sus variantes de mayúsculas/vacío)
    sobrevivían porque ningún test inspeccionaba el CONTENIDO de un punto
    serializado, solo `len(puntos)` -- mismo patrón que
    `test_artefacto_a_dict_serializa_...` ya prueba para
    `ArtefactoDigitacion`. 2 tests nuevos en `test_orquestador_digitacion.py`
    (contenido completo + round-trip JSON).
  - `cli_barrido._construir_parser`: el texto completo de `description`/
    `help` sobrevivía -- el test original solo fijaba `parser.prog`, a
    diferencia del test análogo de la Feature 007
    (`test_construir_parser_expone_prog_descripcion_y_los_dos_argumentos_completos`)
    que sí fija el texto completo. 1 test extendido con las aserciones
    faltantes.
  - `cli_barrido.escribir_resultado_barrida`: `mkdir(parents=True, ...)`
    sobrevivía porque el único test de creación de directorio tenía un
    solo nivel ausente, donde `parents=False` también funciona -- mismo
    patrón que `test_escribir_artefacto_crea_varios_niveles_de_directorio_ausentes`
    de la Feature 007. 1 test nuevo con dos niveles ausentes.
  - `cli_barrido._ejecutar_y_escribir`: `root_dir` mutado a `None` tanto
    en la llamada a `construir_lista_grabaciones` como en
    `ejecutar_barrida_peso_altura` -- el `_monkeypatch_mirdata` de este
    archivo ignoraba `data_home`, así que ningún valor incorrecto era
    observable; mismo patrón que
    `test_ejecutar_y_escribir_pasa_el_mismo_root_dir_a_ambas_llamadas` de
    `test_digitacion_cli.py`. 1 test nuevo, mismo mecanismo.

  **Equivalentes documentados (no corregidos -- verificados, no solo
  "no se me ocurre un test"):**
  - `analytics.metrica_digitacion`, los mismos 8 mutantes ya documentados
    en T027 de la Feature 007 (3× `zip(strict=True)` en
    `_generar_combinaciones_validas`, `grupo_actual: list = None` en
    `agrupar_en_instantes`, y 4× valores iniciales nunca leídos en
    `asignar_secuencia` -- `fila_bp_inicial`/`backptr[0]`, `mejor_k`,
    `camino`) -- verificado con `mutmut show` que están en código SIN
    TOCAR por esta feature (ninguno cae en `_coste_nodo` ni en las dos
    líneas donde `asignar_secuencia` ahora llama a `_coste_nodo` en vez
    de `_estiramiento`) -- el propio hallazgo, no solo la lista, ya
    confirma que el código nuevo de esta feature llegó a 100% de killed.
  - `digitacion.orquestador`, 1 mutante nuevo:
    `ResultadoDigitacionGrabacion(grabacion_id=grabacion_id, ...)` mutado
    a `grabacion_id=None` dentro de `ejecutar_barrida_peso_altura` --
    verificado contra `agregar_conjunto` (research.md/contracts de la
    Feature 007): esa función nunca lee `.grabacion_id`, solo
    `.exclusion`/`.digitacion`/`.notas_con_posicion_real`; estos objetos
    son enteramente locales a la función (nunca se devuelven ni se
    inspeccionan más allá de la agregación inmediata), así que el valor
    de ese campo no tiene ningún efecto observable posible.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin tareas -- nada que bloquee.
- **Foundational (Phase 2)**: T001, sin dependencia -- bloquea las tres user stories.
- **User Story 1 (Phase 3)**: depende de Foundational. No depende de User Story 2 ni 3.
- **User Story 2 (Phase 4)**: depende de Foundational Y de T003 (User Story 1, el coste de nodo que verifica) -- pura verificación, sin implementación propia.
- **User Story 3 (Phase 5)**: depende de Foundational y de T003 (User Story 1, el peso debe tener efecto real sobre el coste para que la barrida mida algo) -- no depende código-a-código de User Story 2, pero por disciplina de este proyecto (nunca medir con evidencia real un mecanismo cuya optimalidad no se confirmó todavía) se recomienda completar Phase 4 antes de correr T009.
- **Polish (Phase 6)**: depende de que las tres user stories estén completas.

### Dentro de cada Story

- Tests antes que implementación; confirmarlos en rojo antes de tocar `analytics/metrica_digitacion.py`/`digitacion/orquestador.py`/`digitacion/cli_barrido.py`.
- User Story 1: T002 (tests) antes que T003 (implementación, el helper `_coste_nodo` que los hace pasar).
- User Story 2: T004 depende de T003 (extiende la verificación de fuerza bruta contra el coste de nodo ya extendido).
- User Story 3: T005/T006 (tests) antes que T007/T008 (implementación que los hace pasar, mismo patrón que la Feature 007: los tests se escriben contra la firma ya fijada en `contracts/digitacion.md`, no contra una implementación existente); T007 antes que T008 (la CLI invoca la función del orquestador); T008 antes que T009 (la ejecución manual real corre la CLI).

### Parallel Opportunities

- T002 (US1) es la única tarea de test de su fase -- sin paralelismo real dentro de Phase 3.
- T004 (US2) es la única tarea de su fase.
- T005 y T006 (US3, archivos distintos: integración vs. CLI) -- en paralelo entre sí.
- T010 y T011 (Polish) -- comandos independientes entre sí.

---

## Parallel Example: User Story 3

```bash
# Estas dos tareas son independientes entre sí (archivos distintos):
Task: "Tests de ejecutar_barrida_peso_altura en tests/integration/test_digitacion_orquestador_integracion.py"
Task: "Tests de digitacion/cli_barrido.py en tests/unit/test_digitacion_cli_barrido.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2)

1. Fase 1: Setup (sin tareas).
2. Fase 2: Foundational -- campo `peso_altura_traste`.
3. Fase 3: User Story 1 -- coste de nodo extendido, verificable con secuencias sintéticas.
4. Fase 4: User Story 2 -- confirmación de optimalidad contra fuerza bruta con el término nuevo.
5. **Parar y validar**: el mecanismo existe, prefiere posiciones bajas cuando el resto del coste empata, y sigue siendo óptimo -- sin GuitarSet real todavía. Esto es el MVP: igual que en la Feature 007, ninguna de las dos historias P1 es útil sola para el objetivo final de la feature (medir contra GuitarSet), pero juntas dejan el mecanismo listo y verificado.

### Incremental Delivery

1. Setup + Foundational -> campo nuevo listo.
2. User Story 1 -> mecanismo de preferencia por posiciones bajas, verificable con secuencias sintéticas.
3. User Story 2 -> optimalidad reconfirmada contra fuerza bruta -> MVP (junto con User Story 1).
4. User Story 3 -> barrida real contra GuitarSet, con su criterio de mejora predeclarado -- resultado real, en cualquier dirección, documentado en `research.md`.
5. Polish -> `just gauntlet`, mutation testing acotado a la capa nueva/extendida.

---

## Notes

- **Por qué Foundational es una sola tarea**: a diferencia de la Feature 007 (Foundational agregaba varios tipos de dominio nuevos), esta feature extiende un tipo ya existente -- el único cambio que las tres historias comparten es el campo nuevo de `ModeloCoste`. `PuntoBarrida`/`ResultadoBarrida` (User Story 3) viven en la fase de la historia que los necesita, mismo criterio que la Feature 007 aplicó a sus propios tipos exclusivos de User Story 3.
- **`_coste_nodo` (T003) no aparece como firma pública en `contracts/digitacion.md`**: es un helper privado extraído por el mismo motivo que `_estiramiento`/`_centroide` ya lo eran en la Feature 007 -- el contrato público (`asignar_secuencia`) no cambia de firma, solo de comportamiento interno (postcondición 4', contracts/digitacion.md).
- **User Story 2 no tiene tarea de implementación propia**: a diferencia de la Feature 007 (donde User Story 2 SÍ era la implementación de `asignar_secuencia`), aquí el mecanismo ya lo entrega User Story 1 -- User Story 2 es puramente la verificación de que ese mecanismo, ya implementado, sigue siendo óptimo. Reflejar esto con una sola tarea de test es intencional, no una fase incompleta.
- **El criterio de mejora de T009 se escribe en `tasks.md` antes de correr la barrida, no en `research.md` después**: pedido explícito de la sesión que generó estas tareas -- fijar qué cuenta como señal real (magnitud + sostenimiento en un vecino) ANTES de ver la curva es lo que distingue esta medición de "mirar el número y decidir que se ve bien" (mismo vicio que Principio VII ya prohíbe para presupuestos, aplicado aquí a un criterio de interpretación, no a un umbral de aprobación -- FR-009 sigue prohibiendo evaluar la curva contra el presupuesto vigente).
- **Ningún resultado de T009 es un fallo**: la tarea documenta explícitamente los tres desenlaces posibles (curva plana/óptimo en cero, mejora real, tiempo divergente) como resultados válidos a registrar -- ninguno bloquea el cierre de la feature ni exige "arreglar" nada, mismo criterio que T025 de la Feature 007 trató la ausencia de asimetría como evidencia negativa válida.
- **Independencia de la fuerza bruta de T004, verificada contra el archivo real, no detectada por `/speckit-analyze` (pedido explícito de la sesión que revisó estas tareas)**: el riesgo genérico es que un test de "coincide con fuerza bruta" comparta el cálculo de coste con la producción -- un error en `_coste_nodo` afectaría ambos lados por igual y el test pasaría en verde sin detectar nada, mismo defecto que ya se cerró en la Feature 002 (el property test deriva su propia tabla de referencia en vez de importar la de producción). Verificado ANTES de escribir T004: la fuerza bruta de la Feature 007 (`tests/unit/test_metrica_digitacion.py`, líneas 527-587) ya es independiente -- no hacía falta corregir nada existente, solo preservar esa independencia al extenderla con el término de altura (T004 ya lo deja como requisito explícito, con el motivo de por qué importa).
