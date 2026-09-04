# Feature Specification: Métrica de separación de guitarra

**Feature Branch**: `[002-metrica-separacion-guitarra]`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: "Feature 002 — Métrica de separación de guitarra

Dada una colección de pistas de guitarra estimadas y una colección de pistas
de guitarra de referencia de un mismo tema, el sistema calcula SI-SDR
(Scale-Invariant Signal-to-Distortion Ratio) emparejando cada referencia con
la estimación que mejor la aproxima, sin que dos referencias compartan la
misma estimación.

Reporta, por tema: el valor de SI-SDR de cada referencia emparejada, el
número de referencias del tema, el número de estimaciones recibidas, y qué
referencias quedaron sin emparejar.

Las referencias sin pareja NO se omiten del reporte. Un tema donde el
separador no produjo nada es un resultado malo, no un tema ausente; omitirlo
inflaría la agregación al considerar solo los casos donde el separador acertó.

Sobre un conjunto de temas, la agregación es la MEDIANA de los valores por
referencia. Se elige mediana y no media porque SI-SDR produce valores
atípicos que la media distorsiona.

Exclusiones del conjunto, con su conteo y motivo reportados junto a la
métrica: los temas sin ninguna guitarra de referencia, y los temas del
directorio `omitted`, que los autores del dataset recomiendan no usar por
duplicación de archivos MIDI entre divisiones.

Caso límite a resolver: una referencia con energía nula (silencio digital)
indefine el cálculo de SI-SDR. Debe decidirse qué hace el sistema en ese
caso, en vez de descubrirlo como una excepción numérica a mitad de una
corrida.

Fuera de alcance, explícitamente:
- Esta feature NO separa audio ni invoca ningún modelo. Recibe estimaciones y
  referencias ya cargadas; de dónde vengan las estimaciones es alcance de
  otra feature.
- Esta feature NO define ni evalúa un umbral de aprobación. Calcula y
  reporta. El presupuesto de la compuerta se fija después de la primera
  medición real, según el Principio VII de la constitución.

Verificación con respuesta conocida: pasar una referencia como su propia
estimación produce el valor máximo de la métrica. Esto permite verificar la
implementación completa sin necesidad de un separador, y debe ser un criterio
de aceptación."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir un tema individual (Priority: P1)

Dada la colección de pistas de guitarra de referencia y la colección de pistas de guitarra estimadas de un mismo tema, se necesita calcular el SI-SDR de cada referencia contra la estimación que mejor la aproxima, sin que dos referencias se emparejen con la misma estimación, y reportar el resultado junto con cuántas referencias y estimaciones había, y cuáles referencias quedaron sin pareja.

**Why this priority**: Es la unidad mínima de valor: sin poder medir un tema, no hay nada que agregar sobre un conjunto. Toda la feature depende de que este cálculo sea correcto.

**Independent Test**: Se puede probar por completo con una colección de referencias y una colección de estimaciones (reales o sintéticas) de un mismo tema, invocando el cálculo y verificando que el reporte devuelto contiene el SI-SDR de cada referencia emparejada, el conteo de referencias, el conteo de estimaciones recibidas, y la lista de referencias sin pareja.

**Acceptance Scenarios**:

1. **Given** un tema con una sola pista de referencia y una sola estimación que la aproxima razonablemente, **When** se calcula la métrica, **Then** el sistema devuelve el SI-SDR de esa referencia emparejada con esa estimación, junto con el conteo de una referencia y una estimación recibida, y ninguna referencia sin pareja.
2. **Given** un tema con varias pistas de referencia y al menos igual número de estimaciones, **When** se calcula la métrica, **Then** cada referencia queda emparejada con una estimación distinta (ninguna estimación se reutiliza entre dos referencias), y el reporte incluye el SI-SDR de cada una.
3. **Given** un tema con más referencias que estimaciones recibidas, **When** se calcula la métrica, **Then** el reporte incluye el SI-SDR de las referencias que sí pudieron emparejarse, y lista explícitamente las referencias que quedaron sin pareja, sin omitirlas del reporte.
4. **Given** un tema para el que no se recibió ninguna estimación, **When** se calcula la métrica, **Then** el reporte indica cero estimaciones recibidas y todas las referencias del tema aparecen listadas como sin pareja, no como un tema ausente del resultado.
5. **Given** una pista de referencia pasada también como su propia estimación, **When** se calcula la métrica, **Then** el SI-SDR reportado para esa referencia es el valor máximo posible de la métrica.
6. **Given** un tema con una pista de referencia cuya señal es silencio digital (energía nula), **When** se calcula la métrica, **Then** el sistema no falla con una excepción numérica no controlada; esa referencia aparece en el reporte con un motivo explícito que la distingue de una referencia simplemente sin estimación disponible.
7. **Given** un tema donde la asignación óptima le habría dado a una referencia una estimación cuya señal es silencio digital (energía nula) — la estimación existe y fue recibida, pero no aporta ninguna señal —, **When** se calcula la métrica, **Then** esa referencia aparece en el reporte como sin pareja, con un motivo que la distingue tanto de una referencia sin estimación disponible como de una referencia con su propia energía nula — un emparejamiento con una estimación silenciosa no es información útil y no debe presentarse como si lo fuera.

