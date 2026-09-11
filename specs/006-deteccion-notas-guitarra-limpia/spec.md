# Feature Specification: Detección de notas sobre guitarra limpia

**Feature Branch**: `[006-deteccion-notas-guitarra-limpia]`

**Created**: 2026-09-07

**Status**: Draft

**Input**: User description: "Hito 2, Feature 001 — Detección de notas sobre guitarra limpia

Dado audio de guitarra sola, el sistema estima las notas que suenan —tono e
instante de inicio— y reporta qué tan bien lo hace contra anotaciones de
referencia.

ALCANCE

Audio limpio de GuitarSet, no la salida del separador del hito 1. Sin línea
base sobre audio limpio no hay contra qué comparar cuando llegue el audio
ruidoso, y ese paso es explícitamente posterior.

Detección de notas, NO digitación. Qué tono y cuándo, no en qué cuerda ni en
qué traste. La digitación y la restricción de la mano son el hito 3.

MODELO

Igual que el hito 1: línea base con modelo preentrenado, sin entrenar ni
afinar. /speckit-plan debe verificar contra la documentación actual qué
modelos de transcripción musical existen hoy, cuáles son específicos de
guitarra, y la licencia TANTO del código COMO de los pesos. La constitución
(Principio IV) exige licencia identificada; una fuente sin licencia clara no
es admisible. Recordar la asimetría que ya encontramos con Demucs: código MIT,
pesos con restricción propia.

QUÉ CUENTA COMO ACIERTO

Una nota acierta si su tono coincide dentro de una tolerancia declarada y su
inicio cae dentro de una ventana temporal declarada. La DURACIÓN se ignora en
este hito: acertar qué nota y cuándo empieza ya produce algo tocable, y la
duración es más difícil y menos útil para leer una tablatura. Queda registrada
como refinamiento posterior, no como omisión.

Los valores concretos de tolerancia y ventana los fija /speckit-plan contra
las convenciones establecidas en transcripción musical, no inventados.

MÉTRICA

Balance entre precisión y exhaustividad. Se reportan las tres cifras
—precisión, exhaustividad y su balance— porque tienen lecturas distintas: una
nota inventada estorba más que una faltante cuando se toca la tablatura, y el
reporte debe permitir ver esa asimetría aunque la cifra principal sea el
balance.

REPORTE SEPARADO POR POLIFONÍA

La métrica clasifica según cuántas notas suenan simultáneamente EN LA
ANOTACIÓN DE REFERENCIA, y reporta monofónico y polifónico por separado. El
detector no decide qué es un acorde: la clasificación viene de la verdad
conocida, no de una inferencia del sistema. Es la misma forma que el hito 1
usó con mono/poli.

PRESUPUESTO

Se fija DESPUÉS de la primera medición, no antes, con la evidencia observada.
Principio VII. Esta feature mide y reporta; la compuerta viene después.

FUERA DE ALCANCE

- NO entrena ni afina.
- NO produce tablatura ni digitación.
- NO transcribe sobre audio separado del hito 1.
- NO evalúa umbral."

## Clarifications

### Session 2026-09-07

- Q: Cuando el modelo de transcripción falla al procesar una grabación
  individual (un error real de inferencia, no la ausencia legítima de
  notas), ¿la medición debe excluir esa grabación con un motivo
  registrado y seguir con el resto, o debe abortar la corrida completa?
  → A: Excluir esa grabación con un motivo explícito registrado en el
  reporte, y seguir midiendo el resto -- mismo patrón que el hito 1
  (fallo duro por tema es terminal, no aborta la corrida).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Juzgar si una nota estimada acierta contra una de referencia (Priority: P1)

Dada una nota de referencia (tono, inicio) y una nota estimada por el
sistema (tono, inicio), se necesita determinar si la estimada acierta:
mismo tono dentro de una tolerancia declarada, e inicio dentro de una
ventana temporal declarada, sin considerar la duración de ninguna de las
dos.

**Why this priority**: Es el mecanismo de juicio del que depende todo lo
demás — sin una regla de acierto clara y verificable, ninguna cifra de
precisión o exhaustividad significa nada. Es viable como slice
independiente porque se puede fijar y probar por completo con notas
sintéticas (tono e inicio inventados), sin ningún modelo ni audio real
de por medio — mismo patrón que el mecanismo de emparejamiento de
referencias del hito 1.

