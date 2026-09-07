# Feature Specification: Compuerta de la métrica

**Feature Branch**: `[005-compuerta-metrica]`

**Created**: 2026-09-06

**Status**: Draft

**Input**: User description: "Feature 005 — Compuerta de la métrica

Evalúa un artefacto de medición ya generado (Feature 004) contra el
presupuesto declarado en la constitución, y falla si la cifra cae por debajo.

RECIBE UN ARTEFACTO, NO EJECUTA UNA MEDICIÓN

La compuerta lee un artefacto existente del repositorio y lo juzga. NO invoca
el modelo, NO lee audio, NO corre una medición. Eso la hace instantánea y
verificable en cualquier momento — una compuerta que tarda 18 horas no puede
estar en el guantelete, y una que nadie corre no protege nada.

Lo que se actualiza cada tanto es el artefacto; la compuerta es fija.

QUÉ EVALÚA

El presupuesto del Principio VII de la constitución (v1.5.0): −8.0 dB sobre la
MEDIANA DE LAS REFERENCIAS EMPAREJADAS. Explícitamente NO sobre la mediana
global, que es estructuralmente −∞ con este modelo — una compuerta sobre ella
no podría fallar nunca.

El veredicto va acompañado OBLIGATORIAMENTE de la fracción de referencias sin
pareja. La constitución lo exige: sin ese dato la mediana de emparejadas
engaña, porque no dice cuántas referencias quedaron sin estimación.

PARA QUÉ SIRVE DE VERDAD

Detección de regresión sobre la calidad del sistema, no sobre el código. Si
alguien cambia el modelo, el pipeline o la métrica y vuelve a medir, la
compuerta dice si empeoró. Es la primera verificación del proyecto que juzga
resultados y no comportamiento.

CASOS A RESOLVER

- Qué hace si el artefacto no existe, está corrupto, o le falta la cifra que
  la compuerta necesita. Fallo abierto no es opción: una compuerta que pasa
  porque no encontró qué evaluar es el modo de fallo que este proyecto ya
  encontró cinco veces.
- Si el artefacto fue generado con un modelo distinto del declarado, ¿la
  compuerta lo acepta? El artefacto registra firma de modelo y semilla; hay
  que decidir si compara contra un valor esperado o solo reporta cuál fue.
- Si hay más de un artefacto (submuestra y conjunto completo), ¿cuál juzga?
  ¿Los dos, con presupuestos distintos? El presupuesto de −8.0 se fijó con
  evidencia de la submuestra; aplicarlo tal cual al conjunto completo es una
  decisión, no una consecuencia.

FUERA DE ALCANCE

- NO ejecuta mediciones ni invoca modelos.
- NO modifica el presupuesto. El número vive en la constitución; la compuerta
  lo aplica.

INTEGRACIÓN

Debe quedar disponible como recipe de `just` e incorporable a `gauntlet`, con
el mismo criterio de fallo cerrado que el resto de las compuertas."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Juzgar un artefacto de medición contra el presupuesto (Priority: P1)

Dado un artefacto de medición ya generado por la Feature 004, se necesita
obtener un veredicto claro de aprobado o rechazado, comparando la mediana de
sus referencias emparejadas contra el presupuesto declarado en la
constitución, sin volver a ejecutar ninguna medición.

**Why this priority**: Es el entregable de la feature — sin este veredicto no
hay detección de regresión posible. Es viable como slice independiente
porque el artefacto de entrada ya existe (Feature 004 lo produce y lo
versiona) y el presupuesto ya está fijado (Principio VII, v1.5.0).

**Independent Test**: Se puede probar por completo construyendo artefactos
sintéticos con distintas medianas de referencias emparejadas (por encima,
igual, y por debajo de −8.0 dB) y verificando que la compuerta produce el
veredicto correcto para cada uno, sin necesitar el artefacto real de la
submuestra ni ningún modelo.

**Acceptance Scenarios**:

1. **Given** un artefacto válido cuya mediana de referencias emparejadas es
   mayor o igual a −8.0 dB, **When** se evalúa con la compuerta, **Then** el
   veredicto es de aprobación, e incluye la mediana observada, el valor del
   presupuesto contra el que se comparó, y la fracción de referencias sin
   pareja.
