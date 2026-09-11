# Feature Specification: Digitación con restricción de la mano

**Feature Branch**: `[007-digitacion-restriccion-mano]`

**Created**: 2026-09-11

**Status**: Draft

**Input**: User description: "Hito 3, Feature 007 — Digitación con restricción de la mano

Dada una secuencia de notas con tono e instante, el sistema asigna a cada una
una posición de cuerda y traste que produzca ese tono, minimizando un coste
de esfuerzo de la mano declarado explícitamente.

ENTRADA
Notas de referencia de GuitarSet (tono e instante), no la salida del hito 2.
Sin línea base sobre entrada limpia no hay contra qué comparar cuando llegue
la entrada ruidosa, y ese paso es posterior.

CORRECCIÓN POR CONSTRUCCIÓN
Toda posición asignada debe producir el tono pedido. Eso no es una métrica:
es una precondición que el sistema no puede violar. Si una nota no es
alcanzable en el instrumento, es un caso a resolver, no un error a tolerar.

MODELO DE COSTE — tres componentes independientes
- Estiramiento: dentro de un mismo instante, cuántos trastes abarcan las
  notas simultáneas. Hay un límite físico más allá del cual la posición es
  imposible, no solo cara.
- Desplazamiento: entre instantes consecutivos, cuánto se mueve la mano a lo
  largo del mástil.
- Cruce de cuerdas: cuánto recorre la mano a lo ancho. El ejemplo que lo
  motiva: traste 1 de la sexta seguido de traste 1 de la primera está a
  distancia horizontal cero pero cruza el mástil entero.

EL TIEMPO ENTRA AL COSTE
El mismo desplazamiento es cómodo con medio segundo de margen e imposible con
cincuenta milisegundos. Un coste que ignora el tiempo produce digitaciones
razonables sobre el papel e intocables en la práctica.

Los valores concretos de límites y ponderaciones los fija /speckit-plan, y se
declaran como parámetros del modelo, no como constantes enterradas.

DOS VERIFICACIONES DISTINTAS, no las mezcles
1. Optimalidad: sobre secuencias cortas, el resultado debe coincidir con el
   óptimo calculado por fuerza bruta. Es un test de corrección del algoritmo,
   no una métrica.
2. Validación del modelo de coste: sobre GuitarSet, comparar la digitación
   producida contra la que el guitarrista realmente usó (el dataset anota
   cuerda y traste). La métrica es la fracción de notas coincidentes.
   Medir "mi coste es bajo" sería circular: el algoritmo lo minimiza por
   construcción.

CONJUNTO RESERVADO
Las 72 grabaciones reservadas (semilla 20260908) siguen intocables. El
Principio VI aplica igual que en el hito 2.

PRESUPUESTO
Se fija después de la primera medición. Principio VII.

FUERA DE ALCANCE
- NO selecciona qué guitarra transcribir cuando hay varias. Eso es el hito 4.
- NO consume la salida del hito 2 todavía.
- NO produce el archivo de tablatura formateado. Asigna posiciones."

## Clarifications

### Session 2026-09-11

- Q: Cuando ninguna posición (o combinación, para un acorde) satisface
  exactamente la corrección tonal + el límite físico de estiramiento para
  un instante -- ya sea porque el tono de referencia es fraccionario
  (GuitarSet anota afinación real, no cuantizada a semitono, dato ya
  conocido del hito 2) o porque un acorde excede el estiramiento en toda
  combinación -- ¿qué hace el sistema?
  → A: La tolerancia de tono se declara como parámetro del modelo (como
  los pesos de coste), fijada en `/speckit-plan` con evidencia real de
  cuán común es la desafinación fraccionaria en GuitarSet -- mismo
  criterio que `TOLERANCIA_TONO_CENTS` del hito 2 y que Principio VII
  (fijar con evidencia, no a ciegas). Un acorde que excede el
  estiramiento incluso con tolerancia se excluye con motivo explícito.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Asignar una posición válida a un instante de notas simultáneas (Priority: P1)

