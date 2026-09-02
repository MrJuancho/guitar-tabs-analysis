# Data Model: Lectura de un tema de Slakh2100

**Input**: [spec.md](./spec.md) `Key Entities` | **Decisions**: [research.md](./research.md)

Todos los tipos son inmutables (lectura, no construcción incremental) y
viven en la capa `ingestion`. Nombres en español para alinear con el
dominio del spec; los campos citan el FR que los origina.

## `PistaAudio`

Representa el audio de un archivo tal como está en disco — mezcla o
pista de guitarra, misma forma.

| Campo | Tipo | Origen / regla |
|---|---|---|
| `muestras` | `numpy.ndarray` | Decodificado con el `dtype` que coincide con el `subtype` real del archivo (research.md #1) — nunca reescalado. Forma `(n_muestras,)` porque Slakh2100 es mono (ver research.md). |
| `frecuencia_muestreo` | `int` | Tal como la reporta el archivo (`soundfile.info().samplerate`). Debe coincidir con la declarada por el conjunto para ese tema (FR-007). |

**Invariantes**:
- `frecuencia_muestreo > 0`.
- `muestras` no contiene `NaN`/`inf`, y está dentro del rango
  representable por su `dtype` de origen (FR-008). Se espera por
  construcción (sin transformación aritmética sobre los valores
  decodificados), pero esa expectativa es una propiedad del decodificador
  elegido hoy (research.md #1), no una garantía del lenguaje — por eso
  queda verificada con una aserción explícita en el mismo test de
  round-trip que cubre SC-005 (ver `tasks.md` T012), no solo documentada
  aquí.

## `PistaGuitarra`

Una pista de guitarra dentro de un tema, con su identidad de origen.

| Campo | Tipo | Origen / regla |
|---|---|---|
| `identificador_origen` | `str` | La clave del stem en `metadata.yaml` (p. ej. `"S01"`) — estable, nativa del dataset (spec.md Assumptions). |
| `audio` | `PistaAudio` | Ver arriba. |

**Invariantes**:
- `audio.muestras` tiene la misma longitud y `audio.frecuencia_muestreo`
  que la `Mezcla` del mismo tema (FR-006) — verificado en el momento de
  lectura, no delegado al llamador.

## `LecturaTema`

El resultado devuelto por la operación de lectura para un tema.

| Campo | Tipo | Origen / regla |
|---|---|---|
| `tema_id` | `str` | El identificador solicitado (eco, para trazabilidad en mensajes de error posteriores). |
| `mezcla` | `PistaAudio` | El audio de `mix.flac` (FR-001). |
| `guitarras` | `list[PistaGuitarra]` | Todas las pistas con `inst_class == "Guitar"` (FR-003) **y** `audio_rendered == true` — una pista de guitarra sin renderizar se excluye por FR-013, no cuenta como error (research.md #3, #4); lista vacía si no hay ninguna guitarra elegible (FR-009). Orden determinista para un mismo tema (spec.md Assumptions), no especificado más allá de eso. |

**Invariantes**:
- `len(guitarras) == 0` es un valor válido, no un estado de error
  (FR-009 / SC-002).
- Cada elemento de `guitarras` cumple las invariantes de
  `PistaGuitarra`, incluida la de longitud/frecuencia compartida con
  `mezcla`.

## Metadatos de origen (no expuestos como tipo público)

`metadata.yaml` por tema tiene, para cada stem, al menos los campos que
`research.md` #3/#4 usan para decidir inclusión:

| Campo (en `metadata.yaml`) | Uso en esta feature |
|---|---|
| `stems.<id>.inst_class` | Determina si el stem es guitarra (`"Guitar"`) o no (p. ej. `"Bass"` para bajo eléctrico) — FR-003, FR-004. |
| `stems.<id>.audio_rendered` | Si es `false`, el stem se excluye de `guitarras` aunque `inst_class == "Guitar"` — **FR-013** (research.md #4). No es un error ni dispara `ArchivoAudioNoLegibleError` (FR-012) — ver la fila de esa excepción más abajo. |

Estos campos se consumen internamente al construir `LecturaTema`; no se
exponen como una estructura pública separada porque ninguna acceptance
scenario del spec pide inspeccionar metadatos crudos, solo el resultado
ya filtrado.

## Errores (no son "entidades" de dominio, pero forman parte del contrato)

Cada uno corresponde a un modo de fallo explícito del spec — ver
[contracts/leer_tema.md](./contracts/leer_tema.md) para las condiciones
exactas de cada uno.

| Excepción | FR | Datos que lleva |
|---|---|---|
| `TemaNoExisteError` | FR-010 | `tema_id` |
| `ArchivoAudioNoLegibleError` | FR-012 | `tema_id`, ruta/nombre del archivo afectado — nunca se lanza para una pista excluida por FR-013 (no renderizada) |
| `LongitudInconsistenteError` | FR-011 | `tema_id`, `identificador_origen` de la pista afectada |

## Relaciones

```
LecturaTema 1 ── 1 PistaAudio (mezcla)
LecturaTema 1 ── * PistaGuitarra
PistaGuitarra 1 ── 1 PistaAudio (audio)
```

No hay transiciones de estado: todo el modelo es el resultado de una
única operación de lectura, sin ciclo de vida propio.
