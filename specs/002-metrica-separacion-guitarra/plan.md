# Implementation Plan: Métrica de separación de guitarra

**Branch**: `002-metrica-separacion-guitarra` | **Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-metrica-separacion-guitarra/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Dada la colección de pistas de guitarra de referencia (`PistaGuitarra`, de
`ingestion.slakh2100`) y una colección de estimaciones de un mismo tema,
calcular el SI-SDR de cada referencia contra la estimación que mejor la
aproxima (asignación óptima uno a uno, FR-002), reportar el resultado por
tema (FR-004) y agregar sobre un conjunto de temas con la mediana de todos
los valores por referencia — incluidas las sin pareja, tratadas como −∞
(FR-007/FR-008) — junto con las exclusiones (FR-009/FR-010) y la
distribución de referencias por tema (FR-015). Enfoque técnico:
`scipy.optimize.linear_sum_assignment` para el emparejamiento (maneja
matrices rectangulares cuando el número de estimaciones y referencias
difiere, cerrando FR-002/FR-003 sin combinatoria propia), cálculo de SI-SDR
en `float64` sin ningún reescalado de amplitud (la invarianza a escala es
propiedad de la fórmula, no de una normalización previa). Detalle completo
de cada decisión en [research.md](./research.md). Esta feature cierra los
dos `ABIERTO` de la constitución que le correspondían: VII (métrica
principal) y VIII (determinismo) — ver Constitution Check.

## Technical Context

**Language/Version**: Python 3.12 (mismo `requires-python` que el resto del proyecto)

