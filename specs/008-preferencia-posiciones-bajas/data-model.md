# Data Model: Preferencia por posiciones bajas en el modelo de coste

Extiende `data-model.md` de la Feature 007 -- un campo nuevo en un tipo
ya existente (`ModeloCoste`) y dos tipos nuevos para la medición de la
barrida (User Story 3). Ningún tipo de la Feature 007 se elimina ni
cambia de forma más allá de lo declarado aquí.

## `ModeloCoste` (extendido)

| Campo | Tipo | Descripción |
|---|---|---|
| `midi_cuerda_abierta` | `dict[str, int]` | Sin cambio (Feature 007) |
| `traste_minimo` | `int` | Sin cambio (Feature 007) |
| `traste_maximo` | `int` | Sin cambio (Feature 007) |
| `tolerancia_tono_cents` | `float` | Sin cambio (Feature 007) |
| `limite_estiramiento_trastes` | `int` | Sin cambio (Feature 007) |
| `ventana_instante_s` | `float` | Sin cambio (Feature 007) |
| `peso_desplazamiento` | `float` | Sin cambio -- `1.0`, MUST NOT modificarse en esta feature (FR-002) |
| `peso_cruce_cuerdas` | `float` | Sin cambio -- `1.0`, MUST NOT modificarse en esta feature (FR-002) |
| `peso_altura_traste` | `float` | **Nuevo (FR-001).** Peso del componente de altura de traste -- `0.0` en `MODELO_COSTE_POR_DEFECTO` (research.md #6, punto de control que reproduce exactamente el comportamiento de la Feature 007) hasta que la barrida (User Story 3) fije el valor final con evidencia real |

`frozen=True`, sin cambio en el resto del contrato del tipo (data-model.md
de la Feature 007).

## Coste de nodo (concepto, no un tipo nuevo)

No es una entidad con tipo propio -- es la función que `asignar_secuencia`
ya calculaba (`_estiramiento`, un peso de nodo, research.md #1 de la
Feature 007) extendida con un segundo sumando (research.md #1/#2 de esta
feature):

```text
costeNodo(combo) = estiramiento(combo) + peso_altura_traste · altura(combo)
altura(combo)    = Σ p.traste para cada p en combo
```

Documentado aquí porque cambia el valor que la recurrencia de
`asignar_secuencia` produce (data-model.md/research.md de la Feature
007, `Digitacion.coste_total`), aunque no introduce ningún campo ni
tipo nuevo en `Digitacion`.

## `PuntoBarrida`

Un único punto de la curva de la barrida (User Story 3): un valor
candidato del nuevo peso, con el resultado de coincidencia medido con
ese valor sobre las 288 grabaciones medibles.

| Campo | Tipo | Descripción |
|---|---|---|
| `peso_altura_traste` | `float` | Uno de los diez valores candidatos declarados en research.md #3/#5 -- nunca un valor agregado después de ver un resultado parcial (FR-007) |
| `resultado_coincidencia` | `ResultadoCoincidencia` | El mismo tipo que la Feature 007 ya define (`fraccion_coincidencia`, `num_notas_medidas`, `num_notas_coincidentes`), medido con `ModeloCoste` en este valor de peso y todos los demás campos iguales a `MODELO_COSTE_POR_DEFECTO` |

`frozen=True`.

## `ResultadoBarrida`

La curva completa (FR-008): el conjunto de todos los `PuntoBarrida`
evaluados, en el mismo orden que el conjunto de valores candidatos
declarado -- nunca solo el punto de mayor `fraccion_coincidencia`.

| Campo | Tipo | Descripción |
|---|---|---|
| `valores_candidatos` | `list[float]` | El conjunto declarado antes de ejecutar la barrida (research.md #3/#5), conservado tal cual para que el artefacto sea autocontenido -- no obliga a releer `research.md` para saber qué se barrió |
| `puntos` | `list[PuntoBarrida]` | Un `PuntoBarrida` por cada valor de `valores_candidatos`, en el mismo orden |

`frozen=True`. Persistido como artefacto versionado
(`mediciones/barrido_altura_traste.json`, mismo mecanismo de escritura
atómica que `ArtefactoDigitacion`) -- dato derivado que se genera con un
script, se verifica por invariantes (cantidad de puntos igual a
cantidad de valores candidatos, el punto `peso_altura_traste == 0.0`
coincide exactamente con la línea base `0.618633...` ya cerrada),
nunca se transcribe a mano (Principio IX).

## Relación entre entidades

```text
ResultadoBarrida
  ├─ valores_candidatos: list[float]  (los diez valores declarados)
  └─ puntos: list[PuntoBarrida]
        ├─ peso_altura_traste: float
        └─ resultado_coincidencia: ResultadoCoincidencia (ya existente, Feature 007)
```

Sin relación con `ArtefactoDigitacion` (Feature 007) más allá de
reutilizar `ResultadoCoincidencia` -- `ResultadoBarrida` es un artefacto
propio de esta feature, con su propio archivo, no un campo agregado a
`ArtefactoDigitacion`.
