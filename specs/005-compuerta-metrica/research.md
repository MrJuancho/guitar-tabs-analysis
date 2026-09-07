# Research: Compuerta de la métrica

## 1. Fuente de verdad del artefacto: JSON crudo, no `medicion.orquestador`

**Decisión:** `compuerta.py` lee el artefacto con `json.load` y extrae
directamente las claves que necesita (`modelo`, `modo`, `semilla`,
`reportes[].emparejadas[].si_sdr`, `reportes[].sin_pareja`). No importa
`medicion.orquestador` ni reconstruye un `ArtefactoMedicion` completo.

**Rationale:** `orquestador.py` no expone ningún `artefacto_desde_dict`
público -- solo `artefacto_a_dict` (dirección de escritura, T019 de la
Feature 004). Las funciones de deserialización que sí existen
(`_reporte_desde_dict`, `_resultado_procesamiento_desde_dict`) son
privadas (prefijo `_`), pensadas para el round-trip interno del progreso
persistido por tema, no para reuso externo. Reconstruir tipos completos
de dominio (`ReporteTema`, `ArtefactoMedicion`) para leer cuatro valores
sería acoplar esta feature a la implementación interna de la Feature 004
en vez de a su contrato (`specs/004-medicion-linea-base/data-model.md`,
`contracts/medicion.md`) -- el mismo motivo por el que FR-001 exige que
todo valor del veredicto venga del propio artefacto, no de recalcularlo.

**Alternativas consideradas:**
- Hacer pública una función `artefacto_desde_dict` en `orquestador.py` y
  reusarla -- descartada: obligaría a la Feature 004 a exponer un
  contrato de deserialización completo que hoy no necesita (nunca lee su
  propio artefacto final de vuelta, solo el progreso por tema), solo
  para que esta feature use una fracción de los campos.
- Importar `separacion.separador.ModeloDeclarado` para tipar la
  información de modelo del veredicto -- descartada: arrastra `numpy` y
  `scipy.signal.resample` transitivamente (`separador.py` los importa)
  para una feature cuyo requisito explícito es no depender de la pila de
  separación. El veredicto lleva el sub-`dict` `modelo` del artefacto tal
  cual, sin reconstruir ningún tipo de dominio.

## 2. Ubicación del módulo: `medicion/compuerta.py`, no `quality/gates.py`

**Decisión:** Nuevo módulo `src/guitar_tabs_analysis/medicion/compuerta.py`
(lógica + `main()` en un único archivo, como `quality/gates.py`, sin
necesidad de separar CLI de lógica porque no hay ninguna dependencia
pesada que aislar -- a diferencia de `medicion/orquestador.py`/`cli.py`,
que sí separan por el import de `torch`/`demucs`).

**Rationale:** `quality/gates.py` es, por su propio docstring, "un
esqueleto FUNCIONAL con UN gate de ejemplo... no una lista real de
compuertas" para un dominio genérico distinto (una tabla `pandas`
curada, gates de tipo "valor <= máximo"). Esta compuerta tiene forma
distinta en los tres ejes que importan: (a) lee JSON, no una tabla
`pandas`/Parquet -- no hace falta la dependencia de `pandas` en absoluto;
(b) el presupuesto es un MÍNIMO ("mediana >= −8.0 dB"), no un máximo
como todo lo que `GOLD_GATES`/`ResultadoGate.aprueba` asumen hoy; (c) el
veredicto lleva un dato obligatorio adicional (fracción sin pareja) que
el modelo `ResultadoGate` (nombre, valor, presupuesto) no contempla.
Forzar esta compuerta dentro de esa abstracción exigiría invertirle el
sentido de la comparación y añadirle un campo -- cambiar un contrato ya
usado por `data-auditor` (`.claude/agents/data-auditor.md`, que interpreta
`GOLD_GATES` contra `docs/adr/`) para un caso que no comparte ni el
formato de entrada ni la forma del resultado. Vive junto a
`orquestador.py`/`cli.py` porque juzga exactamente lo que esos módulos
producen, igual que `medicion` ya agrupa todo lo relativo a la medición
del hito 1.

