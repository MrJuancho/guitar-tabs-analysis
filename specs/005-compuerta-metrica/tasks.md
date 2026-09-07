---

description: "Task list template for feature implementation"
---

# Tasks: Compuerta de la métrica

**Input**: Design documents from `/specs/005-compuerta-metrica/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/compuerta.md](./contracts/compuerta.md), [quickstart.md](./quickstart.md)

**Tests**: Incluidas explícitamente — mismo criterio que Features 001-004 (`just gauntlet` exige cobertura ≥90%, constitución Principio X pide test rojo antes que fix).

**Organization**: Tareas agrupadas por user story (P1/P2/P3 de `spec.md`). Sin fase Setup con tareas propias — ver nota en Phase 1: esta feature no agrega ninguna dependencia nueva, paquete, ni cambio de configuración.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede correr en paralelo con las demás tareas marcadas [P] de la misma fase (archivo distinto, sin dependencia pendiente)
- **[Story]**: A qué user story pertenece (US1/US2/US3) — ausente en Setup, Foundational y Polish, igual que en Features 001-004

## Path Conventions

Proyecto único (`src/`, `tests/` en la raíz). Módulo nuevo, único archivo,
dentro de la capa ya existente `medicion` (research.md #2, plan.md#Project
Structure):

- `src/guitar_tabs_analysis/medicion/compuerta.py` — `PRESUPUESTO_SI_SDR_DB`,
  `Veredicto`, `ArtefactoInvalidoError`, `evaluar_artefacto()`,
  `leer_artefacto()`, `main()`. Solo `stdlib` — no importa
  `medicion.orquestador`, `separacion`, `analytics` ni `ingestion`
  (research.md #1).
- `tests/unit/test_compuerta.py` — `evaluar_artefacto()` con `dict`s
  sintéticos: presupuesto alcanzado/no alcanzado/límite exacto (US1),
  validación de forma y de evidencia insuficiente (US2).
- `tests/unit/test_compuerta_mediana_equivalencia.py` — property test
  (Hypothesis) de la equivalencia entre `statistics.median` y la mediana
  de estadístico de orden que la Feature 002 ya usa, sobre el dominio
  restringido de esta feature (research.md #3).
- `tests/unit/test_compuerta_cli.py` — `leer_artefacto()` y `main()`
  sobre `tmp_path`: ruta ausente, contenido no interpretable (US2),
  `--modo` sin default, dos artefactos independientes con el mismo
  presupuesto, códigos de salida 0/1/2 (US3).
- `justfile` — recipe `compuerta` nueva; paso nuevo en `gauntlet`
  (research.md #8).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar dependencias antes de escribir código de dominio.

**Sin tareas.** A diferencia de las Features 002 (`scipy`) y 003
(`demucs`+`torch`), esta feature no agrega ninguna dependencia de
terceros, ningún paquete nuevo (`medicion/__init__.py` ya existe desde
la Feature 004), y ningún cambio de `pyproject.toml::[tool.importlinter]`
(`medicion` ya está excluida por completo del contrato `layers`, y
`compuerta.py` no cruza ninguna capa — plan.md#Technical Context,
research.md #1/#2). El primer trabajo real es Foundational.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Los tipos de dominio que las tres user stories necesitan
antes de poder escribir ningún test.

**⚠️ CRITICAL**: Ninguna user story empieza hasta que esta fase esté completa.

- [X] T001 Crear `src/guitar_tabs_analysis/medicion/compuerta.py` con el
      docstring del módulo (research.md #1/#2: solo `stdlib`, no importa
      `medicion.orquestador` ni la pila de separación), la constante
      `PRESUPUESTO_SI_SDR_DB = -8.0` (comentario apuntando al Principio
      VII de la constitución, v1.5.0 — mismo patrón que
      `SEMILLA_SUBMUESTRA_HITO1` en `orquestador.py`), el `dataclass(frozen=True)`
      `Veredicto` (campos de data-model.md: `aprobado`, `mediana_emparejadas`,
      `presupuesto`, `fraccion_sin_pareja`, `total_emparejadas`,
      `total_sin_pareja`, `modelo_nombre`, `modelo_variante`,
      `modelo_firma`, `modo`, `semilla`), y `ArtefactoInvalidoError(Exception)`
      con un constructor que arma su mensaje explícito según el motivo
      (mismo patrón que `ModeloCambiadoError` en `orquestador.py`: motivo
      + datos concretos, nunca un mensaje genérico). Sin lógica todavía
      — solo los tipos.

**Checkpoint**: Los tipos existen — las tres user stories pueden empezar a escribirse en paralelo.

---

## Phase 3: User Story 1 - Juzgar un artefacto de medición contra el presupuesto (Priority: P1) 🎯 MVP

**Goal**: Dado un artefacto de medición sintético, calcular y devolver un
`Veredicto` correcto comparando la mediana de referencias emparejadas
contra `-8.0 dB`, con la fracción sin pareja siempre incluida.

**Independent Test**: Construir `dict`s sintéticos con distintas medianas
de `emparejadas` (por encima, igual, y por debajo de `-8.0 dB`) e invocar
`evaluar_artefacto()` directamente — sin CLI, sin artefacto real, sin
modelo.

### Tests for User Story 1 ⚠️

> **NOTE: Escribir estos tests PRIMERO, confirmar que fallan (la función no existe todavía) antes de implementar.**

- [X] T002 [P] [US1] En `tests/unit/test_compuerta.py` (nuevo), tests de
      `evaluar_artefacto()` sobre `dict`s sintéticos con la forma exacta
      de `artefacto_a_dict` (data-model.md): (a) mediana de `emparejadas`
      mayor a `-8.0` → `Veredicto.aprobado is True`; (b) mediana
      exactamente `-8.0` → `aprobado is True` (límite inclusive, spec.md
      US1 AS3); (c) mediana menor a `-8.0` → `aprobado is False`; (d) en
      los tres casos, `Veredicto.presupuesto == -8.0` y
      `Veredicto.fraccion_sin_pareja` calculada correctamente sobre
      `total_sin_pareja / (total_emparejadas + total_sin_pareja)`
      (spec.md US1 AS1/AS2/AS4) — usar `reportes` con más de un tema para
      confirmar que el pool se acumula sobre todos, no solo el primero;
      (e) un artefacto con `modelo.firma` arbitraria/no reconocida (por
      ejemplo `"firma-inventada"`) y una mediana que aprobaría con
      cualquier firma → `Veredicto.aprobado is True` igual, sin ningún
      rechazo por firma (C2 de `/speckit-analyze`, spec.md US3 AS3): hoy
      es cierto porque `evaluar_artefacto` no tiene ningún código de
      comparación de firma (research.md #6) — este caso es la guarda que
      falla el día que alguien agregue esa comparación sin querer romper
      el propósito de la feature ("si alguien cambia el modelo... la
      compuerta dice si empeoró").
- [X] T003 [P] [US1] En `tests/unit/test_compuerta_mediana_equivalencia.py`
      (nuevo), property test (Hypothesis) que genera pools arbitrarios de
      valores finitos y `+inf` (nunca `-inf` — `st.floats(allow_nan=False,
      allow_infinity=False) | st.just(float("inf"))`, research.md #3) y
      verifica que `statistics.median(pool)` coincide exactamente con una
      reimplementación local de la regla de estadístico de orden de
      `analytics.metrica_separacion._mediana_orden` (copiar la lógica de
      esa función privada dentro del test, no importarla — el test fija
      la propiedad matemática, no crea una dependencia). Incluir además
      el caso concreto `[float("inf"), float("-inf")]` marcado para
      demostrar que la propiedad es genuinamente falsa fuera del dominio
      restringido (`pytest.mark.xfail` o un test aparte que confirma la
      divergencia) — evidencia de que la verificación no es vacía
      (research.md #3, verificado ya de forma exploratoria antes de este
      plan).

### Implementation for User Story 1

- [X] T004 [US1] Implementar `evaluar_artefacto(datos: dict[str, Any]) ->
      Veredicto` en `compuerta.py` (contracts/compuerta.md postcondiciones
      3/4/5): recorrer `datos["reportes"]`, acumular `si_sdr` de cada
      `emparejadas` en un pool y contar `len(sin_pareja)` por tema;
      `mediana_emparejadas = statistics.median(pool)`;
      `aprobado = mediana_emparejadas >= PRESUPUESTO_SI_SDR_DB`;
      `fraccion_sin_pareja = total_sin_pareja / (total_emparejadas +
      total_sin_pareja)`; copiar `modelo_nombre/variante/firma` de
      `datos["modelo"]` y `modo`/`semilla` de `datos` tal cual, sin
      compararlos contra nada (research.md #6). Depende de T001-T003;
      debe hacer pasar ambos tests sin modificarlos.

**Checkpoint**: User Story 1 funciona de punta a punta contra artefactos sintéticos bien formados.

---

## Phase 4: User Story 2 - Fallar de forma cerrada ante un artefacto ausente o inválido (Priority: P2)

**Goal**: Ausencia de artefacto, contenido no interpretable, o evidencia
insuficiente para calcular la mediana de emparejadas, siempre terminan en
`ArtefactoInvalidoError` — nunca en una aprobación ni en una excepción no
controlada.

**Independent Test**: Invocar `evaluar_artefacto()` con `dict`s
incompletos y `leer_artefacto()` contra una ruta ausente y un archivo con
contenido no interpretable sobre `tmp_path`, verificando que las cinco
condiciones (FR-004, FR-005, FR-006) levantan la misma excepción con un
mensaje que identifica cuál fue.

### Tests for User Story 2 ⚠️

> **NOTE: Escribir estos tests PRIMERO, confirmar que fallan antes de implementar.**

- [X] T005 [P] [US2] En `tests/unit/test_compuerta.py`, tests de
      `evaluar_artefacto()` levantando `ArtefactoInvalidoError`: (a) `dict`
      sin la clave `reportes`; (b) `reportes == []` (conjunto vacío,
      spec.md Edge Cases); (c) `reportes` no vacío pero **todas** las
      entradas tienen `emparejadas == []` (100% sin pareja — el caso más
      angosto de research.md #5: `total_referencias > 0` pero el pool de
      la mediana está vacío); (d) `dict` **sin la clave `modelo`**
      (hallazgo C1 de `/speckit-analyze`: T004 lee `datos["modelo"]`,
      `datos["modo"]` y `datos["semilla"]` además de `reportes` — sin
      esta validación, un artefacto sin `modelo` levantaría un `KeyError`
      crudo en vez de `ArtefactoInvalidoError`, exactamente el modo de
      fallo que esta feature existe para cerrar). Cada caso verifica que
      el mensaje de la excepción identifica la condición (nunca un
      mensaje genérico), y que `statistics.median` nunca se invoca sobre
      una lista vacía sin control (ningún `StatisticsError` no atrapado).
- [X] T006 [P] [US2] En `tests/unit/test_compuerta_cli.py` (nuevo), tests
      de `leer_artefacto(ruta: Path) -> dict[str, Any]` sobre `tmp_path`:
      (a) ruta que no existe → `ArtefactoInvalidoError` con la ruta en el
      mensaje (FR-004); (b) archivo existente con contenido que no es
      JSON válido (p. ej. `"esto no es json"`) → `ArtefactoInvalidoError`
      con el problema de formato en el mensaje (FR-005).

### Implementation for User Story 2

- [X] T007 [US2] En `evaluar_artefacto()` (`compuerta.py`), agregar la
      validación de forma y de evidencia suficiente ANTES de calcular
      nada (contracts/compuerta.md postcondiciones 1/2): `KeyError`/forma
      inesperada en `datos["reportes"]` o en cualquier `emparejadas`/
      `sin_pareja` → `ArtefactoInvalidoError` identificando la clave;
      **también `datos["modelo"]`, `datos["modo"]` y `datos["semilla"]`
      (C1 de `/speckit-analyze`: T004 los lee para construir el
      `Veredicto`, así que la misma validación de forma debe cubrirlos —
      ninguna clave que `evaluar_artefacto` use puede quedar fuera de
      esta validación)**; pool de `si_sdr` vacío tras recorrer todos los
      `reportes` → `ArtefactoInvalidoError` con motivo "sin evidencia
      suficiente para juzgar" (research.md #5). Depende de T004 (T007
      modifica la misma función); debe hacer pasar T005 sin romper T002.
- [X] T008 [P] [US2] Implementar `leer_artefacto(ruta: Path) ->
      dict[str, Any]` en `compuerta.py` (contracts/compuerta.md,
      `main` postcondiciones 2/3): abre `ruta`, atrapa
      `FileNotFoundError` y `json.JSONDecodeError` por separado,
      relanzando ambos como `ArtefactoInvalidoError` con un mensaje
      distinto para cada uno. Depende de T001; debe hacer pasar T006.

**Checkpoint**: User Stories 1 y 2 funcionan juntas — ningún artefacto ausente o mal formado produce una aprobación ni una excepción no controlada.

---

## Phase 5: User Story 3 - Elegir qué artefacto juzgar entre los dos modos de la Feature 004 (Priority: P3)

**Goal**: Un CLI que permite indicar `--modo` explícitamente (sin
default), resuelve a `mediciones/<modo>.json`, aplica el mismo
presupuesto a cualquiera de los dos modos, y expone el resultado con
códigos de salida distinguibles.

**Independent Test**: Invocar `main()` sobre `tmp_path` con un solo
artefacto sintético presente a la vez (nunca los dos juntos, para
probar independencia real — C3 de `/speckit-analyze`), verificando que
cada invocación juzga el suyo con el mismo presupuesto sin que el otro
modo necesite existir, y que los tres códigos de salida (0/1/2) aparecen
en los casos correspondientes.

### Tests for User Story 3 ⚠️

> **NOTE: Escribir estos tests PRIMERO, confirmar que fallan antes de implementar.**

- [X] T009 [P] [US3] En `tests/unit/test_compuerta_cli.py`, tests de
      `main(argv)` con `monkeypatch` sobre la ruta base de `mediciones/`
      (o invocando sobre `tmp_path` con la ruta resuelta explícita,
      según convenga a la implementación): (a) sin `--modo`, o con un
      valor fuera de `{submuestra_hito1, conjunto_completo}` →
      `SystemExit` con código distinto de 0, mensaje de `argparse` sobre
      `--modo` (mismo patrón que `test_cli.py` de la Feature 004); (b)
      **corregido tras C3 de `/speckit-analyze` — cada sub-caso crea UN
      solo artefacto, nunca los dos, para probar independencia real, no
      solo que cada uno lee el suyo:** (b1) existe únicamente
      `mediciones/submuestra_hito1.json` (con una mediana que aprueba) →
      `main(["--modo", "submuestra_hito1"])` lo juzga correctamente sin
      que `conjunto_completo.json` exista en absoluto; (b2), simétrico,
      existe únicamente `mediciones/conjunto_completo.json` (con una
      mediana que rechaza) → `main(["--modo", "conjunto_completo"])` lo
      juzga correctamente sin que `submuestra_hito1.json` exista — y en
      ambos sub-casos el código aprobado/rechazado observado coincide con
      comparar la mediana del artefacto contra la misma constante
      `PRESUPUESTO_SI_SDR_DB`, confirmando que ninguno de los dos modos
      usa un presupuesto distinto (spec.md FR-008, US3 AS1/AS2); (c) los
      tres códigos de salida: `0` (aprobado), `1` (rechazado por
      presupuesto), `2` (artefacto ausente o inválido, reusando los casos
      de US2).

### Implementation for User Story 3

- [X] T010 [US3] Implementar `main(argv: list[str] | None = None) -> int`
      en `compuerta.py` (contracts/compuerta.md): `argparse` con
      `--modo` `choices=("submuestra_hito1", "conjunto_completo")`,
      `required=True`, sin `default`; resuelve
      `Path("mediciones") / f"{args.modo}.json"`; llama
      `leer_artefacto()` y `evaluar_artefacto()`; atrapa
      `ArtefactoInvalidoError` (imprime a `stderr`, devuelve `2`);
      imprime el veredicto completo a `stdout` y devuelve `0` si
      `aprobado` else `1`. Agregar el bloque `if __name__ == "__main__":
      sys.exit(main())`. Depende de T004, T007, T008; debe hacer pasar
      T009.

**Checkpoint**: Las tres user stories funcionan de forma independiente — el entregable de la feature está completo.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Integración con `just`/`gauntlet`, verificación de cierre,
y triage de mutación — mismo patrón de cierre que el Polish de la
Feature 004.

- [X] T011 [P] Agregar el recipe `compuerta modo` a `justfile` (mismo
      patrón que `medir modo root_dir` de la Feature 004): `uv run
      python -m guitar_tabs_analysis.medicion.compuerta --modo {{ modo }}`.
- [X] T012 [P] Agregar un paso nuevo en el recipe `gauntlet` de
      `justfile` (research.md #8): `uv run python -m
      guitar_tabs_analysis.medicion.compuerta --modo submuestra_hito1`
      después del paso de `pytest`. Si el veredicto es rechazo,
      `gauntlet` debe fallar con el mismo criterio de fallo cerrado que
      `ruff`/`mypy`/`lint-imports`/cobertura.
- [X] T013 Correr `just gauntlet` completo y confirmar verde, incluyendo
      el paso nuevo de T012 contra `mediciones/submuestra_hito1.json`
      (evidencia real: mediana `-6.95 dB` ≥ `-8.0 dB`, aprobado) y
      cobertura ≥90% con `compuerta.py` incluido. Actualizar
      `docs/progress.md` (límite de 40 líneas).
- [X] T014 Ejecutar manualmente la sección de `quickstart.md` de esta
      feature de punta a punta: `just compuerta submuestra_hito1` contra
      el artefacto real, y confirmar que el resultado impreso coincide
      con la evidencia ya registrada en la constitución (Principio VII,
      v1.5.0: mediana `-6.95 dB`, fracción sin pareja `70/110`).
- [X] T015 Correr `just mutation medicion.compuerta` y triar cada
      sobreviviente (equivalente/inalcanzable, documentado con `# pragma:
      no mutate` y una razón verificada; o gap real, cerrado fortaleciendo
      un test existente o agregando uno nuevo rojo-antes-que-verde) —
      mismo criterio "triage, no conteo" que la Feature 004 estableció.
      Esta feature no tiene ningún test `modelo_real` que excluir de la
      corrida de mutación (no invoca ningún modelo). Registrar el triage
      en este archivo.

  **Hallazgo sobre `# pragma: no mutate` en esta versión de `mutmut`,
  verificado no supuesto:** el propio código de `mutmut` instalado
  (`mutmut/__main__.py`) trae el comentario `# TODO: pragma no mutate
  should end up in 'skipped' category` -- confirmado empíricamente
  inspeccionando `mutants/src/.../compuerta.py`: una línea con `# pragma:
  no mutate` sigue generando su mutante con el contenido realmente
  mutado, y ese mutante sigue apareciendo como `survived`, nunca como
  `skipped`. El pragma en este proyecto es, en esta versión de la
  herramienta, documentación para quien lee el código, no un mecanismo
  que mutmut aplique para excluir generación -- el mismo patrón que ya
  se usó en `orquestador.py` (Feature 004, Polish) funciona por la misma
  razón: los sobrevivientes documentados se aceptan por triage humano
  registrado aquí, no porque la herramienta deje de generarlos.

  **Mutación (triage, no conteo)** -- primera corrida: 46 sobrevivientes
  sobre `medicion.compuerta` (0 sobre cualquier otro módulo, mutados por
  separado). Config de `modelo_real` verificada sin cambios antes de
  correr (N/A de todos modos: esta feature no tiene ningún test así).
  Triage:

  - **18 gaps reales, cerrados fortaleciendo tests existentes** (sin
    tests nuevos de producción):
    - `evaluar_artefacto` (12): ningún test comprobaba
      `modelo_nombre`/`modelo_variante`/`modo`/`semilla` del `Veredicto`
      (solo `modelo_firma`, del test de firma arbitraria) -- se agregó
      `test_veredicto_incluye_todo_el_contexto_del_artefacto_sin_alterarlo`.
      Los mensajes de `ArtefactoInvalidoError` ("falta la clave...",
      "sin evidencia suficiente...") no se comprobaban por contenido --
      se agregaron aserciones sobre la palabra diagnóstica de cada uno
      (`"reportes"`, `"evidencia"`, la clave faltante exacta) en
      `test_compuerta.py`, y sobre `.motivo` como atributo público
      además de `str(excinfo.value)`.
    - `leer_artefacto` (1): el mensaje de `json.JSONDecodeError` envuelto
      no se comprobaba por contenido -- se agregó una aserción sobre la
      ruta en `test_contenido_no_interpretable_es_invalido`.
    - `main` (5): nada comprobaba el `stdout` real que imprime el
      veredicto (contracts/compuerta.md, postcondición 4) -- se
      agregaron aserciones sobre el texto completo (incluida la fracción
      exacta `sin_pareja/total`, para distinguir `+` de `-` en el
      cálculo del total) en los dos tests de `main` con un solo
      artefacto presente, más un `.startswith("APROBADO -- "
      )`/`.startswith("RECHAZADO -- ")` para fijar la palabra exacta del
      veredicto (no solo que apareciera como substring, que un mutante
      de tipo `XXAPROBADOXX` seguiría conteniendo).
  - **28 equivalentes/cosméticos, documentados, no cerrados con más
    tests** (verificar su contenido exacto sería una prueba frágil que
    no protege ninguna decisión real -- mismo criterio que motivó no
    fijar el texto de ayuda de `argparse` en la Feature 004):
    - `_construir_parser` (22): mutaciones sobre el texto literal de
      `prog`/`description`/`help` de `argparse` -- pura documentación
      para quien invoca `--help`, no comportamiento. Lo que sí es
      comportamiento (`choices`, `required`, sin `default`) ya está
      cubierto por `SystemExit` en `test_compuerta_cli.py`. Documentado
      con `# pragma: no mutate` en cada línea de texto (advisorio, ver
      hallazgo de arriba) y un docstring explicando el criterio.
    - `evaluar_artefacto` (6): variantes de mayúscula/minúscula y de
      "vaciado" (`XX...XX`) sobre la prosa del mensaje "sin evidencia
      suficiente..." que NO tocan la palabra diagnóstica `"evidencia"`
      ya afirmada (por ejemplo, cambiar "en el artefacto (ni
      referencias..." a mayúsculas). Fijar el contenido exacto de toda
      la prosa, palabra por palabra, sería sobre-ajustar el test al
      texto en vez de a la condición que señaliza -- ya cubierta.

  Re-verificado tras el fix: `just mutation medicion.compuerta` vuelve a
  dar exactamente 28 sobrevivientes, los documentados arriba como
  equivalentes -- los 18 gaps reales quedaron cerrados. `just gauntlet`
  sigue verde (168 tests, 98.69%, `compuerta.py` 99% -- la única línea
  sin cubrir es el `if __name__ == "__main__":` final, mismo patrón no
  cubierto que el resto de los CLI del proyecto).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin tareas — no bloquea nada.
- **Foundational (Phase 2)**: T001 bloquea las tres user stories (los
  tests de todas necesitan `Veredicto`/`ArtefactoInvalidoError` para
  poder siquiera importarse).
- **User Stories (Phase 3-5)**: Todas dependen de Foundational. US1 no
  depende de US2 ni de US3. US2 modifica la misma función que US1
  implementó (T007 extiende T004) — no es una dependencia de bloqueo de
  fase, pero sí de archivo: T007 debe correr después de T004. US3
  depende de que T004/T007/T008 ya existan (US3 es la primera que ensambla
  todo en un CLI) — es la única de las tres que no es plenamente
  independiente de las otras dos, porque su entregable (`main()`) integra
  el trabajo de US1 y US2 en vez de agregar lógica nueva de juicio.
- **Polish (Phase 6)**: Depende de que las tres user stories estén completas.

### Parallel Opportunities

- T002 y T003 (tests de US1) en paralelo — archivos distintos.
- T005 y T006 (tests de US2) en paralelo — archivos distintos.
- T008 puede correr en paralelo con T007 — mismo archivo pero funciones
  distintas sin dependencia entre sí (ninguna llama a la otra todavía).
- T011 y T012 (justfile) en paralelo con T013 solo después de que ambos
  terminen — T013 los verifica a los dos.

---

## Parallel Example: User Story 1

```bash
Task: "En tests/unit/test_compuerta.py, tests de evaluar_artefacto() sobre dict's sintéticos: presupuesto alcanzado/no alcanzado/límite exacto"
Task: "En tests/unit/test_compuerta_mediana_equivalencia.py, property test de equivalencia de mediana"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 2: Foundational (T001).
2. Completar Phase 3: User Story 1 (T002-T004).
3. **DETENERSE Y VALIDAR**: `evaluar_artefacto()` juzga correctamente un
   artefacto bien formado contra el presupuesto.

### Incremental Delivery

1. Foundational → User Story 1 (MVP: juzga artefactos bien formados).
2. + User Story 2 → nunca aprueba por evidencia ausente o incompleta.
3. + User Story 3 → CLI real, entregable completo de la feature.
4. Polish → integrado a `just gauntlet`, mutación triada, cierre.

## Hallazgos de `/speckit-analyze` no implementados (C4, C5)

Cerrados como decisión explícita, no como tarea pendiente:

- **C4 (SC-001, <1s)**: no se agrega una aserción de tiempo dentro de un
  test. Un límite de reloj de pared dentro de un test unitario falla por
  carga de la máquina que corre el guantelete (CI compartido, otro
  proceso pesado en la misma sesión), no por una regresión real de esta
  feature — el mismo tipo de test frágil que el proyecto ya evita en
  otras features (research.md de la Feature 003 nunca puso un límite de
  reloj dentro de un test, solo como referencia operativa documentada).
  SC-001 queda respaldado por el argumento estructural ya escrito en
  plan.md (Performance Goals: sin I/O de audio, sin modelo, un `dict` de
  ~30 KB) y por la observación manual de T014, no por una aserción
  automatizada.
- **C5 (research.md #4, `exclusiones` nunca contribuye)**: no se agrega
  como tarea propia. Es, a lo sumo, una línea dentro de un test ya
  existente (agregar un `dict` con `exclusiones` no vacías a uno de los
  casos de T002 y confirmar que `fraccion_sin_pareja`/`mediana_emparejadas`
  no cambian) — no justifica una tarea nueva ni un archivo nuevo. Queda
  como mejora opcional a criterio de quien implemente T002, no como
  bloqueante de esta feature.

## Notas de triage de mutación (T015)

Ver el detalle completo bajo la propia tarea T015, arriba.
