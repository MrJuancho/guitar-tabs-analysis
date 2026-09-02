# Feature Specification: Lectura de un tema de Slakh2100

**Feature Branch**: `[001-lectura-tema-slakh2100]`

**Created**: 2026-09-01

**Status**: Draft

**Input**: User description: "Feature 1 — Lectura de un tema de Slakh2100

Dado el identificador de un tema del conjunto, el sistema devuelve el arreglo de audio de la mezcla y la colección de arreglos de las pistas identificadas como guitarra, cada una con su identificador de origen.

Una pista se identifica como guitarra si está etiquetada como tal en los metadatos del conjunto, sin distinguir entre limpia, distorsionada o acústica. El bajo eléctrico pertenece a otra familia en la clasificación General MIDI (Musical Instrument Digital Interface) y no cuenta como guitarra; debe verificarse contra los metadatos reales que no haya quedado agrupado con ellas.

El audio se lee tal como viene: no hay remuestreo, ni conversión de canales, ni normalización.

Criterios de aceptación

La mezcla y todas las pistas de guitarra del tema comparten longitud y frecuencia de muestreo.
La frecuencia de muestreo coincide con la declarada por el conjunto.
Las muestras están dentro del rango esperado.
Un tema sin pistas de guitarra devuelve colección vacía, sin error.
Un identificador inexistente falla con mensaje claro.
Una discrepancia de longitud entre la mezcla y cualquier pista de guitarra falla con mensaje claro, indicando el tema y la pista. No se recorta ni se rellena.

Fuera de alcance de esta feature

Qué temas entran al conjunto de evaluación. La colección vacía es un resultado legítimo aquí; el filtrado de temas sin guitarra pertenece a la feature de la métrica."

## Clarifications

### Session 2026-09-01

- Q: Si el identificador del tema existe pero el archivo de audio referenciado por los metadatos (la mezcla o una pista de guitarra) está ausente o no se puede leer del disco, ¿cómo debe responder el sistema? → A: Falla con un mensaje claro que identifica el tema y el archivo específico que no se pudo leer, como modo de fallo distinto de "identificador inexistente".
- Q: Cuando una pista está etiquetada como guitarra en los metadatos pero el propio conjunto de datos indica que esa pista nunca se renderizó a audio (no existe, ni existió, ningún archivo para ella), ¿el sistema debe excluirla silenciosamente de la colección de guitarras, o tratarla como el mismo fallo que un archivo ausente/no legible? → A: Se excluye de la colección de guitarras, igual que si esa pista no existiera — no cuenta como error ni como "archivo ausente".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Leer un tema con pistas de guitarra (Priority: P1)

Dado el identificador de un tema del conjunto Slakh2100 que tiene una o más pistas etiquetadas como guitarra en sus metadatos, se necesita obtener el audio de la mezcla completa junto con el audio de cada pista de guitarra, cada una asociada a su identificador de origen dentro del tema. Esto es lo mínimo indispensable para que cualquier medición o verificación posterior (separación, métrica, inspección cualitativa) tenga con qué trabajar.

**Why this priority**: Sin esta capacidad no existe ningún dato de entrada para el resto del hito 1. Es el punto de partida obligatorio de todo el pipeline.

**Independent Test**: Se puede probar por completo eligiendo el identificador de un tema conocido del conjunto con al menos una pista de guitarra en sus metadatos, invocando la lectura, y verificando que se recibe la mezcla y la colección de pistas de guitarra esperadas con sus identificadores de origen correctos.

**Acceptance Scenarios**:

1. **Given** un tema del conjunto con una única pista etiquetada como guitarra en sus metadatos, **When** se solicita la lectura por su identificador, **Then** el sistema devuelve el audio de la mezcla y una colección con exactamente esa pista, junto con su identificador de origen.
2. **Given** un tema del conjunto con varias pistas etiquetadas como guitarra (por ejemplo limpia, distorsionada y acústica), **When** se solicita la lectura por su identificador, **Then** el sistema devuelve el audio de la mezcla y una colección con todas esas pistas, cada una con su propio identificador de origen, sin fusionarlas.
3. **Given** un tema cuyos metadatos incluyen una pista de bajo eléctrico junto a las pistas de guitarra, **When** se solicita la lectura por su identificador, **Then** la colección devuelta no incluye la pista de bajo eléctrico.
4. **Given** el audio de la mezcla y de cada pista de guitarra devueltos por una lectura, **When** se inspeccionan sus propiedades, **Then** todas comparten la misma longitud (número de muestras) y la misma frecuencia de muestreo, y esa frecuencia coincide con la declarada por el conjunto de datos, y las muestras de audio están dentro del rango esperado para el formato de origen.
5. **Given** un archivo de audio de origen (mezcla o pista de guitarra) dentro del conjunto, **When** se lee a través del sistema, **Then** el contenido devuelto es el mismo que el del archivo de origen, sin remuestreo, sin conversión de número de canales y sin normalización de amplitud.
6. **Given** un tema cuyos metadatos etiquetan una pista como guitarra pero indican que esa pista nunca fue renderizada a audio (no existe archivo para ella), **When** se solicita la lectura por su identificador, **Then** la colección de guitarras devuelta no incluye esa pista, y esto no se trata como un error ni como un archivo ausente.

---

### User Story 2 - Leer un tema sin pistas de guitarra (Priority: P2)

Dado el identificador de un tema del conjunto que no tiene ninguna pista etiquetada como guitarra en sus metadatos, se necesita obtener la mezcla igualmente y una colección vacía de pistas de guitarra, sin que esto se trate como un error.

**Why this priority**: El conjunto de evaluación completo incluye temas sin guitarra, y filtrarlos es responsabilidad de una feature distinta (la de la métrica). Esta feature debe comportarse correctamente ante ese caso para no bloquear ni distorsionar ese filtrado posterior.

**Independent Test**: Se puede probar por completo eligiendo el identificador de un tema conocido sin pistas de guitarra en sus metadatos, invocando la lectura, y verificando que se recibe la mezcla junto con una colección vacía, sin ninguna excepción o fallo.

**Acceptance Scenarios**:

1. **Given** un tema del conjunto sin ninguna pista etiquetada como guitarra en sus metadatos, **When** se solicita la lectura por su identificador, **Then** el sistema devuelve el audio de la mezcla y una colección vacía de pistas de guitarra, sin producir ningún error.

---

### User Story 3 - Manejar identificadores inválidos y datos inconsistentes (Priority: P3)

Dado un identificador de tema que no existe en el conjunto, o un tema cuya mezcla y alguna de sus pistas de guitarra no comparten longitud, se necesita que el sistema falle de forma explícita y con un mensaje que identifique con precisión qué ocurrió, en vez de devolver datos parciales, corruptos o silenciosamente ajustados.

**Why this priority**: Es una salvaguarda necesaria para no propagar datos incorrectos hacia la métrica o el modelo, pero depende de que la lectura del caso normal (User Story 1) ya exista; por eso va después en prioridad, no en importancia.

**Independent Test**: Se puede probar por completo invocando la lectura con un identificador que no corresponde a ningún tema del conjunto y verificando el mensaje de error, y por separado invocando la lectura sobre un tema preparado con una discrepancia de longitud conocida entre la mezcla y una de sus pistas de guitarra, verificando que el mensaje de error identifica tanto el tema como la pista afectada.

**Acceptance Scenarios**:

1. **Given** un identificador que no corresponde a ningún tema del conjunto, **When** se solicita su lectura, **Then** el sistema falla con un mensaje claro que indica que el identificador no existe.
2. **Given** un tema cuya mezcla y una de sus pistas de guitarra tienen distinta longitud (número de muestras), **When** se solicita la lectura de ese tema, **Then** el sistema falla con un mensaje claro que identifica el tema y la pista afectada, sin recortar ni rellenar ninguno de los dos audios para forzar que coincidan.
3. **Given** un tema cuyo identificador existe pero cuyo archivo de audio de la mezcla o de una pista de guitarra está ausente o no se puede leer del disco, **When** se solicita la lectura de ese tema, **Then** el sistema falla con un mensaje claro que identifica el tema y el archivo afectado, distinto del mensaje usado para un identificador inexistente.

