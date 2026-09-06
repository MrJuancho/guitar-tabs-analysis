# Data Model: Medición de la línea base

**Input**: [spec.md](./spec.md) `Key Entities` | **Decisions**: [research.md](./research.md)

Todos los tipos son inmutables y viven en la capa nueva `medicion`. Nombres
en español, consistentes con Features 001-003. Reutiliza `PistaAudio`,
`PistaGuitarra`, `LecturaTema` (`ingestion.slakh2100`); `Estimacion`,
`ReporteTema`, `ReferenciaEmparejada`, `ReferenciaSinPareja` (`analytics.metrica_separacion`);
`ModeloDeclarado`, `ResultadoSeparacionTema`, `TransformacionDeclarada`,
`Separador`, `SeparacionFallidaError` (`separacion.separador`) sin
redefinir ninguno.

## `ModoEjecucion`

Alias de tipo (`Literal["submuestra_hito1", "conjunto_completo"]`) — no una
clase nueva. Los dos modos de FR-001/FR-002/FR-003, mutuamente excluyentes
y sin valor por defecto (FR-004).

## `MotivoExclusionMedicion`

Alias de tipo (`Literal["fallo_procesamiento", "sin_guitarra_referencia"]`)
— **dos** valores, no los tres de `MotivoExclusion` de la Feature 002: el
tercero (`"directorio_omitido"`) nunca puede ocurrir aquí, porque
`construir_lista_temas` no lista jamás el directorio `omitted` (research.md
#7) — no hay una rama de código que necesite representarlo.

- `"fallo_procesamiento"`: la lectura (`leer_tema`) o la separación
  (`separar_guitarra`) del tema fallaron duro (FR-006). Terminal: una vez
  persistido con este motivo, ninguna reanudación lo reintenta (FR-006,
  FR-008, aclaración de `/speckit-clarify`).
- `"sin_guitarra_referencia"`: `leer_tema` devolvió una colección vacía de
  guitarras para el tema — mismo criterio que Feature 002 FR-009, aplicado
  aquí antes de intentar `separar_guitarra` (no hace falta separar nada si
  no hay ninguna referencia contra la cual medir).

## `ExclusionMedicion`

Un tema apartado del resultado agregado de una corrida, con su motivo
(FR-006, FR-010).

| Campo | Tipo | Origen / regla |
|---|---|---|
| `tema_id` | `str` | Identificador calificado por split (research.md #3), p. ej. `"validation/Track00234"`. |
| `motivo` | `MotivoExclusionMedicion` | Ver arriba. |
| `detalle` | `str` | Para `"fallo_procesamiento"`: `str(causa)` de la excepción original (`TemaNoExisteError`, `ArchivoAudioNoLegibleError`, `LongitudInconsistenteError` de Feature 001, o `SeparacionFallidaError` de Feature 003). Para `"sin_guitarra_referencia"`: cadena vacía — no hay una causa que citar, es un hecho sobre los metadatos del tema. |

## `ResultadoProcesamientoTema`

El resultado de procesar un único tema (`procesar_tema`, FR-005) — una
unión etiquetada, nunca ambos casos a la vez.

| Campo | Tipo | Origen / regla |
|---|---|---|
| `tema_id` | `str` | Igual que en `reporte.tema_id` o `exclusion.tema_id` — invariante: siempre coinciden. |
| `reporte` | `ReporteTema \| None` | Presente si el tema se midió con éxito (Feature 002). |
| `exclusion` | `ExclusionMedicion \| None` | Presente si el tema se excluyó (ver arriba). |
| `transformaciones` | `list[TransformacionDeclarada]` | Eco de `ResultadoSeparacionTema.transformaciones` (Feature 003) cuando `reporte` no es `None` — la separación sí corrió, así que sí hay transformaciones que declarar (FR-010, SC-007; spec.md ENTREGABLE y Key Entities "Reporte por tema"/"Artefacto de medición"). Lista vacía cuando `exclusion` no es `None`: ni `"sin_guitarra_referencia"` ni `"fallo_procesamiento"` llegan a invocar `separar_guitarra` con éxito (`procesar_tema`, contracts/medicion.md), así que no existe ningún `ResultadoSeparacionTema` del cual tomarlas — una lista vacía es la respuesta correcta, no un dato faltante. |

**Invariante**: exactamente uno de `reporte`/`exclusion` es `None` y el
otro no — nunca los dos `None`, nunca los dos presentes. `transformaciones`
no está vacía si y solo si `reporte` no es `None`.

## `ManifiestoCorrida`

Los metadatos de identidad de una corrida, persistidos junto con el
progreso (FR-008a) — lo que permite reconocer, al reanudar, si se trata
de la misma corrida o de una con un modelo distinto.

| Campo | Tipo | Origen / regla |
|---|---|---|
| `modo` | `ModoEjecucion` | Fijo para toda la vida de la corrida. |
| `semilla` | `int \| None` | `20260904` para `submuestra_hito1` (research.md #9 de la Feature 003); `None` para `conjunto_completo` (FR-003, sin muestreo). |
| `firma_modelo` | `str` | `separador.modelo_declarado.firma` (Feature 003) al momento de crear la corrida — comparada contra la vigente en cada reanudación (FR-008a). |
| `temas` | `list[str]` | La lista exacta y ordenada de identificadores de tema de esta corrida (FR-001/FR-002/FR-003), fijada una sola vez al crear la corrida — no se recalcula en cada reanudación, para que un cambio futuro en el contenido de `validation/` no altere una corrida ya en curso. |

## `ModeloCambiadoError`

Excepción (FR-008a) — no es un "modo de fallo de tema", es un fallo de la
corrida completa antes de procesar ningún tema.

| Campo | Origen |
|---|---|
| `firma_esperada` | `ManifiestoCorrida.firma_modelo` ya persistido. |
| `firma_actual` | `separador.modelo_declarado.firma` en el momento de la reinvocación. |

Mensaje: identifica ambas firmas explícitamente (User Story 2, escenario
5). Se levanta **antes** de procesar cualquier tema de la reanudación —
nunca a mitad de la corrida.

## `ArtefactoMedicion`

El artefacto final de una corrida completa (FR-010, FR-011) — lo único
que se necesita para interpretar la cifra sin volver a ejecutar nada
(ENTREGABLE de spec.md).

| Campo | Tipo | Origen / regla |
|---|---|---|
| `modo` | `ModoEjecucion` | Eco de `ManifiestoCorrida.modo`. |
| `semilla` | `int \| None` | Eco de `ManifiestoCorrida.semilla`. |
| `modelo` | `ModeloDeclarado` | `separador.modelo_declarado` (Feature 003) — nombre, variante, firma, checksum, licencia. |
| `temas` | `list[str]` | Eco de `ManifiestoCorrida.temas` — la lista exacta medida. |
| `exclusiones` | `list[ExclusionMedicion]` | Todos los temas de `temas` que no tienen un `ReporteTema` — `fallo_procesamiento` o `sin_guitarra_referencia` (research.md #2 no aplica aquí, esto no requiere `agregar_conjunto`). |
| `reportes` | `list[ReporteTema]` | Un `ReporteTema` por cada tema medido con éxito (ni excluido). |
| `transformaciones_por_tema` | `dict[str, list[TransformacionDeclarada]]` | Clave: `tema_id`. Valor: `ResultadoProcesamientoTema.transformaciones` de ese tema (Feature 003) — las transformaciones que `spec.md` exige seis veces (ENTREGABLE, US1 AS3, FR-010, ambas Key Entities, SC-007), y que no viven en `ReporteTema` (tipo de la Feature 002, que no las conoce). Solo tiene una entrada por cada `tema_id` presente en `reportes` — un tema excluido nunca llegó a `separar_guitarra` con éxito (ver `ResultadoProcesamientoTema.transformaciones`), así que no aporta nada que declarar aquí. |
| `mediana` | `float \| None` | `calcular_mediana_agregada(reportes)` (research.md #2) — `None` si `reportes` queda vacío tras las exclusiones, igual que `ResultadoAgregado.mediana` de la Feature 002 (FR-014 de 002). |
| `distribucion_referencias_por_tema` | `dict[int, int]` | `calcular_distribucion_referencias(reportes)` (research.md #2). |

**Invariantes**:
- `len(exclusiones) + len(reportes) == len(temas)`.
- `mediana is None` si y solo si `len(reportes) == 0`.
- `sum(distribucion_referencias_por_tema.values()) == len(reportes)`.
- Ningún `tema_id` aparece a la vez en `exclusiones` y en `reportes`
  (mismo invariante que `ResultadoAgregado` de la Feature 002, SC-005 de
  002).
- `set(transformaciones_por_tema.keys()) == {r.tema_id for r in reportes}`
  — ni más (un tema excluido no aporta entrada) ni menos (todo tema
  medido con éxito declara sus transformaciones, aunque sea la lista
  trivial de "verificado, sin cambio" que `separar_guitarra` produce
  incluso cuando no remuestrea ni duplica canales — Feature 003,
  contracts/separacion.md, postcondición 1).

## Relaciones

```
ManifiestoCorrida 1 ── * str (temas, antes de procesarse)

ResultadoProcesamientoTema 1 ── 0..1 ReporteTema (Feature 002)
ResultadoProcesamientoTema 1 ── 0..1 ExclusionMedicion

ArtefactoMedicion 1 ── * ReporteTema (reportes)
ArtefactoMedicion 1 ── * ExclusionMedicion (exclusiones)
ArtefactoMedicion 1 ── * list[TransformacionDeclarada] (transformaciones_por_tema, una por tema_id de reportes)
ArtefactoMedicion 1 ── 1 ModeloDeclarado (Feature 003)
```

No hay transiciones de estado dentro de un `ArtefactoMedicion` — es,
como en Features 001/002/003, el resultado de una operación (una corrida
completa), sin ciclo de vida propio una vez emitido. La corrida que lo
produce sí tiene un estado observable externo (en progreso / completa),
pero eso vive en el progreso persistido en disco (research.md #4), no en
este tipo.
