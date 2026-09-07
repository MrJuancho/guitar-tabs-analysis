# Implementation Plan: Compuerta de la métrica

**Branch**: `005-compuerta-metrica` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-compuerta-metrica/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Lee el artefacto JSON que produce la Feature 004 (`mediciones/<modo>.json`),
calcula la mediana de SI-SDR sobre las referencias **emparejadas**
(nunca la mediana global, que es estructuralmente `-∞`), y la compara
contra el presupuesto fijo `-8.0 dB` del Principio VII de la
constitución (v1.5.0). El veredicto siempre incluye la fracción de
referencias sin pareja (obligatorio) y el contexto del artefacto
(modelo, modo, semilla), sin comparar este último contra ningún valor
externo. Un artefacto ausente, ilegible, o sin ningún valor emparejado
del que calcular una mediana es un rechazo explícito (código de salida
`2`), nunca una aprobación silenciosa. Módulo nuevo autocontenido
(`medicion.compuerta`, solo `stdlib`, sin importar `medicion.orquestador`
ni la pila de separación) para no acoplar el contrato de esta feature a
la implementación interna de la Feature 004. Se incorpora como paso de
`just gauntlet` sobre el artefacto ya versionado de la submuestra del
hito 1. Detalle completo de cada decisión en [research.md](./research.md).

## Technical Context

**Language/Version**: Python 3.12 (mismo `requires-python` que el resto del proyecto)