**Independent Test**: Se puede probar por completo construyendo pares de
notas (referencia, estimada) con tonos e inicios elegidos a mano —
dentro de tolerancia en ambos ejes, fuera de tolerancia en el tono
solamente, fuera de tolerancia en el inicio solamente, exactamente en el
borde de cada tolerancia — y verificando el veredicto de acierto en cada
caso, sin invocar ningún modelo ni leer ningún archivo de audio.

**Acceptance Scenarios**:

1. **Given** una nota de referencia y una nota estimada con el mismo
   tono e inicios que difieren en menos que la ventana temporal
   declarada, **When** se evalúa el acierto, **Then** el sistema lo
   reporta como acierto.
2. **Given** dos notas cuyo tono difiere más que la tolerancia declarada
   (sin importar qué tan cerca esté el inicio), **When** se evalúa el
   acierto, **Then** el sistema lo reporta como desacierto.
3. **Given** dos notas con el mismo tono cuyo inicio difiere más que la
   ventana temporal declarada, **When** se evalúa el acierto, **Then**
   el sistema lo reporta como desacierto.
4. **Given** dos notas cuya duración difiere sustancialmente pero cuyo
   tono e inicio están ambos dentro de tolerancia, **When** se evalúa el
   acierto, **Then** el sistema lo reporta como acierto — la duración no
   participa del criterio.
5. **Given** un conjunto de varias notas de referencia y varias notas
   estimadas para la misma grabación, **When** se emparejan entre sí,
   **Then** cada nota estimada se acredita a lo sumo a una nota de
   referencia y viceversa — nunca una misma nota estimada cuenta como
   acierto de dos referencias distintas, ni una misma referencia se
   acredita dos veces.

---

### User Story 2 - Obtener las notas que un modelo preentrenado estima sobre una grabación (Priority: P2)

Dada una grabación de guitarra limpia de GuitarSet, se necesita que el
sistema invoque un modelo de transcripción musical preentrenado y
obtenga la lista de notas que estima — tono e inicio de cada una —, sin
entrenar ni afinar ese modelo.

**Why this priority**: Sin esto, User Story 1 no tiene ninguna nota real
que juzgar — sigue siendo necesario para que la feature mida algo, pero
el mecanismo de juicio (User Story 1) es lo primero que hay que fijar
porque todo lo demás depende de que sea correcto. Depende de que
`/speckit-plan` ya haya identificado un modelo admisible (código y pesos
con licencia identificada, Principio IV) antes de poder implementarse.

**Independent Test**: Se puede probar por completo invocando el modelo
declarado sobre una grabación corta de GuitarSet y verificando que el
resultado es una lista de notas (tono, inicio) sin ninguna excepción no
controlada — análogo al test `modelo_real` que el hito 1 ya estableció
para el separador de guitarra.

**Acceptance Scenarios**:

1. **Given** una grabación de guitarra limpia de GuitarSet, **When** se
   invoca el modelo declarado, **Then** el sistema obtiene una lista de
   notas estimadas, cada una con su tono y su instante de inicio.
2. **Given** el mismo modelo, **When** se invoca sobre dos grabaciones
   distintas, **Then** ningún estado de una invocación contamina a la
   otra — dos invocaciones independientes sobre la misma grabación
   producen el mismo resultado.
3. **Given** una grabación sin ninguna nota audible (silencio), **When**
   se invoca el modelo, **Then** el sistema acepta una lista de notas
   estimadas vacía como resultado válido, no como un error.
4. **Given** una grabación sobre la que el modelo falla al inferir (un
   error real, no la ausencia legítima de notas), **When** ocurre ese
   fallo, **Then** el sistema registra esa grabación como excluida con
   un motivo explícito, sin detener el procesamiento del resto de las
   grabaciones del conjunto (Clarifications, sesión 2026-09-07 -- mismo
   patrón que el fallo duro por tema del hito 1).

---

### User Story 3 - Medir el sistema sobre un conjunto de grabaciones y reportar por polifonía (Priority: P3)

Dado un conjunto de grabaciones de GuitarSet con sus anotaciones de
referencia, se necesita que el sistema agregue el resultado de juzgar
cada nota (User Story 1) sobre las notas que el modelo estima para cada
grabación (User Story 2), y reporte precisión, exhaustividad y su
balance — separado entre las notas de referencia monofónicas y las
polifónicas, además de la cifra global.

**Why this priority**: Es el entregable de la feature — las dos
historias anteriores son mecanismo, esta es el resultado medible que
importa para decidir si esta línea base sirve. Depende de que User
Story 1 y 2 ya funcionen: agrega su resultado, no redefine cómo se
juzga una nota ni cómo se obtienen las estimadas.

