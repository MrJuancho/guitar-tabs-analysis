# Implementation Plan: Separación de guitarra con modelo preentrenado

**Branch**: `003-separacion-modelo-preentrenado` | **Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-separacion-modelo-preentrenado/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Dada la mezcla de un tema (`PistaAudio` de `ingestion.slakh2100`), producir
la colección de `Estimacion` (de `analytics.metrica_separacion`) de
guitarra usando Demucs `htdemucs_6s` — la única variante de Demucs con una
fuente `"guitar"` propia (research.md #1) —, verificando (no asumiendo)
la frecuencia de muestreo y el número de canales que el modelo espera
contra los del conjunto, declarando cualquier transformación aplicada
(FR-005/006/007), y devolviendo una colección vacía, nunca una estimación
sintética, cuando el modelo no produce ninguna salida de guitarra
(FR-009). Un fallo real del modelo se propaga como
`SeparacionFallidaError` con causa encadenada, sin reintento (FR-014,
cerrado en `/speckit-clarify`). El modelo, su firma y el checksum de sus
pesos (verificado automáticamente por `torch.hub`, no reimplementado) se
declaran de forma fija y consultable (FR-002), con la asimetría de
licencias (código MIT, pesos con uso restringido) documentada en
`docs/ATRIBUCIONES.md` (FR-003/004). Detalle completo de cada decisión en
[research.md](./research.md).

## Technical Context

**Language/Version**: Python 3.12 (mismo `requires-python` que el resto del proyecto)

**Primary Dependencies**: `demucs` (**nueva**, PyPI, MIT — research.md #2), que arrastra `torch` (**nueva**, transitiva, instalada desde el índice CPU-only de PyTorch para evitar ~370 MB de runtimes de CUDA sin uso, research.md #7), `huggingface-hub`, `einops`, `julius`, `pyyaml`, `safetensors`, `sphn`, `tqdm`. Reutiliza `PistaAudio` de `guitar_tabs_analysis.ingestion.slakh2100` y `Estimacion` de `guitar_tabs_analysis.analytics.metrica_separacion` (research.md #8 — nueva capa `separacion` por encima de ambas)

**Storage**: N/A para el resultado (en memoria, igual que 002). Los pesos del modelo se cachean fuera del repositorio, en la ubicación estándar de `torch.hub` (`~/.cache/torch/hub/checkpoints/` por defecto) — nunca versionados (FR-003)

**Testing**: `pytest` + `hypothesis`. Los tests de la lógica de orquestación (`separar_guitarra`) usan un `Separador` falso (protocolo, data-model.md) y no importan `torch`/`demucs`, corriendo en milisegundos. Un único test de integración carga `htdemucs_6s` real, marcado con un marcador nuevo de pytest (`modelo_real`, a sumar a `markers` en `pyproject.toml`), y se salta (no falla) si no hay red o la carga del modelo falla (research.md #7) — nunca forma parte de `just gauntlet`, solo de una invocación explícita o de `just gauntlet-full`/CI

**Target Platform**: Linux (WSL/Ubuntu, entorno de desarrollo del proyecto), CPU-only por diseño — `device="cpu"` fijo, sin ninguna ruta que intente usar GPU (Assumptions de spec.md: "sin GPU declarada")

**Project Type**: Single project — librería interna, capa nueva `separacion` (ver Project Structure)

**Performance Goals**: Ninguno declarado por el spec sobre throughput de inferencia (FR-012 prohíbe explícitamente que esta feature evalúe umbrales). Restricción operativa real: el test que sí carga el modelo real opera sobre un clip de 1-2 segundos, no un tema completo de varios minutos (SC-006) — una corrida sobre el conjunto completo de cientos de temas es una operación deliberada y separada del ciclo de test-y-verificación, no medida ni acotada por este plan

**Constraints**: `device="cpu"` fijo (sin GPU); ninguna transformación de amplitud (solo remuestreo/canales, ambos declarados — FR-005/006/007); tolerancia numérica para determinismo entre corridas de inferencia (FR-015, research.md #6), nunca igualdad bit a bit; un fallo real del modelo nunca se reintenta automáticamente ni se silencia (FR-014)

**Scale/Scope**: Opera sobre un tema a la vez (`separar_guitarra(tema_id, mezcla, separador)`); orquestar la separación de un conjunto completo de temas (análogo a `agregar_conjunto` de la Feature 002) queda fuera de esta feature — el spec la define en términos de "la mezcla de un tema", no de un conjunto, y ninguna FR pide una función de agregación aquí

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Aplica a esta feature | Estado |
|---|---|---|
| I. Hito 1 es línea base medida | Esta feature ES el separador que produce el stem que Feature 002 mide — completa la otra mitad del criterio de terminado del hito 1 (FR-001, FR-011: usa el modelo preentrenado sin entrenar ni afinar nada) | Compatible, avanza directamente el criterio de terminado |
| II. Caminos descartados con razón | `htdemucs` (4 fuentes) y otros separadores sin fuente de guitarra propia, descartados con su razón (research.md #1) | Compatible |
| III. La guitarra no es un stem estándar | `htdemucs_6s` es, hasta donde se verificó, la única variante pública con guitarra como fuente propia — su propio README documenta calidad limitada ("bleeding y artefactos"), registrado aquí sin esconderlo (research.md #1) | Compatible, refuerza directamente este principio |
| IV. Fuentes de audio admisibles | Esta feature no introduce ninguna fuente de audio nueva (opera sobre `PistaAudio` ya cargado vía Feature 001); sí introduce una categoría nueva — pesos de modelo — que el Principio IV no contempla. Se resuelve en el spec (FR-003/004), no se asume cubierta por la regla de CC BY | Requiere declaración propia (FR-003/004), no una excepción a IV — ver nota de gobernanza abajo |
| V. Qué cuenta como "la guitarra" | No aplica directamente — esta feature no clasifica pistas de referencia, solo produce estimaciones | N/A para esta feature |
| VI. Cuantitativa vs. cualitativa | FR-013: MUST NOT leer ni depender de la división del tema; opera igual sobre cualquier tema que reciba | Compatible, implementado directamente |
| VII. La métrica y su presupuesto | FR-012: MUST NOT calcular métrica ni evaluar umbral — responsabilidad exclusiva de Feature 002 | N/A para esta feature, por diseño |
| VIII. Determinismo | Se extiende (no se reabre) la opción (b) ya cerrada en Feature 002: tolerancia numérica para las muestras de audio resultantes de la inferencia (FR-015, research.md #6), verificado que el modelo carga en modo evaluación (sin fuente de aleatoriedad de `dropout`) | Extendido por este plan a un nuevo tipo de valor calculado; no contradice la decisión de 002 |
| IX. Datos derivados: se generan, no se leen | No aplica directamente — el resultado de esta feature no se persiste (Storage: N/A); la caché de pesos de `torch.hub` es un artefacto descargado, no derivado de datos propios del proyecto | N/A para esta feature |
| X. Tamaño de slice | Gate de `/speckit-tasks`, no de este plan | Diferido a tasks |

**Nota de gobernanza (Principio IV)**: este plan NO amplía ni reinterpreta
el Principio IV — la constitución exige CC BY 4.0 para *fuentes de audio*,
y los pesos de un modelo no son audio. La spec (FR-003/004) resuelve el
caso concreto de esta feature con una declaración explícita, siguiendo el
mismo espíritu ("una fuente sin licencia identificada no es admisible")
sin que la constitución tenga que decidir por adelantado una categoría que
no contemplaba. Se recomienda correr `/speckit-constitution` después de
implementar esta feature para que la constitución registre, con
contenido real, cómo se trata la licencia de pesos de modelo en general —
igual que hizo con SI-SDR y determinismo tras la Feature 002 — no antes,
seguiendo la misma disciplina de "no rellenar `ABIERTO` por adelantado".

Sin violaciones que requieran `Complexity Tracking` en el sentido estricto
de la tabla (ningún principio se contradice), pero se deja registrada la
complejidad real que esta feature introduce: `torch`/`demucs` es, con
diferencia, la dependencia más pesada del proyecto hasta ahora (~185 MB
incluso con la rueda CPU-only, research.md #7). Se acepta porque no hay
alternativa verificada más liviana con una fuente de guitarra explícita
(research.md #1) — no es una elección por conveniencia.

## Project Structure

### Documentation (this feature)

```text
specs/003-separacion-modelo-preentrenado/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── separacion.md    # Phase 1 output (/speckit-plan command)
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/guitar_tabs_analysis/
└── separacion/                    # capa NUEVA -- por encima de analytics (research.md #8)
    ├── __init__.py
    ├── separador.py                # ModeloDeclarado, TransformacionDeclarada,
    │                                 # ResultadoSeparacionTema, Separador (Protocol),
    │                                 # SeparacionFallidaError, separar_guitarra();
    │                                 # NO importa torch ni demucs
    └── demucs_separador.py          # DemucsSeparador (envuelve demucs.api.Separator),
                                      # MODELO_DECLARADO (constante); único módulo que
                                      # importa torch/demucs

docs/
└── ATRIBUCIONES.md                 # NUEVO -- licencia MIT del código de Demucs +
                                     # nota de uso restringido de los pesos (FR-003/004)

tests/
├── unit/
│   └── test_separador.py           # separar_guitarra() con Separador falso: verificación
│                                     # de formato siempre declarada, duplicación de canal,
│                                     # colapso de salida, ausencia total (FR-009),
│                                     # estimación silenciosa pasada intacta (FR-010),
│                                     # SeparacionFallidaError sin reintento (FR-014)
├── integration/
│   └── test_demucs_separador_integracion.py   # ÚNICO test que carga htdemucs_6s real
│                                                 # (@pytest.mark.modelo_real, se salta sin
│                                                 # red/pesos); determinismo real (FR-015)
└── fixtures/
    └── separador_fixture.py         # SeparadorFalso (implementa el protocolo) + variantes
                                       # de escenario; audio sintético de 1-2s para el test real
```

**Structure Decision**: Opción 1 (proyecto único), consistente con
Features 001/002. El módulo nuevo vive en una capa propia, `separacion`,
por encima de `analytics` en el contrato de `import-linter`
(`pyproject.toml::[tool.importlinter]`, edición a hacer en
`/speckit-tasks`: agregar `"guitar_tabs_analysis.separacion"` al inicio de
la lista `layers`) — necesita importar tanto de `analytics` (`Estimacion`)
como de `ingestion` (`PistaAudio`), y ninguna de esas dos capas necesita
importar de `separacion` en sentido contrario (research.md #8). La
separación entre `separador.py` (lógica pura, sin `torch`) y
`demucs_separador.py` (adaptador real) es lo que mantiene rápidos los
tests unitarios (research.md #7).

## Complexity Tracking

*Sin violaciones de principios — tabla omitida. La complejidad real
(dependencia pesada `torch`/`demucs`) queda justificada en la nota al
final de "Constitution Check" arriba, no como una violación sino como un
costo aceptado y registrado.*