Dado un conjunto de una o más notas que suenan en el mismo instante (una
nota sola, o un acorde), se necesita que el sistema asigne a cada una una
posición de cuerda y traste tal que esa posición produzca el tono pedido
(dentro de la tolerancia declarada) y que el conjunto de posiciones del
instante no exceda el límite físico de estiramiento de la mano.

**Why this priority**: Es la unidad de corrección más pequeña de la que
depende todo lo demás -- sin esto, ninguna secuencia completa (User
Story 2) ni ninguna medición (User Story 3) tiene sentido. Es viable
como slice independiente porque se puede verificar por completo con
tonos e instantes elegidos a mano, sin ninguna secuencia larga ni
dataset real -- mismo patrón que el mecanismo de acierto del hito 2.

**Independent Test**: Se puede probar por completo construyendo
instantes con una nota sola, con un acorde de tonos elegidos a mano
(algunos alcanzables dentro del límite de estiramiento, algunos que lo
exceden), y verificando que toda posición devuelta reproduce el tono
pedido dentro de tolerancia y que un acorde que excede el límite se
resuelve según la regla declarada (Requisitos, FR-013), sin invocar
ningún dataset ni ninguna secuencia de más de un instante.

**Acceptance Scenarios**:

1. **Given** una nota con un tono dado, **When** se le asigna una
   posición, **Then** esa posición (cuerda, traste), en afinación
   estándar, produce ese tono dentro de la tolerancia declarada.
2. **Given** un acorde de varias notas simultáneas cuyos tonos son
   alcanzables sin exceder el límite de estiramiento, **When** se le
   asigna una posición a cada una, **Then** cada nota recibe una cuerda
   distinta y el conjunto de trastes usados no excede el límite
   declarado.
3. **Given** un acorde cuyos tonos, en toda combinación posible de
   posiciones (incluida la tolerancia de tono), exceden el límite de
   estiramiento, **When** se evalúa el instante, **Then** el sistema lo
   excluye con un motivo explícito -- nunca produce en silencio una
   posición que excede el límite.
4. **Given** dos notas simultáneas con el mismo tono exacto, **When** se
   les asigna posición, **Then** cada una recibe una cuerda distinta,
   ambas produciendo ese mismo tono.

---

### User Story 2 - Asignar la digitación completa de una secuencia minimizando el coste total (Priority: P1)

Dada una secuencia completa de instantes ordenados en el tiempo, se
necesita que el sistema asigne la combinación de posiciones -- una por
nota, respetando User Story 1 en cada instante -- que minimiza la suma
del coste de estiramiento de cada instante más el coste de
desplazamiento y de cruce de cuerdas entre cada par de instantes
consecutivos, donde ambos costes de movimiento dependen del tiempo real
disponible entre ellos.

**Why this priority**: Es el entregable central de la feature -- sin
esto, User Story 1 solo resuelve instantes aislados, nunca una
digitación tocable de principio a fin. Depende de que User Story 1 ya
produzca candidatos válidos por instante.

**Independent Test**: Se puede probar por completo con secuencias
sintéticas cortas (pocos instantes, tonos e instantes de tiempo
elegidos a mano, acotadas para que un cálculo por fuerza bruta
independiente sea viable), verificando que la digitación que el
sistema produce coincide exactamente en coste total con ese óptimo --
para varias secuencias, incluida al menos una donde el mismo
desplazamiento en trastes es barato con mucho tiempo entre instantes y
caro con poco tiempo.

**Acceptance Scenarios**:

1. **Given** una secuencia corta de instantes con un óptimo calculable
   por fuerza bruta, **When** el sistema asigna la digitación completa,
   **Then** el coste total de esa digitación es igual al coste del
   óptimo por fuerza bruta.
2. **Given** dos instantes consecutivos con el mismo desplazamiento en
   trastes pero separados por intervalos de tiempo distintos, **When**
   se calcula el coste de la transición, **Then** el intervalo más
   corto produce un coste de desplazamiento mayor o igual, nunca menor.
