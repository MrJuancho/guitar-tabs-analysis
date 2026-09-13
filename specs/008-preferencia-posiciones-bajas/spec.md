# Feature Specification: Preferencia por posiciones bajas en el modelo de coste

**Feature Branch**: `[008-preferencia-posiciones-bajas]`

**Created**: 2026-09-12

**Status**: Draft

**Input**: User description: "Feature 008 — Preferencia por posiciones bajas en el modelo de coste

Agrega un componente al modelo de coste de digitación: la altura del traste
tiene coste. Hoy el modelo penaliza el movimiento pero no la posición, así
que quedarse en trastes altos puede ser óptimo según su propio criterio.

EVIDENCIA QUE LO MOTIVA (ADR-0002, hallazgo 4, más research.md #15)
- Sobre una canción real, la digitación producida usa trastes 11-18 en cinco
  cuerdas donde la tablatura que un guitarrista toca usa trastes 1-6 en una
  sola.
- La medición de T025 ya mostraba la asimetría: Δcuerda con mediana 1,
  Δtraste con mediana 5 y hasta 19. El modelo se desplaza por el mástil más
  de lo que lo hace un humano.

FORMA DEL TÉRMINO
Coste proporcional a la altura del traste, con su propio peso declarado.
Se elige sobre la alternativa de umbral (gratis hasta el traste N, caro
después) por tener un parámetro menos que calibrar. La alternativa queda
registrada como opción, no descartada.

UN CAMBIO POR MEDICIÓN — es la restricción central de esta feature
El peso nuevo se introduce SOLO. Los pesos de desplazamiento y cruce siguen
en 1.0 y NO se tocan en esta feature, pese a que la hipótesis de T025 sugiere
que están mal balanceados. Cambiar tres pesos a la vez hace imposible saber
cuál produjo qué efecto. El rebalanceo de los otros dos es una feature
posterior con su propia medición.

CRITERIO DE ÉXITO
fraccion_coincidencia contra GuitarSet sube desde 0.6186, medida sobre las
mismas 288 grabaciones medibles, sin tocar las 72 reservadas.

Si NO sube, eso también es resultado y se documenta: significaría que la
preferencia por posiciones bajas no es lo que separa la digitación del
modelo de la humana en ese conjunto, aunque sí lo fuera en la canción real
que motivó el hallazgo. Esa discrepancia sería en sí misma un hallazgo sobre
GuitarSet como conjunto de evaluación.

EL VALOR DEL PESO
Se fija con una barrida: medir la coincidencia para varios valores y elegir
con la evidencia delante, documentando la curva completa y no solo el
ganador. No se elige a ojo ni se ajusta después de ver el resultado final.

INVARIANTES QUE NO CAMBIAN
- La corrección tonal sigue siendo precondición, no métrica.
- La optimalidad se sigue verificando contra fuerza bruta: agregar un peso de
  nodo no rompe la subestructura óptima, pero hay que confirmarlo.
- El presupuesto vigente (0.55) no se recalibra en esta feature."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agregar el término de altura al modelo de coste (Priority: P1)

Dado que el modelo de coste de digitación (Feature 007) solo penaliza
movimiento (estiramiento, desplazamiento, cruce de cuerdas) y nunca la
posición en sí, se necesita un cuarto componente, independiente de los
otros tres, que le cueste a cada posición asignada su propia altura sobre
el mástil -- proporcional al traste, con un peso propio declarado -- de
forma que, entre dos posiciones que producen el mismo tono con el mismo
coste de movimiento, la más baja resulte más barata.

**Why this priority**: Es el mecanismo mismo de la feature -- sin este
componente no hay nada que medir ni que barrer. Es viable como slice
independiente porque se puede verificar por completo con posiciones e
instantes elegidos a mano (mismo patrón que Feature 007 US1), sin tocar
GuitarSet ni ningún dataset.

**Independent Test**: Se puede probar por completo construyendo un par de
posiciones sintéticas que producen el mismo tono, satisfacen el límite de
estiramiento y tienen el mismo coste de movimiento respecto de un
instante anterior, una en un traste bajo y otra en un traste alto,
verificando que el coste total calculado difiere exactamente en
`peso_altura_traste * (traste_alto - traste_bajo)`, y que una posición al
aire (traste 0) recibe coste cero de este componente -- sin invocar
ninguna secuencia larga ni ningún dataset real.

**Acceptance Scenarios**:

1. **Given** dos posiciones candidatas para la misma nota que producen el
   mismo tono y tienen el mismo coste de estiramiento, desplazamiento y
   cruce de cuerdas respecto del resto de la secuencia, **When** se
   calcula el coste total de cada una, **Then** la posición de traste más
   bajo tiene coste total menor, en una cantidad proporcional a la
   diferencia de traste y al peso declarado.
2. **Given** una posición asignada al traste 0 (cuerda al aire), **When**
   se calcula su coste de altura, **Then** ese componente aporta
   exactamente cero al coste total de esa posición.
3. **Given** el peso del nuevo componente fijado en cero, **When** se
   calcula el coste total de cualquier digitación, **Then** el resultado
   es idéntico al que produce el modelo de coste de la Feature 007 sin
   este componente -- el término nuevo no altera el comportamiento
   existente cuando está apagado.
4. **Given** cualquier digitación calculada con el nuevo componente,
   **When** se inspeccionan los pesos de desplazamiento y de cruce de
   cuerdas usados, **Then** ambos siguen fijados en `1.0`, sin cambio
   respecto de la Feature 007.

---

### User Story 2 - Confirmar que la optimalidad se sigue verificando contra fuerza bruta (Priority: P1)

Dado que la Feature 007 ya verifica, sobre secuencias sintéticas cortas,
que la digitación producida coincide en coste con el óptimo calculado por
fuerza bruta, se necesita repetir esa misma verificación con el nuevo
componente de altura incluido en el coste -- agregar un peso por nodo
(que depende solo de la posición de cada nota, no de la transición entre
instantes) no debe romper la subestructura óptima de la que depende la
programación dinámica, pero eso se confirma, no se asume.

**Why this priority**: Es una verificación de corrección del algoritmo,
no una métrica -- mismo estatus que FR-006 de la Feature 007. Sin ella,
un defecto de implementación del nuevo componente podría producir
digitaciones que ya no son óptimas de verdad, y la medición de User
Story 3 mediría un algoritmo roto en vez del modelo de coste.

**Independent Test**: Se puede probar por completo con las mismas
secuencias sintéticas cortas (o una extensión de ellas) que ya usa la
Feature 007, recalculando el óptimo por fuerza bruta con el término de
altura incluido, para varios valores del nuevo peso (incluido cero),
verificando que la digitación que el sistema produce coincide
exactamente en coste total con ese óptimo en todos los casos.

**Acceptance Scenarios**:

1. **Given** una secuencia corta con un óptimo calculable por fuerza
   bruta que incluye el término de altura, **When** el sistema asigna la
   digitación completa, **Then** el coste total de esa digitación es
   igual al coste del óptimo por fuerza bruta.
2. **Given** la misma secuencia corta evaluada con varios valores
   distintos del nuevo peso (incluido cero), **When** se compara cada
   resultado contra su propio óptimo de fuerza bruta calculado con ese
   mismo valor de peso, **Then** coinciden exactamente en todos los
   casos evaluados.

---

### User Story 3 - Barrer el peso y medir contra GuitarSet (Priority: P2)

Dado el componente de altura ya agregado y verificado, se necesita medir
`fraccion_coincidencia` sobre las mismas 288 grabaciones medibles de
GuitarSet para un conjunto de valores candidatos del nuevo peso, declarado
antes de correr la barrida, y documentar la curva completa de resultados
-- para elegir un valor con la evidencia delante, no a ojo ni ajustado
después de ver el resultado final.

**Why this priority**: Es la validación del cambio contra el criterio de
éxito de la feature -- depende de que User Story 1 y 2 ya funcionen
(el componente existe y no rompe la optimalidad). Es de prioridad menor
que las dos anteriores porque es la medición que consume el mecanismo, no
el mecanismo en sí.

**Independent Test**: Se puede probar por completo ejecutando la
medición existente de la Feature 007 (`agregar_conjunto` /
`fraccion_coincidencia`) repetida una vez por cada valor candidato del
nuevo peso sobre las 288 grabaciones medibles, verificando que el reporte
final incluye una cifra por valor candidato (la curva completa) y no solo
el valor máximo, y que ninguna de las 72 grabaciones reservadas participa
en ninguna de las corridas.

**Acceptance Scenarios**:

1. **Given** un conjunto de valores candidatos del nuevo peso, declarado
   antes de ejecutar cualquier medición, **When** se mide
   `fraccion_coincidencia` sobre las 288 grabaciones medibles para cada
   valor, **Then** el sistema produce una cifra por valor candidato, y el
   reporte conserva la cifra de todos los valores evaluados, no solo la
   más alta.
2. **Given** la curva completa de resultados, **When** alguno de los
   valores candidatos produce una `fraccion_coincidencia` mayor que
   `0.6186` (la línea base de la Feature 007), **Then** ese resultado se
   documenta como evidencia de que la preferencia por posiciones bajas
   mejora el parecido con el uso humano real sobre este conjunto.
3. **Given** la curva completa de resultados, **When** ningún valor
   candidato produce una `fraccion_coincidencia` mayor que `0.6186`,
   **Then** el sistema documenta esa ausencia de mejora como un hallazgo
   real -- nunca lo descarta en silencio ni lo trata como un error de
   ejecución -- y esa ausencia se registra explícitamente junto a la
   evidencia contraria de la canción real (ADR-0002, hallazgo 4) como una
   discrepancia sobre GuitarSet como conjunto de evaluación.
4. **Given** cualquier corrida de esta barrida, **When** se ejecuta,
   **Then** ninguna de las 72 grabaciones reservadas (semilla `20260908`)
   participa, y el presupuesto vigente (`0.55`) no se modifica como parte
   de esta feature.

---

### Edge Cases

- ¿Qué pasa cuando dos posiciones válidas para la misma nota están en
  cuerdas distintas pero el mismo traste (mismo coste de altura, distinto
  coste de cruce de cuerdas)? El nuevo componente no debe introducir
  ningún desempate implícito no declarado entre ellas -- el desempate,
  si existe, sigue siendo responsabilidad de los componentes ya
  existentes.
- ¿Qué pasa con el valor candidato del peso igual a cero durante la
  barrida de User Story 3? Debe reproducir exactamente
  `fraccion_coincidencia = 0.6186`, la línea base ya medida en la
  Feature 007 -- si no coincide, es evidencia de un defecto en la
  integración del nuevo componente, no una variación esperada.
- ¿Qué pasa si un valor candidato del peso es tan grande que domina por
  completo a los otros tres componentes? Es un punto legítimo de la
  curva a documentar, no un caso a excluir de la barrida.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST agregar exactamente un componente nuevo,
  independiente de los tres ya existentes (estiramiento, desplazamiento,
  cruce de cuerdas), al coste total de una digitación: un coste
  proporcional al traste de cada posición asignada, con su propio peso
  declarado explícitamente (mismo criterio que FR-014 de la Feature 007
  -- nunca una constante sin nombre).
- **FR-002**: El sistema MUST NOT modificar el peso de desplazamiento ni
  el peso de cruce de cuerdas en esta feature -- ambos MUST permanecer
  fijados en `1.0`, el mismo valor de la Feature 007, incluso cuando la
  hipótesis registrada en `research.md` #15 de esa feature sugiere que
  podrían estar desbalanceados. Ese rebalanceo queda fuera de alcance,
  reservado para una feature posterior con su propia medición.
- **FR-003**: Una posición asignada al traste `0` (cuerda al aire) MUST
  recibir coste `0` de este nuevo componente -- consecuencia directa de
  la proporcionalidad declarada en FR-001, no un caso especial adicional.
- **FR-004**: El sistema MUST preservar, sin cambio, todas las garantías
  de corrección tonal y de límite de estiramiento ya establecidas por la
  Feature 007 (FR-001/FR-002 de esa feature) -- agregar este componente
  al coste MUST NOT alterar qué posiciones se consideran válidas, solo
  cuánto cuestan las que ya eran válidas.
- **FR-005**: El sistema MUST verificar, sobre secuencias sintéticas
  cortas donde el óptimo se pueda calcular por fuerza bruta incluyendo el
  nuevo componente, que la digitación que produce con el componente
  activo coincide exactamente en coste con ese óptimo -- para varios
  valores del nuevo peso, incluido el valor `0` -- confirmando que
  agregar un peso por posición individual no rompe la subestructura
  óptima de la que depende la minimización (misma verificación que
  FR-006 de la Feature 007, extendida al componente nuevo).
- **FR-006**: El sistema MUST medir `fraccion_coincidencia` (misma
  métrica, misma comparación exacta por cuerda y traste, Principio VIII)
  sobre las mismas 288 grabaciones medibles de GuitarSet de la Feature
  007, una vez por cada valor de un conjunto de valores candidatos del
  nuevo peso, declarado por completo antes de ejecutar cualquier
  medición de la barrida.
- **FR-007**: El sistema MUST NOT elegir el valor final del nuevo peso
  mirando primero el resultado agregado y ajustando la elección después
  de verlo -- el conjunto de valores candidatos MUST quedar declarado
  antes de correr la barrida, y ningún valor adicional se agrega después
  de ver resultados parciales.
- **FR-008**: El sistema MUST documentar la curva completa de
  `fraccion_coincidencia` contra cada valor candidato evaluado en la
  barrida -- nunca solo el valor ganador -- con suficiente detalle para
  que una sesión futura entienda la elección sin volver a ejecutar nada
  (mismo criterio que FR-016 de la Feature 007).
- **FR-009**: El sistema MUST NOT modificar el presupuesto vigente
  (`0.55` sobre `fraccion_coincidencia`, Principio VII de la
  constitución) como parte de esta feature, sin importar el resultado de
  la barrida.
- **FR-010**: Si ningún valor candidato del nuevo peso produce una
  `fraccion_coincidencia` mayor que la línea base `0.6186` de la Feature
  007, el sistema MUST documentar ese resultado como un hallazgo real --
  una discrepancia entre la evidencia de la canción real (ADR-0002,
  hallazgo 4) y el conjunto de evaluación de GuitarSet -- en vez de
  tratarlo como una ejecución fallida o descartarlo en silencio.
- **FR-011**: El sistema MUST NOT medir ni inspeccionar, en ningún punto
  de esta feature, las 72 grabaciones reservadas de GuitarSet (semilla
  `20260908`, Principio VI) -- mismo conjunto ya reservado en los hitos
  2 y 3.
- **FR-012**: El sistema MUST registrar la alternativa de umbral (coste
  cero hasta un traste `N` declarado, costoso después) como una opción de
  diseño considerada y explícitamente no elegida para esta feature -- por
  requerir un parámetro adicional a calibrar frente a la forma
  proporcional elegida -- documentada, no descartada sin registro.

### Key Entities

- **Modelo de coste (extendido)**: Los cuatro componentes independientes
  del coste de una digitación -- los tres ya existentes de la Feature 007
  (estiramiento, desplazamiento, cruce de cuerdas) más el nuevo
  componente de altura de traste, cada uno con su peso declarado.
- **Peso de altura de traste**: El parámetro nuevo que declara cuánto
  cuesta, por unidad de traste, cualquier posición asignada -- el único
  peso que esta feature introduce; se fija con evidencia real de la
  barrida (User Story 3), nunca a ojo.
- **Valor candidato**: Uno de los valores del peso de altura de traste
  declarado antes de ejecutar la barrida, sobre el que se mide una
  `fraccion_coincidencia` propia.
- **Curva de barrida**: El conjunto completo de pares (valor candidato,
  `fraccion_coincidencia` medida) que documenta esta feature -- la
  evidencia completa detrás de la elección final del peso, no solo el
  valor ganador.
- **Hallazgo de comparación GuitarSet/canción real**: El resultado, en
  cualquier dirección, de comparar si la mejora que motivó esta feature
  en la canción real (ADR-0002, hallazgo 4) se confirma o no sobre
  GuitarSet como conjunto de evaluación.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El sistema reporta `fraccion_coincidencia`, medida sobre
  exactamente las mismas 288 grabaciones medibles de la línea base de la
  Feature 007, para cada uno de los valores candidatos del nuevo peso
  declarados antes de la barrida -- ninguna de las 72 grabaciones
  reservadas participa en ninguna de esas mediciones.
- **SC-002**: El 100% de las verificaciones de optimalidad contra fuerza
  bruta sobre secuencias sintéticas cortas siguen coincidiendo
  exactamente, con el nuevo componente incluido, para todos los valores
  de peso evaluados en esa verificación (incluido cero).
- **SC-003**: La curva completa de valor candidato contra
  `fraccion_coincidencia` queda documentada de forma que una sesión
  futura pueda reconstruir la elección del valor final del peso sin
  volver a ejecutar ninguna medición.
- **SC-004**: El 100% de las posiciones asignadas al traste `0` a lo
  largo de cualquier medición de esta feature reciben coste `0` del
  nuevo componente.
- **SC-005**: El peso de desplazamiento y el peso de cruce de cuerdas
  permanecen en `1.0`, sin cambio, en el 100% de las mediciones de esta
  feature.
- **SC-006**: El presupuesto vigente (`0.55`) permanece sin cambio al
  cierre de esta feature, independientemente de si algún valor candidato
  superó `0.6186`.

## Assumptions

- **Alcance del peso nuevo**: El coste de altura se aplica por posición
  individual asignada (una nota, un traste, un coste), no por instante ni
  por transición -- es un peso "de nodo", consistente con cómo el
  usuario describe la forma del término y con la verificación de
  optimalidad de User Story 2 (un peso por nodo no debería romper la
  subestructura óptima que ya asumen los componentes de transición).
- **Conjunto de valores candidatos de la barrida**: El conjunto concreto
  de valores a barrer (cuántos, en qué rango, con qué paso) se fija en
  `/speckit-plan` con su propia justificación, declarado por completo
  antes de ejecutar cualquier medición -- mismo criterio que la
  tolerancia de tono y el límite de estiramiento de la Feature 007
  (FR-014 de esa feature): parámetros del modelo fijados con evidencia,
  nunca inventados ni ajustados después de medir.
- **Reutilización de la partición medible/reservado**: Las mismas 288
  grabaciones medibles y 72 reservadas (semilla `20260908`) que la
  Feature 007 ya usa -- esta feature no define una segunda partición.
- **Comparación exacta**: `fraccion_coincidencia` se sigue midiendo por
  igualdad exacta de cuerda y traste (Principio VIII, sin tolerancia
  numérica), sin cambio respecto de la Feature 007.
- **Alternativa de umbral no implementada**: La forma de umbral (gratis
  hasta un traste `N`, caro después) se documenta como opción registrada
  en `research.md` de esta feature, no se implementa ni se mide en esta
  feature -- una feature futura podría retomarla si la forma proporcional
  no resulta suficiente.