**Primary Dependencies**: `numpy` (ya dependencia directa, aritmética de SI-SDR), `scipy` (**nueva** — `scipy.optimize.linear_sum_assignment` para el emparejamiento óptimo, research.md #2). Reutiliza `PistaAudio`/`PistaGuitarra` de `guitar_tabs_analysis.ingestion.slakh2100` (capa inferior — permitido por el contrato `type = "layers"` de import-linter; esta feature vive en `analytics`, que importa de `ingestion`, nunca al revés)

**Storage**: N/A — cálculo puro en memoria, sin persistencia. El spec no pide guardar el reporte (FR-004/FR-007 hablan de "reportar", no de un artefacto en disco); si una feature futura de compuerta necesita leer este resultado como artefacto persistido (siguiendo el patrón ya usado por `quality/gates.py`, que lee un Parquet, no importa `analytics`), esa es su propia decisión, no de esta feature

**Testing**: `pytest` + `hypothesis`, con fixtures sintéticas construidas como arrays `numpy` a mano (senoidales/ruido con desfase y ganancia conocidos) — sin E/S de archivos en esta feature, así que no aplica la restricción de "no audio real commiteado" del mismo modo que en 001, pero se mantiene igual: ningún array de audio real del dataset se commitea, todo es sintético con propiedades conocidas de antemano (necesario para poder afirmar cuál es "el valor máximo posible de la métrica", SC-001)

**Target Platform**: Linux (entorno de desarrollo/CI del proyecto, igual que 001; `scipy` tiene wheels prebuilt para esa plataforma, sin compilación necesaria)

**Project Type**: Single project — librería interna, capa `analytics` (ver Project Structure)

**Performance Goals**: No declarados por el spec. La operación de mayor costo por tema es la asignación óptima (`linear_sum_assignment`, complejidad polinómica en el número de referencias/estimaciones — típicamente 1–4 guitarras por tema en Slakh2100, research.md del feature 001); sin objetivo de throughput ni de latencia declarado

**Constraints**: Ninguna transformación de las muestras de audio antes de calcular SI-SDR salvo el cast a `float64` necesario para la aritmética (research.md #3) — la invarianza a escala de la fórmula hace innecesario cualquier reescalado, y uno adicional violaría el espíritu de "sin transformación" ya establecido en Feature 001. El sistema MUST NOT fallar con una excepción no controlada ante una referencia de energía nula (FR-006) ni ante los infinitos matemáticamente válidos (+∞/−∞) que la propia fórmula produce (research.md #4, #5)

**Scale/Scope**: El split de prueba oficial de Slakh2100 (~150 temas, Principio VI de la constitución) es el caso de uso principal previsto, pero esta feature opera sobre cualquier conjunto de temas que el llamador construya (`EntradaConjunto`, ver data-model.md) — sin límite de tamaño declarado por el spec

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Aplica a esta feature | Estado |
|---|---|---|
| I. Hito 1 es línea base medida | Esta feature ES la mitad "medir" del criterio de terminado del hito 1 — calcula y reporta la métrica sobre el stem producido por un separador (el separador mismo queda fuera de alcance, FR-012) | Compatible, avanza directamente el criterio de terminado |
| II. Caminos descartados con razón | No introduce RL ni filtrado por banda | N/A |
| III. La guitarra no es un stem estándar | Consistente — mide guitarra como categoría propia; no compara la cifra resultante contra benchmarks publicados de otros stems | Compatible |
| IV. Fuentes de audio admisibles | No lee nada de disco ni introduce una fuente de audio nueva — opera sobre `PistaAudio`/`PistaGuitarra` ya cargados (vía Feature 001 para las referencias) | N/A para esta feature |
| V. Qué cuenta como "la guitarra" | Consistente — múltiples referencias de un tema se reportan por separado, nunca sumadas (FR-004), y el número de referencias del tema se reporta junto con la métrica, exactamente como exige este Principio | Compatible, implementado directamente |
| VI. Cuantitativa vs. cualitativa | Esta feature es el motor de cálculo de la evaluación cuantitativa (Slakh2100); no toca la verificación cualitativa (que no produce métrica por diseño) | Compatible |
| VII. La métrica y su presupuesto | **Se cierra aquí la mitad "métrica"**: SI-SDR (Le Roux et al. 2019), invariante a escala — research.md #1. El presupuesto numérico permanece `ABIERTO` **a propósito**: FR-013 del spec prohíbe explícitamente que esta feature lo defina, y el propio criterio de cierre de la constitución ("después de la primera medición real") no se ha cumplido todavía | Métrica cerrada por este plan; presupuesto sigue `ABIERTO` por diseño, no por omisión |
| VIII. Determinismo | **Se cierra aquí**: opción (b), tolerancia numérica declarada para los valores de SI-SDR calculados (comparación con tolerancia, no igualdad bit a bit), salvo los dos valores que son exactos por construcción y no por cálculo — el `+∞` del criterio de respuesta conocida (FR-011) y el sentinel `−∞` de las referencias sin pareja (FR-008). Los conteos, la lista de referencias sin pareja y qué par quedó emparejado son resultados discretos y se verifican con igualdad exacta, no con tolerancia — research.md #6 | Cerrado por este plan |
| IX. Datos derivados: se generan, no se leen | No aplica directamente — esta feature no persiste ningún artefacto derivado (Storage: N/A) | N/A para esta feature |
| X. Tamaño de slice | Gate de `/speckit-tasks`, no de este plan | Diferido a tasks |

Sin violaciones que requieran `Complexity Tracking`.

**Nota de gobernanza**: cerrar VII y VIII arriba es la decisión técnica de
*este plan*; la constitución misma (`.specify/memory/constitution.md`) solo
se enmienda corriendo `/speckit-constitution` de nuevo — no la edita este
comando. Se recomienda correr `/speckit-constitution` después de este plan
para que los dos checkboxes de Governance reflejen esta decisión.

**Re-chequeo post-diseño (Fase 1)**: `research.md` y `data-model.md` no
introducen nada que contradiga la tabla de arriba. La única dependencia
nueva (`scipy`) es solo para el emparejamiento (research.md #2), no toca
ninguna fuente de audio ni el Principio IV. Los dos tipos de excepción
nuevos (`EstimacionIncompatibleError`, `ReferenciaEnergiaNulaError`) son
fallos explícitos ante datos mal formados o un caso matemáticamente
indefinido — consistentes con el patrón de "fallar con mensaje claro, no
en silencio" que Feature 001 ya estableció, no una desviación. Sin
violaciones nuevas; gate sigue en verde.

## Project Structure

### Documentation (this feature)

```text
specs/002-metrica-separacion-guitarra/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── metrica_separacion.md  # Phase 1 output (/speckit-plan command)
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/guitar_tabs_analysis/
└── analytics/
    ├── __init__.py
    └── metrica_separacion.py   # si_sdr(), emparejar_tema(), agregar_conjunto();
                                 # Estimacion, ReferenciaEmparejada, ReferenciaSinPareja,
                                 # ReporteTema, EntradaConjunto, Exclusion, ResultadoAgregado;
                                 # EstimacionIncompatibleError

tests/
├── unit/
│   └── test_metrica_separacion.py              # si_sdr() puntual: energía nula,
│                                                 # known-answer (+∞), estimación silenciosa
│                                                 # (−∞ calculado), incompatibilidad de forma
├── integration/
│   └── test_metrica_separacion_integracion.py  # emparejar_tema()/agregar_conjunto()
│                                                 # end-to-end con fixtures multi-tema
├── property/
│   └── test_metrica_separacion_property.py     # invariantes: mediana nunca mejora al
│                                                 # incluir un tema con referencias sin pareja
│                                                 # (SC-004), ninguna estimación compartida
│                                                 # entre dos referencias (SC-003), la suma de
│                                                 # la distribución de referencias por tema
│                                                 # coincide con el número de temas evaluados
└── fixtures/
    └── metrica_separacion_fixture.py    # helper: construye PistaGuitarra/Estimacion
                                          # sintéticas (senoidales con desfase/ganancia/ruido
                                          # conocidos, y variantes de energía nula/silencio)
```

**Structure Decision**: Opción 1 (proyecto único), consistente con Feature
001. El módulo nuevo vive en la capa `analytics` (nivel superior del
contrato de `import-linter`: puede importar de `ingestion`, nunca al
revés) porque agrega/computa sobre datos ya leídos — no lee nada de disco
por sí misma. Reemplaza el ejemplo `analytics/resumen.py` como primer
módulo real de esa capa; `resumen.py` se elimina en la fase de
implementación si nada más lo usa (decisión de `/speckit-tasks`, no de
este plan).

## Complexity Tracking

*Sin violaciones — tabla omitida.*