3. **Given** una secuencia de dos notas consecutivas en cuerdas opuestas
   del mástil (por ejemplo, traste 1 de la sexta cuerda seguido de
   traste 1 de la primera) con desplazamiento a lo largo del mástil
   igual a cero, **When** se calcula el coste de la transición, **Then**
   el coste de cruce de cuerdas de esa transición es mayor que cero.
4. **Given** el primer instante de una secuencia, **When** se calcula su
   coste, **Then** no se le atribuye ningún coste de desplazamiento ni
   de cruce de cuerdas -- no hay instante anterior.

---

### User Story 3 - Medir la digitación producida contra la anotación real de GuitarSet (Priority: P3)

Dado un conjunto de grabaciones medibles de GuitarSet (sus notas de
referencia y la digitación real que anotan), se necesita que el sistema
agregue, sobre todas ellas, la fracción de notas cuya posición asignada
coincide exactamente con la posición que el guitarrista realmente usó.

**Why this priority**: Es la validación del modelo de coste contra
comportamiento humano real -- las dos historias anteriores son
mecanismo, esta es la evidencia de si el modelo de coste declarado se
parece a cómo la gente realmente digita. Depende de que User Story 1 y
2 ya funcionen: agrega su resultado, no redefine cómo se asigna una
posición.

**Independent Test**: Se puede probar por completo con notas de
referencia y digitaciones reales anotadas construidas a mano sobre
varias grabaciones sintéticas, verificando que la fracción de
coincidencia reportada coincide con el cálculo esperado a mano.

**Acceptance Scenarios**:

1. **Given** el resultado de asignar digitación a todas las notas de un
   conjunto de grabaciones medibles, **When** se agrega el resultado,
   **Then** el sistema reporta la fracción de notas cuya cuerda y
   traste asignados coinciden exactamente con la anotación real, junto
   con cuántas notas participaron y cuántas quedaron excluidas.
2. **Given** las 72 grabaciones reservadas del Principio VI, **When** se
   ejecuta esta medición durante el desarrollo del hito 3, **Then**
   ninguna de esas 72 grabaciones participa del cálculo.

---

### Edge Cases

- ¿Qué pasa con una nota cuyo tono, incluso dentro de la tolerancia
  declarada, cae fuera del rango físico del instrumento (más grave que
  la sexta al aire, o más agudo que el traste más alto de la primera)?
- ¿Qué pasa con una grabación de GuitarSet cuya anotación real de
  cuerda/traste esté ausente o incompleta para alguna nota, en User
  Story 3?
- ¿Qué pasa con una secuencia de un solo instante (sin ninguna
  transición que costear)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dada una nota con un tono e instante de inicio, el sistema
  MUST asignar una posición (cuerda, traste) que, en afinación estándar,
  produzca ese tono dentro de la tolerancia declarada (FR-012) -- toda
  posición asignada MUST ser físicamente reproducible en el instrumento,
  nunca una aproximación no declarada ni silenciosa.
- **FR-002**: Dado un instante con más de una nota simultánea (acorde),
  el sistema MUST asignar una cuerda distinta a cada nota (nunca dos
  notas simultáneas en la misma cuerda) tal que el conjunto de trastes
  usados en ese instante no exceda el límite de estiramiento declarado
  (parámetro del modelo, FR-014).
- **FR-003**: El sistema MUST calcular, para cualquier secuencia de
  instantes, un coste total como la suma de tres componentes
  independientes: estiramiento dentro de cada instante, desplazamiento a
  lo largo del mástil entre instantes consecutivos, y cruce de cuerdas a
  lo ancho del mástil entre instantes consecutivos.
- **FR-004**: El coste de desplazamiento y el de cruce de cuerdas entre
  dos instantes consecutivos MUST depender del tiempo real transcurrido
  entre ellos -- el mismo desplazamiento físico MUST costar más cuanto
  menos tiempo haya disponible para ejecutarlo.
- **FR-005**: Dada una secuencia completa de notas, el sistema MUST
  asignar la combinación de posiciones (una por nota) que minimiza la
  suma total de coste (FR-003) sobre toda la secuencia -- MUST ser el
  mínimo real sobre el espacio de posiciones válidas, no una
  aproximación heurística sin verificar contra ese mínimo (FR-006).
