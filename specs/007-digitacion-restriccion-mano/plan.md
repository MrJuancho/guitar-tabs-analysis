# Implementation Plan: Digitación con restricción de la mano

**Branch**: `007-digitacion-restriccion-mano` | **Date**: 2026-09-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-digitacion-restriccion-mano/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Dada una secuencia de notas de referencia de GuitarSet (tono e instante,
nunca la salida del hito 2), asigna a cada una una posición (cuerda,
traste) que reproduzca ese tono dentro de una tolerancia declarada (50
cents, misma fuente de desafinación real que el hito 2, verificada aquí
de forma independiente), minimizando un coste de tres componentes
declarados (estiramiento por instante, desplazamiento y cruce de
cuerdas entre instantes consecutivos, ambos divididos por el tiempo
real disponible). El "instante" se agrupa por proximidad de ataque (30
ms, hallazgo real -- research.md #6, no por solape de intervalo
sostenido, que rompe el límite físico de 6 cuerdas). El problema tiene
subestructura óptima verificada contra el modelo de coste declarado
(research.md #1): programación dinámica (Viterbi sobre un enrejado por
instantes) da el óptimo exacto en tiempo lineal sobre la secuencia,
nunca fuerza bruta ni heurística. Un instante sin combinación válida
(ni con tolerancia, ni dentro del límite de estiramiento) es una
exclusión terminal con motivo distinguible, no aborta la secuencia --
mismo patrón que el hito 2. La validación (User Story 3) compara contra
la cuerda/traste real que GuitarSet anota por cuerda
(`track.notes[cuerda]`, nunca `notes_all`) -- nunca contra el propio
coste que el algoritmo minimiza, sería circular. Sin entrenamiento, sin
umbral de aprobación -- el presupuesto se fija después, con evidencia
(Principio VII). Detalle completo de cada decisión, once de ellas
verificadas con evidencia real medida sobre las 288 grabaciones
medibles de GuitarSet (nunca las 72 reservadas), en
[research.md](./research.md).

## Technical Context

**Language/Version**: Python 3.12 (mismo `requires-python` que el resto del proyecto)