**Alternativas consideradas:**
- Reemplazar `GOLD_GATES`/`evaluar_gates` en `quality/gates.py` siguiendo
  su propio docstring ("reemplaza por los presupuestos reales de tu
  dominio") -- descartada por las tres diferencias de forma de arriba.
  `quality/gates.py` queda tal cual, disponible para cuando el proyecto
  tenga un pipeline tabular real que sí calce con ese modelo.
- Paquete nuevo de nivel superior (`compuerta/`) -- descartada: es una
  sola función de juicio sobre un solo tipo de artefacto, no justifica
  una capa propia: `medicion` ya es el lugar natural.

## 3. Mediana de referencias emparejadas: `statistics.median`, no `_mediana_orden`

**Decisión:** La mediana de emparejadas se calcula con `statistics.median`
de la biblioteca estándar sobre el pool de valores `si_sdr` de
`reportes[].emparejadas`, sin mezclar los sentinelas `-inf` de
`sin_pareja` (a diferencia de `mediana` en el artefacto, que sí los
incluye -- Principio VII de la constitución, v1.5.0: el presupuesto se
fija sobre la mediana de emparejadas, nunca sobre la global).

**Rationale, verificado no supuesto:** `analytics.metrica_separacion._mediana_orden`
(privada) implementa una mediana de estadístico de orden con una regla
pesimista específica: cuando el promedio de los dos valores centrales de
un pool de tamaño par sería `NaN` (el único caso posible en IEEE754 es
promediar `+inf` con `-inf`), resuelve al valor más bajo de los dos en
vez de propagar `NaN` (hallado por Hypothesis en la Feature 002,
T027/2026-09-04). Esa divergencia de `statistics.median` **requiere que
el pool contenga simultáneamente `+inf` y `-inf`** -- y el pool de
referencias *emparejadas* nunca contiene `-inf`: ese sentinela es
exclusivo de `sin_pareja` (Feature 002, FR-008), nunca se asigna a una
referencia con pareja. Una referencia emparejada sí puede ser `+inf`
(Principio VII: estimación idéntica a la referencia), pero
`(+inf + finito) / 2 = +inf` y `(+inf + +inf) / 2 = +inf` -- ninguna
combinación posible dentro de un pool sin `-inf` produce `NaN`. Por lo
tanto, sobre el dominio restringido de esta feature (solo valores de
`emparejadas`, nunca sin_pareja), `statistics.median` y `_mediana_orden`
son equivalentes por construcción -- se fija con un property test
(Hypothesis) que lo verifica sobre pools arbitrarios de valores finitos
y `+inf` (nunca `-inf`), mismo patrón que la Feature 004 usó para su
propia prueba de equivalencia incremental/bloque.

**Consecuencia de diseño:** esto es lo que hace seguro usar
`statistics.median` (`stdlib`, sin duplicar ni exponer la función
privada de la Feature 002) en vez de necesitar acceso a
`_mediana_orden`.

**Alternativas consideradas:**
- Hacer pública `_mediana_orden` y reusarla -- descartada: innecesaria
  una vez verificada la equivalencia sobre este dominio restringido; e
  introduciría una dependencia de esta feature sobre un detalle interno
  de `analytics.metrica_separacion` para un cálculo que la biblioteca
  estándar ya resuelve igual en este caso.
- Reimplementar la regla pesimista de `_mediana_orden` de todos modos,
  "por si acaso" -- descartada: código muerto verificable como
  inalcanzable en este dominio (mismo criterio que la rama de `modo`
  inválido eliminada en la Feature 004, Polish/T031) -- cubrirla exigiría
  fabricar un pool de *emparejadas* con un `-inf`, que el propio contrato
  de datos de la Feature 002 no permite.

## 4. Denominador de la fracción sin pareja: solo `reportes`, nunca `exclusiones`

**Decisión:** `fracción sin pareja = total_sin_pareja / (total_emparejadas + total_sin_pareja)`,
sumando ambos conteos únicamente sobre `artefacto["reportes"]`. Los temas
en `artefacto["exclusiones"]` (fallo de procesamiento o sin guitarra de
referencia) no aportan ningún valor al numerador ni al denominador.

**Rationale:** no es una elección de diseño sino una consecuencia directa
de qué guarda el artefacto. `ExclusionMedicion` (`specs/004-medicion-linea-base/data-model.md`)
tiene exactamente tres campos -- `tema_id`, `motivo`, `detalle` -- ninguno
registra cuántas referencias de guitarra tenía ese tema. Un tema excluido
por `sin_guitarra_referencia` sí tenía cero referencias por definición
(no cambiaría el resultado si se pudiera incluir), pero un tema excluido
por `fallo_procesamiento` (Feature 001/003) pudo fallar en la lectura
misma, antes de que el sistema supiera cuántas pistas de guitarra tenía
-- ese número simplemente no existe en ningún lado del artefacto. No hay
una segunda fuente de la que inferirlo sin violar FR-001 (todo valor
sale del propio artefacto, nunca se recalcula).

## 5. Corrección de alcance sobre FR-006: "sin evidencia" es sobre emparejadas vacías, no solo sobre el total

**Hallazgo de planificación:** `spec.md` FR-006 dice "incluyendo el caso
de un conjunto de referencias vacío" pensando en el caso obvio (cero
referencias en total). Mientras se diseñaba el cálculo de la mediana
(#3 arriba) apareció un caso más angosto que el mismo texto ya cubre en
espíritu pero no en la letra: un artefacto puede tener `total_referencias
> 0` (por ejemplo, todas con motivo `sin_estimacion_disponible`) y aun
así tener el pool de **emparejadas** vacío -- `statistics.median([])`
levanta `StatisticsError` en ese caso exacto, sin importar cuántas
referencias sin pareja existan. Se interpreta FR-006 como aplicable a
"el pool de referencias *emparejadas* está vacío", que incluye tanto el
caso de cero referencias totales como este caso más angosto -- ambos son
la misma condición real ("no hay ningún valor de SI-SDR contra el cual
comparar el presupuesto") y ambos se resuelven igual: rechazo explícito,
nunca una excepción no controlada ni una aprobación por ausencia de
evidencia en contra.

## 6. Comparación de firma de modelo: reporta, no compara (confirma spec.md Assumptions)

**Decisión (ya fijada en `spec.md`, confirmada aquí sin cambios tras
revisar si una comparación estática contra un valor de referencia sería
posible):** el veredicto reporta `modelo`/`modo`/`semilla` del artefacto
tal cual, sin compararlos contra ningún valor esperado -- ni siquiera
contra la firma `5c90dfd2` que la constitución registra como evidencia
del presupuesto (Principio VII, v1.5.0).

**Rationale, reconsiderado explícitamente:** una comparación estática
contra un valor "esperado" *sería* técnicamente posible sin invocar
ningún modelo (una constante de texto, no una llamada a `Separador`) --
así que el argumento de `spec.md` ("no hay una segunda fuente de verdad
accesible sin violar el alcance") no es, en rigor, la razón completa. La
razón real es de propósito, no de alcance técnico: el pedido original
declara explícitamente que el caso de uso central es "si alguien cambia
el modelo... la compuerta dice si empeoró" -- una compuerta que
rechazara (o incluso solo marcara con una advertencia distinta) un
artefacto por tener una firma distinta a la de referencia entraría en
conflicto directo con ese propósito declarado en el primer uso real que
tendría. `spec.md` ya deja este razonamiento correcto por el motivo
correcto; se corrige aquí la justificación, no la decisión.

## 7. Interfaz de línea de comandos

**Decisión:** `--modo {submuestra_hito1,conjunto_completo}`, sin
`default` (mismo patrón que `medicion.cli`, FR-004 de la Feature 004),
resuelto a `mediciones/<modo>.json` -- ninguna otra ruta es aceptada.

**Rationale:** FR-008 de esta feature solo exige poder indicar
explícitamente **cuál de los dos modos de la Feature 004** juzgar, no una
ruta arbitraria a cualquier archivo. Restringir a los dos nombres de modo
ya conocidos (en vez de aceptar una ruta libre) hace imposible por
construcción invocar la compuerta contra un archivo que no seguiría la
convención de nombres ya establecida por `medicion.cli`
(`mediciones/<modo>.json`), y mantiene el mismo vocabulario (`--modo`,
mismos dos valores) entre el comando que mide y el que juzga.

**Función núcleo testeable**, mismo patrón que `medicion.cli._ejecutar_y_escribir`:
`evaluar_artefacto(datos: dict[str, Any]) -> Veredicto` recibe el `dict`
ya parseado -- los tests construyen `dict`s sintéticos directamente, sin
tocar disco. `main(argv)` resuelve la ruta, hace `json.load`, atrapa
`FileNotFoundError`/`json.JSONDecodeError`/`KeyError` alrededor de la
lectura y de `evaluar_artefacto`, e imprime el veredicto.

**Códigos de salida** (más finos que el mínimo de FR-007, para que un
guantelete automatizado pueda distinguir programáticamente sin parsear
el mensaje, y no solo por texto): `0` aprobado, `1` presupuesto no
alcanzado, `2` artefacto ausente/ilegible/incompleto (FR-004/005/006).
FR-007 solo exige "distinto de aprobación" para cualquier rechazo; usar
dos códigos distintos de rechazo es una decisión de esta feature que no
contradice ese mínimo, lo excede.

## 8. Integración con `just gauntlet`

**Decisión:** se agrega como paso de `gauntlet` (no solo como recipe
independiente), evaluando por defecto `mediciones/submuestra_hito1.json`
-- si la compuerta falla, `just gauntlet` falla.

**Rationale:** el pedido dice "incorporable a gauntlet", y esta feature
existe precisamente para poder correr en cualquier momento sin costo
(SC-001: menos de un segundo, sin leer audio ni invocar modelo) --
absorbe el mismo criterio de fallo cerrado que `ruff`/`mypy`/`lint-imports`/
cobertura, que si fallan detienen `gauntlet` completo. Difiere del
precedente de `gates` (`quality/gates.py`, NO incluido en `gauntlet`)
porque la razón de esa exclusión no aplica aquí: el artefacto de `gates`
es un ejemplo sobre una ruta que no existe hasta correr un pipeline
propio del dominio tabular (`data/gold/ejemplo.parquet`, nunca versionado);
`mediciones/submuestra_hito1.json` ya está versionado en el repositorio
(commit `c1769f0`) y presente en cualquier checkout, así que incluir la
compuerta en `gauntlet` nunca falla por "artefacto ausente" en un clon
limpio -- solo cuando una medición real y su commit lo reemplacen con una
cifra peor.

**Alternativas consideradas:**
- Recipe `just compuerta-metrica` separada, sin tocar `gauntlet` --
  descartada: no cumple "incorporable a gauntlet" del pedido, y dejaría
  la detección de regresión fuera del único comando que de verdad se
  corre siempre.