---

### User Story 2 - Agregar la métrica sobre un conjunto de temas (Priority: P2)

Dado un conjunto de temas, cada uno con su colección de referencias y de estimaciones, se necesita una única cifra agregada (la mediana de los valores por referencia de todo el conjunto) junto con el detalle de qué temas quedaron fuera del conjunto evaluado y por qué.

**Why this priority**: La cifra por tema (User Story 1) es necesaria pero no suficiente para comparar corridas o reportar el estado del hito; se necesita una agregación única y su alcance declarado. Depende de que la medición por tema ya exista.

**Independent Test**: Se puede probar por completo con un conjunto pequeño de temas preparados (algunos con referencias y estimaciones, algunos sin ninguna pista de referencia, alguno marcado como perteneciente al directorio `omitted`), invocando la agregación y verificando la mediana resultante y el listado de exclusiones con su conteo y motivo.

**Acceptance Scenarios**:

1. **Given** un conjunto de temas con al menos una pista de referencia cada uno, **When** se agrega la métrica sobre el conjunto, **Then** el sistema devuelve la mediana de los valores de SI-SDR de todas las referencias emparejadas y sin emparejar del conjunto, no la media.
2. **Given** un conjunto de temas donde alguno no tiene ninguna pista de guitarra de referencia, **When** se agrega la métrica, **Then** ese tema queda excluido del conjunto evaluado, y aparece contado junto con su motivo ("sin guitarra de referencia") en el reporte de exclusiones.
3. **Given** un conjunto de temas donde alguno pertenece al directorio `omitted` del dataset, **When** se agrega la métrica, **Then** ese tema queda excluido del conjunto evaluado, y aparece contado junto con su motivo ("directorio omitted") en el reporte de exclusiones.
4. **Given** un conjunto de temas donde uno de ellos no tuvo ninguna estimación recibida (el separador no produjo nada para ese tema), **When** se agrega la métrica, **Then** ese tema permanece en el conjunto evaluado (no se excluye) y sus referencias sin pareja empeoran la mediana agregada, en vez de desaparecer del cálculo.
5. **Given** el mismo conjunto de temas evaluado dos veces, una incluyendo un tema con referencias sin emparejar y otra omitiendo ese tema del conjunto, **When** se comparan ambas medianas, **Then** la mediana que incluye el tema con referencias sin emparejar es igual o peor que la que lo omite, nunca mejor — confirmando que omitir no puede inflar el resultado.
6. **Given** un conjunto de temas donde uno tiene una única pista de referencia y otro tiene varias, **When** se agrega la métrica, **Then** cada referencia individual pesa igual en la mediana final, de modo que el tema con más pistas de referencia influye proporcionalmente más en el resultado que el tema con una sola — la agregación no colapsa primero cada tema a un solo valor.
7. **Given** un conjunto de temas evaluado con distintas cantidades de referencias por tema (por ejemplo, algunos con una sola pista de guitarra, otros con dos o tres), **When** se agrega la métrica, **Then** el reporte agregado incluye, junto con la mediana, la distribución del número de referencias por tema (cuántos temas del conjunto evaluado tienen 1 referencia, cuántos tienen 2, etc.), permitiendo determinar sin inspeccionar cada reporte individual si el resultado está dominado por temas con muchas guitarras.

---

### Edge Cases

