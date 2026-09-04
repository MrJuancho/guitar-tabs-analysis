# Contrato: `metrica_separacion`

Este proyecto es una librería (no expone API HTTP ni CLI para esta
feature), así que el contrato es la firma pública de las funciones de
`analytics.metrica_separacion` y el comportamiento observable descrito en
`spec.md`. Tres funciones, cada una construida sobre la anterior.

## `si_sdr`

```python
def si_sdr(referencia: PistaAudio, estimacion: PistaAudio) -> float:
    ...
```

Calcula el SI-SDR de un único par (research.md #1). Es la unidad más
pequeña del contrato — `emparejar_tema` la usa internamente para construir
la matriz de costos, pero también está expuesta directamente para poder
verificar la fórmula de forma aislada (`tests/unit/`).

### Precondiciones

- `referencia.muestras` y `estimacion.muestras` tienen la misma longitud
  y `referencia.frecuencia_muestreo == estimacion.frecuencia_muestreo`
  (research.md #7) — de lo contrario, `EstimacionIncompatibleError`.
- `referencia` no tiene energía nula (research.md #4) — de lo contrario,
  `ReferenciaEnergiaNulaError` (ver tabla de fallos abajo). Esta
  precondición es responsabilidad de quien llama a `si_sdr()`
  directamente; `emparejar_tema` (más abajo) nunca la viola porque
  comprueba la energía de cada referencia antes de invocar `si_sdr()`
  sobre ella (data-model.md, tabla de errores). `estimacion` **sí** puede
  tener energía nula: es un resultado válido (SI-SDR = `-∞` exacto,
  research.md #5), no una precondición violada.

### Postcondiciones

1. El valor devuelto es exacto (no una aproximación) cuando
   `estimacion.muestras` es bit-idéntica a `referencia.muestras`: `+inf`
   (research.md #5, base de SC-001).
2. El valor devuelto es exacto cuando `estimacion.muestras` es el vector
   cero: `-inf` (research.md #5).
3. En cualquier otro caso, el valor devuelto es finito y coincide con la
   fórmula de research.md #1 dentro de la tolerancia de punto flotante
   estándar (research.md #6) — no bit a bit.
4. La función no reescala, normaliza, ni modifica `referencia.muestras`
   ni `estimacion.muestras` — la invarianza a escala es una propiedad del
   resultado, no de una transformación previa a las entradas (research.md
   #3).

### Modos de fallo

| Condición | Excepción | Mensaje debe incluir |
|---|---|---|
| `referencia` y `estimacion` tienen distinta longitud o distinta frecuencia de muestreo | `EstimacionIncompatibleError` | qué propiedad difiere (research.md #7) |
| `referencia` tiene energía nula | `ReferenciaEnergiaNulaError` | que la energía es nula (research.md #4) |

Ninguna de las dos condiciones anteriores llega nunca a `si_sdr()` a
través de `emparejar_tema()`: la primera se verifica antes sobre todos los
pares candidatos (`EstimacionIncompatibleError` sí se propaga desde ahí,
ver más abajo); la segunda se verifica una sola vez por referencia, antes
de construir la matriz de costos, y produce un `ReferenciaSinPareja` en
vez de una llamada a `si_sdr()` (data-model.md).

## `emparejar_tema`

```python
def emparejar_tema(
    referencias: list[PistaGuitarra],
    estimaciones: list[Estimacion],
) -> ReporteTema:
    ...
```

Implementa User Story 1 completa: calcula SI-SDR entre cada referencia y
cada estimación candidata, resuelve la asignación óptima uno a uno
(research.md #2), y produce el reporte de un tema individual.

### Precondiciones

- Ninguna sobre las longitudes de las listas — `referencias` y
  `estimaciones` pueden tener cualquier longitud, incluida cero (FR-003,
  Edge Cases de `spec.md`).
- Cada par `(referencia, estimacion)` que participa en el cálculo cumple
  las precondiciones de `si_sdr` — si no, `EstimacionIncompatibleError`
  se propaga con el `tema_id` (parámetro implícito: el llamador debe usar
  el mismo `tema_id` que usará al construir `ReporteTema.tema_id`, ver
  nota bajo la tabla de fallos).

### Postcondiciones (éxito)

Para cualquier invocación que no falle:

1. `resultado.num_referencias == len(referencias)` y
   `resultado.num_estimaciones_recibidas == len(estimaciones)` (FR-004).
2. `len(resultado.emparejadas) + len(resultado.sin_pareja) == len(referencias)` —
   ninguna referencia se omite del reporte (FR-005, SC-002).
3. Ningún `identificador_estimacion` se repite entre dos elementos de
   `resultado.emparejadas` (FR-002, SC-003).
4. Cada referencia con energía nula aparece en `resultado.sin_pareja` con
   `motivo == "energia_nula"`, nunca en `resultado.emparejadas`, sin
   importar cuántas estimaciones había disponibles (FR-006, research.md
   #4) — la llamada **no** lanza una excepción por esta condición: se
   detecta y se reporta, no se propaga como fallo.
5. Si `estimacion == referencia` para algún par evaluado (misma
   referencia pasada como su propia estimación, con el mismo
   `identificador_origen`/`identificador` usado para construir ambas), esa
   referencia queda en `emparejadas` con `si_sdr == float("inf")` exacto
   (FR-011, SC-001) — siempre que haya suficientes estimaciones para que
   la asignación óptima efectivamente la elija, lo cual ocurre siempre que
   esa estimación exista como candidata (un valor `+∞` domina cualquier
   asignación alternativa finita).
6. Todas las referencias sin pareja por falta de estimaciones suficientes
   (no por energía nula) tienen `motivo == "sin_estimacion_disponible"`
   (FR-003).

### Modos de fallo

| Condición | Excepción | Mensaje debe incluir |
|---|---|---|
| Una referencia y una estimación candidata tienen distinta longitud o distinta frecuencia de muestreo | `EstimacionIncompatibleError` | el identificador de la referencia, el identificador de la estimación, y cuál de las dos propiedades difiere (research.md #7) |

Ninguna otra condición descrita en `spec.md` para User Story 1 se
señaliza con una excepción — la energía nula (FR-006) y la falta de
estimaciones (FR-003) son resultados reportados en `sin_pareja`, nunca
fallos de la llamada.

## `agregar_conjunto`

```python
def agregar_conjunto(entradas: list[EntradaConjunto]) -> ResultadoAgregado:
    ...
```

Implementa User Story 2 completa: aplica las exclusiones (FR-009/FR-010),
llama a `emparejar_tema` sobre cada tema evaluado, agrega la mediana
(FR-007/FR-008) y calcula la distribución de referencias por tema
(FR-015).

### Precondiciones

- Ninguna sobre `len(entradas)` — una lista vacía es válida y produce
  `ResultadoAgregado` con `mediana is None` (FR-014).
- Cada `EntradaConjunto` evaluada (no excluida) cumple las precondiciones
  de `emparejar_tema` sobre su propio `referencias`/`estimaciones`.

### Postcondiciones (éxito)

Para cualquier invocación que no falle:

1. Cada `EntradaConjunto` con `referencias == []` aparece en
   `resultado.exclusiones` con `motivo == "sin_guitarra_referencia"`
   (FR-009), salvo que también aplique la condición 2 siguiente.
2. Cada `EntradaConjunto` con `es_directorio_omitido == True` aparece en
   `resultado.exclusiones` con `motivo == "directorio_omitido"` (FR-010),
   con prioridad sobre la condición 1 si ambas aplican (research.md #10).
3. `resultado.num_temas_evaluados == len(entradas) - len(resultado.exclusiones)`.
4. `resultado.reportes_por_tema` contiene exactamente un `ReporteTema` por
   cada `EntradaConjunto` no excluida, producido por `emparejar_tema`
   sobre sus `referencias`/`estimaciones`.
5. `resultado.mediana` es la mediana de todos los valores por referencia
   de `resultado.reportes_por_tema` — `si_sdr` de cada `emparejada`, y
   `-inf` por cada `sin_pareja` (FR-008) — agrupados en un solo conjunto,
   sin colapsar primero por tema (FR-007, spec.md#Assumptions sobre
   ponderación). `None` si `resultado.num_temas_evaluados == 0` (FR-014).
6. `resultado.distribucion_referencias_por_tema[n]` cuenta cuántos
   `ReporteTema` de `resultado.reportes_por_tema` tienen
   `num_referencias == n`, para cada `n` presente (FR-015).
7. Ningún `tema_id` aparece a la vez en `resultado.exclusiones` y en
   `resultado.reportes_por_tema` (SC-005).
8. `resultado.mediana` sobre un conjunto que incluye un tema con
   referencias sin pareja nunca es mayor que la misma agregación sobre el
   conjunto que omite ese tema por completo (SC-004) — propiedad, no un
   valor concreto a verificar por caso.

### Modos de fallo

Se propaga cualquier excepción de `emparejar_tema` sobre una entrada
evaluada (`EstimacionIncompatibleError`), sin traducirla — el `tema_id` de
la excepción identifica cuál `EntradaConjunto` la disparó. No hay ningún
modo de fallo adicional propio de `agregar_conjunto`.

## Fuera de este contrato

- Separación de audio o invocación de cualquier modelo (FR-012 de
  `spec.md`) — `estimaciones` llega ya calculada.
- Definir o evaluar un umbral de aprobación sobre `resultado.mediana`
  (FR-013 de `spec.md`) — el presupuesto de la compuerta es una decisión
  posterior, fuera de esta feature.
- Cómo se determina `EntradaConjunto.es_directorio_omitido` (qué
  directorio del dataset corresponde a qué tema) — responsabilidad del
  llamador (`spec.md#Assumptions`).
- Persistencia de `ResultadoAgregado`/`ReporteTema` en disco (research.md
  #8).