**Independent Test**: Se puede probar por completo con notas de
referencia y estimadas construidas a mano sobre varias grabaciones
sintéticas (algunas con pasajes monofónicos, otras con acordes),
verificando que las cifras de precisión, exhaustividad y balance
reportadas coinciden con el cálculo esperado a mano, tanto en el
subconjunto monofónico como en el polifónico.

**Acceptance Scenarios**:

1. **Given** el resultado de juzgar todas las notas estimadas contra
   todas las de referencia sobre un conjunto de grabaciones, **When** se
   agrega, **Then** el sistema reporta precisión, exhaustividad y su
   balance (medida F) tanto de forma global como separadas para el
   subconjunto de notas de referencia monofónicas y el polifónico.
2. **Given** una nota de referencia, **When** se determina si es
   monofónica o polifónica, **Then** esa clasificación depende
   exclusivamente de cuántas notas suenan simultáneamente en la
   anotación de referencia en ese instante — nunca de cuántas notas
   detectó el sistema.
3. **Given** un conjunto de grabaciones cuyas notas de referencia son
   todas monofónicas (o todas polifónicas), **When** se agrega el
   resultado, **Then** el subconjunto vacío se reporta explícitamente
   como tal (sin datos), nunca como una cifra calculada sobre cero casos
   ni omitida en silencio.
4. **Given** el reporte agregado, **When** se inspecciona sin volver a
   ejecutar nada, **Then** es posible determinar las tres cifras, su
   desglose por polifonía, y qué modelo y qué valores de tolerancia y
   ventana las produjeron — sin necesitar acceso a la corrida original.

---

### Edge Cases

- Más de una nota de referencia cae dentro de tolerancia y ventana de
  una misma nota estimada (o viceversa): el emparejamiento debe resolver
  esta ambigüedad con una asignación óptima uno a uno (mismo problema
  que el hito 1 ya resolvió al emparejar estimaciones de guitarra contra
  referencias, Feature 002), nunca acreditando la misma nota más de una
  vez ni dejando la asignación a un criterio arbitrario de "el primero
  que aparece".
- Una grabación cuya anotación de referencia no tiene ninguna nota
  (silencio total): la exhaustividad no tiene denominador — se excluye
  de ese cálculo con un motivo explícito, igual que el hito 1 ya
  resuelve el caso de un tema sin ninguna referencia de guitarra
  (Feature 002, FR-009), nunca como una división por cero silenciosa ni
  como un descarte sin registrar.
- El modelo estima notas sobre una grabación sin ninguna nota de
  referencia: esas notas estimadas nunca pueden acertar (no hay nada
  contra qué acertar), y cuentan en contra de la precisión igual que
  cualquier otra nota estimada sin pareja.
- Un modelo que no separa por polifonía en su propia predicción (una
  lista plana de notas estimadas, sin indicar qué notas forman un
  acorde): no importa para esta feature, porque la clasificación
  monofónico/polifónico se decide enteramente por la anotación de
  referencia (spec, "Reporte separado por polifonía"), nunca por lo que
  el modelo cree haber detectado.
- El modelo falla al procesar una grabación individual (un error real de
  inferencia, no la ausencia legítima de notas): esa grabación queda
  excluida con un motivo explícito, distinguible de "sin notas de
  referencia", y la medición continúa con el resto del conjunto sin
  abortar (Clarifications, sesión 2026-09-07) -- mismo criterio que el
  hito 1 ya estableció para un fallo duro por tema (Feature 004, FR-006):
  con un conjunto de ~360 grabaciones, abortar todo por una sola
  problemática descartaría el resto del cómputo ya válido.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dada una grabación de guitarra limpia de GuitarSet y su
  anotación de referencia, el sistema MUST obtener las notas que un
  modelo de transcripción musical preentrenado estima sobre esa
  grabación — tono e instante de inicio de cada una —, sin ejecutar
  ningún paso de entrenamiento ni de ajuste de parámetros del modelo
  (Principio I de la constitución).
- **FR-002**: El sistema MUST NOT usar como entrada la salida de
  separación de guitarra de las Features 003/004 (hito 1) ni ningún
  audio derivado de un separador — opera exclusivamente sobre
  grabaciones limpias de GuitarSet.
