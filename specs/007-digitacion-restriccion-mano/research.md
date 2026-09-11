# Research: Digitación con restricción de la mano

## 1. Subestructura óptima del modelo de coste: SÍ la tiene, programación dinámica da el óptimo exacto en tiempo lineal sobre la secuencia

**La pregunta, verificada, no asumida**: ¿el coste de cada transición
depende solo del instante anterior (propiedad de Markov / subestructura
óptima de Bellman), o depende de la historia completa de la secuencia?
Si depende solo del instante anterior, la recurrencia de programación
dinámica (DP) da el óptimo global exacto sin necesidad de búsqueda
exhaustiva ni heurísticas -- si CUALQUIER componente rompe esa
localidad, DP tal cual no alcanza.

**Verificación contra el modelo de coste declarado en `spec.md`, línea
por componente:**

- **Estiramiento (FR-002/FR-003).** "Dentro de un mismo instante" -- es
  una función del CONJUNTO DE POSICIONES DE ESE INSTANTE únicamente, sin
  ninguna referencia a instantes anteriores ni posteriores. Es, en la
  terminología de un grafo por capas, el **peso de un nodo** (la
  posición completa elegida para el instante `i`), no el de una arista.
- **Desplazamiento (FR-003/FR-004).** El propio texto de `spec.md` lo
  fija: "entre instantes CONSECUTIVOS". Nunca "entre este instante y
  cualquier instante anterior de la secuencia" -- es una función de
  exactamente dos instantes adyacentes (`i-1`, `i`) más `Δt` entre
  ellos (un dato de la entrada, no una decisión, así que no introduce
  dependencia de historia). Es el **peso de una arista** entre nodos
  consecutivos.
- **Cruce de cuerdas (FR-003/FR-004).** Mismo texto, misma estructura:
  "entre instantes consecutivos". El ejemplo que la spec usa para
  motivarlo (traste 1 de la sexta seguido de traste 1 de la primera) es
  explícitamente un par de DOS notas consecutivas, nunca tres o más.
  Mismo tipo de arista que desplazamiento.
- **Combinación de los tres (FR-003).** "El sistema MUST calcular... un
  coste total como la SUMA de tres componentes" -- aditiva, no un
  máximo, ni un promedio, ni ninguna otra combinación no lineal que
  pudiera acoplar términos no adyacentes. La suma de pesos de nodo más
  pesos de arista sobre un camino en un grafo por capas es exactamente
  la estructura que el principio de optimalidad de Bellman exige.

**Ningún componente declarado rompe la localidad.** No hay, en ningún
FR ni en la descripción del modelo de coste, ninguna noción de fatiga
acumulada que dependa de más de un paso atrás, ningún término de
suavizado que mire tres notas a la vez, ni ninguna normalización global
por la longitud de la secuencia (que acoplaría todos los términos entre
sí). El modelo, tal como está declarado, es exactamente un **camino más
corto en un grafo dirigido por capas** (una capa por instante, un nodo
por posición candidata válida de ese instante, una arista por cada par
de posiciones candidatas de instantes consecutivos) -- el mismo tipo de
estructura que resuelve el algoritmo de Viterbi para HMMs.

**Decision**: la digitación completa (User Story 2, FR-005) se calcula
con programación dinámica:

```text
mínCoste(1, p)   = costeEstiramiento(p)                                    para toda posición candidata p del instante 1
mínCoste(i, p)   = costeEstiramiento(p)
                    + mín sobre p' candidata de instante(i-1) de:
                          [ mínCoste(i-1, p') + costeTransición(p', p, Δt_i) ]     para i > 1
```

con `costeTransición = pesoDesplazamiento·costeDesplazamiento(p',p,Δt) +
pesoCruce·costeCruce(p',p,Δt)`, y el resultado final es
`mín sobre p candidata del último instante de mínCoste(último, p)`,
reconstruyendo el camino con backpointers -- exactamente el algoritmo de
Viterbi/programación dinámica sobre un enrejado (*lattice*), NO
búsqueda exhaustiva sobre todas las combinaciones de la secuencia
completa (que sería exponencial en el número de instantes) ni una
heurística sin garantía de optimalidad.

**Caso base explícito (Acceptance Scenario 4, User Story 2)**: el
primer instante no tiene términos de desplazamiento ni cruce, ya
reflejado en la recurrencia de arriba (`mínCoste(1, p) =
costeEstiramiento(p)` solamente).

