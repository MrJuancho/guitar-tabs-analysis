# Implementation Plan: Preferencia por posiciones bajas en el modelo de coste

**Branch**: `008-preferencia-posiciones-bajas` | **Date**: 2026-09-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-preferencia-posiciones-bajas/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Agrega un cuarto componente, independiente de los tres ya existentes,
al modelo de coste de digitación de la Feature 007: un coste
proporcional al traste de cada posición asignada (`altura(combo) = Σ
p.traste`), con su propio peso (`peso_altura_traste`). Es un peso de
NODO -- exactamente el mismo rol que `estiramiento` ya ocupa en la
recurrencia de programación dinámica (`asignar_secuencia`), verificado
contra el código real (research.md #1): no introduce ninguna
dependencia entre instantes no adyacentes, así que la subestructura
óptima que la Feature 007 ya estableció se preserva sin cambio de
forma, solo de valor. `peso_desplazamiento`/`peso_cruce_cuerdas`
permanecen en `1.0`, sin tocar (FR-002) -- un cambio por medición. El
valor final del peso nuevo se fija con una barrida de diez valores en
escala logarítmica (`0` a `100`, research.md #3), elegidos contra la
magnitud real medida del coste actual (traste medio asignado `6.08`,
coste actual por nota `≈7.77`) para que la curva cubra tanto "no cambia
nada" como "domina por completo", ejecutada en un solo proceso que lee
GuitarSet una única vez (research.md #4: la lectura, `8.88s`, domina
sobre la asignación+medición por punto, `1.63s`) -- `~25s` totales
proyectados para los diez puntos, contra las 288 grabaciones medibles
exclusivamente, nunca las 72 reservadas. La elección del valor final,
con la curva completa delante, es una decisión posterior (fuera de
alcance de este plan); esta feature mide y documenta, no cierra el
presupuesto vigente (`0.55`, sin cambio).

## Technical Context

**Language/Version**: Python 3.12 (sin cambio respecto de la Feature 007)

**Primary Dependencies**: Ninguna dependencia nueva de terceros. Esta
feature extiende `analytics.metrica_digitacion` y `digitacion.orquestador`
ya existentes (`mirdata`, `numpy`, ya dependencias desde el hito 2/3) --
no hay ningún modelo ni biblioteca nueva que evaluar (a diferencia de la
Feature 007, research.md #2 de esa feature, que sí tuvo que descartar
alternativas de terceros).

**Storage**: Un artefacto nuevo, `mediciones/barrido_altura_traste.json`
(`ResultadoBarrida`, data-model.md), con el mismo mecanismo de escritura
atómica (archivo temporal + `os.replace()`, verificado releyendo) que
`ArtefactoDigitacion` ya usa. No reemplaza ni modifica
`mediciones/digitacion_medibles.json` de la Feature 007.

**Testing**: `pytest` + `hypothesis`, mismo patrón que la Feature 007.
El coste de nodo extendido (`estiramiento + peso_altura_traste ·
altura`) se prueba con posiciones construidas a mano (US1, sin ningún
dataset real); la verificación de optimalidad (US2, FR-005) extiende el
mismo fixture de fuerza bruta de la Feature 007 con el término nuevo,
para varios valores de `peso_altura_traste` incluido `0`. La barrida
contra GuitarSet (US3) es una ejecución manual real, no un test --
mismo patrón que T024/T025 de la Feature 007.

**Target Platform**: Linux (WSL/Ubuntu), CPU-only. Sin cambio respecto
de la Feature 007 -- sigue siendo un algoritmo de optimización
combinatoria puro, sin GPU ni modelo externo.

**Project Type**: Single project. Extiende dos módulos ya existentes
(`analytics/metrica_digitacion.py`: campo nuevo en `ModeloCoste`, coste
de nodo extendido, dos tipos nuevos `PuntoBarrida`/`ResultadoBarrida`;
`digitacion/orquestador.py`: función nueva `ejecutar_barrida_peso_altura`
y su serialización) y agrega un punto de entrada de proceso nuevo
(`digitacion/cli_barrido.py`, mismo patrón que `digitacion/cli.py`) --
ningún paquete nuevo, ninguna capa nueva.

**Performance Goals**: Ninguno de throughput (Principio VII: el
presupuesto no se recalibra en esta feature). Costo de la barrida
medido con evidencia real, no proyectado a ciegas (research.md #4):
`8.88s` de lectura única de las 288 grabaciones + `1.63s` por cada uno
de los diez valores candidatos de `asignar_secuencia`+
`evaluar_coincidencia` sobre los datos ya leídos ≈ `25.2s` totales --
confirmado en `/speckit-implement` con tiempo de reloj real antes de
asumirlo cerrado, mismo criterio de esta sección para toda afirmación
cuantitativa (AGENTS.md). Sin cambio en la complejidad de
`asignar_secuencia` en sí (research.md #1: el coste de nodo extendido
sigue siendo `O(1)` por combinación candidata).

**Constraints**: `peso_desplazamiento`/`peso_cruce_cuerdas` MUST
permanecer en `1.0` en todas las mediciones de esta feature (FR-002).
El conjunto de valores candidatos de la barrida (`0, 0.01, 0.03, 0.1,
0.3, 1, 3, 10, 30, 100`, research.md #3) MUST declararse como constante
nombrada en código ANTES de correr cualquier medición (FR-007,
research.md #5) -- MUST NOT aceptarse como argumento de línea de
comandos, que invitaría a ajustar el rango después de ver un resultado
parcial. La barrida MUST leer cada grabación una única vez, nunca una
vez por valor candidato (research.md #4). El presupuesto vigente
(`0.55`) MUST permanecer sin cambio (FR-009).

**Scale/Scope**: Mismas 288 grabaciones medibles de GuitarSet que la
Feature 007 (semilla `20260908`, Principio VI, reutilizando
`deteccion.orquestador.construir_lista_grabaciones("medibles", ...)`
tal cual -- sin segunda partición), 49535 notas de referencia medibles
reales, diez valores candidatos del nuevo peso.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Aplica a esta feature | Estado |
|---|---|---|
| I. Hito 1 es línea base medida | N/A directo -- sin cambio respecto de la Feature 007 (no hay modelo que entrenar, es un componente de coste declarado explícitamente) | N/A para esta feature |
| II. Caminos descartados con razón | Alternativa de umbral (coste cero hasta un traste `N`, caro después) evaluada y no elegida por requerir un parámetro adicional a calibrar -- registrada, no descartada sin motivo (research.md #7, spec.md Assumptions) | Compatible |
| III. La guitarra no es un stem estándar | N/A -- sin separación de fuentes en esta feature | N/A para esta feature |
| IV. Fuentes de audio admisibles | GuitarSet ya admisible desde el hito 2 -- esta feature no reabre esa decisión ni agrega una fuente nueva | Compatible, sin fuente nueva |
| V. Qué cuenta como "la guitarra" | N/A -- GuitarSet es guitarra sola por construcción, sin selección de pista (FR-011 de la Feature 007, sin cambio) | N/A para esta feature |
| VI. Cuantitativa vs. cualitativa | Reutiliza tal cual la reserva ya cerrada (72/360, semilla `20260908`) -- FR-011 de esta feature. La barrida corre exclusivamente sobre las 288 medibles (research.md #3/#4), verificado con la misma función de partición ya existente, sin una segunda partición | Compatible, ninguna decisión nueva que cerrar |
| VII. La métrica y su presupuesto | El presupuesto (`0.55`) NO se recalibra en esta feature (FR-009) -- el umbral no se mueve para acomodar un resultado que todavía no existe. La barrida (User Story 3) mide y documenta la curva completa; la elección del valor final del peso, con esa evidencia delante, es una decisión posterior de `/speckit-constitution`, fuera de alcance de este plan (mismo patrón que el propio presupuesto de `fraccion_coincidencia` se fijó después de medir en la Feature 007) | Compatible -- disciplina de "medir antes de decidir" aplicada al parámetro nuevo, no solo al presupuesto |
| VIII. Determinismo | Comparación de coincidencia sigue siendo igualdad exacta (cuerda y traste, sin cambio). `coste_total`/costes de nodo son sumas de punto flotante, comparados con tolerancia numérica, mismo criterio que la Feature 007. Sin fuente nueva de no-determinismo -- el conjunto de valores candidatos es una constante fija, no un muestreo | Compatible |
| IX. Datos derivados: se generan, no se leen | `ResultadoBarrida` (`mediciones/barrido_altura_traste.json`) es un dato derivado producido por un script versionado (`digitacion.orquestador.ejecutar_barrida_peso_altura`), verificado por invariantes (diez puntos, el punto `peso_altura_traste == 0.0` coincide exactamente con `0.618633...`), nunca transcrito a mano. Las cifras de research.md (traste medio `6.08`, coste por nota `≈7.77`, tiempos de lectura/DP) se midieron con scripts sobre datos reales en esta sesión, no inventadas | Compatible |
| X. Tamaño de slice | Gate de `/speckit-tasks`, no de este plan | Diferido a tasks |

**Nota de gobernanza (Principio VII).** Esta feature no cierra ningún
`ABIERTO` de la constitución -- el presupuesto del hito 3 ya está
cerrado (`0.55`, v1.10.0) y permanece así. Si la barrida produce
evidencia de que algún valor de `peso_altura_traste` mejora
`fraccion_coincidencia` de forma sostenida, una sesión posterior podría
proponer fijar ese valor como el nuevo por defecto del modelo (una
enmienda a `research.md`/al código, no necesariamente a la
constitución, salvo que también se decida documentarlo ahí) -- decisión
explícitamente fuera de alcance de este plan (FR-007/FR-009).

Sin violaciones que requieran `Complexity Tracking`.

**Re-chequeo post-Phase 1**: `data-model.md` y
`contracts/digitacion.md` confirman que `PuntoBarrida`/`ResultadoBarrida`
son tipos nuevos porque miden algo que la Feature 007 no medía (una
curva sobre un parámetro, no una corrida única) -- no duplican
`ArtefactoDigitacion`/`ResultadoCoincidencia`, los reutilizan. El campo
nuevo de `ModeloCoste` y el coste de nodo extendido no rompen ningún
contrato ya cerrado de la Feature 007 (verificado línea por línea contra
`analytics/metrica_digitacion.py` real, research.md #1). La tabla de
arriba sigue siendo válida sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/008-preferencia-posiciones-bajas/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── digitacion.md    # Phase 1 output (/speckit-plan command)
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/guitar_tabs_analysis/
├── ingestion/
│   └── guitarset.py                 # hito 3 (Feature 007), sin cambios
│                                      # en esta feature -- la lectura de
│                                      # posición real ya existe
├── analytics/
│   └── metrica_digitacion.py        # EXTENDIDO --
│                                      # ModeloCoste.peso_altura_traste
│                                      # (FR-001/FR-002); coste de nodo
│                                      # extendido dentro de
│                                      # asignar_secuencia (research.md
│                                      # #1/#2); PuntoBarrida,
│                                      # ResultadoBarrida (tipos nuevos,
│                                      # User Story 3, data-model.md)
├── digitacion/                       # paquete de la Feature 007,
│                                      # extendido, sin capa nueva
│   ├── orquestador.py                # EXTENDIDO --
│                                      # ejecutar_barrida_peso_altura()
│                                      # (research.md #4: lee las 288
│                                      # grabaciones UNA vez, corre los
│                                      # diez valores candidatos sobre
│                                      # los datos ya leídos); serialización
│                                      # de ResultadoBarrida (mismo patrón
│                                      # que artefacto_a_dict)
│   ├── cli.py                         # sin cambios -- sigue siendo la
│                                      # CLI de una corrida con un solo
│                                      # modelo de coste
│   └── cli_barrido.py                 # NUEVO -- punto de entrada de
│                                      # proceso para la barrida; valores
│                                      # candidatos como constante
│                                      # nombrada en el módulo, nunca un
│                                      # argumento de CLI (research.md #5)
└── (el resto del árbol, hitos 1/2, sin cambios)
```

**Structure Decision**: proyecto único, sin paquete ni capa nueva --
esta feature extiende exactamente los dos módulos que la Feature 007 ya
declaró como dueños del modelo de coste y de la orquestación
(`analytics.metrica_digitacion`, `digitacion.orquestador`), agregando
solo un punto de entrada de proceso nuevo (`cli_barrido.py`) para la
medición de User Story 3 -- mismo criterio que la Feature 007 usó para
`digitacion.cli`: la lógica vive en `analytics`/`digitacion`, la CLI es
un cascarón delgado sobre ella.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Sin violaciones -- tabla vacía a propósito.