---

### Edge Cases

- Un tema sin pistas de guitarra en sus metadatos devuelve colección vacía, no un error (cubierto por User Story 2).
- Un identificador de tema inexistente falla con mensaje claro que lo identifica (cubierto por User Story 3).
- Una discrepancia de longitud entre la mezcla y cualquier pista de guitarra del mismo tema falla con mensaje claro que indica el tema y la pista, sin recortar ni rellenar (cubierto por User Story 3).
- Un tema con identificador existente cuyo archivo de audio (mezcla o pista de guitarra) está ausente o no se puede leer del disco falla con mensaje claro que identifica el tema y el archivo afectado, distinto del mensaje de identificador inexistente (cubierto por User Story 3, escenario 3).
- Una pista etiquetada como bajo eléctrico en los metadatos del tema, aunque esté agrupada cerca de las pistas de guitarra, no se incluye en la colección devuelta (cubierto por User Story 1, escenario 3).
- Un tema con múltiples pistas de guitarra devuelve cada una por separado con su propio identificador de origen, nunca combinadas en una sola (cubierto por User Story 1, escenario 2).
- Una pista etiquetada como guitarra cuyos metadatos indican que nunca fue renderizada a audio (sin archivo asociado) se excluye de la colección de guitarras, sin señalarse como error ni como archivo ausente (cubierto por User Story 1, escenario 6).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dado el identificador de un tema del conjunto Slakh2100, el sistema MUST devolver el audio de la mezcla de ese tema.
- **FR-002**: El sistema MUST devolver, junto con la mezcla, la colección de audios de todas las pistas del tema etiquetadas como guitarra en los metadatos del conjunto, cada una acompañada de su identificador de origen dentro del tema.
- **FR-003**: El sistema MUST considerar guitarra a toda pista etiquetada como tal en los metadatos, sin distinguir entre guitarra limpia, distorsionada o acústica.
- **FR-004**: El sistema MUST excluir de la colección de guitarras a cualquier pista que los metadatos reales del tema identifiquen como bajo eléctrico u otra familia distinta de guitarra, aun cuando esa pista aparezca agrupada junto a las de guitarra.
- **FR-005**: El sistema MUST leer el audio de la mezcla y de cada pista de guitarra tal como está almacenado en el conjunto: sin remuestreo, sin conversión del número de canales y sin normalización de amplitud.
- **FR-006**: El sistema MUST garantizar que la mezcla y todas las pistas de guitarra devueltas para un mismo tema comparten la misma longitud (número de muestras) y la misma frecuencia de muestreo.
- **FR-007**: El sistema MUST garantizar que la frecuencia de muestreo devuelta para la mezcla y para cada pista de guitarra coincide con la frecuencia de muestreo declarada por el conjunto de datos para ese tema.
- **FR-008**: El sistema MUST garantizar que las muestras de audio devueltas están dentro del rango de valores esperado para el formato de origen del archivo (sin valores no numéricos, infinitos, o fuera del rango representable por ese formato).
- **FR-009**: Cuando un tema no tiene ninguna pista etiquetada como guitarra en sus metadatos, el sistema MUST devolver la mezcla junto con una colección vacía de pistas de guitarra, sin señalar ningún error.
- **FR-010**: Cuando el identificador solicitado no corresponde a ningún tema del conjunto, el sistema MUST fallar con un mensaje de error claro que indique que el identificador no existe.
- **FR-011**: Cuando la mezcla y alguna pista de guitarra de un mismo tema tienen distinta longitud (número de muestras), el sistema MUST fallar con un mensaje de error claro que identifique tanto el tema como la pista afectada, sin recortar ni rellenar ninguno de los dos audios para hacerlos coincidir.
- **FR-012**: Cuando el identificador del tema existe pero el archivo de audio de la mezcla o de alguna pista de guitarra está ausente o no se puede leer del disco, el sistema MUST fallar con un mensaje de error claro que identifique tanto el tema como el archivo afectado, distinguible del mensaje usado para un identificador de tema inexistente (FR-010) — salvo el caso cubierto por FR-013, que no es una falla.
- **FR-013**: Cuando los metadatos del conjunto indican que una pista etiquetada como guitarra nunca fue renderizada a audio (no existe, ni debería existir, ningún archivo para ella), el sistema MUST excluirla de la colección de guitarras devuelta, sin señalarla como error y sin que dispare el fallo de archivo ausente de FR-012.

