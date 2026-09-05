# Data Model: Separación de guitarra con modelo preentrenado

**Input**: [spec.md](./spec.md) `Key Entities` | **Decisions**: [research.md](./research.md)

Todos los tipos son inmutables y viven en la capa nueva `separacion`
(research.md #8). Reutiliza `PistaAudio` de
`guitar_tabs_analysis.ingestion.slakh2100` y `Estimacion` de
`guitar_tabs_analysis.analytics.metrica_separacion` en vez de
redefinirlas — este feature es quien las produce, no quien las declara.

**Separación de responsabilidades entre dos módulos** (research.md #7): la
lógica de orquestación (`separador.py`) no importa `torch` ni `demucs`
directamente — solo depende de un protocolo (`Separador`) que el adaptador
real (`demucs_separador.py`) implementa. Esto es lo que permite que los
tests unitarios de la orquestación corran sin cargar el modelo real.

## `ModeloDeclarado`

El modelo preentrenado fijo, identificado de forma verificable (FR-002).

| Campo | Tipo | Origen / regla |
|---|---|---|
| `nombre` | `str` | `"Demucs"` — fijo para esta feature (research.md #1). |
| `variante` | `str` | `"htdemucs_6s"` — la única variante con fuente `"guitar"` propia (research.md #1). |
| `firma` | `str` | `"5c90dfd2"` — identificador del checkpoint en el repositorio remoto de Demucs (research.md #2). |
| `checksum_sha256_prefijo` | `str` | `"34c22ccb"` — prefijo del SHA-256 del archivo de pesos, verificado automáticamente por `torch.hub` al cargar (research.md #2); esta feature lo declara, no lo recalcula. |
| `licencia_pesos` | `str` | Nota fija citando la restricción de uso de los pesos (distinta del MIT del código), con su fuente (research.md #3) y el archivo de atribuciones del repositorio (`docs/ATRIBUCIONES.md`, FR-004). |

**Invariante**: es una única instancia constante para toda la feature (no
se construye por corrida) — expuesta como atributo del `Separador`
inyectado, no como parámetro adicional de ninguna función (evita el
problema de "campo sin forma de derivarse" señalado por el usuario para
`si_sdr()`/`emparejar_tema()` en la Feature 002).

## `TransformacionDeclarada`

Un cambio de formato aplicado (o verificado y no necesario) entre el audio
del conjunto y la entrada/salida del modelo (FR-005, FR-006, FR-007).

| Campo | Tipo | Origen / regla |
|---|---|---|
| `tipo` | `Literal["frecuencia_muestreo", "canales"]` | Qué propiedad del audio se verificó. |
| `direccion` | `Literal["entrada", "salida"]` | Si la verificación/transformación ocurre antes de la inferencia (entrada) o sobre el resultado del modelo (salida). `"frecuencia_muestreo"` solo aplica a `"entrada"` — el modelo no cambia la frecuencia de muestreo de su salida. |
| `aplicada` | `bool` | `False` si el valor de origen ya coincidía con el que el modelo espera (verificado, sin cambio real); `True` si se ejecutó una conversión real. |
| `detalle` | `str` | Descripción legible de la verificación o el cambio, p. ej. `"44100 Hz -> 44100 Hz (sin cambio)"` o `"1 canal -> 2 canales (duplicado)"`. |

**Invariante**: `separar_guitarra()` (ver contrato) siempre produce
exactamente dos `TransformacionDeclarada` de entrada (`frecuencia_muestreo`
y `canales`) y, cuando produce una estimación, una de salida (`canales`,
el colapso a mono) — nunca se omiten por haber resultado `aplicada=False`
(FR-005: "MUST declarar esa verificación... en el resultado" incluso sin
remuestreo).

## `ResultadoSeparacionTema`

El resultado de separar un tema (FR-001, FR-007).

| Campo | Tipo | Origen / regla |
|---|---|---|
| `tema_id` | `str` | Eco del argumento de `separar_guitarra()`. |
| `estimaciones` | `list[Estimacion]` (de `analytics.metrica_separacion`) | 0 o 1 elementos con `htdemucs_6s` en la práctica (research.md #1), pero el tipo no lo impone — FR-001 dice "cero o más". Vacía si el separador no produjo la fuente `"guitar"` (FR-009); con un elemento si sí la produjo, sin importar si su energía resulta nula (FR-010, delegado a Feature 002). |
| `transformaciones` | `list[TransformacionDeclarada]` | Ver invariante arriba — nunca vacía. |
| `modelo` | `ModeloDeclarado` | Eco de `separador.modelo_declarado` (FR-002). |

**Invariantes**:
- `len(estimaciones) <= 1` es una propiedad observada del adaptador real
  (`htdemucs_6s` produce como máximo una fuente `"guitar"` por tema), no
  una validación que `separar_guitarra()` imponga — un `Separador` de
  prueba con más de una fuente por nombre no tiene sentido dado que las
  claves del diccionario de salida son únicas por construcción de Python.
- Cada `Estimacion` en `estimaciones` tiene `audio.frecuencia_muestreo`
  igual a `separador.samplerate` y `audio.muestras` de una sola dimensión
  (mono, tras el colapso de canales de salida) — nunca el array
  multicanal crudo del modelo.

## `Separador` (protocolo)

La interfaz mínima que `separar_guitarra()` necesita — no una clase
concreta. El adaptador real (`DemucsSeparador`, en `demucs_separador.py`)
la implementa envolviendo `demucs.api.Separator`; los tests unitarios
inyectan un `SeparadorFalso` que la implementa sin importar `torch`.

| Miembro | Tipo | Regla |
|---|---|---|
| `modelo_declarado` | `ModeloDeclarado` | Constante del adaptador (research.md #1/#2). |
| `samplerate` | `int` (propiedad) | Frecuencia de muestreo que el modelo espera — `44100` para `htdemucs_6s`, pero leído de la propiedad real, no hardcodeado (research.md #4). |
| `audio_channels` | `int` (propiedad) | Número de canales que el modelo espera — `2` para `htdemucs_6s`, mismo criterio. |
| `separar(muestras)` | `(NDArray de forma (audio_channels, N)) -> dict[str, NDArray de forma (audio_channels, N)]` | Ejecuta la inferencia sobre audio ya transformado a `samplerate`/`audio_channels`; el diccionario devuelto puede o no incluir la clave `"guitar"` (FR-009). Puede levantar cualquier excepción ante un fallo real del modelo (FR-014) — `separar_guitarra()` la envuelve, no la relanza tal cual. |

## `SeparacionFallidaError`

Excepción propia para un fallo real del modelo o del framework durante un
tema (FR-014) — distinta del caso legítimo de `estimaciones == []`
(FR-009).

| Campo | Tipo | Origen / regla |
|---|---|---|
| `tema_id` | `str` | Identifica qué tema estaba procesándose. |
| `__cause__` | `Exception` | La excepción original de `demucs`/`torch`, encadenada con `raise ... from causa` — nunca silenciada ni reemplazada por un mensaje genérico que pierda la causa real. |

Mensaje: incluye `tema_id` y `str(causa_original)`, siguiendo el patrón ya
establecido en Feature 001 (`AGENTS.md`: "afirma el mensaje completo, no
solo que los identificadores aparezcan").

## Reutilizados sin cambios

- **`PistaAudio`** (`ingestion.slakh2100`): la mezcla de entrada de
  `separar_guitarra()`. `muestras` es un array de una sola dimensión
  (mono, confirmado por Feature 001 y por el input de esta feature).
- **`Estimacion`** (`analytics.metrica_separacion`): lo que esta feature
  produce; `identificador` se fija al nombre del stem del modelo
  (`"guitar"`) — no se inventa un identificador propio, se reutiliza el
  que el propio modelo asigna a esa fuente.