- Una referencia con energía nula (silencio digital) no puede tener un SI-SDR matemáticamente definido; el sistema la detecta antes de intentar el cálculo y la reporta con un motivo distinto de "sin estimación disponible" (cubierto por User Story 1, escenario 6).
- Una referencia y su estimación candidata pueden tener energía nula **simultáneamente**. El sistema no descubre esta combinación como un caso no contemplado: la falla de la referencia (no se puede formar la proyección) es más fundamental que la de la estimación (una proyección bien definida que resulta silenciosa), así que la referencia gana — se reporta igual que cualquier otra referencia de energía nula, no como un tercer caso.
- Cuando la asignación óptima le da a una referencia una estimación cuya propia señal es silencio digital (energía nula) — la estimación existe, fue recibida, y compitió por el emparejamiento — el sistema no la reporta como "emparejada" con un valor numérico que sugeriría una medición real; la reporta como sin pareja, con un motivo propio, distinto tanto de "sin estimación disponible" como de "energía nula de la referencia" (cubierto por User Story 1, escenario 7).
- Un tema sin ninguna estimación recibida permanece en el conjunto evaluado con todas sus referencias marcadas sin pareja; no se trata como un tema ausente (cubierto por User Story 1, escenario 4, y User Story 2, escenario 4).
- Un tema sin ninguna pista de guitarra de referencia se excluye del conjunto evaluado, distinto de un tema con referencias pero sin estimaciones (cubierto por User Story 2, escenario 2).
- Un tema del directorio `omitted` se excluye del conjunto evaluado independientemente de si tiene referencias o estimaciones (cubierto por User Story 2, escenario 3).
- Cuando se reciben más estimaciones que referencias, las estimaciones sobrantes no se emparejan con ninguna referencia y no aparecen en el reporte como error; solo se refleja su conteo total en "número de estimaciones recibidas".
- Un conjunto de temas que queda vacío tras aplicar las exclusiones no produce una mediana numérica; el sistema lo reporta explícitamente como conjunto vacío evaluado, no como error ni como cero.
- Pasar una referencia como su propia estimación produce el valor máximo posible de la métrica, sirviendo como verificación de respuesta conocida sin necesidad de un separador real (cubierto por User Story 1, escenario 5).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dada la colección de pistas de guitarra de referencia y la colección de pistas de guitarra estimadas de un mismo tema, el sistema MUST calcular el SI-SDR (*Scale-Invariant Signal-to-Distortion Ratio*) entre cada referencia y cada estimación candidata a emparejarla.
- **FR-002**: El sistema MUST emparejar cada referencia con, a lo sumo, una estimación, y cada estimación con, a lo sumo, una referencia (ninguna estimación se comparte entre dos referencias), eligiendo entre los emparejamientos posibles el que mejor aproxima el conjunto completo de referencias del tema.
- **FR-003**: Cuando el número de estimaciones recibidas para un tema es menor que el número de referencias, el sistema MUST dejar sin emparejar a las referencias que no alcanzan estimación, sin fallar y sin inventar una estimación para ellas.
- **FR-004**: El sistema MUST reportar, por tema: el valor de SI-SDR de cada referencia emparejada, el número de referencias del tema, el número de estimaciones recibidas, y la lista de referencias que quedaron sin emparejar.
- **FR-005**: El sistema MUST incluir en el reporte de un tema a las referencias sin pareja, identificadas individualmente, en vez de omitirlas o representarlas solo como una cifra agregada.
- **FR-006**: Cuando una pista de referencia tiene energía nula (silencio digital), el sistema MUST detectarlo antes de intentar el cálculo de SI-SDR sobre ella y MUST reportarla como no evaluable, con un motivo explícito distinto del usado para una referencia que simplemente no recibió estimación, en vez de propagar una excepción numérica no controlada.
- **FR-007**: Dado un conjunto de temas, el sistema MUST calcular la mediana (no la media) de los valores por referencia de todas las referencias del conjunto evaluado, agrupando en un solo conjunto todas las referencias de todos los temas (no un valor por tema primero) e incluyendo tanto las emparejadas como las que quedaron sin pareja por cualquier motivo (falta de estimaciones o energía nula de la referencia) — de forma que un tema con más pistas de referencia pesa proporcionalmente más en la mediana final que uno con menos.
- **FR-008**: El sistema MUST tratar a cada referencia sin pareja, para efectos de la agregación, como si tuviera un valor de SI-SDR igual a infinito negativo (−∞) — el límite inferior teórico de la métrica, nunca producido por un cálculo real, que garantiza ordenar por debajo de cualquier resultado finito sin introducir una constante numérica arbitraria (por ejemplo, "−100 dB" sería un número inventado, no un límite).

  **Dependencia con FR-007, no coincidencia.** Este tratamiento es válido únicamente porque la agregación (FR-007) es la mediana: un estadístico de orden que solo necesita la posición relativa de cada valor en el ranking, no su magnitud, y para el que −∞ es una posición perfectamente definida (siempre el mínimo). FR-007 y FR-008 son una sola decisión con dos partes, no dos elecciones independientes que dan la casualidad de ser compatibles. Si la agregación cambiara en el futuro a un estadístico sensible a la magnitud (por ejemplo, un promedio, donde −∞ contaminaría cualquier resultado que lo incluya, o una desviación estándar), este tratamiento de las referencias sin pareja deja de ser válido y debe revisarse junto con FR-007, no por separado.
