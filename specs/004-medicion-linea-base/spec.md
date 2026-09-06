# Feature Specification: Medición de la línea base

**Feature Branch**: `[004-medicion-linea-base]`

**Created**: 2026-09-05

**Status**: Draft

**Input**: User description: "Feature 004 — Medición de la línea base

Orquesta las Features 001, 002 y 003 para producir la medición del hito 1:
dado un conjunto de temas, lee cada uno, separa su guitarra con el modelo
preentrenado, calcula SI-SDR (Scale-Invariant Signal-to-Distortion Ratio)
contra las referencias, y emite un reporte agregado.

ENTREGABLE

Un comando reproducible que, dado un conjunto de temas, produce un artefacto
en disco con el reporte por tema y la agregación. El artefacto se versiona en
el repositorio: es pequeño, es la evidencia de la medición, y permite comparar
corridas sin volver a esperar 36 minutos.

El artefacto debe incluir todo lo necesario para interpretar la cifra sin
volver a correr: identificador del modelo y su firma, semilla de la
submuestra, lista de temas medidos, valores por referencia, agregación,
exclusiones con su motivo, distribución de referencias por tema, y las
transformaciones declaradas.

FUERA DE ALCANCE, EXPLÍCITAMENTE

- NO define ni evalúa umbral de aprobación. Esta feature mide y reporta. La
  compuerta es otra feature, y solo puede escribirse después de que el
  presupuesto se fije en la constitución con la evidencia que esta produce.
- NO entrena ni afina.
- NO toca el split `test`. Principio VI.

MODOS DE EJECUCIÓN

Dos, y la spec debe distinguirlos:
- Submuestra del hito 1: 40 temas de `validation`, semilla 20260904, ~36 min.
- Conjunto evaluable completo: 1710 temas, ~25.4 h. Debe ser invocable, no
  bloqueado — la submuestra existe para poder repetir la medición mientras se
  itera, no porque el conjunto completo sea inalcanzable.

El modo se elige explícitamente. Ninguno es un efecto lateral del otro.

RESTRICCIÓN DE MEMORIA

Los temas se procesan de a uno. Un tema son ~10.6M muestras en float32, y uno
con seis guitarras son siete arreglos de ~40 MB. Cargar los 40 temas
simultáneamente no cabe con holgura. El diseño retiene los reportes, no el
audio.

TESTS Y COSTO

Ningún test del guantelete puede tardar 36 minutos. La orquestación se
verifica con el Separador falso de la Feature 003 y unos pocos temas
sintéticos, en milisegundos. La corrida contra el modelo real es invocación
manual, siguiendo el mismo patrón del marcador `modelo_real` que la Feature
003 ya estableció, incluido el aviso visible de tests saltados.

CASOS A RESOLVER

- Qué ocurre si la corrida se interrumpe a mitad. Con 36 minutos, y sobre todo
  con 25 horas, perder todo el progreso por un fallo en el tema 39 es un
  problema real, no teórico.
- Si un tema individual falla (error de lectura, fallo de inferencia), ¿aborta
  la corrida o se registra como excluido y continúa? Las Features 001 y 003
  definen fallos duros por tema; falta decidir qué hace el orquestador con
  ellos."

## Clarifications

### Session 2026-09-05

- Q: Si el modelo declarado (Feature 003) cambia entre que una corrida se
  interrumpe y se reanuda, ¿qué debe hacer el sistema con los reportes ya
  persistidos de esa corrida? → A: El sistema detecta que la firma del
  modelo difiere de la registrada en el progreso persistido y falla con un
  mensaje claro, sin reanudar ni mezclar resultados de dos modelos
  distintos.
- Q: Cuando un tema falla duro (lectura o separación) durante una corrida,
  ¿ese tema queda marcado como terminado en el progreso persistido, o puede
  volver a intentarse en una reanudación posterior? → A: El fallo es
  terminal: el tema queda persistido como excluido, igual que un tema
  exitoso queda persistido como medido — ninguna reanudación futura lo
  vuelve a intentar.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir la submuestra del hito 1 y obtener el artefacto (Priority: P1)

Dado el modo "submuestra del hito 1" seleccionado explícitamente, se necesita
que el sistema procese, uno a la vez, los 40 temas declarados (lectura,
separación de guitarra, cálculo de SI-SDR contra las referencias), y al
terminar emita un único artefacto en disco con todo lo necesario para
interpretar la cifra sin volver a correr nada.

