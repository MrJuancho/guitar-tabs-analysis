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

**Primary Dependencies (proyecto principal, Python 3.12)**: `mir_eval`
(MIT -- research.md #3/#4/#5), `mirdata` (BSD-3-Clause -- research.md
#7). Ninguna reemplaza ni convive en conflicto con las dependencias del
hito 1 (`torch`/`demucs` siguen siendo exclusivas de `separacion`).
**`basic-pitch` NO es una dependencia del proyecto principal** --
corregido en `/speckit-implement` (research.md #2/#15): es irresoluble
en Python 3.12 (su dependencia base arrastra `tensorflow<2.15.1`, sin
rueda `cp312`). Vive en `envs/basic_pitch_py310/`, un segundo proyecto
`uv` fijado a Python 3.10, con sus propias dependencias (`basic-pitch`
sin extra, `numpy<2`, `setuptools<81` -- research.md #15) y su propio
`uv.lock`, invocado por subproceso desde `transcripcion/basic_pitch_transcriptor.py`.

**Storage**: Ninguna nueva más allá del patrón ya establecido -- el
artefacto final (`ArtefactoDeteccion`) se persiste como JSON pequeño y
versionado, mismo mecanismo de escritura atómica (archivo temporal +
`os.replace()`) que `medicion` ya usa en el hito 1. Ubicación exacta a
fijar en `/speckit-tasks`.

**Testing**: `pytest` + `hypothesis`. Toda la lógica de emparejamiento,
clasificación de polifonía y agregación se prueba con notas construidas
a mano y un `TranscriptorFalso` sintético (mismo patrón que
`SeparadorFalso` del hito 1), en milisegundos, sin invocar el
subproceso de `basic_pitch` en absoluto. Un único test nuevo marcado
`modelo_real` ejercita `BasicPitchTranscriptor.transcribir()` de punta a
punta -- subproceso real incluido -- sobre una grabación corta real de
GuitarSet -- nunca corre como parte de `just gauntlet`.

**Target Platform**: Linux (WSL/Ubuntu), CPU-only -- sin cambios
respecto al hito 1; Basic Pitch corre sobre TFLite (research.md #2/#15,
corregido de la decisión original de ONNX -- irresoluble en cp312 y en
cp310 por igual), dentro de un entorno Python 3.10 aparte, sin GPU ni
framework de ML pesado adicional.

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
contradicción. El backend de inferencia de Basic Pitch MUST ser TFLite,
nunca TensorFlow completo (research.md #2/#15, corregido -- ONNX
resultó irresoluble en cp312 y en cp310 por igual). El proyecto
principal MUST NOT bajar su `requires-python` de `>=3.12` para
acomodar `basic-pitch` -- vive en un entorno Python 3.10 aparte,
invocado por subproceso (research.md #15), nunca importado en proceso.

**Scale/Scope**: 360 grabaciones de GuitarSet (research.md #7, ~30 s
cada una). **288 (80%) medibles por esta feature; 72 (20%) reservadas
como conjunto intocable del hito 2** (constitución Principio VI, v1.8.0;
research.md #14): semilla declarada `20260908` sobre los 360
identificadores ordenados, mismo criterio de muestreo que la submuestra
del hito 1. `ejecutar_deteccion()` (contracts/deteccion.md) no decide por
sí misma qué grabaciones mide -- recibe la lista explícita de su
llamador; es responsabilidad de quien construye esa lista (la CLI, fuera
de alcance de este plan hasta que `/speckit-tasks` la agregue) excluir
las 72 reservadas de cualquier corrida de desarrollo.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Aplica a esta feature | Estado |
|---|---|---|
| I. Hito 1 es línea base medida | El principio en sí es específico del hito 1 en su redacción ("hito 1"), pero esta feature aplica su mismo criterio al hito 2: línea base con modelo preentrenado, sin entrenar ni afinar (FR-010). No reabre ni contradice el criterio de terminado del hito 1, que ya está cerrado (Features 001-005) | Compatible por extensión del mismo criterio, no una relectura del hito 1 |
| II. Caminos descartados con razón | Se descartan Omnizart (checkpoints sin licencia verificable, y no es en realidad guitar-específico pese a la apariencia inicial), MT3 (licencia de checkpoints no verificada, runtime más pesado) y CREPE (monofónico puro, sin inicio de nota) -- research.md #1. Se descarta reimplementar el emparejamiento óptimo y la conversión MIDI↔Hz en vez de reusar `mir_eval` -- research.md #5 | Compatible |
| III. La guitarra no es un stem estándar | N/A directo -- esta feature no clasifica pistas por instrumento, GuitarSet ya es guitarra sola por construcción | N/A para esta feature |
| IV. Fuentes de audio admisibles | GuitarSet ya declarado admisible (CC BY 4.0) desde la enmienda de constitución que fijó las fuentes del hito 2 -- esta feature no reabre esa decisión (spec.md, Assumptions). El modelo (Basic Pitch) se verifica aquí por primera vez: Apache-2.0 para código y pesos, sin asimetría, verificado contra el archivo `LICENSE` real (research.md #1) -- entrada nueva en `docs/ATRIBUCIONES.md` (research.md #13) | Compatible, verificado no supuesto |
| V. Qué cuenta como "la guitarra" | N/A directo -- GuitarSet es guitarra sola por construcción del propio dataset, no hay clasificación de pistas que reabrir | N/A para esta feature |
| VI. Cuantitativa vs. cualitativa | Generalizado a v1.7.0: todo hito reserva una porción intocable de su conjunto de evaluación. Esta feature la fija: 72 de 360 grabaciones de GuitarSet (20%), semilla `20260908` (research.md #14, constitución v1.8.0) -- protegida por el mismo hook `PreToolUse` que `tests/holdout/`, igual que el split `test` de Slakh2100 del hito 1 | Compatible, cerrado con evidencia (spec.md, Assumptions actualizado) |
| VII. La métrica y su presupuesto | FR-009: MUST NOT definir ni evaluar ningún umbral de aprobación -- esta feature mide y reporta, el presupuesto se fija después con la evidencia (mismo patrón que el hito 1, Feature 004 → enmienda de constitución) | N/A para esta feature, por diseño -- es la entrada del futuro cierre de presupuesto para el hito 2, no el cierre en sí |
| VIII. Determinismo | Basic Pitch corre sobre CPU vía TFLite (corregido de ONNX, research.md #2/#15), en un subproceso Python 3.10 aparte -- sin ninguna fuente de aleatoriedad declarada en el modelo en sí (a diferencia de Demucs, que sí tenía `shifts` aleatorio por defecto, Feature 003); el límite de proceso agrega una superficie nueva a verificar (¿produce el subproceso el mismo resultado invocación tras invocación sobre el mismo archivo?) que Demucs no tenía -- se verifica en `/implement` que dos invocaciones sobre la misma grabación producen el mismo resultado exacto o dentro de tolerancia numérica, mismo criterio que el resto del proyecto | Compatible, a verificar empíricamente en `/implement` (mismo criterio que Feature 003 verificó `shifts=0`) |
| IX. Datos derivados: se generan, no se leen | El artefacto final es un dato derivado producido por un script versionado; se verifica por invariantes (cantidad de grabaciones, exclusiones, denominadores de cada cifra), nunca leyendo el JSON completo a mano | Compatible, mismo patrón que el hito 1 |
| X. Tamaño de slice | Gate de `/speckit-tasks`, no de este plan | Diferido a tasks |

**Nota de gobernanza (Principios VI/VII)**: los Principios VI y VII ya
se generalizaron a cualquier hito en la constitución v1.7.0 (no son
específicos del hito 1 desde entonces). Esta feature cierra la instancia
del hito 2 de Principio VI: 72 de 360 grabaciones de GuitarSet (20%)
reservadas, semilla `20260908` (research.md #14, constitución v1.8.0) --
spec.md (Assumptions) se actualizó para reflejar esta decisión, en vez
de mantener la justificación anterior ("no hay conjunto reservado
dentro de GuitarSet") que la enmienda de constitución dejó obsoleta.
Principio VII (métrica y presupuesto del hito 2) sigue sin poder
cerrarse: su propio criterio de cierre es la primera medición real de
esta feature, que todavía no ocurrió.

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
│   └── basic_pitch_transcriptor.py # invoca por subproceso el
│                                     # intérprete de envs/basic_pitch_py310/
│                                     # (research.md #15) -- NO importa
│                                     # basic_pitch en proceso, es
│                                     # irresoluble en Python 3.12
│                                     # (research.md #2)
├── analytics/
│   ├── metrica_separacion.py       # hito 1, sin cambios
│   └── metrica_deteccion_notas.py  # NUEVO -- NotaEstimada,
│                                     # ExclusionDeteccion,
│                                     # ResultadoDeteccionGrabacion (**no**
│                                     # en deteccion/orquestador.py --
│                                     # agregar_conjunto() las necesita en
│                                     # su propia firma, y analytics no
│                                     # puede importar de deteccion sin
│                                     # ciclo, research.md #11),
│                                     # clasificar_polifonia_en_instante(),
│                                     # evaluar_subconjunto(),
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
                                      # ArtefactoDeteccion (importa
                                      # ExclusionDeteccion/
                                      # ResultadoDeteccionGrabacion desde
                                      # analytics, no las define); fallo
                                      # de inferencia por grabación es
                                      # terminal (research.md #10)

envs/
└── basic_pitch_py310/                # NUEVO -- segundo proyecto uv,
                                       # Python 3.10 fijo (research.md #15).
                                       # El proyecto principal (>=3.12) NO
                                       # depende de este directorio para
                                       # nada -- es el entorno principal el
                                       # que lo invoca por subproceso, no
                                       # al revés.
    ├── pyproject.toml                 # basic-pitch (sin extra), numpy<2,
    │                                   # setuptools<81 -- los tres pines
    │                                   # verificados necesarios, no solo
    │                                   # basic-pitch a secas
    ├── uv.lock                        # versionado -- reproducibilidad,
                                        # no opcional
    └── transcribir_subproceso.py      # CLI: <ruta_audio> <ruta_salida_json>
                                        # -- éxito escribe el JSON y sale 0;
                                        # fallo NUNCA escribe el archivo,
                                        # sale distinto de 0
                                        # (contracts/deteccion.md)

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

**Corrección (sesión de `/speckit-implement`, T010-T015): un segundo
entorno, `envs/basic_pitch_py310/`, se suma a la Opción 1 de arriba --
no la reemplaza.** `src/`/`tests/` del proyecto principal siguen siendo
un único proyecto Python 3.12; `envs/basic_pitch_py310/` es un proyecto
`uv` independiente, con su propio `pyproject.toml`/`uv.lock`, fuera del
árbol de import-linter por completo (no es un paquete de
`guitar_tabs_analysis`, corre bajo otro intérprete) -- ver research.md
#15 para por qué es necesario (`basic-pitch` es irresoluble en 3.12) y
research.md #2 para la corrección del backend (TFLite, no ONNX).

## Complexity Tracking

*Sin violaciones de principios que requieran justificación -- tabla
omitida. La complejidad real nueva (una capa más, un segundo paquete
orquestador, y -- corrección de esta sesión -- un segundo entorno Python
para `basic-pitch`) sigue un patrón justificado por necesidad técnica
verificada (research.md #2/#15: sin ONNX ni un `basic-pitch` resoluble
en 3.12, no hay forma de correr el modelo declarado sin un entorno
aparte), no una excepción ad hoc ni una preferencia arquitectónica sin
respaldo.*