2. **Given** un artefacto válido cuya mediana de referencias emparejadas es
   menor a −8.0 dB, **When** se evalúa con la compuerta, **Then** el
   veredicto es de rechazo, con la misma información obligatoria del
   escenario anterior, y el proceso termina señalando el fallo de forma
   distinguible de una aprobación.
3. **Given** un artefacto válido cuya mediana de referencias emparejadas es
   exactamente −8.0 dB, **When** se evalúa con la compuerta, **Then** el
   veredicto es de aprobación — el presupuesto es un mínimo inclusive, no un
   umbral estrictamente mayor.
4. **Given** cualquier artefacto válido, **When** se evalúa con la compuerta,
   **Then** el veredicto reporta la fracción de referencias sin pareja
   (referencias sin estimación disponible sobre el total de referencias del
   artefacto) junto con la mediana, nunca la mediana sola.
5. **Given** un artefacto válido, **When** se evalúa con la compuerta,
   **Then** la evaluación se completa sin leer ningún archivo de audio, sin
   invocar ningún modelo de separación, y sin ejecutar ningún cálculo de
   SI-SDR — solo lee el artefacto y compara los valores que ya contiene.

---

### User Story 2 - Fallar de forma cerrada ante un artefacto ausente o inválido (Priority: P2)

Dado que la compuerta va a formar parte de la verificación automática del
proyecto, se necesita que la ausencia del artefacto, su corrupción, o la
falta de algún valor que la compuerta necesita para juzgar, se traten siempre
como un rechazo explícito y señalado con claridad — nunca como una
aprobación silenciosa ni como un veredicto ambiguo.

**Why this priority**: Una compuerta que aprueba porque no encontró qué
evaluar no protege nada; es el modo de fallo que este proyecto ya identificó
como inaceptable en otras compuertas. Depende de que User Story 1 ya defina
qué es un artefacto válido y qué veredicto correcto se le aplica, para poder
distinguir "inválido" de "válido y rechazado".

**Independent Test**: Se puede probar por completo invocando la compuerta
contra una ruta de artefacto que no existe, contra un archivo cuyo
contenido no se puede interpretar como un artefacto de medición, y contra
artefactos por lo demás reconocibles a los que les falta la mediana de
referencias emparejadas o el detalle de referencias sin pareja —
verificando que los tres casos terminan en rechazo con un mensaje que
identifica cuál fue el problema, nunca en aprobación.

**Acceptance Scenarios**:

1. **Given** una ruta de artefacto que no existe en el sistema de archivos,
   **When** se invoca la compuerta sobre esa ruta, **Then** el resultado es
   un rechazo con un mensaje que identifica la ruta ausente, distinguible de
   un rechazo por presupuesto no alcanzado.
2. **Given** un archivo en la ruta esperada cuyo contenido no se puede
   interpretar como un artefacto de medición, **When** se invoca la
   compuerta, **Then** el resultado es un rechazo con un mensaje que
   identifica el problema de formato, sin intentar extraer ningún valor
   parcial de él.
3. **Given** un artefacto por lo demás reconocible pero al que le falta el
   valor que la compuerta necesita para calcular el veredicto (por ejemplo,
   no queda claro cuáles de sus referencias están emparejadas y cuáles
   no), **When** se invoca la compuerta, **Then** el resultado es un
   rechazo con un mensaje que identifica el dato faltante, nunca una
   aprobación por ausencia de evidencia en contra.
4. **Given** cualquiera de los tres casos anteriores, **When** se observa el
   código de salida del proceso de la compuerta, **Then** es distinto del
   que indica aprobación, de forma que un guantelete automatizado que
   dependa de él se detiene igual que ante un presupuesto no alcanzado.

---

### User Story 3 - Elegir qué artefacto juzgar entre los dos modos de la Feature 004 (Priority: P3)

Dado que la Feature 004 puede producir un artefacto de la submuestra del
hito 1 o uno del conjunto evaluable completo, se necesita poder indicarle a
la compuerta explícitamente cuál de los dos artefactos juzgar, aplicando el
mismo presupuesto declarado en la constitución a cualquiera de los dos, y
reportando de forma visible con qué modelo y bajo qué modo se generó el
artefacto evaluado.

**Why this priority**: Sin esto, la compuerta quedaría atada a un único
artefacto fijo y no serviría para el caso real de comparar corridas futuras
sobre cualquiera de los dos modos de la Feature 004. Depende de que User
Story 1 y 2 ya definan el mecanismo de juicio y de fallo cerrado sobre un
artefacto — esta historia solo agrega de cuál.