### Key Entities

- **Tema**: Unidad del conjunto Slakh2100, identificada por un identificador único, que agrupa una mezcla y las pistas individuales (con sus metadatos de instrumento) que la componen.
- **Mezcla**: El audio combinado de un tema, con una longitud (número de muestras) y una frecuencia de muestreo determinadas.
- **Pista de guitarra**: Una pista individual dentro de un tema cuyos metadatos la etiquetan como guitarra (limpia, distorsionada o acústica) y que efectivamente tiene audio renderizado (ver FR-013), identificada por su identificador de origen dentro del tema, con su propia longitud y frecuencia de muestreo.
- **Metadatos del conjunto**: Información descriptiva por tema y por pista (incluida la familia de instrumento según la clasificación General MIDI) que el sistema usa para determinar qué pistas cuentan como guitarra y cuáles no.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Para el 100% de los temas del conjunto que tienen al menos una pista de guitarra en sus metadatos, la lectura devuelve la mezcla junto con exactamente esas pistas de guitarra, correctamente identificadas por su origen, sin pistas de más ni de menos.
- **SC-002**: Para el 100% de los temas del conjunto sin pistas de guitarra en sus metadatos, la lectura se completa sin error y devuelve una colección vacía.
- **SC-003**: 0% de las pistas devueltas como guitarra corresponden en realidad a bajo eléctrico u otra familia de instrumento distinta, verificado contra los metadatos reales del conjunto.
- **SC-004**: 100% de los casos de identificador inexistente, de discrepancia de longitud, y de archivo de audio ausente o no legible producen un mensaje de error que identifica con precisión la causa (el identificador; o el tema y la pista; o el tema y el archivo), en vez de una falla silenciosa, datos truncados/rellenados, o un error genérico sin esa información.
- **SC-005**: El audio devuelto (mezcla y pistas de guitarra) es idéntico, muestra por muestra, al contenido de los archivos de origen del conjunto, confirmando la ausencia de remuestreo, conversión de canales o normalización.

## Assumptions

- El identificador de un tema es el identificador nativo que usa el conjunto Slakh2100 para nombrar cada tema (por ejemplo, el nombre de su directorio dentro de la distribución), y es estable entre lecturas.
- "Rango esperado" para las muestras de audio se interpreta como el rango representable por el formato de almacenamiento de origen del archivo (por ejemplo, el rango de un entero de 16 bits, o el rango [-1.0, 1.0] típico de PCM de punto flotante), sin valores no numéricos ni infinitos; no se exige ningún rango adicional impuesto por esta feature.
- El orden en que se devuelven las pistas de guitarra dentro de la colección no está definido por esta feature más allá de ser determinista para un mismo tema; la feature de la métrica es la que decide si ese orden le importa.
- Esta feature no decide qué temas del conjunto se usan para evaluación ni filtra temas sin guitarra; una colección vacía es un resultado válido y esperado, y ese filtrado corresponde a la feature de la métrica, fuera de este alcance.
- El conjunto Slakh2100 y sus metadatos (incluida la etiqueta de instrumento por pista) ya están disponibles localmente, referenciados según la política de fuentes de audio del proyecto; esta feature no cubre su descarga ni su verificación de integridad.
