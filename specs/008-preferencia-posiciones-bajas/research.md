# Research: Preferencia por posiciones bajas en el modelo de coste

## 1. El nuevo término es un peso de nodo -- preserva la subestructura óptima, verificado contra la implementación real, no solo contra `spec.md`

**La pregunta, verificada, no asumida (mismo criterio que research.md #1
de la Feature 007, ahora contra el código real en vez de solo contra la
spec):** ¿el nuevo componente de altura de traste introduce alguna
dependencia entre instantes no adyacentes, que rompería la recurrencia
de programación dinámica que `asignar_secuencia` ya implementa?

**Contra el código real** (`analytics/metrica_digitacion.py`,
`asignar_secuencia`, líneas 371-406): la recurrencia implementada hoy
es, literalmente,

```text
dp[0][j]  = estiramiento(combo_j)
dp[i][j]  = min sobre k de ( dp[i-1][k] + costeArista(combo_k, combo_j, Δt) )
            + estiramiento(combo_j)                                          para i > 0
```

donde `estiramiento(combo_j)` (línea 379 y línea 403,
`_estiramiento(posiciones_cur)`) ya ocupa exactamente el rol de **peso
de nodo** que research.md #1 de la Feature 007 identificó: una función
que depende ÚNICAMENTE de las posiciones candidatas del instante `j`
mismo, sumada una vez por nodo visitado, nunca de ningún instante
anterior ni posterior al par `(i-1, i)` que ya cubre `costeArista`.

**El nuevo componente ocupa el mismo rol, no uno nuevo.** Coste de
altura de una combinación `combo_j` es
`peso_altura_traste · altura(combo_j)`, con `altura(combo_j) = Σ
p.traste para p en combo_j` (decisión de diseño, ver hallazgo #4 más
abajo) -- una función que depende únicamente de las posiciones
candidatas de ESE instante, exactamente como `estiramiento`. Extender
el nodo a `costeNodo(combo_j) = estiramiento(combo_j) +
peso_altura_traste · altura(combo_j)` no introduce ningún término nuevo
de arista, ninguna dependencia de instantes no adyacentes, ni ningún
acoplamiento no lineal entre nodos -- es una suma adicional dentro de un
lugar de la recurrencia que ya existía y ya se sumaba una vez por nodo.

**Consecuencia para la prueba de optimalidad (User Story 2, FR-005 de
esta feature).** El argumento de Bellman que research.md #1 de la
Feature 007 ya estableció (suma de pesos de nodo más pesos de arista
sobre un camino en un grafo por capas = subestructura óptima) sigue
aplicando sin modificación: agregar un segundo sumando al mismo término
de nodo no cambia la forma de la recurrencia, solo el valor que
`costeNodo` devuelve. La verificación contra fuerza bruta (FR-005,
mismo patrón que FR-006 de la Feature 007) confirma esto con evidencia
empírica sobre secuencias sintéticas cortas, para varios valores del
nuevo peso incluido `0` -- pero el argumento estructural de por qué debe
sostenerse ya está cerrado aquí, contra el código real, no solo
razonado en abstracto.

**Complejidad.** Sin cambio: `costeNodo` sigue siendo `O(1)` por
combinación candidata (una suma sobre como mucho 6 posiciones), así que
la complejidad total de `asignar_secuencia` permanece
`O(Σᵢ |candidatas(i-1)| × |candidatas(i)|)`, lineal en el número de
instantes de la secuencia -- el nuevo término no agrega ningún factor
multiplicativo nuevo.

## 2. Forma exacta del nuevo término: suma por posición dentro del instante, no un agregado del acorde

**Decisión**: `altura(combo) = Σ p.traste para cada p en combo` -- el
coste de altura de una combinación completa es la suma de la altura de
CADA posición asignada en ese instante, no el máximo, ni el promedio, ni
solo la posición más grave.