**Independent Test**: Se puede probar por completo construyendo dos
artefactos sintéticos distintos (uno marcado como submuestra, otro como
conjunto completo) e invocando la compuerta sobre cada uno por separado,
verificando que cada invocación juzga el artefacto que se le indicó, con el
mismo presupuesto en ambos casos, y que evaluar uno no requiere que el otro
exista.

**Acceptance Scenarios**:

1. **Given** dos artefactos distintos disponibles, uno de cada modo de la
   Feature 004, **When** se invoca la compuerta indicando explícitamente
   cuál evaluar, **Then** el veredicto corresponde únicamente al artefacto
   indicado, sin requerir que el otro exista ni verlo afectado por su
   contenido.
2. **Given** un artefacto de cualquiera de los dos modos, **When** se evalúa
   con la compuerta, **Then** se aplica exactamente el mismo valor de
   presupuesto (−8.0 dB) que en el otro modo — el presupuesto es una
   propiedad de la constitución, no del modo de la corrida que produjo el
   artefacto.
3. **Given** un artefacto cuya firma de modelo registrada no coincide con
   ninguna expectativa externa a la propia compuerta, **When** se evalúa,
   **Then** el veredicto reporta igualmente esa firma de modelo (y el modo y
   la semilla, cuando aplica) como parte de la información obligatoria del
   resultado, sin que la compuerta rechace el artefacto únicamente por no
   reconocer esa firma.

---

### Edge Cases