**Complejidad**: `O(Σᵢ |candidatas(i-1)| × |candidatas(i)|)` -- lineal
en el número de instantes de la secuencia, con un factor por transición
acotado por el cuadrado del número de candidatas por instante. Ese
número de candidatas está acotado por una constante pequeña en la
práctica (research.md #8 más abajo, evidencia real: percentil 99 de
polifonía por ataque es ≤6, y las combinaciones de cuerda/traste válidas
para un acorde de ese tamaño, ya podadas por tolerancia de tono y límite
de estiramiento, son un puñado, no miles) -- **no exponencial, no hace
falta acotar artificialmente la longitud de la secuencia** (a diferencia
de la Feature 003 del hito 1, donde la duración real de un tema completo
sí forzó reducir el alcance de la medición con evidencia de reloj,
research.md #9 de esa feature -- aquí la propia estructura del problema
evita ese riesgo, verificado, no supuesto por analogía).

**Distinto de la verificación de optimalidad (FR-006).** Que el
algoritmo TEÓRICAMENTE dé el óptimo no exime de probar que la
IMPLEMENTACIÓN lo hace -- un error de índices en la recurrencia de
arriba seguiría produciendo un resultado, solo que incorrecto. FR-006
exige comparar contra fuerza bruta sobre secuencias sintéticas cortas
precisamente para esto: es un test de corrección de la implementación
de la DP, no una segunda decisión de diseño.

**Alternatives considered**: búsqueda exhaustiva sobre el producto
completo de candidatas de todos los instantes -- descartada, exponencial
en el número de instantes, inviable para una grabación real de GuitarSet
(cientos de notas). Heurísticas (voraz nota-a-nota, recocido simulado,
etc.) -- descartadas: el modelo tiene subestructura óptima verificada
arriba, así que una heurística sin garantía de optimalidad renunciaría a
una solución EXACTA que sí está al alcance sin costo adicional de
complejidad -- usar una heurística aquí sería exactamente el tipo de
"aproximación sin verificar" que FR-005 prohíbe explícitamente.

## 2. Precedente externo: DP/Viterbi es el enfoque académico estándar para este problema exacto

Búsqueda de literatura/bibliotecas existentes (antes de comprometerse a
una implementación propia, mismo criterio que el hito 2 evaluó modelos
de transcripción existentes en `/plan`): el enfoque de "programación
dinámica sobre un grafo de digitaciones candidatas, penalizando saltos
de posición" es el método clásico documentado para este problema desde
Sayegh (*Optimum Path Paradigm*) -- el benchmark académico estándar para
inferencia de tablatura asigna costes a transiciones entre digitaciones
y usa programación dinámica (Viterbi) para encontrar el camino óptimo
sobre un grafo pesado. Esto corrobora la sección #1 con precedente
externo -- no la reemplaza: la verificación de #1 se hizo contra el
modelo de coste que ESTA spec declara, no asumida porque la literatura
general use DP para problemas similares.

**Sin biblioteca directamente reusable.** Ninguna de las bibliotecas
Python encontradas implementa el modelo de coste declarado aquí (tres
componentes independientes, ponderados, con dependencia explícita del
tiempo real entre instantes, más tolerancia de tono y exclusión
explícita por instante) tal cual:

- [`tuttut`](https://pypi.org/project/tuttut/) -- modela el mástil como
  grafo completo y hace búsqueda en profundidad para encontrar TODAS las
  digitaciones que producen un conjunto de notas dado. Relevante como
  corroboración del enfoque de generación de candidatas por instante
  (User Story 1), no para la optimización de secuencia completa (User
  Story 2) ni para el modelo de coste de esta feature -- no se adopta
  como dependencia.
- [`PyGuitarPro`](https://pypi.org/project/PyGuitarPro/),
  [`fretboardgtr`](https://pypi.org/project/fretboardgtr/0.0.4/),
  [`fretboard`](https://pypi.org/project/fretboard/) -- formato de
  archivo y visualización de mástil/acordes, no optimización de
  digitación. Fuera de alcance de esta feature (FR-010: no produce
  tablatura formateada).
- [`guitar_dp`](https://github.com/jgollub1/guitar_dp) (GitHub, sin
  publicar en PyPI) -- proyecto de referencia que sí usa DP para este
  problema, confirma el enfoque general pero no es una biblioteca
  instalable/mantenida para reusar como dependencia.

**Decision**: implementación propia del algoritmo de DP (research.md
#1), siguiendo el patrón académico establecido -- no se reimplementa
"desde cero" un enfoque nuevo, se implementa la forma estándar del
problema para el modelo de coste específico que esta spec declara,
igual que el hito 2 usó `mir_eval` para el emparejamiento pero escribió
la lógica de agregación/clasificación propia porque ninguna biblioteca
existente resolvía esa parte específica.

Sources:
- [guitar_dp (GitHub)](https://github.com/jgollub1/guitar_dp)
- [tuttut (PyPI)](https://pypi.org/project/tuttut/)
- [PyGuitarPro (PyPI)](https://pypi.org/project/PyGuitarPro/)

## 3. Afinación estándar de GuitarSet: verificada contra el código fuente real de `mirdata`

Verificado contra `mirdata/datasets/guitarset.py` (instalado en este
proyecto), no contra documentación externa: `_GUITAR_STRINGS = ["E",
"A", "D", "G", "B", "e"]` (grave a agudo). Las frecuencias estándar de
afinación de guitarra (E2=82.4069, A2=110.0, D3=146.8324, G3=195.9977,
B3=246.9417, E4=329.6276 Hz) corresponden exactamente a los números MIDI
40, 45, 50, 55, 59, 64 (verificado con la fórmula estándar
`69 + 12·log2(f/440)`, sin redondeo -- los seis dan un entero exacto).
Confirma la Assumption "Afinación e instrumento" de `spec.md`: guitarra
de 6 cuerdas en afinación estándar Mi-La-Re-Sol-Si-Mi.

**Decision**: `MIDI_CUERDA_ABIERTA = {"E": 40, "A": 45, "D": 50, "G":
55, "B": 59, "e": 64}`, parámetro del modelo (FR-014), no una constante
enterrada sin nombre.

## 4. Rango de trastes: verificado con evidencia real, no estimado

Medido sobre las 288 grabaciones medibles reales (`construir_lista_grabaciones("medibles",
...)`, la misma partición del hito 2 -- Principio VI, nunca las 72
reservadas): para cada una de las 49538 notas de referencia, `traste =
round(tono_midi - MIDI_CUERDA_ABIERTA[cuerda_real])`. **Rango
observado: 0 a 19, el 100% de las notas dentro de ese rango.** Consistente
con un mástil de guitarra acústica de 19-20 trastes (GuitarSet es
guitarra acústica, Principio IV de la constitución).

**Decision**: rango de trastes válido `[0, 19]`, parámetro del modelo,
verificado contra el 100% de las notas medibles reales -- no un número
de catálogo de fabricante sin verificar contra este dataset en
particular.

## 5. Fuente de la posición real anotada: `track.notes[cuerda]`, el traste se DERIVA, no viene directo

Verificado contra el código fuente real de `mirdata` (`Track.notes`,
`load_notes`): `track.notes` es un `dict[str, NoteData]` con una
entrada por cuerda (`"E"`, `"A"`, `"D"`, `"G"`, `"B"`, `"e"`) -- **la
cuerda real anotada es la clave del diccionario en la que aparece la
nota**, no un campo separado. `notes_all` (que `ingestion.guitarset` del
hito 2 ya usa) es la SUMA de las seis, y pierde esa información de
cuerda al agregarlas -- por eso el hito 2 nunca necesitó leer `track.notes`
directamente, y esta feature sí.

**El traste NO se anota directamente.** `load_notes` (verificado leyendo
su código fuente completo) solo extrae `(tiempo, duración, tono_midi)`
de la anotación `note_midi` del JAMS -- ningún campo de traste. El
"traste real anotado" para User Story 3 se DERIVA:
`traste_real = round(tono_midi_real - MIDI_CUERDA_ABIERTA[cuerda])`. El
redondeo es necesario y está justificado con evidencia (research.md #9
más abajo: el tono real está afinado de forma fraccionaria, nunca cae
exacto en un traste entero, pero las 49538 notas medibles nunca se
desvían más de 50 cents del traste entero más cercano -- ninguna queda
ambigua entre dos trastes).

**Decision**: la posición real anotada de una nota es
`(cuerda_del_diccionario, round(tono_midi - MIDI_CUERDA_ABIERTA[cuerda]))`.
`round()` estándar de Python (redondeo al par más cercano en un empate
exacto) -- no se observó ningún empate exacto en 49538 notas reales
(máxima desviación medida: 49.98 de 50 cents), así que la convención de
desempate no cambia ningún resultado real, documentado igual por
completitud.

## 6. Definición de "instante": agrupar por PROXIMIDAD DE ATAQUE, NUNCA por solape de intervalo sostenido -- hallazgo real, no el primer intento

**El primer intento fue incorrecto, y se descartó con evidencia, no a
priori.** `spec.md` (Key Entities) define "Instante" como "notas...
simultáneas" sin fijar el criterio exacto de simultaneidad -- research.md
#8 de la Feature 006 (hito 2) ya había resuelto una pregunta parecida
para CLASIFICAR polifonía (por solape del intervalo `[inicio,fin]`), así
que ese fue el primer criterio probado aquí también. Verificado contra
las 288 grabaciones medibles reales, **rompe**: usando solape de
intervalo (una nota participa del instante de otra si su intervalo
`[inicio,fin]` cubre el `inicio` de la otra), la polifonía real máxima
observada es **7** -- una cuerda de más para un instrumento de 6
cuerdas. Diagnóstico: una nota puede seguir SONANDO (intervalo abierto,
por sostenido o cuerda al aire dejada vibrar) mucho después de que la
mano ya se movió a otra posición -- el intervalo anotado en GuitarSet
mide decaimiento ACÚSTICO, no cuánto tiempo el dedo sigue físicamente
sobre el traste. Confirmado con un caso extremo real, verificado por
grabación (no solo contado en agregado, para no repetir el error de
precisión que este mismo hallazgo señala en el criterio de instante):
estiramiento medido por solape de intervalo llega a 16 trastes en 2
instantes, ambos de la MISMA grabación (`00_SS1-68-E_solo`) --
físicamente imposible para una sola mano, evidencia de que el criterio
mide sonido sostenido, no postura de la mano.

**El criterio correcto: agrupar por cercanía del ATAQUE (el `inicio` de
la nota), con una ventana fija sin arrastre (todas las notas del grupo
dentro de la ventana desde el PRIMER `inicio` del grupo, no de la
última agregada -- evita que la ventana "camine" y encadene notas que
en realidad no son un mismo ataque).** Verificado con las mismas 288
grabaciones, tres ventanas (20/30/50 ms): con agrupación por ataque, la
polifonía real máxima es **6 en el 100% de los casos**, para las tres
ventanas -- nunca excede el número de cuerdas del instrumento. A 50 ms
aparecen 2 grupos con dos notas en la MISMA cuerda (imposible que sean
un mismo ataque -- una cuerda no puede iniciar dos notas a la vez); a
20 ms y 30 ms, cero. Se elige **30 ms**: cero colisiones de cuerda
repetida, y suficientemente ancha para cubrir un rasgueo real con
ligero *roll* entre cuerdas (percentil 25 de los huecos entre onsets
consecutivos ya medidos es de 7.4 ms -- 30 ms cubre eso con margen sin
acercarse a la ventana de 50 ms donde sí aparecen colisiones).

**Decision**: `VENTANA_INSTANTE_S = 0.03` (30 ms), parámetro del
modelo. Un "instante" es un grupo de notas cuyos `inicio_s` caen todos
dentro de esa ventana desde el primer `inicio_s` del grupo (agrupación
codiciosa sin arrastre, recorriendo la secuencia ordenada por inicio).
Esta es la fuente de verdad tanto para el estiramiento (User Story 1)
como para qué notas conforman una capa del grafo de la DP (User Story
2) -- **nunca** el solape de intervalo sostenido, que corresponde a un
concepto distinto (qué suena al mismo tiempo acústicamente) y no al que
esta feature necesita (qué debe fretear la mano al mismo tiempo).

**Alternatives considered**: solape de intervalo (research.md #8 del
hito 2) -- descartado arriba, con evidencia real de que rompe el límite
físico de 6 cuerdas. Ventana con arrastre (cada nota se compara contra
la ÚLTIMA agregada al grupo, no la primera) -- descartada: permite que
la ventana se extienda indefinidamente en una ráfaga de notas rápidas
pero no simultáneas (ej. un *run* melódico rápido), agrupando notas que
un guitarrista real toca una a la vez, no como acorde.

## 7. Estiramiento: las cuerdas al aire (traste 0) no participan del cálculo de envergadura

Hallazgo real, verificado antes de fijar el límite de estiramiento
(research.md #8 más abajo): incluso agrupando por ataque (research.md
#6), el estiramiento medido (traste máximo − traste mínimo del grupo)
todavía tenía una cola de casos hasta 14 trastes -- inconsistente con
cualquier mano humana. Al excluir las cuerdas AL AIRE (traste 0) del
cálculo de envergadura, 255 de 333 casos con estiramiento > 6 bajan a
≤ 6. Razón física: una cuerda al aire no requiere ningún dedo -- no le
exige nada a la mano que sí estén ocupando los dedos en otras cuerdas
del mismo instante.

**Decision**: el estiramiento de un instante se calcula como
`max(trastes pisados) − min(trastes pisados)` sobre las notas del
instante con `traste ≥ 1` únicamente. Si el instante tiene 0 o 1 notas
pisadas (el resto al aire), el estiramiento es 0 -- ninguna resta entre
menos de dos valores.

## 8. Límite físico de estiramiento (FR-002): evidencia real, no inventado

Medido sobre los 10457 "ataques" reales POLIFÓNICOS (2 o más notas
simultáneas, sin colisión de cuerda repetida, ventana 30 ms -- research.md
#6) de un total de 29936 ataques en las 288 grabaciones medibles,
estiramiento sobre trastes pisados únicamente (research.md #7):
**percentil 50 = 1, percentil 90 = 2, percentil 95 = 3, percentil 99 =
4, percentil 99.9 = 7, máximo = 14.**

(Corrección respecto a una primera cifra de esta misma sección: una
versión anterior citaba 32300 ataques y percentiles [0, 2, 2, 3, 5, 14]
-- mezclaba, por error, el total de ataques de la ventana de 20 ms con
percentiles calculados sobre TODOS los ataques, incluidos los
monofónicos (estiramiento 0 por definición, que diluye los percentiles
hacia abajo sin aportar nada a la pregunta real: dado que HAY un
acorde, cuánto estira). Corregido con una sola medición, coherente de
principio a fin, antes de fijar el parámetro -- el error se encontró
releyendo esta misma sección contra la salida real de los scripts, no
se dejó pasar por ser un hallazgo propio.)

**La cola residual (> 5, 21 casos de 10457, 0.20%) no se atribuye a
técnica real.** GuitarSet reconoce en su propia documentación que la
anotación de nota es AUTOMÁTICA a partir de un pickup hexafónico
(`audio_hex_original` vs. `audio_hex_debleeded` -- el propio dataset
distribuye una versión "sin fuga" precisamente porque hay fuga entre
canales de cuerdas adyacentes). Un estiramiento de 14 trastes en un
"mismo ataque" no es una postura de mano real -- es más consistente con
una detección espuria por fuga entre canales que con una digitación que
nadie podría tocar.

**Decision**: `LIMITE_ESTIRAMIENTO_TRASTES = 5`, parámetro del modelo
(FR-002/FR-014) -- por encima del percentil 99 (4) con un pequeño
margen, cubre el 99.8% de los ataques polifónicos reales medidos. El
0.2% residual (ruido de medición plausible -- ver percentil 99.9 = 7,
ya lejos de cualquier estiramiento tocable, y máximo 14, imposible
literalmente -- no técnica real) se excluye correctamente vía FR-013 --
**subir el límite para "cubrir" esa cola sería ocultar ruido de
anotación como si fuera una instrucción de digitación real**, el mismo
vicio que Principio VII prohíbe para
recalibrar un presupuesto después de ver el resultado, aplicado aquí a
un parámetro del modelo en vez de al presupuesto final.

## 9. Tolerancia de tono (FR-012): evidencia real, mismo valor que el hito 2 por coincidencia verificada, no por copiar sin mirar

Medido sobre las 49538 notas de referencia medibles reales: desviación
del tono real respecto del traste entero más cercano de su cuerda real
anotada. Media 7.16 cents (sesgo positivo pequeño, consistente con que
fretear una cuerda real la tensiona levemente y la afina un poco
agudo -- fenómeno físico conocido, no ruido sin explicación), desvío
estándar 11.09 cents. **100% de las 49538 notas caen dentro de 50
cents** del traste entero más cercano; percentil 99.9 = 49.13 cents (ni
siquiera la cola extrema se acerca al borde ambiguo de 50 cents exactos,
donde una nota quedaría a mitad de camino entre dos trastes).

**Decision**: `TOLERANCIA_TONO_CENTS = 50.0`, parámetro del modelo
(FR-012/FR-014) -- el mismo valor que `TOLERANCIA_TONO_CENTS` del hito
2, pero verificado aquí de forma independiente para un propósito
distinto (ahí, tolerancia de EMPAREJAMIENTO entre una estimación y una
referencia; acá, tolerancia de qué trastes pueden REPRODUCIR una
referencia fraccionaria) -- coincide en valor porque ambos describen la
misma fuente real de desafinación de GuitarSet, no porque se haya
copiado sin comprobar.

## 10. Polifonía > 6 cuerdas: imposible con la definición correcta de "instante" (#6), pero la exclusión se declara de todas formas

Con la definición de instante por solape de intervalo sostenido
(descartada en #6), 2 de 288 grabaciones medibles reales mostraban un
instante con 7 notas simultáneas -- más cuerdas de las que el
instrumento tiene. Con la definición correcta (agrupar por ataque,
ventana 30 ms), la polifonía real máxima observada es 6 en el 100% de
los casos -- el hallazgo de #6 ya resuelve esto en los datos reales
disponibles.

**Decision**: FR-013 (exclusión por instante sin combinación válida)
cubre este caso por construcción -- si algún instante futuro (fuera de
las 288 grabaciones medibles, o de una fuente de datos distinta) tuviera
más notas simultáneas que cuerdas disponibles, ninguna asignación de
cuerdas distintas (FR-002) sería posible, y el instante se excluye con
un motivo distinguible ("más notas simultáneas que cuerdas
disponibles"), separado del motivo "excede el límite de estiramiento" --
mismo criterio de motivo distinguible que `GrabacionNoExisteError` vs.
`TranscripcionFallidaError` en el hito 2. No hace falta un mecanismo
nuevo: es el mismo camino de exclusión de FR-013, con un motivo más.

## 11. Violaciones de no-solape dentro de una misma cuerda: ruido de anotación conocido, no bloqueante

Verificado: dentro de una misma cuerda, dos notas de referencia NUNCA
deberían solaparse en el tiempo (una cuerda suena una nota a la vez).
Medido sobre las 288 grabaciones medibles reales: **6 violaciones de
49538 notas (0.012%)** -- probablemente el mismo fenómeno de fuga entre
canales de la sección #8, o transición legato/bend en el límite de
detección de la anotación automática.

**Decision**: no se trata como error bloqueante -- es una propiedad
conocida de los datos, del mismo orden de magnitud que otras
imperfecciones ya documentadas de datasets reales en este proyecto
(Slakh sintetizado, hito 1; afinación fraccionaria, hito 2). Cuando
estas 6 notas participen de un instante (research.md #6), su
inconsistencia queda absorbida naturalmente: si producen una polifonía
aparente mayor a la real, el mecanismo de #10 ya la trata como
exclusión distinguible si corresponde -- no se necesita un chequeo de
integridad nuevo y separado para esto en el modelo de coste en sí,
aunque sí conviene registrarlo como limitación conocida en el reporte
final de User Story 3 (mismas dos limitaciones ya declaradas para Slakh
y para afinación fraccionaria, Principio VI de la constitución).

## 12. Unidad de distancia: trastes y cuerdas, no distancia física en milímetros -- simplificación consciente, no ignorancia

Los trastes de una guitarra real NO están espaciados uniformemente (la
escala es logarítmica -- cada traste más angosto que el anterior a
medida que sube el mástil). Una misma diferencia de N trastes es
físicamente más ancha cerca de la cejilla que cerca del cuerpo.

**Decision**: el estiramiento, el desplazamiento y el cruce de cuerdas
se calculan en unidades de NÚMERO de trastes/cuerdas, no en milímetros
sobre una escala de mástil real. Es una simplificación deliberada, no
una omisión sin registrar (mismo criterio que FR-004 de la Feature 006
exige para la duración ignorada a propósito): modelar la escala física
exacta agrega un parámetro más (la longitud de cuerda/escala) sin
evidencia todavía de que cambie las conclusiones de la validación (User
Story 3) lo suficiente para justificar la complejidad en esta primera
línea base. Si la medición contra GuitarSet muestra un sesgo sistemático
hacia posiciones bajas o altas del mástil (donde el error de esta
simplificación sería mayor o menor, respectivamente), esa es la primera
hipótesis a revisar -- declarado ahora para que no se descubra por
accidente.

## 13. Forma funcional del coste de movimiento: el tiempo divide, no resta -- pesos sin calibrar, declarados como parámetros

FR-004 exige que el mismo desplazamiento físico cueste más con menos
tiempo disponible. La forma más simple consistente con esto es
`coste = peso × distancia / Δt` (o `distancia × peso / max(Δt, ε)` para
evitar división por cero si dos notas comparten instante por construcción
-- no debería ocurrir, research.md #6 ya agrupa notas del mismo ataque
en un único instante, así que `Δt` entre instantes consecutivos es
siempre estrictamente positivo por construcción, pero `ε` se declara
igual como salvaguarda explícita, no como confianza ciega en esa
garantía).

**Decision**: `costeDesplazamiento(p', p, Δt) = pesoDesplazamiento ×
|trastes(p) − trastes(p')| / Δt`; misma forma para cruce de cuerdas
sobre distancia de cuerdas. Los pesos (`pesoDesplazamiento`,
`pesoCruce`, y el peso implícito 1.0 de estiramiento como referencia)
se declaran como parámetros del modelo (FR-014) **sin calibrar
numéricamente todavía** -- no hay, en este proyecto, un procedimiento
de ajuste automático de pesos (eso sería más cerca de entrenar un
modelo que de fijar una línea base, fuera del alcance de esta feature).
Se fijan en 1.0 cada uno como punto de partida neutral, documentado
explícitamente como valor de partida, no como resultado de evidencia --
a diferencia de los demás parámetros de esta sección (tolerancia,
límite de estiramiento, rango de trastes), que SÍ tienen evidencia real
detrás. Si la validación de User Story 3 muestra que el modelo con
pesos iguales se aleja sistemáticamente de la digitación real en una
dirección identificable (por ejemplo, favorece demasiado cruces de
cuerda sobre desplazamiento), esa es evidencia real para una sesión
posterior de recalibración -- no se ajusta a ciegas ahora para
"mejorar" una cifra que todavía no existe.

**Alternatives considered**: `coste = peso × distancia × (1/Δt²)`
(penalización cuadrática) -- descartada por ahora, sin evidencia de que
la relación real entre urgencia temporal y dificultad sea cuadrática en
vez de lineal; se documenta como alternativa a revisar con la misma
evidencia de User Story 3 mencionada arriba, no descartada para
siempre.

## 14. T024 -- primera medición real: la complejidad lineal proyectada se confirma con evidencia de reloj, no solo con el análisis de research.md #1

**Corrida real** (`just digitar medibles /home/mrjuancho/datos/guitarset`,
Basic Pitch/GPU no interviene aquí -- esta feature no tiene inferencia,
solo lectura de anotaciones + programación dinámica): las 288
grabaciones medibles reales, **0 excluidas** por completo (ninguna
`GrabacionNoExisteError`) -- **11.1 segundos de reloj real, de punta a
punta**, medido con `time`. Muy por debajo de cualquier riesgo de
escala: plan.md (Performance Goals) ya anticipaba, con el análisis de
complejidad de research.md #1, que esta feature NO enfrentaría el mismo
problema que forzó acotar el alcance de la medición del hito 1
(Feature 003, ~25 h proyectadas para el conjunto completo) -- **esta
medición lo confirma con tiempo real, no solo con el argumento teórico
de complejidad**, mismo criterio de esta feature para toda afirmación
cuantitativa.

**Resultado de `resultado_coincidencia` (FR-007, entrada real para el
futuro cierre del Principio VII del hito 3 -- esta tarea NO cierra el
presupuesto, solo lo produce)**:

- `num_notas_medidas` = 49535
- `num_notas_coincidentes` = 30644
- `fraccion_coincidencia` = **0.6186**

**Exclusiones de instante: solo 1 en las 288 grabaciones completas**
(sobre 49536 instantes procesados, prácticamente cero) -- consistente
con `LIMITE_ESTIRAMIENTO_TRASTES=5` (research.md #8) cubriendo el 99.8%
de los ataques polifónicos reales medidos: la cola de casos que ese
límite deja fuera es rara en la práctica real de punta a punta, tal
como research.md #8 ya predijo con la medición aislada de estiramiento.

**Recordatorio explícito (spec.md, "Dos verificaciones distintas" --
mismo que `ResultadoCoincidencia` ya documenta en su docstring):**
0.6186 es una fracción de COINCIDENCIA con la digitación real, no una
tasa de acierto/corrección -- el 38% restante no son "errores": una
posición distinta de la real puede reproducir el mismo tono y ser
igual de válida para tocar. Esta cifra es la validación del modelo de
coste contra comportamiento humano real, nunca "mi coste salió bajo"
(sería circular, FR-007) ni un porcentaje que se lea como fallos.

## 15. T025 -- calibración de pesos de movimiento: señal real medida, sin reponderar

**Medido sobre la corrida real de T024** (research.md #14): de las 49535
notas medidas, 18891 (38.1%) tienen una posición asignada que NO
coincide con la real -- para cada una, `Δcuerda = |índice_cuerda_asignada
- índice_cuerda_real|` (0=E grave a 5=e agudo) y `Δtraste =
|traste_asignado - traste_real|`, calculados con un script aparte sobre
el propio artefacto (`mediciones/digitacion_medibles.json`), nunca
inventados ni estimados.

**Primer hallazgo, estructural, ANTES de cualquier pregunta de
calibración -- el criterio que la tarea proponía originalmente
("¿discrepa solo en cuerda, o solo en traste?") resulta VACÍO para este
dominio, verificado, no asumido**: de los 18891 desacuerdos, el 100%
difiere en AMBAS dimensiones a la vez -- 0 casos de "solo cuerda"
(`Δtraste==0`, `Δcuerda>=1`), 0 casos de "solo traste" (`Δcuerda==0`,
`Δtraste>=1`). La razón es mecánica, no una propiedad del modelo de
coste: para un tono fijo, `traste = tono_midi - MIDI_CUERDA_ABIERTA[cuerda]`
es una función determinista de la cuerda -- dos posiciones con la misma
cuerda tienen necesariamente el mismo traste (mismo tono), y dos
posiciones con distinta cuerda tienen necesariamente distinto traste
(las seis cuerdas nunca comparten afinación). Ningún desacuerdo puede
aislar una sola dimensión -- documentado aquí para que una sesión
futura no vuelva a proponer el mismo criterio esperando un resultado
distinto.

**Segundo hallazgo, la señal real de asimetría (la pregunta que sí
tiene sentido: no "pura vs. mixta", sino la MAGNITUD relativa de cada
dimensión sobre los mismos 18891 desacuerdos)**:

- `Δcuerda`: media 1.15, mediana 1, percentiles [50,75,90,95,99,100] =
  [1, 1, 2, 2, 3, 4] -- **acotado y concentrado cerca de 0**: en la
  mitad de los desacuerdos, la cuerda asignada es la cuerda adyacente a
  la real, y el 95% se queda dentro de 2 cuerdas de distancia.
- `Δtraste`: media 5.39, mediana 5, percentiles [50,75,90,95,99,100] =
  [5, 5, 9, 10, 14, 19] -- **mucho más disperso y con un rango mayor**:
  la mitad de los desacuerdos ya está a 5 trastes o más de la posición
  real, y la cola llega hasta el extremo físico del mástil (19).

**Asimetría real, pero su interpretación como señal de recalibración
tiene un matiz que también hay que declarar (Principio VII: no
reponderar a ciegas, tampoco sobre-interpretar a ciegas)**: `Δtraste`
tiende a ser mayor que `Δcuerda` en términos absolutos en parte porque
la propia afinación estándar lo impone -- moverse una cuerda adyacente
mientras se mantiene el mismo tono cambia el traste en ~5 (una cuarta
justa) o ~4 (el par G-B) por construcción del instrumento, no por una
decisión del modelo de coste. Aun así, la concentración de `Δcuerda` en
valores bajos (rara vez más de 2-3 cuerdas de distancia) frente a la
dispersión mucho mayor de `Δtraste` (hasta 19) es una asimetría
observable en las UNIDADES de cada componente del coste, no solo un
artefacto de la afinación -- es consistente con la hipótesis de que
`peso_cruce_cuerdas` desalienta el cruce de cuerdas más de lo que
`peso_desplazamiento` desalienta el desplazamiento en trastes (ambos en
1.0 sin calibrar, research.md #13), aunque NO es una prueba concluyente
por sí sola: haría falta repetir esta medición tras una recalibración
real para confirmar que mover el balance de pesos hacia
`peso_desplazamiento` (relativo a `peso_cruce_cuerdas`) efectivamente
sube `fraccion_coincidencia`, no solo mueve la distribución de
`Δcuerda`/`Δtraste` sin mejorar la cifra que importa.

**Decisión de esta tarea: NO se reponderan `peso_desplazamiento`/
`peso_cruce_cuerdas` aquí.** Ajustar los pesos mirando el resultado que
se acaba de medir es la misma forma de sesgo que mover un umbral
después de verlo (Principio VII) -- el hallazgo queda registrado, con
su evidencia completa, como la entrada de una sesión posterior de
recalibración, que debe tener su propia medición de que el cambio
propuesto mejora `fraccion_coincidencia` de verdad, no solo mueve estas
distribuciones.
