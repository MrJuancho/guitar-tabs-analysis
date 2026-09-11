# Data Model: Detección de notas sobre guitarra limpia

## `NotaReferencia`

Una nota anotada por GuitarSet (`ingestion/guitarset.py`, envuelve
`mirdata`'s `Track.notes_all`).

| Campo | Tipo | Descripción |
|---|---|---|
| `tono_midi` | `float` | Tono en número MIDI (puede ser fraccionario -- GuitarSet anota afinación real, no cuantizada a semitono entero) |
| `inicio_s` | `float` | Instante de inicio, segundos |
| `fin_s` | `float` | Instante de fin, segundos -- **no participa del criterio de acierto** (FR-004), solo de la clasificación de polifonía (research.md #8) |

`frozen=True`. Fuente: `Track.notes_all.intervals` (`[inicio_s, fin_s]`
por fila) + `Track.notes_all.values` (tono MIDI), `mirdata`, verificado
en research.md #7.

## `NotaEstimada`

Una nota que `transcripcion.transcriptor.Transcriptor.transcribir()`
predice sobre una grabación.

| Campo | Tipo | Descripción |
|---|---|---|
| `tono_midi` | `float` | Tono estimado, número MIDI |
| `inicio_s` | `float` | Instante de inicio estimado, segundos |
| `fin_s` | `float` | Instante de fin estimado -- se conserva aunque no participe del criterio de acierto (FR-004), como la duración de referencia; refinamiento futuro declarado, no un campo muerto |

`frozen=True`. Fuente: `basic_pitch.inference.predict()`, tupla
`(start_time_s, end_time_s, pitch_midi, velocity, pitch_bend)` --
`velocity` y `pitch_bend` no se conservan en este tipo: no los usa
ningún requisito de esta feature (FR-001 solo pide tono e inicio).

## `ClasificacionPolifonia`

```python
ClasificacionPolifonia = Literal["monofonica", "polifonica"]
```

Propiedad derivada, nunca persistida de forma independiente -- se
calcula sobre un instante de tiempo contra un conjunto de
`NotaReferencia` (research.md #8): 0 o 1 referencias solapando ese
instante → `"monofonica"`; 2 o más → `"polifonica"`. Se evalúa para cada
`NotaReferencia` en su propio inicio. Para una `NotaEstimada`, la regla
depende de si se acredita contra una referencia (FR-005) o no
(research.md #17, FR-014): si se acredita, HEREDA la clasificación de
la referencia con la que empareja -- nunca se reevalúa por su propio
inicio; solo una estimada SIN pareja (un falso positivo) se clasifica
por su propio inicio contra las referencias de la misma grabación. En
ambos casos la fuente de la clasificación es siempre la referencia,
nunca la propia predicción (FR-006) -- lo que cambia es SOBRE QUÉ
instante se evalúa esa fuente cuando la estimada sí tiene con qué
heredar.

## `Acierto`

No es un tipo propio -- es el resultado booleano de evaluar FR-003/004
sobre un par `(NotaReferencia, NotaEstimada)`: tono dentro de
`TOLERANCIA_TONO_CENTS` (50.0, research.md #3) Y inicio dentro de
`VENTANA_INICIO_SEGUNDOS` (0.05, research.md #3), ambas condiciones
necesarias. Se calcula con `mir_eval.transcription`
(`offset_ratio=None`, research.md #4), nunca reimplementado
(research.md #5).

## `ExclusionDeteccion`

Módulo: `analytics/metrica_deteccion_notas.py` -- **no**
`deteccion/orquestador.py` (corrección de la sesión de `/speckit-tasks`,
research.md #11: `agregar_conjunto`, más abajo, recibe
`list[ResultadoDeteccionGrabacion]` en su propia firma pública, y
`analytics` no puede importar de `deteccion` sin crear una dependencia
circular -- `deteccion` es el paquete que importa de las tres capas de
abajo, nunca al revés). `deteccion/orquestador.py` importa este tipo
desde aquí, igual que `NotaReferencia`/`NotaEstimada`.

Una grabación apartada de la medición por fallo de inferencia (FR-012).

| Campo | Tipo | Descripción |
|---|---|---|
| `grabacion_id` | `str` | Identificador de la grabación excluida |
| `detalle` | `str` | Mensaje de la excepción real que causó el fallo |

`frozen=True`. Único motivo posible en esta feature (a diferencia de
`ExclusionMedicion` del hito 1, que distingue varios motivos): un fallo
de inferencia real. Una grabación sin ninguna nota de referencia (Edge
Cases de `spec.md`) **no** es una exclusión -- se mide igual, solo que
su exhaustividad queda sin denominador (FR-008).

## `ResultadoDeteccionGrabacion`

Módulo: `analytics/metrica_deteccion_notas.py` (misma corrección que
`ExclusionDeteccion` arriba -- `agregar_conjunto` lo necesita en su
propia firma pública).

El resultado de medir una única grabación -- unión etiquetada, igual
patrón que `ResultadoProcesamientoTema` del hito 1.

| Campo | Tipo | Descripción |
|---|---|---|
| `grabacion_id` | `str` | Identificador reproducible de la grabación |
| `notas_referencia` | `list[NotaReferencia] \| None` | `None` si `exclusion` no es `None` |
| `notas_estimadas` | `list[NotaEstimada] \| None` | `None` si `exclusion` no es `None` |
| `exclusion` | `ExclusionDeteccion \| None` | `None` si la grabación se procesó con éxito |

`frozen=True`. Se persiste el par crudo de listas de notas, no un
veredicto ya agregado -- la agregación (precisión/exhaustividad/balance
por subconjunto) es responsabilidad de `deteccion.orquestador`, que
puede recalcularla sobre cualquier subconjunto de grabaciones sin
volver a invocar el modelo, mismo motivo que Feature 004 persistió
`ReporteTema` crudo en vez de una cifra ya agregada.

## `ResultadoSubconjunto`

Precisión, exhaustividad y balance sobre un subconjunto de notas (global,
monofónico, o polifónico).

| Campo | Tipo | Descripción |
|---|---|---|
| `precision` | `float \| None` | `None` si el subconjunto de notas *estimadas* está vacío (denominador de precisión) |
| `exhaustividad` | `float \| None` | `None` si el subconjunto de notas *de referencia* está vacío (denominador de exhaustividad, FR-008) |
| `balance_f1` | `float \| None` | `None` si `precision` o `exhaustividad` son `None` |
| `num_notas_referencia` | `int` | Denominador real de `exhaustividad` -- se reporta aunque sea 0 (FR-008, nunca una cifra sin decir con cuántos casos se calculó) |
| `num_notas_estimadas` | `int` | Denominador real de `precision` |
| `verdaderos_positivos` | `int` | Conteo crudo de notas acertadas (`len(matching)` de `mir_eval.transcription.match_notes`) -- agregado en `/speckit-implement` (research.md #16, FR-013) para que `agregar_conjunto` pueda SUMAR conteos entre grabaciones y derivar la razón final, en vez de emparejar un pool de notas crudas de grabaciones distintas (defecto real: OOM medido en ~61 GB, y aciertos espurios entre clips sin relación) |

`frozen=True`.

## `ModeloTranscripcionDeclarado`

Mismo patrón que `ModeloDeclarado` del hito 1
(`separacion.separador.ModeloDeclarado`), para el modelo de
transcripción.

| Campo | Tipo | Descripción |
|---|---|---|
| `nombre` | `str` | `"Basic Pitch"` |
| `variante` | `str` | `"icassp_2022"` (nombre del modelo dentro del paquete, research.md #1) |
| `firma` | `str` | Identificador corto verificado en vivo contra el modelo real durante `/implement` -- no se inventa en este documento, mismo criterio que la Feature 003 aplicó para `htdemucs_6s` |
| `backend` | `str` | `"tflite"` -- corregido en `/speckit-implement` (research.md #2/#15: `onnx` resultó irresoluble tanto en Python 3.12 como en 3.10; el backend real, único disponible sin instalar TensorFlow completo, es TFLite) -- declarado explícitamente para que el artefacto registre con qué backend de inferencia se corrió |
| `licencia` | `str` | `"Apache-2.0 (código y pesos) -- ver docs/ATRIBUCIONES.md"` |

`frozen=True`.

## `ArtefactoDeteccion`

Módulo: `deteccion/orquestador.py` -- a diferencia de `ExclusionDeteccion`/
`ResultadoDeteccionGrabacion` arriba, este tipo sí vive en el orquestador:
nada por debajo de `deteccion` necesita referenciarlo en ninguna firma,
así que no hay riesgo de ciclo.

El artefacto final de una corrida completa sobre un conjunto de
grabaciones -- mismo rol que `ArtefactoMedicion` del hito 1.

| Campo | Tipo | Descripción |
|---|---|---|
| `modelo` | `ModeloTranscripcionDeclarado` | Modelo usado |
| `tolerancia_tono_cents` | `float` | `50.0`, declarada (FR-011) |
| `ventana_inicio_s` | `float` | `0.05`, declarada (FR-011) |
| `grabaciones` | `list[str]` | Lista exacta de grabaciones medidas |
| `exclusiones` | `list[ExclusionDeteccion]` | Con su motivo (FR-011) |
| `resultados_por_grabacion` | `list[ResultadoDeteccionGrabacion]` | Notas crudas por grabación, no agregadas |
| `global_` | `ResultadoSubconjunto` | Sobre todas las notas de referencia/estimadas del conjunto |
| `monofonico` | `ResultadoSubconjunto` | Sobre el subconjunto monofónico, partición heredada de un único emparejamiento (research.md #8/#17, FR-014) |
| `polifonico` | `ResultadoSubconjunto` | Sobre el subconjunto polifónico, misma partición |

Invariante permanente entre estos tres (SC-007, research.md #17):
`monofonico.verdaderos_positivos + polifonico.verdaderos_positivos ==
global_.verdaderos_positivos` -- igual que ya vale, sin excepción, para
`num_notas_referencia` y `num_notas_estimadas` de los tres.

`frozen=True`. `global_` lleva guion bajo final porque `global` es
palabra reservada de Python -- se serializa como `"global"` en el JSON
final (mismo criterio que cualquier otro campo, sin el guion bajo hacia
afuera).

## Relación entre entidades

```text
ArtefactoDeteccion
  ├─ 1 ModeloTranscripcionDeclarado (modelo)
  ├─ * ExclusionDeteccion (exclusiones)
  ├─ * ResultadoDeteccionGrabacion (resultados_por_grabacion)
  │     ├─ * NotaReferencia (notas_referencia)
  │     └─ * NotaEstimada (notas_estimadas)
  └─ 3 ResultadoSubconjunto (global_, monofonico, polifonico)

ClasificacionPolifonia -- propiedad derivada, calculada bajo demanda
  sobre NotaReferencia/NotaEstimada + el conjunto de NotaReferencia de
  la misma grabación (research.md #8), nunca persistida por separado.
```

No hay transiciones de estado -- como el hito 1, `ArtefactoDeteccion` es
el resultado final de una corrida completa, no un objeto con ciclo de
vida propio.
