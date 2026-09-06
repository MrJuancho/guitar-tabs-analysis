# Implementation Plan: Medición de la línea base

**Branch**: `004-medicion-linea-base` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-medicion-linea-base/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Orquesta, tema a tema, `leer_tema` (Feature 001) → `separar_guitarra` con
`DemucsSeparador` (Feature 003) → `emparejar_tema` (Feature 002), persiste
el resultado de cada tema de inmediato (éxito o exclusión, nunca el audio),
y al completar todos los temas de una corrida ensambla un único artefacto
JSON pequeño y versionable con la mediana, la distribución de referencias
y las exclusiones. Dos modos explícitos, sin default (FR-004): la
submuestra del hito 1 (40 temas de `validation`, semilla `20260904`) y el
conjunto evaluable completo de esta feature (`train`+`validation`, 1559
temas, excluyendo `test` y `omitted` por construcción — nunca se listan
esos directorios, research.md #7). Un fallo duro de lectura o separación
se persiste como exclusión terminal (`fallo_procesamiento`) y la corrida
sigue; un progreso persistido cuya firma de modelo no coincide con la
vigente aborta la reanudación con un mensaje explícito (`ModeloCambiadoError`,
FR-008a). Detalle completo de cada decisión en [research.md](./research.md).

## Technical Context

**Language/Version**: Python 3.12 (mismo `requires-python` que el resto del proyecto)

**Primary Dependencies**: Ninguna dependencia nueva de terceros. Reutiliza
`ingestion.slakh2100.leer_tema` (Feature 001), `separacion.separador.separar_guitarra`
y `separacion.demucs_separador.DemucsSeparador` (Feature 003),
`analytics.metrica_separacion.emparejar_tema` (Feature 002) y dos funciones
nuevas extraídas de `agregar_conjunto` para no duplicar la aritmética de la
mediana (research.md #2). Solo `stdlib` nueva para este módulo: `argparse`,
`json`, `random`, `os`, `dataclasses`.

**Storage**: Archivos JSON en disco, dos ubicaciones con propósitos
distintos (research.md #4): progreso persistido efímero y regenerable en
`data/silver/mediciones/<modo>/` (ya cubierto por la regla existente
`data/silver/*` de `.gitignore`, sin cambios ahí), y el artefacto final
pequeño y versionado en `mediciones/<modo>.json` (nuevo directorio de nivel
superior, trackeado — FR-011).

**Testing**: `pytest` + `hypothesis`. Toda la orquestación se prueba con
`SeparadorFalso` (fixture de la Feature 003) y `construir_tema_sintetico`
(fixture de la Feature 001, reutilizada sin modificar) sobre `tmp_path`,
en milisegundos, sin `torch`/`demucs`. Un único test nuevo marcado
`modelo_real` ejercita `procesar_tema` de punta a punta con
`DemucsSeparador` real sobre un tema sintético de 1-2s (mismo patrón que
`test_demucs_separador_integracion.py` de la Feature 003) — nunca corre
como parte de `just gauntlet`. La corrida real de 40 o 1559 temas
completos **no es un test de pytest**: es una invocación manual del CLI
(quickstart.md), fuera del ciclo de test-y-verificación.

**Target Platform**: Linux (WSL/Ubuntu), CPU-only — sin cambios respecto a
la Feature 003.

**Project Type**: Single project — nueva capa `medicion`, por encima de
`separacion`, `analytics` e `ingestion`, deliberadamente **excluida** del
contrato `type = "layers"` de import-linter por ser el orquestador
(AGENTS.md, "Arquitectura": "si el proyecto tiene un orquestador... no lo
agregues a la lista `layers`").

**Performance Goals**: Ninguno de throughput (FR-012 prohíbe evaluar
umbral). Referencia operativa, no un objetivo que este plan mida: ~36 min
para 40 temas, ~23,1 h para 1559 (spec.md, research.md #9 de la Feature
003).

**Constraints**: Un tema en memoria a la vez, nunca dos (FR-005) —
`procesar_tema` recibe y libera su propio `PistaAudio`/`Estimacion` antes
de que el bucle continúe con el siguiente tema, sin acumular audio en
ninguna lista de nivel de corrida. Escritura de progreso atómica (archivo
temporal + `os.replace`, research.md #5) para que una interrupción a
mitad de escritura nunca deje un reporte de tema corrupto y a medias.
Ningún modo por defecto (FR-004): el CLI exige `--modo` sin valor por
omisión. Verificación de firma del modelo antes de reanudar (FR-008a).

**Scale/Scope**: 40 temas (submuestra del hito 1) o 1559 temas (conjunto
evaluable completo de esta feature: `train` + `validation`, excluyendo
`test` y `omitted`), procesados secuencialmente, uno a la vez, en una o
más invocaciones (reanudable).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Aplica a esta feature | Estado |
|---|---|---|
| I. Hito 1 es línea base medida | Esta feature entrega la primera mitad del "criterio de terminado" del principio: "un comando reproducible que, dado el conjunto de evaluación, emite la métrica agregada y por pista" (FR-001 a FR-011). La segunda mitad — "una compuerta que falla si cae por debajo del presupuesto declarado" — queda explícitamente fuera de alcance (FR-012): el presupuesto sigue `ABIERTO` en el Principio VII y esta feature es la que produce la evidencia para cerrarlo, no la que lo evalúa | Compatible, avanza el criterio de terminado sin completarlo — a propósito |
| II. Caminos descartados con razón | Se descarta usar `agregar_conjunto` en bloque sobre `list[EntradaConjunto]` para la agregación final, por incompatible con la restricción de memoria (exigiría retener referencias/estimaciones de todos los temas hasta el final); se usa `emparejar_tema` por tema + dos funciones de agregación extraídas (research.md #1/#2) | Compatible |
| III. La guitarra no es un stem estándar | N/A directo — esta feature no clasifica pistas, reutiliza Features 001-003 tal como las definen | N/A para esta feature |
| IV. Fuentes de audio admisibles | No introduce ninguna fuente de audio nueva; opera sobre Slakh2100 vía `leer_tema` ya cerrado | Compatible |
| V. Qué cuenta como "la guitarra" | N/A directo — la clasificación de guitarra ya está resuelta por Feature 001/metadatos; esta feature no la reabre | N/A para esta feature |
| VI. Cuantitativa vs. cualitativa | FR-003/FR-014: el modo "conjunto evaluable completo" nunca lista ni procesa el split `test` — por construcción (solo se listan `train`/`validation`), no por un chequeo que podría fallar en tiempo de ejecución | Compatible, implementado por diseño (no por validación posterior) |
| VII. La métrica y su presupuesto | FR-012: MUST NOT definir ni evaluar umbral de aprobación — el artefacto que esta feature produce es exactamente la evidencia que el Principio VII exige antes de cerrar el presupuesto numérico | N/A para esta feature, por diseño — es la entrada del próximo cierre de `ABIERTO`, no el cierre en sí |
| VIII. Determinismo | No introduce un nuevo tipo de valor calculado (reutiliza `si_sdr`/`emparejar_tema` de la Feature 002 tal como están); si se reanuda con un modelo de firma distinta, FR-008a evita mezclar resultados no comparables entre sí en el mismo artefacto — refuerza la disciplina de determinismo del principio a nivel de corrida completa, no solo de una inferencia individual | Compatible, refuerza el principio a un nivel más alto |
| IX. Datos derivados: se generan, no se leen | El artefacto final (`mediciones/<modo>.json`) es un dato derivado producido por un script versionado (`medicion.cli`); se verifica por invariantes (longitudes, suma de la distribución, ver data-model.md), nunca leyendo el JSON completo a mano como criterio de corrección | Compatible, implementado directamente |
| X. Tamaño de slice | Gate de `/speckit-tasks`, no de este plan | Diferido a tasks |

**Nota de gobernanza (Principio VII)**: este plan no cierra el `ABIERTO`
del presupuesto numérico — sigue prohibido rellenarlo por adelantado. Una
vez que este comando corra sobre la submuestra del hito 1 y produzca
`mediciones/submuestra_hito1.json`, se recomienda correr
`/speckit-constitution` para registrar el número resultante y cerrar ese
`ABIERTO` con la cifra real, siguiendo la misma disciplina que ya se usó
para SI-SDR y determinismo tras la Feature 002.

Sin violaciones que requieran `Complexity Tracking`. La única
complejidad real nueva — una capa por encima de las otras tres,
excluida a propósito del contrato de import-linter — está justificada y
documentada arriba (Project Structure) y en AGENTS.md, no es una
excepción ad hoc de esta feature.

**Re-chequeo post-Phase 1**: `data-model.md` y `contracts/medicion.md`
confirman que ningún tipo nuevo duplica un contrato ya cerrado (reutiliza
`ReporteTema`, `ModeloDeclarado`, `Separador` tal cual) y que la única
extensión a una feature ya cerrada (`calcular_mediana_agregada`/
`calcular_distribucion_referencias` extraídas de `agregar_conjunto`,
research.md #2) no cambia el comportamiento observable de la Feature 002.
La tabla de arriba sigue siendo válida sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/004-medicion-linea-base/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── medicion.md      # Phase 1 output (/speckit-plan command)
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/guitar_tabs_analysis/
└── medicion/                       # capa NUEVA -- orquestador, excluida
                                     # del contrato de layers (research.md #6)
    ├── __init__.py
    ├── orquestador.py              # ModoEjecucion, ExclusionMedicion,
    │                                # ArtefactoMedicion, ManifiestoCorrida,
    │                                # ModeloCambiadoError; derivar_temas_*(),
    │                                # procesar_tema(), ejecutar_corrida();
    │                                # NO importa torch ni demucs directamente
    │                                # (recibe un Separador ya construido)
    └── cli.py                       # argparse (--modo, --root-dir, sin
                                      # default -- FR-004); único módulo de
                                      # esta capa que importa
                                      # separacion.demucs_separador
                                      # (construye DemucsSeparador una vez)

mediciones/                          # NUEVO directorio de nivel superior,
                                      # trackeado -- artefactos finales
                                      # pequeños y versionables (FR-011)
└── .gitkeep

data/silver/mediciones/              # progreso persistido efímero, ya
                                      # cubierto por `data/silver/*` de
                                      # .gitignore (sin cambios ahí)

tests/
├── unit/
│   └── test_orquestador.py         # procesar_tema()/derivar_temas_*() con
│                                     # SeparadorFalso + construir_tema_sintetico:
│                                     # fallo terminal (FR-006), no reintento al
│                                     # reanudar (FR-008), firma de modelo
│                                     # distinta (FR-008a), modo sin default
│                                     # (FR-004), conjunto vacío (Edge Cases)
├── integration/
│   ├── test_orquestador_integracion.py  # ejecutar_corrida() end-to-end:
│   │                                       interrupción simulada + reanudación
│   │                                       (US2), artefacto final equivalente
│   │                                       con/sin interrupción (FR-009),
│   │                                       ambos modos con dataset sintético
│   │                                       de varios splits (US1, US3)
│   └── test_medicion_modelo_real_integracion.py  # ÚNICO test
│                                       # @pytest.mark.modelo_real de esta
│                                       # feature: procesar_tema() con
│                                       # DemucsSeparador real sobre un tema
│                                       # sintético corto
└── fixtures/
    └── dataset_sintetico_fixture.py    # construye varios temas (varios
                                          # splits) sobre un mismo tmp_path
                                          # reutilizando construir_tema_sintetico
                                          # de Feature 001, sin modificarla
```

**Structure Decision**: Opción 1 (proyecto único), consistente con
Features 001-003. `medicion` es la primera capa de este proyecto que
importa de las tres capas existentes a la vez (`ingestion`, `separacion`,
`analytics`) — exactamente el caso que AGENTS.md ya anticipa y por el que
pide dejarla **fuera** de la lista `layers` del contrato de
import-linter, documentado como excepción deliberada en vez de forzarla a
encajar en una capa (edición de `pyproject.toml::[tool.importlinter]` a
hacer en `/speckit-tasks`, mismo patrón que la Feature 003 usó para
agregar su propia capa nueva). La separación entre `orquestador.py`
(lógica pura + persistencia con `json`/`pathlib`, sin `torch`) y
`cli.py` (única puerta de entrada que construye `DemucsSeparador`) es la
misma que ya usan `separacion/separador.py` y
`separacion/demucs_separador.py` — mantiene los tests de orquestación
rápidos sin cargar el modelo real (research.md #3).

## Complexity Tracking

*Sin violaciones de principios — tabla omitida. La única complejidad
real nueva (una capa que cruza las otras tres a propósito) está
justificada arriba, en "Constitution Check" y en "Structure Decision",
como una excepción documentada del contrato de import-linter, no como
una violación.*
