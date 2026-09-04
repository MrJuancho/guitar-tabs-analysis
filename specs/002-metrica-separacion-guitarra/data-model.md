# Data Model: Métrica de separación de guitarra

**Input**: [spec.md](./spec.md) `Key Entities` | **Decisions**: [research.md](./research.md)

Todos los tipos son inmutables (resultado de un cálculo, no construcción
incremental) y viven en la capa `analytics`. Nombres en español para
alinear con el dominio del spec y con Feature 001; los campos citan el FR
que los origina. Reutiliza `PistaAudio`/`PistaGuitarra` de
`guitar_tabs_analysis.ingestion.slakh2100` en vez de redefinirlos.

## `Estimacion`

Una pista estimada por un separador (fuera de alcance de esta feature — de
dónde viene queda en `spec.md#Assumptions`), con un identificador que el
llamador le asigna para poder nombrarla en el reporte.

| Campo | Tipo | Origen / regla |
|---|---|---|
| `identificador` | `str` | Asignado por el llamador (p. ej. el nombre de archivo de salida del separador); solo necesita ser único dentro del tema. |
| `audio` | `PistaAudio` (de `ingestion.slakh2100`) | Sin transformación adicional — se reutiliza el mismo tipo que ya usa Feature 001, ver research.md #3. |

## `MotivoSinPareja`

Alias de tipo (`Literal["sin_estimacion_disponible", "energia_nula",
"estimacion_silenciosa"]`) — no una clase nueva. Distingue las tres razones,
mutuamente excluyentes, por las que una referencia queda sin pareja
(FR-003, FR-006, FR-016): falta de estimaciones, energía nula de la propia
referencia, o una estimación candidata que sí existía pero resultó
silenciosa. Tres fallas distintas — nunca se colapsan en un solo valor
(spec.md, Key Entities "Referencia sin pareja").

## `ReferenciaEmparejada`

Una referencia que sí quedó asociada a una estimación (FR-002).