- **FR-006**: El sistema MUST verificar, sobre secuencias sintéticas
  cortas donde el óptimo se pueda calcular por fuerza bruta, que la
  digitación que produce coincide exactamente en coste con ese óptimo
  -- es una prueba de corrección del algoritmo de minimización, nunca
  reportada como una métrica del modelo de coste.
- **FR-007**: El sistema MUST medir, sobre un conjunto de grabaciones
  medibles de GuitarSet, la fracción de notas cuya posición asignada
  (cuerda y traste) coincide exactamente con la posición que el
  guitarrista real usó según la anotación del dataset -- MUST NOT
  sustituir esta medición por ninguna cifra derivada del propio coste
  que el algoritmo minimiza (sería circular: el algoritmo lo minimiza
  por construcción, no es evidencia de que se parezca al uso real).
- **FR-008**: El sistema MUST NOT medir ni inspeccionar, en ningún punto
  del desarrollo del hito 3, las 72 grabaciones reservadas de GuitarSet
  (semilla `20260908`, Principio VI) -- mismo conjunto ya reservado en
  el hito 2, protegido por el mismo mecanismo.
- **FR-009**: El sistema MUST NOT consumir la salida de detección de
  notas del hito 2 (transcripción con Basic Pitch) -- opera
  exclusivamente sobre notas de referencia de GuitarSet.
- **FR-010**: El sistema MUST NOT producir ningún archivo de tablatura
  formateado -- su responsabilidad termina en asignar una posición
  (cuerda, traste) a cada nota de la secuencia de entrada.
- **FR-011**: El sistema MUST NOT seleccionar qué pista de guitarra
  digitar cuando una grabación tiene más de una (Principio V) -- esa
  selección es responsabilidad de una feature posterior (hito 4).
- **FR-012**: Cuando ningún traste entero, en ninguna cuerda, reproduce
  exactamente el tono de una nota de referencia (afinación real
  fraccionaria, ya observada en el hito 2), el sistema MUST resolver la
  posición dentro de una tolerancia de tono declarada explícitamente
  como parámetro del modelo -- mismo criterio que
  `TOLERANCIA_TONO_CENTS` del hito 2 -- fijada en `/speckit-plan` con
  evidencia real de cuán común es la desafinación fraccionaria en
  GuitarSet, nunca inventada (Clarifications, sesión 2026-09-11).
- **FR-013**: Cuando un acorde no tiene ninguna combinación de
  posiciones que respete el límite de estiramiento, ni siquiera dentro
  de la tolerancia de tono de FR-012, el sistema MUST excluir ese
  instante con un motivo explícito y distinguible, y MUST continuar con
  el resto de la secuencia -- mismo patrón que la exclusión terminal por
  grabación del hito 2, aplicado aquí a nivel de instante dentro de una
  secuencia.
- **FR-014**: El sistema MUST declarar los parámetros del modelo de
  coste (límite de estiramiento, la tolerancia de tono de FR-012, los
  pesos de cada componente de coste, y cómo el tiempo entre instantes
  modula el coste de movimiento) de forma explícita y documentada --
  nunca como constantes sin nombre dentro del código -- fijados en
  `/speckit-plan` con su justificación.
- **FR-015**: El sistema MUST NOT definir ni evaluar ningún umbral de
  aprobación sobre la fracción de coincidencia medida en User Story 3 --
  su responsabilidad termina en medir y reportar (Principio VII de la
  constitución: el presupuesto se fija después de medir, con evidencia).
- **FR-016**: El reporte que produce User Story 3 MUST incluir
  suficiente información para interpretar la cifra sin volver a
  ejecutar nada: los parámetros del modelo de coste aplicados (FR-014),
  la lista de grabaciones medidas, las exclusiones con su motivo
  (FR-013), y la fracción de coincidencia con el número de notas que la
  componen.

### Key Entities

- **Nota de entrada**: Una nota de referencia con tono (MIDI, posiblemente
  fraccionario) e instante de inicio -- mismo dato que `NotaReferencia`
  del hito 2, sin cuerda ni traste todavía.