**Why this priority**: Es el entregable de la feature y la razón de ser del
hito 1: sin este artefacto no hay evidencia de medición que pueda entrar a la
constitución para cerrar el presupuesto del Principio VII. Es viable como
slice independiente porque las tres features que orquesta (001, 002, 003) ya
existen y están cerradas.

**Independent Test**: Se puede probar por completo invocando el modo
submuestra sobre un conjunto pequeño de temas sintéticos con el Separador
falso de la Feature 003 (sin modelo real ni red), y verificando que el
artefacto resultante contiene el modelo declarado y su firma, la semilla, la
lista exacta de temas procesados, los valores por referencia, la mediana
agregada, las exclusiones con su motivo, la distribución de referencias por
tema y las transformaciones declaradas.

**Acceptance Scenarios**:

1. **Given** el modo "submuestra del hito 1" y ningún progreso previo,
   **When** se invoca la medición, **Then** el sistema deriva los mismos 40
   identificadores de tema aplicando el procedimiento de muestreo declarado
   (semilla fija `20260904` sobre el split `validation`, research.md #9 de la
   Feature 003), sin requerir que nadie los enumere a mano.
2. **Given** la lista de temas del paso anterior, **When** la medición
   procesa cada tema, **Then** lo hace de a uno: lee su audio (Feature 001),
   obtiene las estimaciones de guitarra con el modelo declarado (Feature
   003), calcula el SI-SDR de cada referencia contra su estimación
   emparejada (Feature 002), y persiste el reporte de ese tema antes de
   empezar el siguiente.
3. **Given** que todos los temas de la submuestra terminaron de procesarse,
   **When** la corrida concluye, **Then** el sistema emite un único artefacto
   que incluye: el identificador del modelo declarado y su firma, la semilla
   de la submuestra, la lista exacta de temas medidos, los valores de SI-SDR
   por referencia, la mediana agregada, las exclusiones con su motivo, la
   distribución de referencias por tema, y las transformaciones declaradas
   aplicadas durante la corrida.
4. **Given** dos invocaciones del modo submuestra sobre el mismo conjunto de
   datos, **When** se comparan los temas que cada una procesó, **Then** son
   exactamente los mismos 40 identificadores en ambos casos.
5. **Given** el artefacto producido, **When** se inspecciona sin volver a
   correr nada, **Then** es posible determinar la cifra agregada, qué la
   respalda, y qué se excluyó y por qué, sin necesitar acceso a la corrida
   original ni a los datos crudos.

---

### User Story 2 - Reanudar una corrida interrumpida sin perder el progreso (Priority: P2)

Dada una corrida en curso que se interrumpe antes de terminar (por ejemplo,
el proceso se cae o la máquina se apaga), se necesita que reiniciar la misma
corrida continúe desde los temas que faltan, sin recalcular los que ya
quedaron medidos.

**Why this priority**: Con 36 minutos, y sobre todo con 25 horas, perder todo
el progreso por un fallo a mitad de camino es un costo real que desalienta
repetir la medición. Depende de que User Story 1 ya sepa procesar un tema y
persistir su reporte; añade la capacidad de detectar y saltar lo ya hecho.

**Independent Test**: Se puede probar por completo interrumpiendo
deliberadamente una corrida sintética (con el Separador falso) después de
procesar algunos temas, reinvocándola con los mismos parámetros, y
verificando que los temas ya medidos no se vuelven a procesar (por ejemplo,
contando cuántas veces se invoca el separador falso por tema) y que el
artefacto final es equivalente al de una corrida sin interrupciones sobre el
mismo conjunto.

**Acceptance Scenarios**:

1. **Given** una corrida que procesó y persistió el reporte de una parte de
   sus temas antes de interrumpirse, **When** se reinvoca con el mismo modo y
   los mismos parámetros, **Then** el sistema detecta qué temas ya tienen
   reporte persistido y no repite su lectura, separación ni cálculo de
   métrica para ninguno de ellos.
2. **Given** una corrida en la que un tema falló duro (lectura o separación)
   y quedó persistido como excluido antes de interrumpirse, **When** se
   reinvoca la corrida, **Then** el sistema no vuelve a intentar la lectura
   ni la separación de ese tema — lo mantiene excluido con el mismo motivo,
   igual que si hubiera sido un tema medido con éxito.
3. **Given** la misma corrida interrumpida y reanudada, **When** termina de
   procesar los temas restantes, **Then** el artefacto final contiene los
   mismos valores por referencia, la misma mediana agregada y las mismas
   exclusiones que hubiera producido una corrida idéntica sin ninguna
   interrupción.