**Primary Dependencies**: `mirdata` (BSD-3-Clause, ya dependencia desde
el hito 2 -- esta feature agrega un uso nuevo, `Track.notes` por cuerda,
research.md #5, nunca usado por `ingestion.guitarset.leer_grabacion`
hasta ahora) y `numpy` (ya dependencia del proyecto). **Sin dependencia
nueva de terceros para el algoritmo de asignación en sí** -- research.md
#2 evaluó bibliotecas existentes (`tuttut`, `PyGuitarPro`, `fretboardgtr`,
`fretboard`) y ninguna implementa el modelo de coste de tres componentes
con dependencia explícita del tiempo que esta spec declara; se
implementa el algoritmo estándar de la literatura (programación
dinámica/Viterbi sobre un enrejado, research.md #1/#2), no un enfoque
nuevo sin precedente.

**Storage**: Ninguna nueva más allá del patrón ya establecido -- el
artefacto final (`ArtefactoDigitacion`) se persiste como JSON pequeño y
versionado, mismo mecanismo de escritura atómica (archivo temporal +
`os.replace()`) que `medicion`/`deteccion` ya usan. Ubicación exacta a
fijar en `/speckit-tasks`.

**Testing**: `pytest` + `hypothesis`. La generación de posiciones
candidatas, el cálculo de cada componente de coste, y la programación
dinámica se prueban con notas construidas a mano -- sin ningún dataset
real. La verificación de optimalidad (FR-006) compara contra fuerza
bruta sobre secuencias sintéticas cortas (acotadas para que la fuerza
bruta sea viable -- es un test de corrección de la implementación, no
del algoritmo en sí, research.md #1). La medición de User Story 3 se
prueba con notas de referencia y posiciones reales anotadas construidas
a mano sobre grabaciones sintéticas, mismo patrón que
`agregar_conjunto` del hito 2.

**Target Platform**: Linux (WSL/Ubuntu), CPU-only. Sin modelo de
inferencia de ningún tipo -- es un algoritmo de optimización combinatoria
puro, sin GPU, sin framework de ML, sin subproceso de otro entorno
Python (a diferencia de `transcripcion.basic_pitch_transcriptor` del
hito 2).

**Project Type**: Single project -- un módulo nuevo en `analytics/`
(tipos de dominio + generación de candidatas + modelo de coste +
programación dinámica + métrica de validación, todo pure computation
sin I/O, mismo criterio que `analytics.metrica_deteccion_notas`), una
función nueva en `ingestion/guitarset.py` ya existente (leer la
posición real anotada por cuerda, research.md #5 -- nunca un módulo de
ingestion paralelo: es el mismo dataset, la misma capa), y un paquete
orquestador nuevo (`digitacion/`), excluido del contrato `layers` de
import-linter por el mismo motivo que `deteccion`/`medicion`
(research.md #11 del hito 2). **Sin una capa `transcripcion`-equivalente
nueva**: a diferencia del hito 2, no hay ningún modelo externo que
envolver -- el algoritmo de asignación es autocontenido, así que vive
directamente en `analytics`, no en una capa productora aparte
(justificado en Project Structure más abajo, no una decisión implícita).

**Performance Goals**: Ninguno de throughput (Principio VII: FR-015
prohíbe evaluar umbral). La complejidad de la programación dinámica es
lineal en el número de instantes de la secuencia, con un factor
acotado por el cuadrado del número de posiciones candidatas por
instante (research.md #1) -- ese número está acotado por una constante
pequeña en la práctica, verificado con evidencia real (research.md #6:
el 100% de los ataques reales medidos, en las 288 grabaciones medibles,
tiene 6 notas simultáneas o menos). No se anticipa el
mismo riesgo de escala que forzó acotar el alcance de la medición en el
hito 1 (research.md #9 de la Feature 003, ~25 h de cómputo proyectadas)
-- se confirma igual con evidencia de reloj real en `/speckit-implement`
antes de asumirlo cerrado, mismo criterio de esta sección para toda
afirmación cuantitativa (AGENTS.md).

**Constraints**: El emparejamiento -- en este caso, la programación
dinámica -- MUST ocurrir siempre dentro de una única grabación, nunca
pooleado entre grabaciones distintas (misma disciplina que FR-013 del
hito 2, aplicada aquí por diseño desde el principio: User Story 2 ya
define "secuencia" como una grabación completa, spec.md Assumptions
"Reutilización del conjunto medible"). Determinismo: posiciones
asignadas y motivos de exclusión son resultados discretos, se comparan
con igualdad exacta (Principio VIII, opción (b) ya cerrada); costes
totales son sumas de punto flotante, se comparan con tolerancia
numérica.

**Scale/Scope**: 288 grabaciones medibles de GuitarSet (el mismo
complemento del hito 2, semilla `20260908`, Principio VI -- nunca las
72 reservadas, verificado en cada medición de este plan reutilizando
`deteccion.orquestador.construir_lista_grabaciones("medibles", ...)`
tal cual, no una segunda partición). 49538 notas de referencia medibles
reales (research.md #4/#9), hasta 6 notas simultáneas por instante en
el 100% de los casos reales medidos con la definición correcta de
instante (research.md #6).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Aplica a esta feature | Estado |
|---|---|---|
| I. Hito 1 es línea base medida | Específico del hito 1 en su redacción, pero el mismo criterio aplica por extensión: línea base con un algoritmo declarado explícitamente, sin entrenar ni afinar nada (no hay modelo que entrenar aquí -- es un algoritmo exacto, no aprendido) | Compatible por extensión del mismo criterio |
| II. Caminos descartados con razón | Búsqueda exhaustiva sobre el producto completo de candidatas -- descartada, exponencial (research.md #1). Heurísticas sin garantía de optimalidad -- descartadas, el modelo tiene subestructura óptima verificada, renunciar a la solución exacta sin motivo (research.md #1). Modelar distancia física en mm en vez de número de trastes -- descartada por ahora, simplificación consciente y declarada (research.md #12). Bibliotecas de terceros evaluadas y descartadas por no implementar el modelo de coste declarado (research.md #2) | Compatible |
| III. La guitarra no es un stem estándar | N/A directo -- no hay separación de fuentes en esta feature | N/A para esta feature |
| IV. Fuentes de audio admisibles | GuitarSet ya admisible (CC BY 4.0) desde el hito 2 -- esta feature no reabre esa decisión, ni introduce ninguna fuente nueva (usa el mismo dataset, con un acceso nuevo a datos ya admitidos: `track.notes` por cuerda en vez de `notes_all`) | Compatible, sin fuente nueva que verificar |
| V. Qué cuenta como "la guitarra" | GuitarSet es guitarra sola por construcción, sin pistas múltiples que elegir (FR-011 defiere explícitamente esa pregunta al hito 4) | N/A para esta feature, deferred a FR-011 |
| VI. Cuantitativa vs. cualitativa | Reutiliza tal cual la reserva ya cerrada del hito 2 (72/360, semilla `20260908`, v1.8.0) -- FR-008/spec.md Assumptions. Esta feature NO abre una reserva nueva: verificado en research.md #4/#8/#9 que toda medición se corrió exclusivamente sobre las 288 medibles, reproduciendo la misma partición con la misma función ya existente | Compatible, ninguna decisión nueva que cerrar |
| VII. La métrica y su presupuesto | FR-015: MUST NOT definir ni evaluar ningún umbral de aprobación -- esta feature mide y reporta (User Story 3), el presupuesto se fija después con evidencia real (mismo patrón que hito 1 → Feature 004, hito 2 → Feature 006) | N/A para esta feature, por diseño -- es la entrada del futuro cierre de presupuesto del hito 3, no el cierre en sí |
| VIII. Determinismo | Opción (b) ya cerrada (v1.2.0): posiciones/exclusiones (resultados discretos) con igualdad exacta; costes totales (sumas de punto flotante) con tolerancia numérica. Sin ninguna fuente de aleatoriedad en el algoritmo -- ni semillas, ni muestreo, ni modelo entrenado | Compatible, sin superficie nueva de no-determinismo |
| IX. Datos derivados: se generan, no se leen | El artefacto final (`ArtefactoDigitacion`) es un dato derivado producido por un script versionado; se verifica por invariantes (cantidad de grabaciones, exclusiones con motivo, fracción de coincidencia con su denominador), nunca leyendo el JSON completo a mano. Las cifras de research.md (afinación, rango de trastes, estiramiento real) se midieron con scripts sobre datos reales, nunca transcritas a mano | Compatible |
| X. Tamaño de slice | Gate de `/speckit-tasks`, no de este plan | Diferido a tasks |

**Nota de gobernanza (Principios VI/VII)**: Principio VI no tiene
ninguna decisión nueva que cerrar para el hito 3 -- reutiliza tal cual
la reserva ya cerrada del hito 2 (spec.md, Assumption "Reutilización
del conjunto medible"), verificado con evidencia (research.md #4)
sobre las 288 medibles exclusivamente. Principio VII (métrica y
presupuesto del hito 3) sigue sin poder cerrarse: su propio criterio de
cierre es la primera medición real de User Story 3, que todavía no
ocurrió -- no se rellena por adelantado (mismo criterio que la
constitución ya aplicó dos veces, hito 1 y hito 2).

Sin violaciones que requieran `Complexity Tracking`.

**Re-chequeo post-Phase 1**: `data-model.md` y `contracts/digitacion.md`
confirman que ningún tipo nuevo duplica un contrato ya cerrado --
`Posicion`/`Instante`/`Digitacion` son nuevos porque el dominio es
distinto (posiciones físicas de mástil, no notas ni stems de audio),
pero siguen el mismo patrón de diseño ya establecido: `frozen=True`,
unión etiquetada para resultados con exclusión, `verdaderos_positivos`-
style de conteos expuestos para agregar sin recalcular, mismo mecanismo
de escritura atómica. La tabla de arriba sigue siendo válida sin
cambios -- ningún hallazgo de Phase 0/1 introdujo una dependencia
nueva, una fuente de datos nueva, ni una fuente de no-determinismo
nueva.

## Project Structure

### Documentation (this feature)

```text
specs/007-digitacion-restriccion-mano/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── digitacion.md    # Phase 1 output (/speckit-plan command)
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/guitar_tabs_analysis/
├── ingestion/
│   ├── slakh2100.py                 # hito 1, sin cambios
│   └── guitarset.py                 # EXTENDIDO -- nueva
│                                      # leer_posiciones_reales(), envuelve
│                                      # track.notes (por cuerda, research.md
│                                      # #5) -- leer_grabacion() del hito 2
│                                      # NO se toca, sigue usando notes_all
├── transcripcion/                    # hito 2, sin cambios
├── analytics/
│   ├── metrica_separacion.py        # hito 1, sin cambios
│   ├── metrica_deteccion_notas.py   # hito 2, sin cambios
│   └── metrica_digitacion.py        # NUEVO -- Posicion, Instante,
│                                      # Digitacion, ModeloCoste,
│                                      # InstanteExcluido (tipos de
│                                      # dominio); generar_candidatas()
│                                      # (User Story 1, research.md #9);
│                                      # asignar_instante() (User Story 1,
│                                      # research.md #6/#7/#8);
│                                      # asignar_secuencia() (User Story 2,
│                                      # la programación dinámica,
│                                      # research.md #1/#13);
│                                      # evaluar_coincidencia()/
│                                      # agregar_conjunto() (User Story 3) --
│                                      # todo pure computation, sin I/O,
│                                      # mismo patrón que
│                                      # metrica_deteccion_notas. Sin capa
│                                      # productora aparte (a diferencia de
│                                      # transcripcion/ en el hito 2):
│                                      # ningún modelo externo que envolver
├── medicion/                         # hito 1, sin cambios
├── deteccion/                        # hito 2, sin cambios
└── digitacion/                       # paquete NUEVO -- orquestador,
                                       # excluido a propósito del contrato
                                       # layers (mismo criterio que
                                       # deteccion/medicion, research.md
                                       # #11 del hito 2)
    ├── __init__.py
    └── orquestador.py                # ejecutar_digitacion(); reutiliza
                                       # deteccion.orquestador.construir_lista_grabaciones
                                       # tal cual (Principio VI, sin
                                       # segunda partición); ArtefactoDigitacion;
                                       # fallo de lectura por grabación es
                                       # exclusión terminal, mismo patrón
                                       # que el hito 2 (no aborta la corrida)
```

**Structure Decision**: proyecto único, sin capa productora nueva
(`digitacion.asignador` NO existe como paquete separado) -- toda la
lógica de asignación y de coste vive en `analytics.metrica_digitacion`
porque, a diferencia de `transcripcion` en el hito 2, no hay ningún
modelo/subproceso externo que aislar: es un algoritmo autocontenido
sobre tipos ya declarados, exactamente el mismo tipo de "pure
computation" que ya vive en `analytics` para las otras dos features de
métrica. El único paquete nuevo es el orquestador (`digitacion/`), que
ata `ingestion.guitarset` (notas + posición real) con
`analytics.metrica_digitacion` (asignación + medición), mismo rol
relativo que `deteccion/` cumple para el hito 2.