- El artefacto existe y es reconocible con la forma esperada, pero su
  conjunto de referencias está vacío (cero referencias en total, por ejemplo
  si todos los temas de la corrida que lo produjo quedaron excluidos). La
  compuerta no puede calcular una mediana sobre un conjunto vacío ni
  reportar una fracción sin pareja con denominador cero; este caso se trata
  como un rechazo explícito con un motivo distinguible ("sin evidencia
  suficiente para juzgar"), nunca como una aprobación ni como una división
  por cero silenciosa (cubierto por User Story 2).
- El artefacto tiene referencias emparejadas, pero el 100% de sus
  referencias totales están sin pareja (mediana de emparejadas calculable
  sobre muy pocos valores). La compuerta igual calcula y reporta el
  veredicto sobre las emparejadas disponibles, junto con la fracción sin
  pareja obligatoria — que en este caso será alta y visible, cumpliendo su
  propósito de no ocultar la información (cubierto por User Story 1,
  escenario 4).
- Se invoca la compuerta sin indicar explícitamente sobre qué artefacto
  juzgar. **Corregido tras F2 de `/speckit-analyze`:** la compuerta en sí
  misma no tiene ningún valor por defecto — omitir la indicación de cuál
  artefacto evaluar se trata siempre igual que cualquier invocación
  inválida (mismo mecanismo que cualquier ruta de artefacto ausente,
  cubierto por User Story 2, escenario 1), sin excepción según el
  contexto desde el que se invoque. El guantelete no depende de ningún
  comportamiento por defecto de la compuerta: su paso de verificación
  indica explícitamente qué artefacto juzgar (la submuestra del hito 1)
  en la propia invocación, exactamente como cualquier otra invocación.
- El valor de presupuesto que la compuerta aplica deja de coincidir con el
  de la constitución vigente (por ejemplo, tras una enmienda futura que
  cambie el número). Esta feature no define un mecanismo para mantenerlos
  sincronizados automáticamente; es responsabilidad de quien enmiende la
  constitución actualizar también el valor que la compuerta aplica, igual
  que el resto del código que depende de una decisión de la constitución.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST leer un artefacto de medición existente (el
  producido por la Feature 004) y calcular un veredicto de aprobado o
  rechazado, sin invocar ningún modelo de separación, sin leer ningún
  archivo de audio, y sin recalcular ningún valor de SI-SDR — todos los
  valores que el veredicto usa MUST provenir del propio artefacto.
- **FR-002**: El sistema MUST comparar la mediana de las referencias
  emparejadas del artefacto (nunca la mediana global de todas las
  referencias, emparejadas y sin pareja) contra el presupuesto declarado en
  el Principio VII de la constitución (−8.0 dB), y MUST considerar el
  presupuesto alcanzado cuando la mediana es mayor o igual a ese valor.
- **FR-003**: Todo veredicto que el sistema emita MUST incluir, como parte
  obligatoria del mismo resultado y no como un dato aparte u opcional: la
  mediana de referencias emparejadas observada, el valor del presupuesto
  contra el que se comparó, y la fracción de referencias sin pareja sobre
  el total de referencias del artefacto.
- **FR-004**: Cuando la ruta del artefacto indicado no existe, el sistema
  MUST terminar en rechazo con un mensaje que identifique la ruta ausente,
  MUST NOT terminar en aprobación, y MUST señalar el resultado de forma
  distinguible de un rechazo por presupuesto no alcanzado.
- **FR-005**: Cuando el contenido en la ruta del artefacto no se puede
  interpretar, o no tiene la forma reconocible de un artefacto de medición,
  el sistema MUST terminar en rechazo con un mensaje que identifique el
  problema de formato, y MUST NOT intentar calcular un veredicto a partir
  de un valor parcial o inferido.
- **FR-006**: Cuando el artefacto es válido como documento pero le falta
  cualquier valor indispensable para calcular el veredicto de FR-002 y
  FR-003 (incluyendo el caso de un conjunto de referencias vacío, que
  impide calcular tanto la mediana como la fracción sin pareja), el sistema
  MUST terminar en rechazo con un mensaje que identifique el valor faltante
  o la condición que impide el cálculo, y MUST NOT terminar en aprobación
  por ausencia de evidencia en contra.
- **FR-007**: El código o señal de salida del proceso de la compuerta MUST
  distinguir sin ambigüedad entre "aprobado" y cualquiera de los casos de
  rechazo (presupuesto no alcanzado, artefacto ausente, artefacto inválido,
  valor faltante), de forma que un guantelete automatizado que dependa de
  ese resultado se detenga ante cualquiera de ellos igual que ante los
  demás.
- **FR-008**: El sistema MUST permitir indicar explícitamente sobre cuál de
  los artefactos posibles (el de la submuestra del hito 1 o el del conjunto
  evaluable completo, Feature 004) evaluar el veredicto, MUST NOT asumir
  ninguno de los dos por defecto ante la ausencia de esa indicación (F2 de
  `/speckit-analyze`: ni siquiera en un contexto de invocación específico
  como el guantelete — ver Edge Cases), MUST aplicar exactamente el mismo
  valor de presupuesto a cualquiera de los dos, y MUST permitir evaluar uno
  sin requerir que el otro exista.
- **FR-009**: Todo veredicto MUST reportar la firma del modelo, el modo de
  ejecución, y la semilla (cuando el artefacto la registre) que produjeron
  el artefacto evaluado, como información de contexto del resultado. El
  sistema MUST NOT rechazar un artefacto únicamente por el valor de esa
  firma, ese modo, o esa semilla — el veredicto depende solo de la mediana
  de referencias emparejadas contra el presupuesto (FR-002).
- **FR-010**: El sistema MUST NOT modificar, recalcular, ni sobrescribir
  ningún valor del presupuesto: el número vive en la constitución
  (Principio VII) y el sistema únicamente lo aplica como viene declarado.
- **FR-011**: El sistema MUST NOT ejecutar ningún paso de medición, de
  separación de guitarra, ni de entrenamiento o ajuste de ningún modelo
  (Principio I de la constitución) — su responsabilidad empieza y termina
  en juzgar un artefacto ya existente.

### Key Entities

- **Veredicto**: El resultado de evaluar un artefacto contra el presupuesto:
  si el presupuesto se alcanzó o no, la mediana de referencias emparejadas
  observada, el valor del presupuesto usado, la fracción de referencias sin
  pareja, y la información de contexto del artefacto evaluado (firma de
  modelo, modo, semilla). Es lo único que hace falta para saber si una
  medición ya generada cumple el presupuesto, sin volver a leer el
  artefacto completo a mano.
- **Presupuesto**: El valor numérico fijo declarado en el Principio VII de
  la constitución (−8.0 dB sobre la mediana de referencias emparejadas) que
  esta feature aplica pero no define ni recalcula.
- **Rechazo por artefacto inválido**: Una categoría de resultado distinta
  del rechazo por presupuesto no alcanzado — cubre artefacto ausente,
  ilegible, o incompleto para calcular el veredicto (FR-004, FR-005,
  FR-006). Se distingue del rechazo por presupuesto porque señala un
  problema con la evidencia misma, no con la calidad medida.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dado cualquier artefacto de medición válido de la Feature 004,
  evaluarlo con la compuerta produce un veredicto en menos de un segundo,
  sin leer ningún archivo de audio ni invocar ningún modelo.
- **SC-002**: El 100% de los artefactos cuya mediana de referencias
  emparejadas es menor al presupuesto declarado producen un veredicto de
  rechazo, y el 100% de los que la igualan o superan producen un veredicto
  de aprobación.
- **SC-003**: El 100% de los veredictos, sean de aprobación o de rechazo,
  incluyen la fracción de referencias sin pareja junto con la mediana — el
  0% de los veredictos reporta la mediana sin ese dato.
- **SC-004**: El 100% de las invocaciones sobre una ruta de artefacto
  ausente, un archivo no reconocible como artefacto, o un artefacto sin el
  valor necesario para juzgar, terminan en rechazo con un mensaje que
  identifica la causa — el 0% de esos casos termina en una aprobación.
- **SC-005**: Es posible evaluar el artefacto de cualquiera de los dos modos
  de la Feature 004 (submuestra del hito 1 o conjunto evaluable completo)
  indicando cuál, con el mismo presupuesto aplicado en ambos casos.

## Assumptions

- El artefacto de entrada es el que produce la Feature 004
  (`artefacto_a_dict`, `specs/004-medicion-linea-base/data-model.md`): esta
  feature lee su forma ya definida, no la redefine ni le agrega campos. La
  "mediana de referencias emparejadas" (FR-002) y la "fracción de
  referencias sin pareja" (FR-003) se derivan de los valores por referencia
  que el artefacto ya contiene por tema (emparejadas y sin pareja), no de
  un campo agregado nuevo que la Feature 004 tendría que empezar a producir
  — si esa derivación no fuera posible con la forma actual del artefacto,
  es un hallazgo para `/speckit-plan`, no una redefinición silenciosa aquí.
- **Sobre el modelo declarado (segundo caso a resolver):** la compuerta
  reporta la firma de modelo, modo y semilla del artefacto evaluado
  (transparencia, FR-009), pero no la compara contra ningún valor externo
  esperado. Esta feature no invoca ni construye ningún `Separador` (fuera de
  alcance explícito), así que no tiene forma de conocer, en el momento de
  evaluar, cuál sería "el modelo vigente" fuera de lo que el propio
  artefacto ya declara — no hay una segunda fuente de verdad accesible sin
  violar el alcance. Esto además sirve al propósito declarado de la
  feature ("si alguien cambia el modelo... la compuerta dice si empeoró"):
  una compuerta que rechazara artefactos de un modelo distinto no podría
  cumplir ese propósito.
- **Sobre múltiples artefactos (tercer caso a resolver):** la compuerta
  recibe una indicación explícita de cuál artefacto evaluar (no juzga
  ambos a la vez ni elige uno por defecto de forma implícita fuera del
  contexto del guantelete, FR-008), y aplica el mismo presupuesto de
  −8.0 dB a cualquiera de los dos modos, porque la constitución declara un
  único número de Principio VII, no uno por modo. Definir presupuestos
  distintos por modo requeriría una enmienda de la constitución con su
  propia evidencia — fuera del alcance de esta feature.
- La integración con el guantelete y con `just` (mencionada en el pedido
  original) usa por defecto el artefacto de la submuestra del hito 1
  (`mediciones/submuestra_hito1.json`) — es el único artefacto cuya
  evidencia ya está versionada en el repositorio y el que respalda el
  número de presupuesto cerrado en la constitución. Evaluar el artefacto
  del conjunto evaluable completo, cuando exista, es una invocación
  explícita separada, no parte del guantelete por defecto — igual que la
  Feature 004 no agregó una corrida real de 36 minutos ni de horas al
  guantelete.
- Un artefacto con cero referencias en total (Edge Cases) se trata como
  inválido para juzgar (FR-006), no como "presupuesto alcanzado por
  ausencia de evidencia en contra" ni como "presupuesto no alcanzado por
  falta de datos" — ninguna de las dos lecturas estaría respaldada por
  ninguna medición real.