4. **Given** una corrida que ya terminó por completo (todos sus temas tienen
   reporte persistido), **When** se reinvoca con los mismos parámetros,
   **Then** el sistema no vuelve a procesar ningún tema y produce el mismo
   artefacto ya disponible, en vez de recalcular la corrida completa desde
   cero.
5. **Given** una corrida interrumpida cuyo progreso persistido registra la
   firma de un modelo declarado, **When** se reinvoca para reanudarla pero el
   modelo declarado actual tiene una firma distinta, **Then** el sistema
   falla con un mensaje claro que identifica ambas firmas, sin reanudar la
   corrida ni mezclar reportes calculados con modelos distintos en el mismo
   artefacto.

---

### User Story 3 - Ejecutar la medición sobre el conjunto evaluable completo (Priority: P3)

Dado el modo "conjunto evaluable completo" seleccionado explícitamente, se
necesita que el sistema procese cada tema del conjunto evaluable (no solo la
submuestra del hito 1) con el mismo mecanismo de medición, para que una
corrida completa sea una opción real y no una promesa bloqueada por el
diseño.

**Why this priority**: La submuestra existe para iterar rápido, no porque el
conjunto completo sea inalcanzable; sin este modo, la feature dejaría sin
resolver la pregunta de cómo se produce, eventualmente, una medición sobre
todo lo que sí se puede medir. Depende de que User Stories 1 y 2 ya
funcionen, porque una corrida de horas es precisamente la que más necesita
poder reanudarse.

**Independent Test**: Se puede probar por completo invocando el modo
"conjunto evaluable completo" sobre un conjunto sintético pequeño que
sustituye al conjunto real (mismo mecanismo, distinta lista de temas), y
verificando que el sistema procesa exactamente los temas de esa lista — sin
aplicar el muestreo ni la semilla del modo submuestra — y que invocar un modo
no dispara ni bloquea al otro.

**Acceptance Scenarios**:

1. **Given** el modo "conjunto evaluable completo" seleccionado, **When** se
   invoca la medición, **Then** el sistema procesa todos los temas de los
   splits `train` y `validation`, excluyendo el directorio `omitted`
   (Feature 002, FR-010) y excluyendo por completo el split `test`
   (Principio VI de la constitución), sin aplicar ningún muestreo ni semilla.
2. **Given** ninguna selección de modo explícita, **When** se invoca la
   medición, **Then** el sistema falla con un mensaje claro en vez de
   ejecutar por defecto la submuestra o el conjunto completo.
3. **Given** una invocación del modo submuestra y otra del modo conjunto
   completo sobre el mismo conjunto de datos, **When** se ejecutan por
   separado, **Then** ninguna de las dos desencadena ni bloquea a la otra:
   comparten el mismo mecanismo de procesamiento por tema, pero cada una
   opera solo sobre su propia lista de temas.

---

### Edge Cases

- Un tema individual falla durante la lectura (Feature 001) o durante la
  separación (Feature 003) — un fallo duro, no la ausencia legítima de
  estimaciones. El sistema lo registra como excluido con un motivo
  distinguible ("fallo de procesamiento del tema"), distinto de "sin
  guitarra de referencia" (Feature 002, FR-009) y de "directorio `omitted`"
  (FR-010), y continúa con el siguiente tema. La corrida completa no se
  aborta por el fallo de un tema individual — con corridas de hasta 25
  horas, abortar todo por un solo tema malo descartaría horas de cómputo ya
  válido (cubierto por User Story 1 y 3, FR-006). Este fallo es terminal:
  queda persistido igual que un tema medido con éxito, así que ninguna
  reanudación posterior lo vuelve a intentar (cubierto por User Story 2,
  escenario 2, FR-006, FR-007, FR-008).
- Una corrida se interrumpe por una causa externa (proceso terminado, caída
  del sistema) en cualquier punto, incluso a mitad del procesamiento de un
  tema. El tema que estaba en curso en el momento de la interrupción no
  queda con reporte persistido, así que al reanudar se procesa de nuevo
  desde cero; ningún tema ya persistido se recalcula (cubierto por User
  Story 2).
- El conjunto evaluado por cualquiera de los dos modos puede quedar vacío
  tras las exclusiones (por ejemplo, si todos los temas de una lista de
  prueba fallan o no tienen guitarra de referencia); el sistema lo reporta
  explícitamente como conjunto vacío, siguiendo el mismo comportamiento ya
  definido por la Feature 002 (FR-014), sin señalar un error.
