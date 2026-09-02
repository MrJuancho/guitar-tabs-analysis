# Implementation Plan: Lectura de un tema de Slakh2100

**Branch**: `001-lectura-tema-slakh2100` | **Date**: 2026-09-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-lectura-tema-slakh2100/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Dado el identificador de un tema de Slakh2100 y la raíz local del
dataset, devolver el audio de la mezcla y la colección de audios de sus
pistas de guitarra (identificadas vía `inst_class == "Guitar"` en
`metadata.yaml`, excluyendo bajo eléctrico y stems no renderizados),
cada una con su identificador de origen — sin ninguna transformación
del audio (FR-005), y fallando explícitamente ante id inexistente,
archivo ausente/no legible, o discrepancia de longitud. Enfoque técnico:
`soundfile` para decodificar `.flac` preservando el `dtype` nativo (sin
reescalado), `PyYAML` para los metadatos, sin dependencia de red ni de
un manifiesto de dataset (fuera de alcance de esta feature). Detalle
completo de cada decisión en [research.md](./research.md).

## Technical Context

**Language/Version**: Python 3.12 (`pyproject.toml` ya fija `requires-python = ">=3.12"`)

**Primary Dependencies**: `soundfile` (decodificación de `.flac` sin resampleo/normalización — research.md #1), `PyYAML` (parseo de `metadata.yaml` — research.md #2), `numpy` (tipo de retorno de las muestras; ya transitivo vía `pandas`, se añade como dependencia directa porque el dominio lo usa explícitamente)

**Storage**: Sistema de archivos local — copia de Slakh2100 fuera del repositorio, referenciada por un `root_dir` explícito (research.md #5); no hay base de datos ni manifiesto en esta feature

**Testing**: `pytest` + `hypothesis` (ya en `dependency-groups.dev`), con fixtures sintéticas construidas en `tmp_path` — nunca audio real commiteado (research.md #6, constitución Principio IV)

**Target Platform**: Linux (entorno de desarrollo/CI del proyecto; sin dependencia de plataforma más allá de lo que `soundfile`/`libsndfile` ya soportan multiplataforma)

**Project Type**: Single project — librería interna dentro de `src/guitar_tabs_analysis/`, capa `ingestion` (ver Project Structure)

**Performance Goals**: No declarados por el spec para esta feature — operación de lectura de un único tema por invocación, sin objetivo de throughput ni de latencia (fuera del alcance de `spec.md`)

**Constraints**: Cero transformación del audio leído (FR-005: sin resampleo, sin conversión de canales, sin normalización de amplitud); cero audio real en el repositorio, incluidos los tests (constitución Principio IV)

**Scale/Scope**: Slakh2100 completo tiene 2100 temas, pero esta feature opera sobre un tema a la vez (FR-001/FR-002); no hay requisito de lectura por lotes en este spec

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Aplica a esta feature | Estado |
|---|---|---|
| I. Hito 1 es línea base medida | Parcial — esta feature es un prerrequisito de datos para esa línea base, no la línea base misma (no entrena, no mide métrica) | Compatible, no viola |
| II. Caminos descartados con razón | No introduce RL ni filtrado por banda | N/A |
| III. La guitarra no es un stem estándar | Consistente — lee guitarra como categoría propia, no la fusiona en "otros" | Compatible |
| IV. Fuentes de audio admisibles | Slakh2100 (CC BY 4.0), ya admitido para hito 1. Repositorio sin audio: tests usan fixtures sintéticas, nunca grabaciones (research.md #6) | Compatible |
| V. Qué cuenta como "la guitarra" | Implementado directamente — `inst_class == "Guitar"` incluye limpia/distorsionada/acústica; bajo eléctrico excluido por `inst_class == "Bass"` (research.md #3); múltiples guitarras devueltas por separado (FR-002) | Compatible |
| VI. Cuantitativa vs. cualitativa | No aplica — esta feature no evalúa, solo lee | N/A |
| VII. La métrica y su presupuesto | `ABIERTO` en la constitución; no aplica a esta feature (no calcula métrica). No se cierra aquí — ver research.md #8 | N/A para este plan, `ABIERTO` se mantiene |
| VIII. Determinismo | `ABIERTO` en la constitución; esta feature no tiene ninguna operación no determinista que decidir (research.md #7) | N/A para este plan, `ABIERTO` se mantiene |
| IX. Datos derivados: se generan, no se leen | No aplica — esta feature lee datos *fuente*, no produce un artefacto derivado | N/A |
| X. Tamaño de slice | Gate de `/speckit-tasks`, no de este plan | Diferido a tasks |

Sin violaciones que requieran `Complexity Tracking`.

## Project Structure

### Documentation (this feature)

```text
specs/001-lectura-tema-slakh2100/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── leer_tema.md     # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/guitar_tabs_analysis/
└── ingestion/
    ├── __init__.py
    └── slakh2100.py          # leer_tema(), LecturaTema/PistaAudio/PistaGuitarra,
                               # TemaNoExisteError/ArchivoAudioNoLegibleError/
                               # LongitudInconsistenteError

tests/
├── unit/
│   └── test_slakh2100_lectura.py         # casos de error, clasificación guitarra/bajo
├── integration/
│   └── test_slakh2100_lectura_integracion.py  # lectura end-to-end contra fixture sintética en tmp_path
├── property/
│   └── test_slakh2100_lectura_property.py     # invariantes: longitud/sr compartidos, round-trip de contenido
└── fixtures/
    └── slakh2100_fixture.py  # helper: construye un TrackXXXXX sintético (metadata.yaml + .flac) en tmp_path
```

**Structure Decision**: Opción 1 (proyecto único), ya establecida por el
esqueleto del template. El módulo nuevo vive en la capa `ingestion`
(nivel más bajo del contrato de `import-linter`) porque es lectura pura
de la fuente — no agrega (`analytics`) ni evalúa (`quality`) nada.
Reemplaza el ejemplo `ingestion/normalizar.py` como primer módulo real
de esa capa; `normalizar.py` se elimina en la fase de implementación si
nada más lo usa (decisión de `/speckit-tasks`, no de este plan).

## Complexity Tracking

*Sin violaciones — tabla omitida.*
