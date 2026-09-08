# Implementation Plan: Detección de notas sobre guitarra limpia

**Branch**: `006-deteccion-notas-guitarra-limpia` | **Date**: 2026-09-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-deteccion-notas-guitarra-limpia/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Dada una grabación de guitarra limpia de GuitarSet, transcribe sus notas
(tono e inicio) con Basic Pitch (Spotify, Apache-2.0 para código y
pesos, sin la asimetría de licencia que Demucs tuvo en el hito 1), las
empareja contra la anotación de referencia con `mir_eval.transcription`
(tolerancia de tono 50 cents, ventana de inicio 50 ms -- convención
MIREX Note Tracking, no inventada), ignora la duración a propósito
(`offset_ratio=None`), y agrega precisión/exhaustividad/balance (F1)
sobre un conjunto de grabaciones -- global y separado entre notas de
referencia monofónicas y polifónicas, clasificadas exclusivamente desde
la verdad conocida. Un fallo de inferencia por grabación individual es
una exclusión terminal, no aborta la corrida (mismo patrón que el hito
1). Sin entrenamiento, sin umbral de aprobación -- el presupuesto se
fija después, con la evidencia real (Principio VII). Detalle completo de
cada decisión, verificada contra el código fuente real de cada
dependencia (no memoria ni documentación de segunda mano), en
[research.md](./research.md).

## Technical Context

**Language/Version**: Python 3.12 (mismo `requires-python` que el resto del proyecto)