- **FR-009**: El sistema MUST excluir del conjunto evaluado a todo tema que no tenga ninguna pista de guitarra de referencia, y MUST reportar, junto con la métrica agregada, el número de temas excluidos por este motivo.
- **FR-010**: El sistema MUST excluir del conjunto evaluado a todo tema perteneciente al directorio `omitted` del dataset, y MUST reportar, junto con la métrica agregada, el número de temas excluidos por este motivo, distinguible del motivo de FR-009.
- **FR-011**: El sistema MUST calcular el SI-SDR de una referencia pasada como su propia estimación, y ese valor MUST ser el máximo posible de la métrica, sirviendo como verificación de respuesta conocida.
- **FR-012**: El sistema MUST NOT separar audio ni invocar ningún modelo de separación; recibe únicamente colecciones de audio ya cargadas para un tema.
- **FR-013**: El sistema MUST NOT definir ni evaluar un umbral de aprobación sobre la métrica calculada; su responsabilidad termina en calcular y reportar.
- **FR-014**: Cuando el conjunto de temas evaluado queda vacío tras aplicar las exclusiones, el sistema MUST reportarlo explícitamente como un conjunto vacío, sin producir un valor numérico de mediana y sin señalar un error.
- **FR-015**: El sistema MUST reportar, junto con la mediana agregada, la distribución del número de referencias por tema dentro del conjunto evaluado (cuántos temas tienen 1 referencia, cuántos tienen 2, y así sucesivamente), de forma que se pueda juzgar si el resultado está dominado por temas con muchas pistas de guitarra sin tener que inspeccionar el reporte de cada tema por separado, y comparar dos corridas cuyas medianas difieren sobre subconjuntos con distinta composición.
- **FR-016**: Cuando la asignación óptima (FR-002) le asignaría a una referencia una estimación cuya propia señal es silencio digital (energía nula), el sistema MUST reportar esa referencia como sin pareja, no como emparejada — un valor numérico de SI-SDR en el reporte implica una medición real, y un emparejamiento con una estimación silenciosa no lo es. El motivo reportado MUST ser distinguible tanto del de FR-006 (energía nula de la referencia) como del de FR-003 (sin estimación disponible): son tres diagnósticos distintos sobre tres fallas distintas — la referencia, la estimación asignada, y la ausencia total de candidatos — y no deben colapsarse en un solo motivo.

### Key Entities

- **Tema evaluado**: Unidad de evaluación identificada de forma unívoca, con su colección de pistas de guitarra de referencia y su colección de pistas de guitarra estimadas.
- **Emparejamiento**: Asociación uno a uno entre una referencia y una estimación de un mismo tema, con el valor de SI-SDR resultante; una referencia y una estimación participan en, a lo sumo, un emparejamiento cada una.
- **Referencia sin pareja**: Una pista de referencia del tema que no quedó asociada a ninguna estimación *utilizable*, con uno de tres motivos explícitos y mutuamente distinguibles: falta de estimaciones disponibles (FR-003), energía nula de la propia referencia (FR-006), o la asignación óptima le habría dado una estimación cuya señal es silencio digital (FR-016) — en este último caso sí existía una estimación candidata y participó del emparejamiento, pero no se reporta como "emparejada" porque no representa una medición real.
- **Reporte por tema**: El resultado del cálculo sobre un tema individual: los valores de SI-SDR de sus referencias emparejadas, el número de referencias, el número de estimaciones recibidas, y la lista de referencias sin pareja con su motivo.
- **Conjunto evaluado**: El subconjunto de temas de una corrida que participa en la agregación, tras aplicar las exclusiones declaradas.
- **Exclusión**: Un tema apartado del conjunto evaluado antes de calcular la métrica, con su motivo (sin guitarra de referencia, o directorio `omitted`) y su conteo, reportado junto con la métrica agregada.
- **Resultado agregado**: La mediana de los valores por referencia (emparejados y sin pareja) de todos los temas del conjunto evaluado, junto con el detalle de exclusiones y la distribución del número de referencias por tema del conjunto evaluado.
- **Distribución de referencias por tema**: Conteo de cuántos temas del conjunto evaluado tienen cada cantidad de pistas de referencia (1, 2, 3, ...), reportado junto con la mediana agregada para que su composición sea auditable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Para toda referencia pasada como su propia estimación, el SI-SDR reportado es el valor máximo posible de la métrica, verificable sin necesidad de un separador real.
- **SC-002**: El 100% de las referencias de cada tema del conjunto evaluado aparecen en el reporte de ese tema, ya sea con su valor de SI-SDR emparejado o marcadas explícitamente como sin pareja con su motivo — ninguna referencia desaparece del reporte.
- **SC-003**: En ningún reporte, dos referencias del mismo tema comparten la misma estimación emparejada.
- **SC-004**: Al comparar la agregación de un mismo conjunto de temas con y sin un tema que tiene referencias sin emparejar, la mediana que incluye ese tema nunca resulta mejor que la que lo omite — confirmando que el sistema no infla el resultado por omisión.
- **SC-005**: El 100% de los temas excluidos del conjunto evaluado (sin guitarra de referencia, o del directorio `omitted`) aparecen contados con su motivo en el reporte de exclusiones, y ninguno de ellos aparece también dentro del conjunto evaluado.
- **SC-006**: El 100% de las referencias con energía nula presentes en un conjunto de temas se reportan con un motivo explícito, sin que ninguna corrida se interrumpa por una excepción numérica no controlada.
- **SC-009**: En ningún reporte por tema aparece una `ReferenciaEmparejada` cuya estimación asociada sea silencio digital — toda referencia en esa situación aparece en la lista de sin pareja, con un motivo distinguible de los otros dos.
- **SC-007**: Ningún reporte por tema u agregado incluye un umbral de aprobación ni un veredicto de pase/falla sobre la métrica.
- **SC-008**: Dado el reporte agregado de cualquier corrida, se puede determinar cuántos temas del conjunto evaluado tienen cada cantidad de referencias sin recalcular nada ni abrir los reportes individuales por tema, y esa distribución es suficiente para explicar una diferencia entre las medianas de dos corridas sobre subconjuntos con distinta composición de referencias por tema.