- "Conjunto evaluable completo" para esta feature (train + validation,
  excluyendo `omitted` y `test`: 1559 temas, ~23,1 horas extrapoladas según
  research.md #9 de la Feature 003) es distinto del número de 1710 temas que
  aparece en esa misma investigación para "conjunto evaluable" a nivel de
  dataset — ese número incluye el split `test` porque la Feature 002, al
  calcular la métrica, no razona sobre splits (solo excluye `omitted`). Esta
  feature sí razona sobre splits porque es la que decide qué temas entran a
  una corrida, y el split `test` es un conjunto reservado que ningún agente
  toca durante el desarrollo (Principio VI, bloqueado mecánicamente por el
  mismo hook que protege `tests/holdout/`).
- Un tema con el máximo de guitarras observado en la submuestra (6, research
  research.md #9 de la Feature 003) implica mantener en memoria, durante su
  procesamiento, la mezcla más las estimaciones y referencias de ese único
  tema (siete arreglos de audio de tamaño comparable); el sistema nunca
  mantiene en memoria el audio de más de un tema a la vez, sin importar
  cuántos temas tenga la corrida completa (cubierto por FR-005).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dado un modo de ejecución explícito ("submuestra del hito 1" o
  "conjunto evaluable completo") y ningún otro insumo manual, el sistema
  MUST determinar por sí mismo la lista completa de identificadores de tema a
  procesar para ese modo.
- **FR-002**: En el modo "submuestra del hito 1", el sistema MUST resolver
  siempre a los mismos 40 identificadores de tema: el resultado de aplicar el
  procedimiento de muestreo aleatorio ya declarado, con la semilla fija
  `20260904`, sobre la lista ordenada de temas del split `validation`
  (research.md #9 de la Feature 003 / Principio VII de la constitución) —
  sin depender de ningún estado externo para reproducirlo.
- **FR-003**: En el modo "conjunto evaluable completo", el sistema MUST
  procesar todos los temas de los splits `train` y `validation`, MUST
  excluir todo tema del directorio `omitted` (mismo criterio que Feature 002
  FR-010), y MUST excluir por completo todo tema del split `test` bajo
  cualquier circunstancia (Principio VI de la constitución: conjunto
  reservado que ningún agente inspecciona durante el desarrollo).
- **FR-004**: El sistema MUST NOT ejecutar ningún modo por defecto; una
  invocación sin un modo explícitamente seleccionado MUST fallar con un
  mensaje claro en vez de ejecutar silenciosamente la submuestra o el
  conjunto completo.
- **FR-005**: Para cada tema, en cualquiera de los dos modos, el sistema
  MUST: leer su audio (Feature 001), obtener sus estimaciones de guitarra
  con el modelo declarado (Feature 003), calcular el SI-SDR de sus
  referencias contra las estimaciones emparejadas (Feature 002), persistir
  el reporte resultante de ese tema, y descartar de memoria el audio de ese
  tema (mezcla, referencias, estimaciones) antes de continuar con el
  siguiente — el sistema MUST NOT mantener en memoria el audio de más de un
  tema a la vez, sin importar el tamaño total de la corrida.
- **FR-006**: Cuando la lectura o la separación de un tema individual falla
  de forma dura (Features 001 y 003 ya definen estos fallos), el sistema
  MUST registrar ese tema como excluido con un motivo distinguible de "sin
  guitarra de referencia" (Feature 002 FR-009) y de "directorio `omitted`"
  (FR-010), MUST NOT abortar el resto de la corrida por ese fallo individual,
  y MUST continuar con el siguiente tema de la lista. Este fallo es
  terminal para ese tema dentro de la corrida (FR-007): ninguna reanudación
  posterior lo vuelve a intentar, siguiendo el mismo criterio de "no
  reintentar automáticamente" que la Feature 003 ya fija para un fallo de
  separación (FR-014 de 003).
- **FR-007**: El sistema MUST persistir el reporte de cada tema tan pronto
  como termina de procesarse, sea con éxito o con un fallo duro (FR-006), no
  solo al finalizar la corrida completa, de forma que una interrupción
  después del tema K deje disponibles de forma durable los reportes —
  exitosos o de exclusión por fallo — de los temas 1 a K.
- **FR-008**: Al (re)invocar una corrida con el mismo modo y los mismos
  parámetros de una corrida previa que no terminó, el sistema MUST detectar,
  por tema, si ya existe un reporte persistido para él — exitoso o excluido
  por fallo duro (FR-006, FR-007) —, MUST omitir reprocesarlo (relectura,
  reseparación, recálculo de métrica) en cualquiera de los dos casos, y MUST
  procesar únicamente los temas que todavía no tienen reporte persistido.
- **FR-008a**: El progreso persistido de una corrida MUST registrar la firma
  del modelo declarado (Feature 003) usada para calcularlo. Antes de
  reanudar, el sistema MUST comparar esa firma con la del modelo declarado
  vigente en el momento de la reinvocación; si difieren, el sistema MUST
  fallar con un mensaje claro que identifique ambas firmas, MUST NOT reanudar
  la corrida, y MUST NOT mezclar en ningún artefacto reportes calculados con
  modelos de firma distinta.
- **FR-009**: El artefacto final de una corrida que fue reanudada tras una
  interrupción MUST ser equivalente al artefacto de una corrida idéntica sin
  ninguna interrupción sobre el mismo conjunto de temas y el mismo modelo
  declarado: mismos valores por referencia, misma mediana agregada, mismas
  exclusiones.
- **FR-010**: Al completarse todos los temas de una corrida (en una sola
  pasada o a través de una o más reanudaciones), el sistema MUST emitir un
  único artefacto que incluya: el identificador del modelo declarado y su
  firma (Feature 003), el modo de ejecución usado y, cuando aplique, la
  semilla de la submuestra, la lista exacta de temas procesados, los valores
  de SI-SDR por referencia, la mediana agregada (Feature 002), todas las
  exclusiones con su motivo (incluyendo el motivo nuevo de FR-006), la
  distribución de referencias por tema, y las transformaciones declaradas
  aplicadas durante la corrida (Feature 003).
- **FR-011**: El artefacto de FR-010 MUST quedar en una forma adecuada para
  versionarse como archivo pequeño dentro del repositorio, de modo que los
  artefactos de dos corridas distintas MUST poder compararse entre sí sin
  volver a ejecutar ninguna de las dos.
- **FR-012**: El sistema MUST NOT definir ni evaluar ningún umbral de
  aprobación sobre la mediana agregada ni sobre ningún valor del artefacto;
  su responsabilidad termina en medir y reportar (Principio VII de la
  constitución, presupuesto todavía abierto).
- **FR-013**: El sistema MUST NOT ejecutar ningún paso de entrenamiento ni de
  ajuste de parámetros del modelo declarado (Principio I de la
  constitución).
- **FR-014**: El sistema MUST NOT leer, procesar, ni incluir en ningún
  artefacto ningún tema del split `test`, bajo ninguno de los dos modos de
  ejecución (Principio VI de la constitución).

### Key Entities

- **Corrida**: Una ejecución de la medición, identificada por su modo
  ("submuestra del hito 1" o "conjunto evaluable completo"), cuando aplica,
  la semilla usada para derivar su lista de temas, y la firma del modelo
  declarado (Feature 003) con la que se está calculando. Tiene un estado
  observable (en progreso o completa) determinado por cuántos de sus temas
  tienen ya un reporte persistido.
- **Progreso persistido**: El registro incremental, por tema, de que su
  reporte ya fue calculado y guardado, junto con la firma del modelo
  declarado usada para calcularlo. Es lo que permite, al reanudar una
  corrida, distinguir los temas que faltan de los que ya están listos sin
  volver a leer ni separar los ya hechos, y detectar si el modelo declarado
  cambió desde la interrupción (FR-008a).
- **Reporte por tema** (reutilizado de la Feature 002, con un motivo de
  exclusión adicional): el resultado del cálculo sobre un tema individual
  dentro de una corrida — sus valores de SI-SDR por referencia, sus
  referencias sin pareja con su motivo (incluyendo ahora "fallo de
  procesamiento del tema" cuando la lectura o la separación fallaron
  duro), y las transformaciones declaradas que se le aplicaron.
- **Artefacto de medición**: El documento final que una corrida completa
  produce: modelo declarado y su firma, modo y semilla (si aplica), lista
  exacta de temas procesados, reportes por tema, mediana agregada,
  exclusiones con motivo, distribución de referencias por tema, y
  transformaciones declaradas. Es lo único que hace falta para interpretar
  la cifra de una corrida sin volver a ejecutarla.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Invocar el modo "submuestra del hito 1" sin ningún progreso
  previo produce un artefacto completo tras procesar exactamente 40 temas, y
  resuelve a los mismos 40 identificadores en cualquier invocación posterior
  sobre el mismo conjunto de datos.
- **SC-002**: Una corrida interrumpida después de completar al menos un
  tema, al reanudarse, termina sin volver a procesar ningún tema cuyo
  reporte ya estuviera persistido antes de la interrupción — exitoso o
  excluido por fallo duro.
- **SC-003**: El artefacto de una corrida reanudada y el de una corrida
  equivalente sin interrupciones sobre el mismo conjunto de temas contienen
  los mismos valores por referencia y la misma mediana agregada.
- **SC-004**: El 100% de los fallos individuales de lectura o separación
  durante una corrida aparecen en el artefacto como exclusiones con un
  motivo distinguible, y el 0% de ellos detiene la corrida antes de que se
  intenten todos los temas restantes.
- **SC-005**: En ningún momento de una corrida el sistema mantiene en
  memoria el audio de más de un tema a la vez, sin importar cuántos temas
  tenga la corrida en total.
- **SC-006**: El modo "conjunto evaluable completo" procesa el 100% de los
  temas de `train` y `validation` excluyendo `omitted`, y el 0% de las
  corridas de cualquiera de los dos modos lee, procesa o incluye en su
  artefacto un tema del split `test`.
- **SC-007**: Dado cualquier artefacto producido por esta feature, se puede
  determinar sin volver a ejecutar nada: el modelo y su firma, la semilla
  (cuando aplica), la lista exacta de temas medidos, los valores por
  referencia, la mediana agregada, las exclusiones con su motivo, la
  distribución de referencias por tema, y las transformaciones aplicadas.
- **SC-008**: Ningún artefacto producido por esta feature incluye un umbral
  de aprobación ni un veredicto de pase/falla.
- **SC-009**: La suite de verificación de esta feature (excluyendo la
  invocación manual marcada como uso del modelo real) se ejecuta por
  completo en segundos, sin requerir en ningún caso una corrida de 36
  minutos ni de horas para pasar.
- **SC-010**: El 100% de los intentos de reanudar una corrida cuyo modelo
  declarado cambió desde la interrupción terminan en un fallo explícito que
  identifica ambas firmas, y 0% de esos intentos producen un artefacto que
  mezcle reportes calculados con modelos de firma distinta.

## Assumptions

- Esta feature es pura orquestación: reutiliza `leer_tema` (Feature 001),
  `separar_guitarra` con el modelo declarado (Feature 003), y el cálculo de
  SI-SDR y su agregación (Feature 002) tal como esas features ya los
  definen; no redefine ninguno de sus contratos.
- Los tests de esta feature usan el `SeparadorFalso` de la Feature 003 y
  unos pocos temas sintéticos, en milisegundos; la corrida contra el modelo
  real es una invocación manual, marcada con el mismo patrón `modelo_real`
  que la Feature 003 ya estableció (incluido el aviso visible de tests
  saltados en `tests/conftest.py`), no una corrida automática del guantelete.
- El mecanismo concreto de persistencia del progreso y del artefacto final
  (formato de archivo, ubicación exacta dentro del repositorio) se decide en
  `/speckit-plan`; esta spec solo fija que debe ser incremental por tema, y
  que el artefacto final debe ser un archivo pequeño versionable.
- Una interrupción se asume siempre externa (el proceso se termina, la
  máquina se apaga, un fallo del sistema operativo) — esta feature no ofrece
  un mecanismo para pausar una corrida deliberadamente; el mismo mecanismo
  de progreso persistido cubre ambos orígenes de interrupción por igual.
- El procedimiento y la semilla de muestreo de la submuestra del hito 1 ya
  están declarados y cerrados (research.md #9 de la Feature 003, Principio
  VII de la constitución); esta feature los ejecuta, no los redefine ni los
  vuelve a decidir.
- "Conjunto evaluable completo" para esta feature se define como train +
  validation, excluyendo `omitted` y `test` (1559 temas, ~23,1 horas
  extrapoladas según la propia tabla de research.md #9 de la Feature 003),
  distinto del número de 1710 temas que esa misma investigación usa para el
  concepto de "conjunto evaluable" a nivel de dataset (que no excluye
  `test` porque la Feature 002 no razona sobre splits); esta feature sí lo
  hace porque decide qué temas entran a una corrida, y el split `test` es un
  conjunto reservado por el Principio VI.