- **FR-003**: El sistema MUST determinar si una nota estimada acierta
  contra una nota de referencia mediante dos condiciones, ambas
  necesarias: el tono de ambas coincide dentro de una tolerancia
  declarada, y el instante de inicio de ambas coincide dentro de una
  ventana temporal declarada. Los valores concretos de tolerancia y
  ventana se fijan en `/speckit-plan` contra las convenciones ya
  establecidas en evaluación de transcripción musical, no se inventan
  en esta especificación.
- **FR-004**: El sistema MUST NOT considerar la duración de ninguna nota
  (estimada ni de referencia) al determinar si hay acierto. La duración
  correcta queda declarada como refinamiento futuro fuera de esta
  feature, no como una omisión sin registrar.
- **FR-005**: Al emparejar el conjunto de notas estimadas de una
  grabación contra el conjunto de notas de referencia de esa misma
  grabación, el sistema MUST asignar cada nota estimada a lo sumo a una
  nota de referencia y cada nota de referencia a lo sumo a una nota
  estimada, mediante una asignación óptima -- nunca acreditando la misma
  nota más de una vez ni resolviendo la ambigüedad con el primer
  candidato encontrado.
- **FR-006**: Para cada nota de referencia, el sistema MUST determinar
  si es monofónica o polifónica exclusivamente a partir de cuántas notas
  suenan simultáneamente en la anotación de referencia en ese instante —
  nunca a partir de las notas que el propio sistema estimó.
- **FR-007**: El sistema MUST calcular precisión, exhaustividad, y su
  balance (medida F) sobre el conjunto agregado de una o más
  grabaciones, tanto de forma global como separadas para el subconjunto
  de notas de referencia monofónicas y el subconjunto polifónico —
  nunca solo la cifra global ni solo el balance sin las otras dos.
- **FR-008**: Cuando el subconjunto monofónico o el polifónico de un
  conjunto de grabaciones queda vacío, el sistema MUST reportarlo
  explícitamente como sin datos para ese subconjunto, y MUST NOT
  calcular ni publicar una cifra derivada de un denominador cero.
- **FR-009**: El sistema MUST NOT definir ni evaluar ningún umbral de
  aprobación sobre ninguna de las cifras que produce; su responsabilidad
  termina en medir y reportar (Principio VII de la constitución,
  presupuesto fijado después de la primera medición, no antes).
- **FR-010**: El sistema MUST NOT ejecutar ningún paso de entrenamiento,
  ajuste, ni afinado de ningún modelo, en ningún punto de esta feature
  (Principio I de la constitución).
- **FR-011**: El reporte que produce esta feature MUST incluir
  suficiente información para interpretar las cifras sin volver a
  ejecutar nada: identificador del modelo usado, los valores de
  tolerancia de tono y de ventana temporal aplicados, la lista de
  grabaciones medidas, las exclusiones con su motivo (FR-012), y el
  desglose global/monofónico/polifónico de las tres cifras.
- **FR-012**: Cuando el modelo falla al procesar una grabación individual
  (Clarifications, sesión 2026-09-07), el sistema MUST registrar esa
  grabación como excluida con un motivo distinguible de "sin notas de
  referencia" (Edge Cases), MUST NOT abortar el resto de la medición por
  ese fallo individual, y MUST continuar con la siguiente grabación del
  conjunto -- mismo criterio que el hito 1 ya estableció para un fallo
  duro por tema (Feature 004, FR-006).