- **Instante**: Un momento de la secuencia con una o más notas de
  entrada simultáneas (una nota sola, o un acorde), la unidad sobre la
  que se aplica el límite de estiramiento.
- **Posición**: Una asignación física de cuerda y traste sobre el
  mástil, correspondiente a una nota de entrada.
- **Digitación**: La secuencia completa de posiciones asignadas, una
  por nota de entrada, para toda una grabación.
- **Modelo de coste**: Los tres componentes independientes (estiramiento,
  desplazamiento, cruce de cuerdas) y sus parámetros declarados (límite
  de estiramiento, tolerancia de tono, pesos, dependencia del tiempo
  entre instantes) -- nunca constantes enterradas en el código.
- **Posición real anotada**: La cuerda y el traste que GuitarSet
  registra que el guitarrista realmente usó para una nota -- fuente de
  verdad exclusiva de User Story 3, nunca usada para decidir qué
  posición asignar.
- **Exclusión**: Un instante apartado de la digitación por no tener
  ninguna combinación de posiciones válida dentro de la tolerancia y el
  límite de estiramiento declarados (FR-013), con un motivo distinguible.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de las posiciones que el sistema asigna, sobre
  cualquier entrada, producen el tono exacto solicitado dentro de la
  tolerancia declarada -- el 0% de las posiciones asignadas produce un
  tono fuera de esa tolerancia sin que el instante quede reportado como
  excluido.
- **SC-002**: El 100% de los instantes con más de una nota que el
  sistema no excluye respeta el límite de estiramiento declarado.
- **SC-003**: Sobre un conjunto de secuencias sintéticas cortas
  (acotadas para que un cálculo por fuerza bruta independiente sea
  viable), el 100% de las digitaciones que el sistema produce coincide
  en coste total con el óptimo calculado de forma independiente.
- **SC-004**: Dado cualquier conjunto de grabaciones medibles de
  GuitarSet, el sistema produce la fracción de notas cuya posición
  coincide con la anotación real, acompañada de cuántas notas se
  midieron y cuántas quedaron excluidas -- sin requerir ningún juicio
  manual.
- **SC-005**: El 0% de las ejecuciones de esta feature mide o inspecciona
  las 72 grabaciones reservadas de GuitarSet.
- **SC-006**: El 0% de las ejecuciones de esta feature produce un
  archivo de tablatura formateado, consume la salida del hito 2, o
  selecciona qué pista de guitarra digitar cuando una grabación tiene
  más de una.

## Assumptions

- **Afinación e instrumento**: Guitarra de 6 cuerdas en afinación
  estándar (Mi-La-Re-Sol-Si-Mi grave a agudo), consistente con
  GuitarSet -- se verifica contra la documentación del dataset en
  `/speckit-plan`, no se asume sin evidencia.
- **Rango de trastes**: Se toma de la distribución real de trastes que
  las propias anotaciones de GuitarSet usan -- mismo criterio que el
  hito 1 fijó su submuestra con evidencia real en vez de un número
  inventado; se cierra en `/speckit-plan`.
- **Fuente de la posición real anotada**: GuitarSet expone, para cada
  nota, la cuerda y el traste reales que el guitarrista tocó (distinto
  de `notes_all`, que el hito 2 ya usa para tono e instante agregados
  sin cuerda) -- se verifica el mecanismo exacto de `mirdata` en
  `/speckit-plan`.
- **Temperamento**: "Reproducir el tono pedido" se interpreta bajo
  temperamento igual de 12 tonos (12-TET), el estándar de un traste de
  guitarra -- no hay microtonalidad ni bends modelados en esta feature.
- **Una nota, una posición**: Una nota de entrada es un tono fijo con un
  único instante de inicio; esta feature no modela bends, slides, ni
  cambios de tono dentro de una misma nota.
- **Reutilización del conjunto medible**: La partición medibles/reservado
  de GuitarSet (72/360, semilla `20260908`) es la misma que el hito 2 ya
  calcula en vivo -- esta feature no define una segunda partición
  independiente que pudiera divergir.