| Campo | Tipo | Origen / regla |
|---|---|---|
| `identificador_referencia` | `str` | `identificador_origen` de la `PistaGuitarra` emparejada. |
| `identificador_estimacion` | `str` | `identificador` de la `Estimacion` emparejada. |
| `si_sdr` | `float` | Resultado de `si_sdr()` (research.md #1) para este par, siempre genuinamente calculado — puede ser `+inf` (FR-011, exacto por cálculo, research.md #5). **Nunca** el `-inf` por convención de una estimación silenciosa (FR-016): esa referencia se reclasifica a `sin_pareja` antes de construir este reporte, así que un valor aquí siempre representa una medición real, nunca un sentinel. |

**Invariantes**: `identificador_estimacion` no se repite entre dos
`ReferenciaEmparejada` del mismo `ReporteTema` (FR-002, SC-003).

## `ReferenciaSinPareja`

Una referencia del tema que no quedó asociada a ninguna estimación
(FR-005).

| Campo | Tipo | Origen / regla |
|---|---|---|
| `identificador_referencia` | `str` | `identificador_origen` de la `PistaGuitarra` sin pareja. |
| `motivo` | `MotivoSinPareja` | `"sin_estimacion_disponible"` si el número de estimaciones recibidas era insuficiente (FR-003); `"energia_nula"` si la propia referencia tiene energía nula (FR-006, research.md #4) — detectado antes de intentar el cálculo, nunca por una excepción numérica; `"estimacion_silenciosa"` si la asignación óptima le habría dado una estimación cuya propia señal es silencio digital (FR-016) — reclasificada después de la asignación, no excluida antes de ella (research.md, sección del hallazgo 2026-09-04 posterior a T005). |

## `ReporteTema`

El resultado del cálculo sobre un tema individual (FR-004).

| Campo | Tipo | Origen / regla |
|---|---|---|
| `tema_id` | `str` | Eco del identificador de la `EntradaConjunto` o del argumento directo a `emparejar_tema()`. |
| `num_referencias` | `int` | `len(referencias)` de la entrada. |
| `num_estimaciones_recibidas` | `int` | `len(estimaciones)` de la entrada — incluye estimaciones sobrantes que no se emparejaron con ninguna referencia (Edge Cases de `spec.md`). |
| `emparejadas` | `list[ReferenciaEmparejada]` | Resultado de la asignación óptima (research.md #2). |
| `sin_pareja` | `list[ReferenciaSinPareja]` | Nunca se omite (FR-005) — lista vacía es un valor válido cuando todas las referencias quedaron emparejadas. |

**Invariantes**:
- `len(emparejadas) + len(sin_pareja) == num_referencias`.
- Cada referencia con energía nula está siempre en `sin_pareja` con motivo `"energia_nula"`, nunca en `emparejadas`, independientemente de cuántas estimaciones hubiera disponibles (research.md #4: la comparación ni se intenta).
- Cada referencia cuya estimación asignada por la asignación óptima resultó silenciosa está siempre en `sin_pareja` con motivo `"estimacion_silenciosa"`, nunca en `emparejadas` (FR-016) — la asignación sí la considera un candidato válido durante la optimización (a diferencia de una referencia con su propia energía nula, que ni participa), pero el resultado se reclasifica antes de reportarse.
- `len(emparejadas)` es, por lo tanto, `min(num_referencias, num_estimaciones_recibidas)` **menos** el número de referencias con energía nula propia **y menos** el número de referencias cuya mejor asignación resultó ser una estimación silenciosa — no una fórmula cerrada más simple, porque ambos motivos restan de la misma cuenta.

## `EntradaConjunto`

Un tema tal como lo aporta el llamador a la agregación sobre un conjunto
(FR-007 en adelante) — antes de aplicar las exclusiones.

| Campo | Tipo | Origen / regla |
|---|---|---|
| `tema_id` | `str` | Identificador del tema (mismo espacio de nombres que Feature 001). |
| `referencias` | `list[PistaGuitarra]` | Puede ser una lista vacía — modela directamente "tema sin ninguna guitarra de referencia" (FR-009), sin un campo booleano aparte. |
| `estimaciones` | `list[Estimacion]` | Puede ser una lista vacía — modela directamente "el separador no produjo nada para este tema" (Edge Cases de `spec.md`); ese tema **no** se excluye por esto (distinto de `referencias` vacío). |
| `es_directorio_omitido` | `bool` | Provisto por el llamador — esta feature no redefine cómo se determina (`spec.md#Assumptions`); solo necesita saber sí/no para FR-010, no enumerar el resto de la estructura de directorios del dataset. |

## `MotivoExclusion`

Alias de tipo (`Literal["sin_guitarra_referencia", "directorio_omitido"]`)
— FR-009 y FR-010 respectivamente. Un tema con ambas condiciones se
reporta solo con `"directorio_omitido"` (research.md #10).

## `Exclusion`

Un tema apartado del conjunto evaluado antes de agregar (FR-009/FR-010).

| Campo | Tipo | Origen / regla |
|---|---|---|
| `tema_id` | `str` | El tema excluido. |
| `motivo` | `MotivoExclusion` | Ver research.md #10 para el criterio cuando ambas condiciones aplican. |

## `ResultadoAgregado`

El resultado de `agregar_conjunto()` sobre una `list[EntradaConjunto]`
(FR-007 en adelante).

| Campo | Tipo | Origen / regla |
|---|---|---|
| `mediana` | `float \| None` | Mediana (research.md, spec.md#Assumptions sobre ponderación) de todos los valores por referencia — emparejadas (`si_sdr`) y sin pareja (`-inf`, FR-008) — de todos los temas evaluados, agrupadas en un solo conjunto (no por tema primero). `None` si el conjunto evaluado queda vacío tras las exclusiones (FR-014) — nunca `0.0` ni una excepción. |
| `num_temas_evaluados` | `int` | `len(entradas) - len(exclusiones)`. |
| `distribucion_referencias_por_tema` | `dict[int, int]` | FR-015, research.md #9 — clave: número de referencias; valor: cuántos temas evaluados tienen ese número. |
| `exclusiones` | `list[Exclusion]` | FR-009/FR-010, con conteo implícito (`len(exclusiones)`, o agrupable por `motivo` para el conteo por razón que pide `spec.md`). |
| `reportes_por_tema` | `list[ReporteTema]` | Un `ReporteTema` por cada tema evaluado (no por los excluidos) — el detalle que sustenta `mediana` y `distribucion_referencias_por_tema`, consistente con la entidad "Conjunto evaluado" de `spec.md`. |

**Invariantes**:
- `mediana is None` si y solo si `num_temas_evaluados == 0` (FR-014).
- `sum(distribucion_referencias_por_tema.values()) == num_temas_evaluados` (research.md #9).
- `len(reportes_por_tema) == num_temas_evaluados`.
- Ningún `tema_id` aparece a la vez en `exclusiones` y en `reportes_por_tema` (SC-005).

## Errores (no son "entidades" de dominio, pero forman parte del contrato)

Ver [contracts/metrica_separacion.md](./contracts/metrica_separacion.md)
para las condiciones exactas.

| Excepción | Origen | Datos que lleva | Quién la ve realmente |
|---|---|---|---|
| `EstimacionIncompatibleError` | research.md #7 | `identificador_referencia`, `identificador_estimacion`, motivo (longitud o frecuencia de muestreo distinta) | Se propaga hasta el llamador de `emparejar_tema`/`agregar_conjunto` — es un fallo real de datos mal formados. |
| `ReferenciaEnergiaNulaError` | research.md #4 | `identificador_referencia` | Solo la ve quien llama a `si_sdr()` directamente. `emparejar_tema()` **nunca** la deja escapar: comprueba la energía de cada referencia antes de invocar `si_sdr()` sobre ella (research.md #4) y, si es nula, la coloca directamente en `sin_pareja` con `motivo == "energia_nula"` — la excepción es la defensa de `si_sdr()` como función de bajo nivel llamada de forma aislada (p. ej. en `tests/unit/`), no un modo de fallo observable de `emparejar_tema`/`agregar_conjunto` (FR-006 exige justamente lo contrario: nunca una excepción no controlada). |

## Relaciones

```
EntradaConjunto 1 ── * PistaGuitarra (referencias)
EntradaConjunto 1 ── * Estimacion (estimaciones)

ReporteTema 1 ── * ReferenciaEmparejada
ReporteTema 1 ── * ReferenciaSinPareja

ResultadoAgregado 1 ── * ReporteTema (reportes_por_tema, solo temas evaluados)
ResultadoAgregado 1 ── * Exclusion (temas no evaluados)
```

No hay transiciones de estado: todo el modelo es el resultado de una única
operación de cálculo, sin ciclo de vida propio — igual que Feature 001.