**Por qué, con el mismo criterio que `_estiramiento` ya declara para
las cuerdas al aire (research.md #7 de la Feature 007)**: a diferencia
de `_estiramiento`, que excluye `traste == 0` porque una cuerda al aire
no exige dedo y por lo tanto no aporta envergadura de la mano, el nuevo
término SÍ debe incluir `traste == 0` en la suma -- pero como
`0 · peso_altura_traste = 0` para cualquier peso, incluirlo o excluirlo
de la suma no cambia el resultado numérico; se declara la regla como
"todas las posiciones, sin excepción" para que sea la MISMA regla para
las seis cuerdas, sin una condición especial que un lector tenga que
recordar (spec.md FR-003: "consecuencia directa de la
proporcionalidad", no un caso especial adicional).

**Por qué suma y no promedio ni máximo**: un acorde de tres notas en
trastes altos debe costar más que una nota sola en el mismo traste --
un promedio o un máximo tratarían un acorde de tres notas en el traste
12 igual de caro que una sola nota en el traste 12, lo cual diluiría la
señal exactamente en el caso (acordes) donde ADR-0002 hallazgo 4
reportó el problema más visible (cinco cuerdas en trastes 11-18). La
suma escala con el número de notas, igual que `costeArista` ya escala
implícitamente con el número de instantes de la secuencia (research.md
#1 de la Feature 007: coste total = SUMA de tres componentes).

## 3. Rango de la barrida: diez valores en escala logarítmica, elegidos contra la magnitud real medida del coste existente, no a ojo

**El argumento del pedido de esta sesión, verificado con evidencia
real, no solo razonado**: un peso demasiado chico no debe cambiar nada
(el término se pierde frente al resto del coste); uno demasiado grande
debe hacer que el modelo se pegue al traste más bajo alcanzable,
ignorando el coste de movimiento. Para que la curva muestre un óptimo
INTERIOR (visible como pico, no como borde del rango explorado), el
rango debe cubrir ambos extremos con margen real, no apenas rozarlos.

**Medido sobre la corrida real ya persistida
(`mediciones/digitacion_medibles.json`, misma corrida de T024/T025 de
la Feature 007, reconfirmada en esta sesión -- `fraccion_coincidencia =
0.618633...`, `30644/49535`, idéntica a la cifra ya cerrada en
Principio VII):**

- **Traste asignado, sobre las 49535 posiciones de la digitación
  actual**: media `6.08`, mediana `6`, percentil 90 `12` -- confirma
  con evidencia fresca, no solo con el caso de la canción real de
  ADR-0002, que el modelo hoy se asienta en trastes medios-altos.
- **Coste total actual (estiramiento + desplazamiento + cruce, los
  tres componentes de la Feature 007) por nota, agregado sobre las 288
  grabaciones**: `384733.80 / 49535 ≈ 7.77` por nota.

**De estos dos números, el rango de la barrida**:

- **Extremo chico**: `peso_altura_traste = 0.01` aporta, para una nota
  en el traste medio (`6.08`), un coste de altura de `≈0.061` -- menos
  del `1%` del coste actual por nota (`7.77`). Un valor de este orden
  no debería mover `fraccion_coincidencia` de forma perceptible; si lo
  hace, es en sí un hallazgo (el término es más sensible de lo
  esperado incluso en magnitudes chicas).
- **Extremo grande**: `peso_altura_traste = 100` aporta, para la MISMA
  nota en el traste medio, un coste de altura de `≈608` -- casi **80
  veces** el coste actual total por nota, y para una nota en el traste
  más alto observado en la práctica (`19`), `≈1900`. A esa escala, el
  término de altura domina por completo cualquier coste de movimiento
  real medido (research.md #15 de la Feature 007: hasta `Δtraste = 19`
  en los desacuerdos, un caso extremo, no el típico) -- el óptimo
  DEBE preferir la posición de traste más bajo alcanzable en casi
  cualquier instante, moviéndose solo cuando el tono lo exige.
- **Valor de control**: `peso_altura_traste = 0`. Por el Edge Case ya
  declarado en `spec.md`, MUST reproducir exactamente
  `fraccion_coincidencia = 0.618633...` -- si no coincide, es evidencia
  de un defecto de integración, no una variación esperable de la
  barrida.

**Conjunto de valores candidatos, declarado ahora, antes de correr
ninguna medición (FR-007 de esta feature -- no se agrega ni se quita
ningún valor después de ver un resultado parcial):**

```text
0, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100
```

Diez valores, escala logarítmica de base 10 con paso `×3`/`×10`
alternado (patrón estándar de barrida cuando se desconoce el orden de
magnitud correcto de antemano) -- cubre casi cuatro órdenes de magnitud
alrededor del punto donde el término de altura y el coste de movimiento
actual tienen la MISMA magnitud aproximada (`peso_altura_traste ≈ 1`,
dado que el coste por nota medido es `≈7.77` y la altura media es
`≈6.08`, así que `peso ≈ 1` ya los pone en el mismo orden de magnitud).
Si el óptimo de la curva cae en `1` o `3`, el rango tiene margen de
sobra en ambas direcciones para confirmarlo como interior; si cae en un
extremo (`0.01` o `100`), la barrida documenta ese borde como resultado
real, no lo oculta (mismo criterio que Edge Case de `spec.md`: "un
punto legítimo de la curva a documentar, no un caso a excluir").

## 4. Costo de ejecutar la barrida: medido, no proyectado -- reutilizar la lectura evita repetir el costo dominante diez veces

**Medido sobre la corrida real** (mismo entorno, mismos datos que
research.md #14 de la Feature 007, GuitarSet en
`/home/mrjuancho/datos/guitarset`):

- **Corrida completa vía CLI** (`just digitar medibles ...`, un
  proceso por corrida): `14.19s` y `12.42s` en dos repeticiones
  (`13.14s`/`13.33s` de tiempo de usuario+sistema, medido con `time`) --
  consistente con los `11.1s` ya reportados en research.md #14 de la
  Feature 007 (variación de entorno, no una regresión).
- **Desglosado dentro de un único proceso Python** (sin la sobrecarga
  de `uv run` -- medida aparte, `uv run python -c "pass"` tarda `0.03s`,
  despreciable frente al resto): **lectura de las 288 grabaciones
  (`leer_grabacion_con_posicion_real`, I/O + `mirdata`): `8.88s`**;
  **una pasada completa de `asignar_secuencia` + `evaluar_coincidencia`
  sobre las 288 grabaciones ya leídas: `1.63s`**.

**La lectura de GuitarSet (I/O + parseo de `mirdata`) es el costo
dominante y NO depende de `peso_altura_traste`** -- leer las
anotaciones reales de una grabación es idéntico sin importar qué
modelo de coste se vaya a aplicar después. Repetir esa lectura una vez
por valor candidato (diez veces, vía diez invocaciones separadas de la
CLI) desperdiciaría `~80s` de los `~90s` totales en trabajo idéntico
repetido.

**Decisión**: la barrida se implementa como un bucle EN UN SOLO
PROCESO que lee las 288 grabaciones UNA VEZ
(`leer_grabacion_con_posicion_real` por grabación, igual que
`ejecutar_digitacion` ya hace) y, para cada uno de los diez valores
candidatos, construye un `ModeloCoste` con ese `peso_altura_traste` (el
resto de los campos igual a `MODELO_COSTE_POR_DEFECTO`, Principio del
"un cambio por medición") y corre `asignar_secuencia` +
`evaluar_coincidencia` sobre los datos YA leídos, agregando con
`agregar_conjunto` -- **nunca** re-invocando `ejecutar_digitacion` (que
volvería a leer disco) diez veces.

**Costo total proyectado con esta arquitectura, confirmado con los
números medidos arriba**: `8.88s` (lectura, una vez) + `10 × 1.63s`
(diez pasadas de asignación+medición) `≈ 25.2s` -- muy por debajo de
los `~2 minutos` que el pedido de esta sesión estimaba asumiendo diez
corridas completas independientes, y confirmado con evidencia de reloj
real, no solo con el argumento de complejidad de la sección 1. Sigue
sin acercarse al riesgo de escala que forzó acotar la Feature 003 del
hito 1 (~25 h proyectadas) -- se reconfirma igual con tiempo real en
`/speckit-implement`, mismo criterio de esta sección para toda
afirmación cuantitativa (AGENTS.md), antes de asumirlo cerrado.

**Consecuencia de diseño**: la función que ejecuta la barrida
(`digitacion.orquestador.ejecutar_barrida_peso_altura`, contracts/
digitacion.md) recibe la lista de grabaciones y el conjunto de valores
candidatos, y hace la lectura una sola vez internamente -- no delega en
`ejecutar_digitacion` llamado en bucle desde afuera, que sería la forma
obvia pero forzaría a releer disco por cada punto de la curva.

## 5. El conjunto de valores candidatos se declara en código, no como argumento de línea de comandos

**Por qué**: FR-007 de esta feature prohíbe elegir el peso final
mirando el resultado y ajustando después de verlo. Un flag de CLI que
aceptara una lista arbitraria de valores candidatos permitiría, en la
práctica, correr la barrida, mirar la curva, y "volver a correr con
otro rango" hasta que el resultado se vea bien -- exactamente el vicio
que Principio VII ya prohíbe para presupuestos, aplicado aquí al
conjunto de valores candidatos de un parámetro de modelo. Declarar el
conjunto como una constante nombrada en el módulo (mismo patrón que
`MODELO_COSTE_POR_DEFECTO`) hace que cambiarlo sea un commit visible en
el historial, con su propia justificación escrita -- no un argumento
efímero de una invocación de terminal que no deja rastro.

## 6. Valor por defecto de `peso_altura_traste` en el modelo hasta que la barrida lo fije: `0.0`, el punto de control

**Decisión**: el campo nuevo de `ModeloCoste` se agrega con el modelo
por defecto (`MODELO_COSTE_POR_DEFECTO`) en `0.0` -- reproduce
exactamente el comportamiento de la Feature 007 sin este componente
(Acceptance Scenario 3, User Story 1 de `spec.md`) hasta que
`/speckit-implement` corra la barrida (User Story 3) y una sesión
posterior de `/speckit-constitution` fije el valor final con la
evidencia de la curva completa -- mismo patrón que la Feature 007 dejó
`peso_desplazamiento`/`peso_cruce_cuerdas` en `1.0` como punto de
partida explícito, nunca inventando un valor final antes de medir
(Principio VII).

## 7. Alternativa de umbral registrada, no implementada (spec.md, Assumptions)

La forma de umbral (coste cero hasta un traste `N` declarado, costoso
después) exigiría un segundo parámetro (el propio `N`) además del peso
-- un grado de libertad más para calibrar con la misma barrida, sin
evidencia de que produzca una curva mejor que la forma proporcional.
Se deja registrada aquí, no en el código: si una sesión futura necesita
retomarla, el argumento para no elegirla ahora (un parámetro menos que
calibrar) queda escrito y es la primera referencia a revisar antes de
reabrir la pregunta.
