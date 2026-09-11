# Data Model: Digitación con restricción de la mano

## `NotaEntrada`

**No es un tipo nuevo** -- reutiliza `ingestion.guitarset.NotaReferencia`
del hito 2 tal cual (`tono_midi`, `inicio_s`, `fin_s`), sin agregar
cuerda ni traste. `spec.md` (Key Entities) ya lo fija así: "mismo dato
que `NotaReferencia` del hito 2, sin cuerda ni traste todavía". Definir
un tipo paralelo sería duplicar un contrato ya cerrado sin ningún campo
nuevo que lo justifique.

## `NotaConPosicionReal`

Módulo: `ingestion/guitarset.py` (extendido, no un módulo nuevo -- research.md
#5: es el mismo dataset, la misma capa). Una nota real, leída
directamente de `track.notes` (por cuerda), con su cuerda y traste
reales ya resueltos en la misma lectura -- nunca reconciliada después
contra una segunda lista leída por separado (evita cualquier riesgo de
desalineamiento entre dos fuentes que deberían coincidir pero se leen
de forma independiente).

| Campo | Tipo | Descripción |
|---|---|---|
| `tono_midi` | `float` | Igual que `NotaReferencia.tono_midi` -- puede ser fraccionario (afinación real, research.md #9) |
| `inicio_s` | `float` | Igual que `NotaReferencia.inicio_s` |
| `fin_s` | `float` | Igual que `NotaReferencia.fin_s` |
| `cuerda_real` | `str` | Una de `"E"`, `"A"`, `"D"`, `"G"`, `"B"`, `"e"` -- la clave del diccionario `track.notes` en la que apareció la nota (research.md #5) |
| `traste_real` | `int` | `round(tono_midi - MIDI_CUERDA_ABIERTA[cuerda_real])` (research.md #3/#5) -- derivado, GuitarSet no anota traste directamente |

`frozen=True`. La lista completa de una grabación se ordena por
`inicio_s` de forma explícita al construirla (fusión de seis listas por
cuerda, sin asumir que ya vienen ordenadas).

## `Posicion`

| Campo | Tipo | Descripción |
|---|---|---|
| `cuerda` | `str` | Una de `"E"`, `"A"`, `"D"`, `"G"`, `"B"`, `"e"` |
| `traste` | `int` | `0` a `19` (research.md #4, rango verificado contra el 100% de las notas medibles reales) |

`frozen=True`. Una posición candidata o asignada -- el mismo tipo sirve
para ambos usos, no hay una distinción de tipo entre "candidata" y
"elegida" (la elección es simplemente cuál de las candidatas devuelve
`asignar_secuencia`).

## `ModeloCoste`

Los parámetros declarados del modelo (FR-014) -- nunca constantes sin
nombre dentro del código. Todos los valores tienen evidencia real
detrás (research.md #3/#4/#8/#9), salvo los pesos de movimiento,
declarados explícitamente como punto de partida sin calibrar
(research.md #13).

| Campo | Tipo | Descripción |
|---|---|---|
| `midi_cuerda_abierta` | `dict[str, int]` | `{"E": 40, "A": 45, "D": 50, "G": 55, "B": 59, "e": 64}` (research.md #3) |
| `traste_minimo` | `int` | `0` |
| `traste_maximo` | `int` | `19` (research.md #4) |
| `tolerancia_tono_cents` | `float` | `50.0` (research.md #9) |
| `limite_estiramiento_trastes` | `int` | `5` (research.md #8) |
| `ventana_instante_s` | `float` | `0.03` (research.md #6) |
| `peso_desplazamiento` | `float` | `1.0`, sin calibrar (research.md #13) |
| `peso_cruce_cuerdas` | `float` | `1.0`, sin calibrar (research.md #13) |

`frozen=True`. Se construye una vez (valores por defecto de esta
tabla) y se pasa explícitamente a cada función que lo necesita -- nunca
leído de una variable global ni de un módulo de configuración implícito.

## `Instante`

Un grupo de una o más `NotaEntrada` (o `NotaConPosicionReal`, según el
contexto) cuyos `inicio_s` caen dentro de `ventana_instante_s` desde el
primer `inicio_s` del grupo (research.md #6 -- agrupación codiciosa sin
arrastre, nunca por solape de intervalo sostenido).

| Campo | Tipo | Descripción |
|---|---|---|
| `notas` | `list[NotaEntrada]` | Una o más -- un `Instante` con una sola nota es el caso "nota sola", no un caso especial distinto |
| `inicio_representativo_s` | `float` | El primer `inicio_s` del grupo (el que definió la ventana) -- se usa para calcular `Δt` contra el instante anterior |

`frozen=True`. `len(notas) > 6` no puede ocurrir por construcción con
la definición de arriba sobre datos reales de GuitarSet (research.md
#6/#10), pero el código que consume `Instante` no asume el límite --
lo verifica (FR-002/FR-013), no lo da por garantizado por el tipo.

## `PosicionAsignada`

| Campo | Tipo | Descripción |
|---|---|---|
| `nota` | `NotaEntrada` | La nota de entrada a la que corresponde |
| `posicion` | `Posicion` | La posición que el algoritmo le asignó |

`frozen=True`. Una nota por posición, nunca al revés -- no hay ningún
escenario donde una misma `NotaEntrada` reciba dos posiciones.

## `InstanteExcluido`

Un instante apartado de la digitación por no tener ninguna combinación
de posiciones válida (FR-013) -- mismo patrón que `ExclusionDeteccion`
del hito 2, a nivel de instante dentro de una secuencia en vez de a
nivel de grabación completa.

| Campo | Tipo | Descripción |
|---|---|---|
| `inicio_representativo_s` | `float` | Identifica qué instante de la secuencia se excluyó |
| `motivo` | `str` | Distinguible entre, al menos: `"excede el límite de estiramiento"` y `"más notas simultáneas que cuerdas disponibles"` (research.md #10) -- nunca un mensaje genérico único para ambos casos |

`frozen=True`.

## `Digitacion`

El resultado de `asignar_secuencia()` (User Story 2) sobre una
secuencia completa de instantes de una grabación.

| Campo | Tipo | Descripción |
|---|---|---|
| `posiciones` | `list[PosicionAsignada]` | Una entrada por cada nota que SÍ recibió posición, en el mismo orden que la entrada -- las notas de instantes excluidos no aparecen aquí |
| `exclusiones` | `list[InstanteExcluido]` | Los instantes que no recibieron ninguna posición, con su motivo |
| `coste_total` | `float` | La suma de coste de la digitación elegida (FR-003) -- expuesto para que la verificación de optimalidad (FR-006) lo compare contra fuerza bruta sin tener que recalcularlo por fuera |

`frozen=True`.

## `PosicionReal`

La posición que GuitarSet anota que el guitarrista realmente usó para
una nota -- fuente de verdad exclusiva de User Story 3 (spec.md, Key
Entities), nunca usada para decidir qué posición asignar en User Story
1/2.

| Campo | Tipo | Descripción |
|---|---|---|
| `cuerda` | `str` | `NotaConPosicionReal.cuerda_real` |
| `traste` | `int` | `NotaConPosicionReal.traste_real` |

`frozen=True`. Estructuralmente idéntico a `Posicion` en sus campos,
pero es un tipo aparte a propósito: mezclar "la posición que el
algoritmo elige" con "la posición que el guitarrista realmente usó" en
un solo tipo invitaría a pasar una donde corresponde la otra sin que el
tipo lo marque -- mismo criterio de separación de tipos que
`NotaEstimada` vs `NotaReferencia` en el hito 2.

## `ResultadoCoincidencia`

Fracción de notas cuya posición asignada coincide exactamente con la
posición real anotada (FR-007) -- mismo patrón de diseño que
`ResultadoSubconjunto` del hito 2: conteos crudos expuestos para poder
sumarse entre grabaciones sin recalcular, denominador-cero resuelto
antes de dividir (FR-008 del hito 2, mismo criterio aquí).

| Campo | Tipo | Descripción |
|---|---|---|
| `fraccion_coincidencia` | `float \| None` | `None` si `num_notas_medidas == 0` (nunca una división por cero) |
| `num_notas_medidas` | `int` | Notas que recibieron una posición asignada Y tienen posición real conocida -- el denominador real de la fracción |
| `num_notas_coincidentes` | `int` | Cuántas de esas coinciden exactamente (`Posicion == PosicionReal`, comparación de `(cuerda, traste)`) |

`frozen=True`.

## `ExclusionDigitacion`

Una grabación completa apartada de la medición por fallo de lectura
(mismo patrón que `ExclusionDeteccion` del hito 2, a nivel de
grabación).

| Campo | Tipo | Descripción |
|---|---|---|
| `grabacion_id` | `str` | |
| `detalle` | `str` | Motivo distinguible del error real |

`frozen=True`.

## `ResultadoDigitacionGrabacion`

El resultado de digitar y medir una única grabación -- unión etiquetada,
mismo patrón que `ResultadoDeteccionGrabacion` del hito 2.

| Campo | Tipo | Descripción |
|---|---|---|
| `grabacion_id` | `str` | |
| `digitacion` | `Digitacion \| None` | `None` si y solo si `exclusion` no es `None` |
| `notas_con_posicion_real` | `list[NotaConPosicionReal] \| None` | `None` si y solo si `exclusion` no es `None` -- se conserva crudo, no solo el resultado de compararlo (mismo criterio que el hito 1/2: el dato derivado se recalcula desde la fuente, no se relee el propio artefacto) |
| `exclusion` | `ExclusionDigitacion \| None` | `None` si la grabación se procesó con éxito |

`frozen=True`.

## `ArtefactoDigitacion`

El artefacto final de una corrida completa sobre un conjunto de
grabaciones -- mismo rol que `ArtefactoDeteccion` del hito 2.

| Campo | Tipo | Descripción |
|---|---|---|
| `modelo_coste` | `ModeloCoste` | Los parámetros aplicados (FR-014/FR-016) |
| `grabaciones` | `list[str]` | Lista exacta de grabaciones medidas |
| `exclusiones_grabacion` | `list[ExclusionDigitacion]` | Grabaciones completas excluidas, con motivo |
| `resultados_por_grabacion` | `list[ResultadoDigitacionGrabacion]` | Resultados crudos, no agregados |
| `resultado_coincidencia` | `ResultadoCoincidencia` | Fracción agregada sobre todas las grabaciones no excluidas -- suma de conteos entre grabaciones, NUNCA promedio de fracciones por grabación (misma disciplina que `agregar_conjunto` del hito 2, research.md #16 de esa feature: una grabación con más notas pesa más que una con pocas) ni pool de notas crudas entre grabaciones (misma disciplina que FR-013 del hito 2: la programación dinámica corre siempre dentro de una única grabación) |

`frozen=True`. `resultado_coincidencia` se deriva sumando
`num_notas_medidas`/`num_notas_coincidentes` de cada
`ResultadoDigitacionGrabacion` no excluido, nunca promediando
`fraccion_coincidencia` por grabación.

## Relación entre entidades

```text
ArtefactoDigitacion
  ├─ 1 ModeloCoste (modelo_coste)
  ├─ * ExclusionDigitacion (exclusiones_grabacion)
  ├─ * ResultadoDigitacionGrabacion (resultados_por_grabacion)
  │     ├─ 1 Digitacion (digitacion) -- si no excluida
  │     │     ├─ * PosicionAsignada (posiciones)
  │     │     │     ├─ 1 NotaEntrada (nota)
  │     │     │     └─ 1 Posicion (posicion)
  │     │     └─ * InstanteExcluido (exclusiones)
  │     └─ * NotaConPosicionReal (notas_con_posicion_real) -- si no excluida
  └─ 1 ResultadoCoincidencia (resultado_coincidencia)
```
