# Feature Specification: Separación de guitarra con modelo preentrenado

**Feature Branch**: `[003-separacion-modelo-preentrenado]`

**Created**: 2026-09-04

**Status**: Draft

**Input**: User description: "Feature 003 — Separación de guitarra con modelo preentrenado

Dada la mezcla de un tema, el sistema produce una o más estimaciones de pista
de guitarra usando un modelo preentrenado, sin entrenar ni afinar nada.

MODELO Y LICENCIAS

El modelo, su versión exacta y su procedencia quedan declarados y fijados: una
medición no es reproducible si el modelo puede cambiar bajo los pies.

Sobre las licencias, hay una asimetría que debe quedar registrada: el código de
Demucs es MIT, pero los pesos no. El repositorio oficial dice literalmente
"The model weights are not covered by the MIT license, and are provided only
for scientific purposes."

Consecuencia práctica, a escribir en la spec: este proyecto no redistribuye
pesos, y su uso es personal y educativo, lo que encaja en la restricción
declarada. La regla del Principio IV de la constitución ("toda fuente debe ser
CC BY 4.0 o más permisiva") se escribió para fuentes de audio; los pesos de un
modelo son otra categoría y la constitución no la contempla. La spec lo
resuelve para esta feature dejando la identificación explícita, no suponiéndola.

TRANSFORMACIONES

Toda transformación entre el audio del conjunto y la entrada del modelo —y
entre la salida del modelo y lo que recibe la métrica— es explícita y
declarada, no un efecto lateral.

Verificar en concreto:
- Frecuencia de muestreo del conjunto contra la que espera el modelo. Slakh2100
  está a 44.1 kHz; si el modelo trabaja a la misma tasa, no hay remuestreo y el
  punto queda cerrado por verificación, no por suposición.
- Número de canales. El conjunto es mono; el modelo puede esperar estéreo. Si
  hay que duplicar el canal a la entrada, y colapsar la salida a mono antes de
  comparar, ambas son transformaciones y ambas se declaran.

Si hay conversión en cualquiera de los dos sentidos, se documenta que la
métrica resultante incluye su efecto y no solo el error de separación.

NÚMERO DE ESTIMACIONES

El modelo puede producir menos estimaciones que referencias tiene el tema —
típicamente una sola salida de guitarra frente a varias pistas de referencia.
Eso es comportamiento esperado del modelo, no un fallo de esta feature; la
métrica de la Feature 002 ya lo contabiliza como referencias sin pareja.

FUERA DE ALCANCE, EXPLÍCITAMENTE

- NO entrena ni afina. Constitución, Principio I.
- NO calcula la métrica ni evalúa umbral. Recibe una mezcla, devuelve
  estimaciones. La Feature 002 mide.
- NO toca la división de prueba del conjunto. Principio VI.

CASO A RESOLVER

Qué hace el sistema si el modelo no produce ninguna estimación de guitarra
para un tema. La Feature 002 ya define qué significa una estimación silenciosa
(energía nula, −∞ por convención); falta decidir si ausencia de estimación y
estimación silenciosa son lo mismo en esta capa, o si son estados distintos
que la métrica debe poder diferenciar.

RESTRICCIONES DEL ENTORNO

Sin GPU declarada; presupuesto de cómputo local en WSL/Ubuntu. La inferencia
sobre un tema completo de varios minutos puede ser lenta, y el conjunto tiene
cientos de temas. El plan debe enfrentar explícitamente si eso afecta la
ejecutabilidad de los tests y de una corrida completa, en vez de descubrirlo a
mitad de la primera medición."

## Clarifications

### Session 2026-09-04

- Q: ¿Qué debe hacer el sistema cuando la llamada al modelo falla en sí misma
  durante un tema (excepción de runtime, audio con forma no soportada, error
  del framework) — un caso distinto de que el modelo corra bien y simplemente
  no produzca guitarra? → A: Falla dura con mensaje claro que identifica el
  tema y la causa, distinguible del caso legítimo de cero estimaciones
  (FR-009) — mismo patrón que Feature 001 usa para archivos ilegibles.
- Q: ¿Debe exigirse que dos corridas de inferencia sobre el mismo tema con el
  mismo modelo declarado produzcan resultados idénticos, y con qué criterio
  de igualdad? → A: Con tolerancia numérica declarada, extendiendo el
  Principio VIII ya cerrado en la Feature 002 (tolerancia para acumulación de
  punto flotante del modelo, igualdad exacta solo para lo construido por
  definición) en vez de introducir una segunda política de determinismo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Producir estimaciones de guitarra para un tema (Priority: P1)

Dada la mezcla de audio de un tema, se necesita obtener una colección de
estimaciones de pista de guitarra generadas por un modelo preentrenado, con
cualquier transformación de formato entre el audio del conjunto y lo que el
modelo espera aplicada y declarada explícitamente, para que el resultado
pueda entrar directamente a la Feature 002 sin ajustes manuales.

**Why this priority**: Es la razón de ser de la feature. Sin poder producir
estimaciones a partir de una mezcla, no hay nada que medir con la Feature 002
ni ningún otro entregable posible del hito 1.

**Independent Test**: Se puede probar por completo con la mezcla de un tema
conocido (real o sintética, de longitud y formato representativos de
Slakh2100), invocando la separación y verificando que se recibe una colección
de estimaciones de guitarra, cada una con su audio y un identificador, junto
con el registro de qué transformaciones de formato se aplicaron.

**Acceptance Scenarios**:

1. **Given** la mezcla de un tema cuya frecuencia de muestreo coincide con la
   que espera el modelo, **When** se ejecuta la separación, **Then** el
   sistema no aplica ningún remuestreo, y el resultado lo declara
   explícitamente (frecuencias verificadas iguales, no una suposición).
2. **Given** la mezcla de un tema cuya frecuencia de muestreo difiere de la
   que espera el modelo, **When** se ejecuta la separación, **Then** el
   sistema remuestrea la entrada a la frecuencia que el modelo requiere antes
   de la inferencia, y declara en el resultado que ocurrió un remuestreo.
3. **Given** la mezcla mono de un tema y un modelo que espera audio
   estéreo, **When** se ejecuta la separación, **Then** el sistema duplica el
   canal mono para formar la entrada estéreo que el modelo requiere, colapsa
   cada estimación de salida de vuelta a mono antes de entregarla, y declara
   ambas transformaciones junto con el resultado.
4. **Given** cualquier resultado producido con una transformación de
   frecuencia de muestreo o de canales aplicada, **When** ese resultado se
   entrega junto con sus estimaciones, **Then** el registro de
   transformaciones aplicadas acompaña al resultado, dejando constancia de que
   una métrica calculada después sobre esas estimaciones incluye el efecto de
   la transformación y no únicamente el error de separación del modelo.
5. **Given** un tema con varias pistas de guitarra de referencia, **When** el
   modelo produce menos estimaciones de guitarra que referencias tiene el
   tema (por ejemplo, una sola salida de guitarra), **Then** el sistema
   devuelve exactamente las estimaciones producidas, sin inventar
   estimaciones adicionales para las referencias sobrantes y sin fallar.
6. **Given** una mezcla que provoca un error del propio modelo o del
   framework de inferencia (por ejemplo, una forma de audio no soportada o un
   error de runtime), **When** se ejecuta la separación, **Then** el sistema
   falla de forma explícita con un mensaje claro que identifica el tema y la
   causa del fallo, distinguible del caso legítimo de que el modelo corra
   bien y no produzca ninguna estimación (User Story 3, escenario 1).
7. **Given** la misma mezcla de un tema procesada dos veces con el mismo
   modelo declarado, **When** se comparan las estimaciones resultantes de
   ambas corridas, **Then** coinciden dentro de la tolerancia numérica
   declarada para esta feature, sin exigir igualdad bit a bit.

---

### User Story 2 - Declarar el modelo y sus licencias de forma fija y verificable (Priority: P2)

Dado que dos corridas de esta feature deben ser comparables, se necesita que
el modelo usado (nombre, versión exacta y procedencia) quede fijado y
declarado de forma verificable, junto con el registro explícito de que los
pesos del modelo no se redistribuyen y de que su uso es personal y
educativo.

**Why this priority**: Sin esta declaración, una medición no es reproducible
— el modelo podría cambiar entre corridas sin que nadie lo note, invalidando
cualquier comparación posterior. Es independiente de que la inferencia ya
funcione: se puede verificar la declaración sin ejecutar ni una sola
separación.

**Independent Test**: Se puede probar por completo verificando que existe una
declaración fija (nombre, versión exacta, procedencia/checksum del modelo, y
la nota de licencia de los pesos) accesible sin ejecutar ninguna inferencia,
y que esa declaración es la misma entre dos consultas sucesivas.

**Acceptance Scenarios**:

1. **Given** cualquier corrida de esta feature, **When** se consulta qué
   modelo se usó, **Then** el sistema expone el nombre del modelo, su versión
   exacta y su procedencia (fuente de descarga y verificación de integridad),
   de forma que dos corridas que declaran la misma versión usan exactamente
   los mismos pesos.
2. **Given** los pesos del modelo preentrenado, **When** se documenta su uso
   en el proyecto, **Then** la documentación declara explícitamente que el
   repositorio no redistribuye los pesos, que su uso es personal y
   educativo, y cita la licencia real de los pesos (distinta de la licencia
   del código del modelo) sin asumir que la regla de fuentes de audio del
   Principio IV de la constitución le aplica automáticamente a esta otra
   categoría de artefacto.

---

### User Story 3 - Tema sin ninguna estimación de guitarra producida (Priority: P3)

Dado un tema para el cual el modelo, al ejecutarse, no produce ninguna pista
que el sistema identifique como guitarra, se necesita que el resultado
distinga con claridad esa ausencia total de una estimación que sí existe pero
resulta ser silencio digital, para que la Feature 002 pueda seguir
clasificando cada caso con el motivo correcto sin ambigüedad.

**Why this priority**: Es un caso límite del comportamiento normal del
modelo (User Story 1 ya lo señala como esperado, no como fallo), y depende de
que la separación básica ya funcione; su prioridad más baja refleja que es
una precisión sobre el caso general, no una capacidad nueva.

**Independent Test**: Se puede probar por completo simulando una salida del
modelo sin ninguna pista de guitarra para un tema, invocando la separación, y
verificando que el resultado es una colección vacía de estimaciones para ese
tema — no una estimación sintética marcada como silenciosa.

**Acceptance Scenarios**:

1. **Given** un tema para el que el modelo no produce ninguna salida
   identificable como guitarra, **When** se completa la separación, **Then**
   el sistema devuelve una colección vacía de estimaciones para ese tema, sin
   fallar y sin sintetizar una estimación "silenciosa" artificial en su
   lugar.
2. **Given** un tema para el que el modelo sí produce una salida identificada
   como guitarra, pero esa salida resulta ser silencio digital (energía
   nula), **When** se completa la separación, **Then** el sistema devuelve
   esa salida como una estimación real dentro de la colección (no la omite),
   dejando que sea la Feature 002 — que ya distingue "sin estimación
   disponible" de "estimación silenciosa" — quien la clasifique.

---

### Edge Cases

- Ausencia total de estimación (el modelo no produjo ninguna pista de
  guitarra) y estimación con energía nula (el modelo sí produjo una pista,
  pero es silencio digital) son estados distintos en esta capa: el primero se
  representa con una colección vacía, el segundo con una `Estimacion` real
  cuyo audio resulta tener energía nula. Esta feature no colapsa ambos casos
  en uno solo ni sintetiza una estimación artificial para el primero
  (cubierto por User Story 3).
- Cuando la frecuencia de muestreo del conjunto y la que espera el modelo
  coinciden, no se aplica ningún remuestreo, y esa verificación (no
  suposición) queda igualmente declarada en el resultado (cubierto por User
  Story 1, escenario 1).
- Cuando el conjunto es mono y el modelo espera estéreo, la duplicación del
  canal a la entrada y el colapso de la salida a mono son dos
  transformaciones declaradas por separado, no una sola operación implícita
  (cubierto por User Story 1, escenario 3).
- El modelo puede producir más estimaciones de guitarra que referencias tiene
  el tema; esta feature no descarta estimaciones sobrantes ni las trata como
  error — la Feature 002 ya define qué hace con estimaciones que no se
  emparejan con ninguna referencia.
- Los pesos del modelo no se redistribuyen dentro del repositorio: se
  obtienen y verifican desde su procedencia declarada en tiempo de
  configuración o de ejecución, nunca como archivo versionado en el
  repositorio (mismo principio que "el repositorio no contiene audio" del
  Principio IV, extendido a esta otra categoría de artefacto).
- El entorno de desarrollo no declara GPU; una corrida de inferencia sobre un
  tema completo puede tardar varios minutos, y el conjunto tiene cientos de
  temas. Los tests de esta feature no dependen de una corrida completa sobre
  el conjunto para pasar (ver Assumptions).
- Una falla del propio modelo o del framework de inferencia durante el
  procesamiento de un tema (excepción de runtime, forma de audio no
  soportada) es un fallo duro con mensaje claro que identifica el tema y la
  causa — no se colapsa con el caso legítimo de "el modelo corrió bien y no
  produjo ninguna estimación" (FR-009), ni se reintenta automáticamente, ni
  se convierte en una exclusión silenciosa del conjunto (cubierto por User
  Story 1, escenario 6).
- Dos corridas de inferencia sobre la misma mezcla con el mismo modelo
  declarado no están garantizadas a coincidir bit a bit; deben coincidir
  dentro de una tolerancia numérica declarada, siguiendo la misma política ya
  cerrada por el Principio VIII de la constitución para SI-SDR (cubierto por
  User Story 1, escenario 7).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dada la mezcla de audio de un tema, el sistema MUST producir
  cero o más estimaciones de pista de guitarra usando un modelo preentrenado
  fijo, sin ejecutar ningún paso de entrenamiento ni de ajuste de parámetros
  del modelo (Principio I de la constitución).
- **FR-002**: El sistema MUST declarar, para toda corrida, el nombre exacto
  del modelo, su versión exacta, y su procedencia (fuente de descarga y un
  mecanismo de verificación de integridad), de forma que repetir la corrida
  con la misma versión declarada garantice el uso de los mismos pesos.
- **FR-003**: El sistema MUST NOT redistribuir los pesos del modelo dentro
  del repositorio; los pesos se obtienen y se referencian por manifiesto
  desde su procedencia declarada (FR-002), nunca como archivo versionado en
  el repositorio.
- **FR-004**: El sistema MUST documentar, en un lugar identificable del
  repositorio, que el uso de los pesos del modelo es personal y educativo, y
  MUST citar la licencia real de los pesos como una categoría distinta de la
  licencia del código del modelo y de la regla de fuentes de audio del
  Principio IV de la constitución (que no contempla pesos de modelo).
- **FR-005**: Antes de cada inferencia, el sistema MUST verificar la
  frecuencia de muestreo del audio de entrada contra la que espera el
  modelo. Si coinciden, el sistema MUST NOT remuestrear, y MUST declarar esa
  verificación (no suposición) en el resultado. Si difieren, el sistema MUST
  remuestrear la entrada a la frecuencia que el modelo requiere y MUST
  declarar que ocurrió un remuestreo.
- **FR-006**: Antes de cada inferencia, el sistema MUST verificar el número
  de canales del audio de entrada contra el que espera el modelo. Si
  difieren, el sistema MUST aplicar la transformación de canales necesaria
  tanto a la entrada (por ejemplo, duplicar un canal mono para formar
  estéreo) como a la salida (por ejemplo, colapsar una salida estéreo a
  mono), y MUST declarar cada transformación aplicada por separado.
- **FR-007**: Cuando el resultado de una separación incluye alguna
  transformación de frecuencia de muestreo o de canales (FR-005, FR-006), el
  sistema MUST documentar junto con las estimaciones producidas que cualquier
  métrica calculada después sobre ellas incluye el efecto de esa
  transformación, no únicamente el error de separación del modelo.
- **FR-008**: Cuando el modelo produce menos estimaciones de pista de
  guitarra que referencias tiene el tema (incluyendo cero), el sistema MUST
  devolver exactamente las estimaciones producidas, sin inventar
  estimaciones adicionales para completar el número de referencias y sin
  fallar por esa diferencia.
- **FR-009**: Cuando el modelo no produce ninguna estimación de pista de
  guitarra para un tema, el sistema MUST devolver una colección vacía de
  estimaciones para ese tema, MUST NOT sintetizar una estimación "silenciosa"
  artificial para representar esa ausencia — la Feature 002 ya clasifica un
  tema con cero estimaciones recibidas mediante el motivo "sin estimación
  disponible" (FR-003 de 002), y esta feature no introduce un mecanismo
  paralelo para el mismo caso.
- **FR-010**: Cuando el modelo produce una salida real identificada como
  guitarra cuyo audio resulta tener energía nula (silencio digital), el
  sistema MUST devolverla como una `Estimacion` genuina dentro de la
  colección, no omitirla — distinta del caso de FR-009 (ausencia total), para
  que la Feature 002 la clasifique con su motivo ya existente de estimación
  asignada silenciosa (FR-016 de 002).
- **FR-011**: El sistema MUST NOT entrenar ni afinar ningún parámetro del
  modelo bajo ninguna circunstancia (Principio I de la constitución).
- **FR-012**: El sistema MUST NOT calcular ninguna métrica de separación ni
  evaluar ningún umbral de aprobación; su responsabilidad termina en recibir
  una mezcla y devolver estimaciones. El cálculo de la métrica es
  responsabilidad exclusiva de la Feature 002.
- **FR-013**: El sistema MUST NOT leer, modificar, ni depender de a qué
  división (entrenamiento/validación/prueba) pertenece un tema; opera igual
  sobre cualquier tema que reciba (Principio VI de la constitución).
- **FR-014**: Cuando la llamada al modelo o al framework de inferencia falla
  en sí misma durante el procesamiento de un tema (excepción de runtime,
  forma de audio no soportada, error del framework), el sistema MUST
  propagar un fallo explícito con un mensaje claro que identifique el tema y
  la causa, MUST NOT reintentar automáticamente, y MUST NOT tratarlo como el
  caso legítimo de FR-009 (el modelo corrió bien y no produjo ninguna
  estimación) ni como una exclusión silenciosa del conjunto.
- **FR-015**: Dos ejecuciones de inferencia sobre la misma mezcla con el
  mismo modelo declarado (FR-002) MUST producir estimaciones que coincidan
  dentro de una tolerancia numérica explícita, siguiendo la misma política de
  determinismo ya cerrada por el Principio VIII de la constitución
  (tolerancia para valores resultantes de acumulación de punto flotante,
  igualdad exacta solo para lo exacto por construcción); esta feature no
  introduce una segunda política de determinismo distinta de la ya
  establecida.

### Key Entities

- **Modelo declarado**: El modelo preentrenado fijo que esta feature usa
  para inferencia, identificado por nombre, versión exacta, procedencia
  (fuente de descarga) y un mecanismo de verificación de integridad. Incluye
  la licencia de sus pesos como un atributo propio, distinto de la licencia
  del código que lo implementa.
- **Transformación declarada**: Un cambio de formato aplicado entre el audio
  de entrada del conjunto y la entrada que el modelo requiere, o entre la
  salida del modelo y lo que se entrega como resultado — de frecuencia de
  muestreo o de número de canales —, con su dirección (entrada o salida) y
  su motivo, registrado junto con el resultado de la separación.
- **Estimación**: Una pista de audio producida por el modelo e identificada
  como guitarra, con su propio identificador dentro del tema. Reutiliza la
  entidad `Estimacion` ya definida por la Feature 002; esta feature es la que
  la produce, no la redefine.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Para el 100% de los temas de prueba con mezcla válida, la
  separación produce una colección de estimaciones (posiblemente vacía) sin
  interrumpirse por una excepción no controlada.
- **SC-002**: El modelo usado en cualquier corrida es identificable de forma
  exacta (nombre, versión y procedencia) sin ambigüedad; consultar la
  declaración dos veces sobre la misma instalación produce el mismo
  resultado.
- **SC-003**: El 100% de las transformaciones de frecuencia de muestreo o de
  número de canales efectivamente aplicadas en una corrida quedan declaradas
  junto con el resultado, nunca como efecto lateral sin registrar.
- **SC-004**: 0% de las corridas de esta feature modifican los pesos o
  parámetros del modelo declarado.
- **SC-005**: El 100% de los temas donde el modelo no produce ninguna
  estimación de guitarra se distinguen, en el resultado devuelto, de los
  temas donde produce una estimación cuya propia señal resulta ser silencio
  digital — nunca colapsados en el mismo estado.
- **SC-006**: La suite de tests de esta feature se ejecuta por completo en el
  entorno de desarrollo (sin GPU) sin requerir una corrida de inferencia
  sobre el conjunto completo de cientos de temas para pasar.
- **SC-007**: Ningún reporte producido por esta feature incluye un umbral de
  aprobación ni un veredicto de pase/falla, ni indica a qué división
  (entrenamiento/validación/prueba) pertenece el tema procesado.
- **SC-008**: El 100% de las fallas del modelo o del framework de inferencia
  durante un tema producen un mensaje de error que identifica el tema y la
  causa, sin excepción numérica no controlada ni corrida interrumpida sin
  explicación, y son distinguibles del caso legítimo de cero estimaciones
  (SC-005).
- **SC-009**: Dos ejecuciones de inferencia sobre la misma mezcla con el
  mismo modelo declarado producen estimaciones cuyos valores de audio
  coinciden dentro de la tolerancia numérica declarada, verificable
  comparando ambas corridas directamente.

## Assumptions

- El modelo preentrenado es Demucs (Meta AI / Deezer); la variante exacta
  del checkpoint (por ejemplo, cuántos stems separa y cuál es su nombre de
  release) y el mecanismo concreto de verificación de integridad se fijan
  durante `/speckit-plan`, siguiendo el mismo patrón que la Feature 002 usó
  para cerrar la elección de fórmula de SI-SDR: la spec fija la decisión de
  producto (qué modelo, qué restricciones de licencia), el plan fija el
  detalle técnico de la decisión ya tomada.
- El audio de entrada de un tema de Slakh2100 es mono y está a 44.1 kHz,
  según lo establecido y verificado por la Feature 001 (que lee el audio tal
  como viene, sin transformación). Si la frecuencia o el número de canales
  que el modelo declarado espera coinciden con estos valores, FR-005/FR-006
  se satisfacen sin aplicar ninguna transformación real — la verificación
  ocurre siempre, el remuestreo o la duplicación de canal solo si hace
  falta.
- Los pesos del modelo se descargan y almacenan fuera del repositorio (por
  ejemplo, en una caché local o en la ubicación estándar del framework que
  lo distribuye), referenciados por el manifiesto de FR-002; esta feature no
  cubre la infraestructura de descarga en sí, solo la declaración
  verificable de qué versión se usó.
- Dado que el entorno de desarrollo no declara GPU, los tests de esta
  feature ejercitan la inferencia sobre fixtures de audio pequeños y
  sintéticos (segundos, no minutos), no sobre temas completos del conjunto;
  una corrida completa sobre el conjunto de cientos de temas es una
  operación aparte, fuera del ciclo de test-y-verificación, cuyo presupuesto
  de tiempo se decide en `/speckit-plan`.
- Esta feature recibe la mezcla ya cargada con el contrato de datos de la
  Feature 001 (arreglo de audio, frecuencia de muestreo); no cubre la lectura
  del tema desde disco.
- Las estimaciones que esta feature produce se entregan en el formato de
  entrada que la Feature 002 ya espera (`Estimacion` de
  `specs/002-metrica-separacion-guitarra/data-model.md`); esta feature no
  redefine ese contrato.