**Primary Dependencies**: `basic-pitch[onnx]` (Apache-2.0, código y
pesos -- research.md #1/#2, nunca el extra `[tf]`), `mir_eval` (MIT --
research.md #3/#4/#5, ya viene como dependencia transitiva de
`basic-pitch` pero se declara directa porque este proyecto la usa
explícitamente, no solo indirectamente), `mirdata` (BSD-3-Clause --
research.md #7). Ninguna reemplaza ni convive en conflicto con las
dependencias del hito 1 (`torch`/`demucs` siguen siendo exclusivas de
`separacion`).

**Storage**: Ninguna nueva más allá del patrón ya establecido -- el
artefacto final (`ArtefactoDeteccion`) se persiste como JSON pequeño y
versionado, mismo mecanismo de escritura atómica (archivo temporal +
`os.replace()`) que `medicion` ya usa en el hito 1. Ubicación exacta a
fijar en `/speckit-tasks`.

**Testing**: `pytest` + `hypothesis`. Toda la lógica de emparejamiento,
clasificación de polifonía y agregación se prueba con notas construidas
a mano y un `TranscriptorFalso` sintético (mismo patrón que
`SeparadorFalso` del hito 1), en milisegundos, sin `basic_pitch`/
`onnxruntime` cargando ningún modelo. Un único test nuevo marcado
`modelo_real` ejercita `BasicPitchTranscriptor.transcribir()` de punta a
punta sobre una grabación corta real de GuitarSet -- nunca corre como
parte de `just gauntlet`.

**Target Platform**: Linux (WSL/Ubuntu), CPU-only -- sin cambios
respecto al hito 1; Basic Pitch corre sobre `onnxruntime` (research.md
#2), sin GPU ni framework de ML pesado adicional.

**Project Type**: Single project -- dos capas nuevas (`ingestion/guitarset.py`
en la capa ya existente; `transcripcion/`, capa nueva paralela a
`separacion/`) más un módulo nuevo en `analytics/` y un paquete
orquestador nuevo (`deteccion/`), excluido del contrato `layers` de
import-linter por el mismo motivo que `medicion` (research.md #11).

**Performance Goals**: Ninguno de throughput (FR-009 prohíbe evaluar
umbral). El tiempo real de inferencia sobre GuitarSet se mide en
`/speckit-implement`, no se estima aquí (research.md #12) -- referencia
operativa, no un objetivo que este plan fije: las grabaciones de
GuitarSet (~30 s cada una) son mucho más cortas que un tema de Slakh2100
(~240 s), así que se espera (sin ser una medición) que el presupuesto de
tiempo total sea manejable.

**Constraints**: Un fallo de inferencia por grabación es terminal, no
aborta la corrida (FR-012, research.md #10). La duración de las notas
(estimadas y de referencia) nunca participa del criterio de acierto
(FR-004, research.md #4) aunque sí participa de la clasificación de
polifonía (research.md #8) -- dos usos distintos del mismo dato, no una
contradicción. El backend de inferencia de Basic Pitch MUST ser
`onnxruntime`, nunca TensorFlow (research.md #2).

**Scale/Scope**: 360 grabaciones de GuitarSet (research.md #7, ~30 s
cada una), medidas todas -- esta feature no aparta un subconjunto de
desarrollo/evaluación dentro de GuitarSet (spec.md, Assumptions: no hay
entrenamiento ni selección de modelo basada en el resultado).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Aplica a esta feature | Estado |
|---|---|---|
| I. Hito 1 es línea base medida | El principio en sí es específico del hito 1 en su redacción ("hito 1"), pero esta feature aplica su mismo criterio al hito 2: línea base con modelo preentrenado, sin entrenar ni afinar (FR-010). No reabre ni contradice el criterio de terminado del hito 1, que ya está cerrado (Features 001-005) | Compatible por extensión del mismo criterio, no una relectura del hito 1 |
| II. Caminos descartados con razón | Se descartan Omnizart (checkpoints sin licencia verificable, y no es en realidad guitar-específico pese a la apariencia inicial), MT3 (licencia de checkpoints no verificada, runtime más pesado) y CREPE (monofónico puro, sin inicio de nota) -- research.md #1. Se descarta reimplementar el emparejamiento óptimo y la conversión MIDI↔Hz en vez de reusar `mir_eval` -- research.md #5 | Compatible |
| III. La guitarra no es un stem estándar | N/A directo -- esta feature no clasifica pistas por instrumento, GuitarSet ya es guitarra sola por construcción | N/A para esta feature |
| IV. Fuentes de audio admisibles | GuitarSet ya declarado admisible (CC BY 4.0) desde la enmienda de constitución que fijó las fuentes del hito 2 -- esta feature no reabre esa decisión (spec.md, Assumptions). El modelo (Basic Pitch) se verifica aquí por primera vez: Apache-2.0 para código y pesos, sin asimetría, verificado contra el archivo `LICENSE` real (research.md #1) -- entrada nueva en `docs/ATRIBUCIONES.md` (research.md #13) | Compatible, verificado no supuesto |
| V. Qué cuenta como "la guitarra" | N/A directo -- GuitarSet es guitarra sola por construcción del propio dataset, no hay clasificación de pistas que reabrir | N/A para esta feature |
| VI. Cuantitativa vs. cualitativa | El principio en su redacción actual es específico de Slakh2100/hito 1 (split `test` reservado). Esta feature no aparta un subconjunto reservado de GuitarSet -- justificado explícitamente en spec.md (Assumptions): sin entrenamiento ni selección de modelo basada en el resultado, el riesgo que el principio protege no aplica de la misma forma. Si una feature futura comparara varios modelos entre sí, esa sí necesitaría su propio conjunto reservado | Compatible por el argumento explícito de spec.md, no una omisión |
| VII. La métrica y su presupuesto | FR-009: MUST NOT definir ni evaluar ningún umbral de aprobación -- esta feature mide y reporta, el presupuesto se fija después con la evidencia (mismo patrón que el hito 1, Feature 004 → enmienda de constitución) | N/A para esta feature, por diseño -- es la entrada del futuro cierre de presupuesto para el hito 2, no el cierre en sí |
| VIII. Determinismo | Basic Pitch corre sobre CPU vía ONNX, sin ninguna fuente de aleatoriedad declarada (a diferencia de Demucs, que sí tenía `shifts` aleatorio por defecto, Feature 003) -- se verifica en `/implement` que dos corridas sobre la misma grabación producen el mismo resultado exacto o dentro de tolerancia numérica, mismo criterio que el resto del proyecto | Compatible, a verificar empíricamente en `/implement` (mismo criterio que Feature 003 verificó `shifts=0`) |
| IX. Datos derivados: se generan, no se leen | El artefacto final es un dato derivado producido por un script versionado; se verifica por invariantes (cantidad de grabaciones, exclusiones, denominadores de cada cifra), nunca leyendo el JSON completo a mano | Compatible, mismo patrón que el hito 1 |
| X. Tamaño de slice | Gate de `/speckit-tasks`, no de este plan | Diferido a tasks |

**Nota de gobernanza (Principios VI/VII)**: esta feature toca dos
principios cuya redacción literal es específica del hito 1 (Slakh2100,
Principio VI; el presupuesto de guitarra separada, Principio VII). No
los contradice -- los aplica al hito 2 por extensión del mismo criterio,
con su propia justificación explícita donde diverge (no hay conjunto
reservado dentro de GuitarSet, spec.md Assumptions). Una vez que esta
feature mida y `/speckit-constitution` fije el presupuesto real del
hito 2, sería razonable que esa misma sesión generalice la redacción de
estos principios para cubrir ambos hitos explícitamente -- no es trabajo
de este plan, se deja registrado como sugerencia para esa sesión futura.

Sin violaciones que requieran `Complexity Tracking`.

**Re-chequeo post-Phase 1**: `data-model.md` y `contracts/deteccion.md`
confirman que ningún tipo nuevo duplica un contrato ya cerrado del hito
1 (`NotaReferencia`/`NotaEstimada` son nuevos porque el dominio es
distinto -- notas, no stems de audio -- pero siguen el mismo patrón de
diseño: `frozen=True`, unión etiquetada para resultados con exclusión,
mismo mecanismo de escritura atómica). La tabla de arriba sigue siendo
válida sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/006-deteccion-notas-guitarra-limpia/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── deteccion.md     # Phase 1 output (/speckit-plan command)
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/guitar_tabs_analysis/
├── ingestion/
│   ├── slakh2100.py                # hito 1, sin cambios
│   └── guitarset.py                # NUEVO -- leer_grabacion(), envuelve
│                                     # mirdata para audio_mic + notas_all
│                                     # (research.md #6/#7)
├── transcripcion/                   # capa NUEVA, paralela a separacion/,
│                                     # excluida de nada -- SÍ entra en el
│                                     # contrato layers de import-linter
│                                     # (research.md #11)
│   ├── __init__.py
│   ├── transcriptor.py             # Protocol Transcriptor,
│                                     # ModeloTranscripcionDeclarado
│   └── basic_pitch_transcriptor.py # único módulo que importa
│                                     # basic_pitch; backend onnx forzado
│                                     # (research.md #2)
├── analytics/
│   ├── metrica_separacion.py       # hito 1, sin cambios
│   └── metrica_deteccion_notas.py  # NUEVO -- NotaEstimada,
│                                     # clasificar_polifonia_en_instante(),
│                                     # evaluar_grabacion(),
│                                     # agregar_conjunto(); envuelve
│                                     # mir_eval.transcription
│                                     # (research.md #3/#4/#5/#8/#9)
├── medicion/                        # hito 1, sin cambios
└── deteccion/                       # paquete NUEVO -- orquestador,
                                      # excluido a propósito del contrato
                                      # layers (research.md #11), mismo
                                      # criterio que medicion/
    ├── __init__.py
    └── orquestador.py               # ejecutar_deteccion();
                                      # ArtefactoDeteccion,
                                      # ExclusionDeteccion; fallo de
                                      # inferencia por grabación es
                                      # terminal (research.md #10)

docs/
└── ATRIBUCIONES.md                  # TOCADO -- nueva sección para Basic
                                      # Pitch/GuitarSet/mir_eval/mirdata
                                      # (research.md #13)

tests/
├── unit/
│   ├── test_metrica_deteccion_notas.py       # acierto (tono+inicio,
│   │                                           # duración ignorada),
│   │                                           # emparejamiento óptimo,
│   │                                           # clasificación de
│   │                                           # polifonía, subconjunto
│   │                                           # vacío (US1, US3)
│   └── test_guitarset.py                      # leer_grabacion() sobre
│                                                # fixtures sintéticas
├── integration/
│   ├── test_deteccion_orquestador_integracion.py  # ejecutar_deteccion()
│   │                                                 # end-to-end con
│   │                                                 # TranscriptorFalso:
│   │                                                 # exclusión terminal
│   │                                                 # por fallo (US2 AS4),
│   │                                                 # agregación sobre
│   │                                                 # varias grabaciones
│   │                                                 # (US3)
│   └── test_basic_pitch_modelo_real_integracion.py  # ÚNICO test
│                                                       # @pytest.mark.modelo_real
│                                                       # de esta feature
└── fixtures/
    └── transcriptor_fixture.py      # TranscriptorFalso, mismo patrón
                                       # que separador_fixture.py del
                                       # hito 1
```

**Structure Decision**: Opción 1 (proyecto único), consistente con las
Features 001-005. `transcripcion` es la primera capa nueva desde
`separacion` (Feature 003) -- entra en el contrato `layers` de
import-linter en la misma posición relativa que `separacion` ya ocupa
(puede importar de `analytics` e `ingestion`, ninguna de las dos importa
de ella), verificado por el mismo argumento que research.md #8 de la
Feature 003 ya estableció. `deteccion` es el segundo paquete orquestador
del proyecto (después de `medicion`) -- mismo criterio de exclusión del
contrato `layers`, documentado en el propio `pyproject.toml` con un
comentario, mismo patrón que la Feature 004 ya dejó para `medicion`
(research.md #6 de esa feature).

## Complexity Tracking

*Sin violaciones de principios que requieran justificación -- tabla
omitida. La complejidad real nueva (una capa más y un segundo paquete
orquestador) sigue exactamente el mismo patrón arquitectónico que el
hito 1 ya estableció y validó, documentado arriba y en research.md #11,
no una excepción ad hoc de esta feature.*