**Primary Dependencies**: Ninguna dependencia nueva de terceros, y
ninguna dependencia siquiera de otros paquetes del propio proyecto más
allá de `stdlib` (research.md #1/#2): `json`, `statistics`, `argparse`,
`dataclasses`, `pathlib`, `sys`. No importa `medicion.orquestador`,
`separacion`, `analytics` ni `ingestion` -- el contrato de entrada es la
forma JSON del artefacto (`specs/004-medicion-linea-base/data-model.md`),
no la implementación de quien lo produce.

**Storage**: Ninguna propia. Lee (nunca escribe) el archivo ya
versionado `mediciones/<modo>.json` que produce `medicion.cli` (Feature
004). El `Veredicto` no se persiste -- se imprime y se refleja en el
código de salida del proceso.

**Testing**: `pytest` + `hypothesis`. Todos los casos de esta feature se
prueban con `dict`s sintéticos construidos directamente en los tests
(nunca invocando `medicion.orquestador` ni el modelo real) -- no hay
ningún test marcado `modelo_real` en esta feature, porque no hay ningún
camino que toque el modelo (SC-001). Un property test (Hypothesis)
verifica la equivalencia entre `statistics.median` y la mediana de
estadístico de orden que la Feature 002 ya usa, sobre el dominio
restringido de valores finitos y `+inf` (research.md #3) -- confirmada
empíricamente antes de escribir este plan (200.000 casos aleatorios, sin
divergencias; y una divergencia real confirmada cuando el pool sí
contiene `+inf`/`-inf` mezclados, para probar que la verificación no es
vacía).

**Target Platform**: Linux (WSL/Ubuntu) -- sin relevancia real, no hay
código específico de plataforma ni de CPU/GPU (a diferencia de la
Feature 003, esta feature no toca `torch`).

**Project Type**: Single project -- módulo nuevo `medicion/compuerta.py`,
capa de invocación `main()` en el mismo archivo (sin separar CLI de
lógica, a diferencia de `orquestador.py`/`cli.py`, porque no hay ninguna
dependencia pesada que aislar -- mismo patrón que `quality/gates.py`,
research.md #2).

**Performance Goals**: SC-001 -- menos de un segundo por evaluación,
sin leer audio ni invocar ningún modelo. Trivial de cumplir: el trabajo
real es `json.load` sobre un archivo de ~30 KB y una mediana sobre como
mucho unos pocos cientos de valores.

**Constraints**: Fallo cerrado obligatorio (FR-004/005/006/007): ningún
camino de error puede terminar en código de salida `0`. El presupuesto
(`-8.0 dB`) es una constante de código, nunca un argumento de `main`
(FR-010) -- cambiarlo requiere una enmienda de la constitución y una
edición de código explícita, nunca un flag de invocación.

**Scale/Scope**: Un solo artefacto por invocación (FR-008), hasta ~1710
temas en el caso de `conjunto_completo` -- ninguna preocupación de
volumen: el artefacto completo ya cabe entero en memoria como el `dict`
que produce `json.load` (~30 KB para 40 temas, research.md de la Feature
004).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Aplica a esta feature | Estado |
|---|---|---|
| I. Hito 1 es línea base medida | Esta feature entrega la segunda mitad del "criterio de terminado" del principio: "una compuerta que falla si cae por debajo del presupuesto declarado" (FR-002, FR-007) -- la primera mitad ("un comando reproducible que... emite la métrica agregada y por pista") ya la entregó la Feature 004 | Compatible, completa el criterio de terminado |
| II. Caminos descartados con razón | Se descarta repurpose de `quality/gates.py` (modelo de "valor <= máximo" sobre una tabla `pandas`, no calza con un presupuesto de mínimo sobre un artefacto JSON con un dato obligatorio adicional, research.md #2); se descarta importar `ModeloDeclarado`/`_mediana_orden` de otros módulos para no acoplar el contrato a implementación interna ni arrastrar dependencias no necesarias (research.md #1/#3) | Compatible |
| III. La guitarra no es un stem estándar | N/A directo -- esta feature no clasifica pistas, solo lee valores ya calculados | N/A para esta feature |
| IV. Fuentes de audio admisibles | N/A directo -- no lee ningún archivo de audio (FR-001, FR-011) | N/A para esta feature |
| V. Qué cuenta como "la guitarra" | N/A directo -- no reabre la clasificación de guitarra, opera sobre referencias ya emparejadas por la Feature 002 | N/A para esta feature |
| VI. Cuantitativa vs. cualitativa | N/A directo -- no lee ningún dataset ni ningún split; el artefacto que juzga ya es el resultado de una corrida que respetó ese principio | N/A para esta feature |
| VII. La métrica y su presupuesto | Es la implementación directa del principio: aplica `-8.0 dB` sobre la mediana de referencias emparejadas (FR-002), nunca sobre la mediana global (research.md #3/#4), y reporta obligatoriamente la fracción sin pareja junto al veredicto (FR-003) -- exactamente lo que el principio exige tras el cierre del `ABIERTO` en v1.5.0. MUST NOT modificar el número (FR-010) | Compatible, es el propósito central de esta feature |
| VIII. Determinismo | El artefacto de entrada ya es determinista (Feature 004); el cálculo nuevo (mediana sobre `stdlib`) se verifica equivalente al que la Feature 002 ya usa, con property test, antes de confiar en él (research.md #3) -- ninguna fuente de no-determinismo nueva | Compatible, verificado con Hypothesis antes de implementar |
| IX. Datos derivados: se generan, no se leen | El `Veredicto` no es un dato persistido -- es la salida de un proceso que termina, no un artefacto que otro paso vuelva a leer. No aplica la prohibición de "leer el dato completo a mano": el artefacto de entrada mismo (Feature 004) ya se generó por script y se verifica por invariantes, no a mano | N/A para el `Veredicto`; compatible para el artefacto de entrada |
| X. Tamaño de slice | Gate de `/speckit-tasks`, no de este plan | Diferido a tasks |

**Nota de gobernanza (Principio VII)**: esta feature no vuelve a abrir el
`ABIERTO` que `/speckit-constitution` ya cerró en v1.5.0 -- lee la
constante `-8.0 dB` como un hecho ya fijado, la misma disciplina que
`orquestador.py` ya aplica para `SEMILLA_SUBMUESTRA_HITO1`.

Sin violaciones que requieran `Complexity Tracking`.

**Re-chequeo post-Phase 1**: `data-model.md` y `contracts/compuerta.md`
confirman que `medicion.compuerta` no importa ningún módulo de dominio
existente (solo lee la forma JSON documentada) y que el único cálculo
nuevo (mediana sobre `stdlib`) fue verificado equivalente al de la
Feature 002 sobre el dominio restringido que esta feature usa
(research.md #3, verificado empíricamente con 200.000 casos antes de
escribir este plan). La tabla de arriba sigue siendo válida sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/005-compuerta-metrica/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── compuerta.md     # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/guitar_tabs_analysis/
└── medicion/
    ├── __init__.py
    ├── orquestador.py               # Feature 004, sin cambios
    ├── cli.py                       # Feature 004, sin cambios
    └── compuerta.py                 # NUEVO -- PRESUPUESTO_SI_SDR_DB,
                                       # Veredicto, ArtefactoInvalidoError,
                                       # evaluar_artefacto(), main(); solo
                                       # stdlib, no importa orquestador.py
                                       # ni la pila de separación
                                       # (research.md #1/#2)

mediciones/
├── .gitkeep
└── submuestra_hito1.json            # Feature 004, ya versionado -- el
                                       # artefacto que `just gauntlet`
                                       # evalúa por defecto (research.md #8)

tests/
└── unit/
    └── test_compuerta.py            # evaluar_artefacto() con dict()s
                                       # sintéticos: presupuesto alcanzado/
                                       # no alcanzado/límite exacto (US1),
                                       # artefacto ausente/irreconocible/
                                       # sin evidencia suficiente (US2),
                                       # dos modos independientes (US3),
                                       # property test de equivalencia de
                                       # mediana (research.md #3), y
                                       # main()/CLI con monkeypatch de
                                       # rutas (sin tocar el artefacto real)
```

**Structure Decision**: Opción 1 (proyecto único), consistente con
Features 001-004. `compuerta.py` vive junto a `orquestador.py`/`cli.py`
dentro de `medicion/` porque juzga exactamente lo que esos módulos
producen (cohesión de dominio), pero a diferencia de ellos no necesita
separar lógica de CLI en dos archivos: no importa nada pesado que aislar
(ni `torch`, ni siquiera el resto del propio proyecto -- research.md
#1/#2), así que un único archivo con `main()` incluido sigue el mismo
patrón que `quality/gates.py` ya establece para este caso. No se toca
`pyproject.toml::[tool.importlinter]`: `medicion` ya está excluida por
completo del contrato `layers` desde la Feature 004, y `compuerta.py`
no introduce ninguna dependencia nueva entre capas que ese contrato
necesite conocer.

## Complexity Tracking

*Sin violaciones de principios -- tabla omitida. Esta feature reduce
superficie en vez de aumentarla: no agrega ninguna dependencia nueva, ni
de terceros ni entre paquetes propios del proyecto.*