## Assumptions

- Esta feature recibe las colecciones de audio de referencia y de estimaciones ya cargadas en memoria, con el contrato de datos establecido por la feature de lectura de un tema (001); no cubre de dónde provienen las estimaciones ni cómo se cargan.
- El emparejamiento "que mejor aproxima el conjunto completo de referencias" se resuelve como una asignación óptima global (uno a uno, sin repetir estimaciones) que maximiza la suma de SI-SDR del tema, siguiendo la práctica estándar de evaluación invariante a permutación en separación de fuentes, no una asignación voraz referencia por referencia.
- La fórmula de SI-SDR sigue la definición estándar de la literatura de separación de fuentes (invariante a escala, comparando la señal objetivo escalada contra el error residual); no se documentan variantes propietarias.
- "Peor valor posible" para una referencia sin pareja es, concretamente, infinito negativo (−∞) — ver FR-008 para el valor y su dependencia explícita con la elección de la mediana como agregación (FR-007).
- El directorio `omitted` y la ausencia de pistas de guitarra de referencia se determinan a partir de los mismos metadatos e identificadores de tema que usa la feature de lectura (001); esta feature no redefine qué identifica a un tema.
- El presupuesto numérico (umbral de aprobación) mencionado en el Principio VII de la constitución no se fija en esta feature ni en ninguna posterior hasta contar con una primera medición real sobre el conjunto de desarrollo.
- **Ponderación de la mediana agregada (decisión explícita, no implícita).** La mediana sobre un conjunto de temas se calcula agrupando todas las referencias de todos los temas en un solo conjunto (FR-007), no calculando primero un valor por tema y agregando esos valores. Esto significa que un tema con varias pistas de referencia pesa proporcionalmente más que uno con una sola. Se elige esta ponderación para el hito 1, en vez de dar el mismo peso a cada tema, porque el Principio V de la constitución exige que la caída de rendimiento con la polifonía sea un resultado visible y no un defecto a esconder; dar a cada tema el mismo peso diluiría ese efecto, ya que un tema difícil con tres guitarras contaría igual que un tema fácil con una sola. La distribución de referencias por tema (FR-015) es lo que hace esta ponderación auditable en vez de opaca.

> Alternativa registrada para el futuro, no descartada: ponderar por tema (mediana de medianas), con peso igual sin importar el número de referencias. Es la pregunta correcta para el hito 1 (¿qué tan bien se recupera cada pista de guitarra?), pero probablemente deje de serlo en el hito 2, donde lo que importa es si un tema completo resulta transcribible, no si una pista suelta se separó bien. Esta feature y la constitución (Principio VII, aún `ABIERTO`) no cierran esa puerta: la ponderación por referencia es la elegida para esta medición, no una regla permanente sobre qué pesa qué en toda métrica futura.