- **FR-013**: El emparejamiento (FR-005) MUST ocurrir siempre dentro de
  una única grabación -- una nota estimada MUST NOT poder acreditarse
  contra una nota de referencia de una grabación distinta, sin importar
  qué tan cerca caigan sus instantes de inicio. Al agregar sobre un
  conjunto de grabaciones (FR-007), el sistema MUST sumar los conteos ya
  resueltos por grabación (notas acertadas, número de referencias,
  número de estimadas) y derivar precisión/exhaustividad/balance de esa
  suma -- MUST NOT juntar las notas crudas de distintas grabaciones en
  un solo conjunto antes de emparejar. Es una propiedad de corrección de
  la métrica, no una optimización de rendimiento: dos grabaciones son
  clips independientes sin relación temporal entre sí, y emparejar entre
  ellas produciría aciertos espurios por coincidencia de reloj relativo
  -- inflando las cifras reportadas sin que reflejen nada real sobre la
  calidad de la detección. (Hallazgo de `/speckit-implement`,
  2026-09-09: la primera implementación de `agregar_conjunto` violaba
  esto -- pooleaba notas crudas de las 288 grabaciones antes de
  emparejar, lo que además demostró ser inviable en memoria, ver
  research.md #16.)
- **FR-014**: La clasificación monofónico/polifónico de una nota
  estimada que SÍ se acredita contra una nota de referencia (FR-005)
  MUST heredarse de esa nota de referencia -- MUST NOT determinarse
  evaluando el propio instante de inicio de la estimada por separado.
  El sistema MUST derivar el desglose mono/poli (FR-007) de un ÚNICO
  emparejamiento por grabación (FR-005), nunca de emparejamientos
  independientes recalculados dentro de cada subconjunto ya partido --
  es la misma propiedad que FR-013 exige entre grabaciones, aplicada
  ahora dentro de una sola: clasificar o agrupar antes de emparejar, en
  cualquiera de sus dos formas, produce aciertos que existen en el
  conjunto global y desaparecen de ambos subconjuntos parciales. Una
  nota estimada que NO se acredita contra ninguna referencia (un falso
  positivo) no tiene de qué heredar: para ese caso, y solo para ese
  caso, el sistema MUST clasificarla con la misma regla de FR-006
  evaluada en su propio instante de inicio contra las notas de
  referencia de la misma grabación (research.md #8) -- FR-007 exige la
  cifra de precisión completa en ambos subconjuntos, y una nota sin
  pareja MUST contar en el denominador de alguno de los dos, nunca
  quedar sin clasificar.
  (Hallazgo posterior a T035, sesión 2026-09-10: sobre
  `mediciones/deteccion_medibles.json`, la suma de verdaderos positivos
  de monofónico + polifónico (29682) era menor que el global (36995) --
  una diferencia de 7313, confirmada de forma independiente contando
  7329 pares del emparejamiento global cuya nota de referencia y su
  estimada acreditada clasificaban distinto. Causa: `evaluar_grabacion`
  reclasificaba y volvía a emparejar cada lado por separado dentro de
  cada subconjunto, en vez de derivar la partición del emparejamiento
  ya resuelto.)

### Key Entities

- **Grabación de guitarra limpia**: Un archivo de audio de GuitarSet con
  guitarra sola, sin mezcla con otros instrumentos, identificado de
  forma reproducible.
- **Nota de referencia**: Una nota anotada por GuitarSet sobre una
  grabación -- tono, instante de inicio, y su extensión temporal
  (necesaria para clasificar polifonía, aunque la duración no participe
  del criterio de acierto de FR-003/FR-004).
- **Nota estimada**: Una nota que el modelo declarado predice sobre una
  grabación -- tono e instante de inicio.
- **Acierto**: El resultado de juzgar una nota estimada contra una nota
  de referencia según FR-003/FR-004 -- verdadero o falso, nunca parcial.
- **Clasificación de polifonía**: Monofónica o polifónica, una propiedad
  de cada nota de referencia (FR-006), derivada de cuántas notas de
  referencia suenan simultáneamente con ella.
- **Exclusión**: Una grabación apartada de la medición con un motivo
  distinguible (FR-012) -- fallo de inferencia del modelo, a diferencia
  de una grabación sin ninguna nota de referencia (Edge Cases), que sí
  se mide, solo que su exhaustividad queda sin denominador.
- **Reporte agregado**: El resultado de esta feature sobre un conjunto
  de grabaciones -- precisión, exhaustividad y balance, global y por
  polifonía, las exclusiones con su motivo, junto con el modelo, la
  tolerancia y la ventana declaradas (FR-011).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dada cualquier grabación de guitarra limpia de GuitarSet
  con su anotación de referencia, el sistema produce precisión,
  exhaustividad y balance sin requerir ningún juicio manual de qué nota
  acierta contra cuál.
- **SC-002**: El 100% de los aciertos reportados cumplen simultáneamente
  el criterio de tono y el de inicio -- ninguno se reporta como acierto
  por cumplir solo uno de los dos. El 100% de los aciertos, además,
  emparejan una nota estimada con una de referencia de la MISMA
  grabación -- el 0% son aciertos entre grabaciones distintas (FR-013).
- **SC-003**: El 100% de las cifras reportadas (global, monofónica,
  polifónica) están acompañadas de cuántas notas de referencia se
  calcularon, y el 0% de los subconjuntos vacíos produce una cifra
  numérica en lugar de una marca explícita de "sin datos".
- **SC-004**: El 0% de las ejecuciones de esta feature modifica ningún
  parámetro del modelo declarado -- ninguna corrida entrena ni afina.
- **SC-005**: Dado el reporte agregado de cualquier corrida, es posible
  determinar el modelo, los valores de tolerancia y ventana, y las tres
  cifras con su desglose por polifonía, sin acceso a la corrida
  original ni a los datos crudos.
- **SC-006**: El 100% de los fallos de inferencia sobre una grabación
  individual aparecen en el reporte como exclusiones con un motivo
  distinguible, y el 0% de ellos detiene la medición antes de que se
  intenten todas las grabaciones restantes del conjunto.
- **SC-007**: Para cualquier conjunto de grabaciones medidas, la suma de
  verdaderos positivos del subconjunto monofónico y del polifónico es
  siempre exactamente igual al de la cifra global -- igual que la suma
  de referencias y la suma de estimadas de ambos subconjuntos ya lo son
  (FR-014). Ninguna corrida reporta una cifra global que sea mayor (ni
  menor) que ambas cifras parciales a la vez, cuando ambos subconjuntos
  tienen datos.

## Assumptions

- **Modelo:** qué modelo de transcripción musical preentrenado se usa,
  y la verificación de que su código y sus pesos tienen licencia
  identificada (Principio IV) según la documentación vigente al momento
  de planificar, se decide en `/speckit-plan` -- esta especificación
  fija el contrato (una lista de notas con tono e inicio), no el modelo
  concreto. Se espera la misma asimetría de licencias que Demucs en el
  hito 1 (código con una licencia, pesos con otra) hasta que se
  verifique lo contrario.
- **Fuente de audio:** GuitarSet ya está declarado admisible por el
  Principio IV de la constitución (CC BY 4.0, declarado desde la
  enmienda que cerró las fuentes del hito 2) -- esta feature no reabre
  esa decisión, solo la ejecuta.
- **Qué señal de audio de GuitarSet se usa:** GuitarSet distribuye tanto
  una mezcla monofónica de la guitarra completa como capturas separadas
  por cuerda (pastilla hexafónica). Esta feature usa la mezcla
  monofónica -- es la que corresponde a "audio de guitarra sola" tal
  como llegaría de una grabación real, sin acceso a señales
  por-cuerda que un sistema real no tendría. Verificar en `/plan` que el
  nombre exacto de ese subconjunto en la distribución de GuitarSet
  coincide con esta descripción.
- **Partición de desarrollo/evaluación dentro de GuitarSet -- actualizado
  tras la enmienda de constitución v1.7.0/v1.8.0:** esta Assumption
  originalmente argumentaba que GuitarSet no necesitaba ningún
  subconjunto reservado, porque el Principio VI (en su redacción
  específica del hito 1) protegía contra ajustar el sistema en base a un
  resultado ya visto, y esta feature no entrena, no afina, ni elige el
  modelo en base a qué tan bien le va contra GuitarSet. Esa lectura quedó
  obsoleta cuando la constitución generalizó el Principio VI (v1.7.0) a
  que **todo** hito reserva una porción intocable de su conjunto de
  evaluación -- con un propósito más amplio que solo la selección de
  modelo: confirmar, al cerrar el hito, que la cifra medida no fue
  sobreajuste al propio procedimiento de desarrollo. Esta feature fija
  esa instancia (v1.8.0, `/speckit-plan` revisado): **72 de las 360
  grabaciones de GuitarSet (20%) quedan reservadas**, muestreo aleatorio
  con semilla declarada `20260908`, protegidas por el mismo hook
  `PreToolUse` que ya cubre `tests/holdout/` -- ningún agente las
  inspecciona durante el desarrollo del hito 2, se usan una sola vez al
  cerrarlo (research.md #14, plan.md#Scale/Scope). Las 288 restantes
  siguen disponibles para medir sin restricción.
- **Balance = medida F (F1):** "balance entre precisión y exhaustividad"
  se interpreta como la media armónica de ambas (F1), la convención
  estándar en evaluación de transcripción musical, no un promedio simple
  ni una cifra inventada para esta feature.
- **Granularidad de la medición:** cada grabación de GuitarSet se mide
  completa (todas sus notas), no un recorte -- misma granularidad "por
  archivo" que el hito 1 usó "por tema".
- **Simultaneidad para clasificar polifonía (FR-006):** dos notas de
  referencia se consideran simultáneas si sus intervalos de inicio-fin
  se superponen en el tiempo. El criterio exacto de superposición
  (superposición parcial cuenta, umbral mínimo de superposición, etc.)
  se fija en `/plan` con la evidencia de las anotaciones reales de
  GuitarSet -- esta especificación fija que la fuente de la
  clasificación es la anotación de referencia, no el criterio exacto de
  solape.
