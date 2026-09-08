# Research: Detección de notas sobre guitarra limpia

## 1. Modelo preentrenado: Basic Pitch (Spotify)

**Decision**: `basic-pitch` (Spotify, paquete `basic-pitch` en PyPI),
instalado con el extra `[onnx]`.

**Rationale, verificado no supuesto**: es el único candidato investigado
con una licencia única y sin ambigüedad cubriendo TANTO el código COMO
los pesos preentrenados -- **Apache License 2.0**, verificada
directamente contra el archivo `LICENSE` real del repositorio
(`github.com/spotify/basic-pitch`, copyright Spotify AB) y contra su
`README.md`, que no distingue ninguna licencia separada para los pesos
(`basic_pitch/saved_models/icassp_2022/`). Nunca aparece la asimetría
código/pesos que sí existe en Demucs (Feature 003,
`docs/ATRIBUCIONES.md`).

Produce directamente lo que FR-001 necesita: `predict()` devuelve una
lista de eventos de nota `(start_time_s, end_time_s, pitch_midi,
velocity, pitch_bend)` -- polifónico, con tono e inicio, verificado
contra `basic_pitch/inference.py` (`save_note_events()`). No es
específico de guitarra, pero tampoco lo era Demucs para separación en el
hito 1 (Feature 003) -- la especificidad de guitarra es preferible, no
obligatoria.

**Alternatives considered**:

- **Omnizart** (`Music-and-Culture-Technology-Lab/omnizart`, código MIT
  verificado) -- descartado en dos ejes: (a) sus checkpoints se
  descargan aparte (`omnizart download-checkpoints`) y no llevan ninguna
  licencia declarada en ningún lado del repositorio -- inadmisible por
  Principio IV sin importar lo demás; (b) pese a una búsqueda inicial
  sugerente, su propia tabla de aplicaciones soportadas no incluye
  guitarra -- la transcripción de guitarra pertenece a un paper de
  investigación separado (arXiv 2402.15258) sin código ni modelo
  publicados ("disponible por pedido a los autores"), también
  inadmisible por falta de licencia verificable.
- **MT3** (`magenta/mt3`, código Apache-2.0 verificado) -- descartado:
  los checkpoints se alojan aparte (Google Cloud Storage) y su licencia
  no se verificó de forma independiente (se dejó de investigar en cuanto
  Basic Pitch mostró una historia de licencia limpia y completa) --
  además, el runtime de referencia es T5X/JAX orientado a Colab/GPU, más
  pesado que el patrón CPU-only que este proyecto ya estableció con
  Demucs. Si se reconsiderara MT3 en el futuro, la licencia de sus
  checkpoints sigue sin verificar.
- **CREPE** (`marl/crepe`, código MIT) -- descartado por forma, no por
  licencia: es un rastreador de tono (F0) monofónico puro, sin detección
  de inicio ni de polifonía -- no puede producir lo que FR-001 exige
  (notas discretas con inicio) ni distinguir acordes, que esta feature
  necesita medir por separado (FR-006).

## 2. Backend de inferencia: `onnx`, nunca `tensorflow`

**Decision**: instalar `basic-pitch[onnx]` explícitamente, sin el extra
`[tf]`, y confirmar en `/implement` que `onnxruntime` queda como único
backend disponible.

**Rationale, verificado no supuesto**: el `pyproject.toml` real de
`basic-pitch` NO incluye `tensorflow` en sus dependencias base -- vive
solo bajo el extra `tf`. Pero `basic_pitch/__init__.py` elige el backend
por prioridad en tiempo de import: TensorFlow primero si está presente,
luego CoreML, luego TFLite, y ONNX al final
(`if TF_PRESENT: ... elif CT_PRESENT: ... elif TFLITE_PRESENT: ... elif
ONNX_PRESENT: ...`). Si el extra `[tf]` se instalara (aunque sea
transitivamente por otra dependencia), `basic-pitch` preferiría
TensorFlow en silencio. Instalar únicamente `[onnx]` garantiza que
`ONNX_PRESENT` sea la única opción verdadera, y mantiene el mismo
espíritu que la Feature 003 ya estableció para Demucs: CPU-only, sin
arrastrar un framework de ML más pesado del necesario (research.md #7 de
003, índice `pytorch-cpu`). `onnxruntime` en sí es MIT (verificado
contra `LICENSE` de `microsoft/onnxruntime`).

**Alternatives considered**: dejar el backend por defecto (TensorFlow) --
descartado porque agrega una dependencia mucho más pesada que no aporta
nada sobre ONNX para este caso de uso (inferencia CPU, sin
entrenamiento), y porque el propio código de `basic-pitch` la prioriza
en silencio si está presente -- un riesgo de regresión invisible si
cualquier otra dependencia futura arrastrara `tensorflow` de forma
transitiva.

## 3. Tolerancia de tono y ventana de inicio: los defaults de `mir_eval`, no inventados

**Decision**: tolerancia de tono `50.0` cents, ventana de inicio `0.05`
segundos (50 ms) -- los valores por defecto de
`mir_eval.transcription.precision_recall_f1_overlap`
(`onset_tolerance=0.05`, `pitch_tolerance=50.0`).

**Rationale, verificado no supuesto**: confirmado directamente contra el
código fuente real de `mir_eval/transcription.py`
(`github.com/craffel/mir_eval`, licencia MIT verificada). El docstring
del propio módulo atribuye estos valores al estándar **MIREX Note
Tracking (task 2)**: "a returned note is assumed correct if its onset is
within ±50ms of a reference note and its F0 is within ± quarter tone... "
-- exactamente la "convención establecida en transcripción musical" que
`spec.md` (FR-003) pide citar, no inventar.

## 4. Duración ignorada: `offset_ratio=None` explícito

**Decision**: invocar la función de emparejamiento de `mir_eval` con
`offset_ratio=None`.

**Rationale, verificado no supuesto**: el default real de
`precision_recall_f1_overlap` es `offset_ratio=0.2` (20% de superposición
de duración exigida) -- **no** ignora la duración por defecto. El propio
docstring documenta que pasar `offset_ratio=None` la ignora por completo
("If `offset_ratio` is set to `None`, offsets are ignored in the
evaluation"). FR-004 exige ignorar la duración explícitamente, así que
esta feature diverge a propósito del default de la biblioteca, no lo
hereda por accidente -- se documenta como una decisión explícita, no
como un descuido.

## 5. Emparejamiento óptimo y conversión MIDI↔Hz: reusar `mir_eval`, no reimplementar

**Decision**: `mir_eval` (MIT) se agrega como dependencia directa y se
usa para el emparejamiento (FR-005) y la conversión de tono (`pitch_midi`
de Basic Pitch → Hz que espera `mir_eval`), en vez de reimplementar un
algoritmo de asignación óptima o una fórmula de conversión propios.

**Rationale, verificado no supuesto**: `mir_eval.transcription` ya
resuelve exactamente el problema de FR-005 (ambigüedad de a qué nota de
referencia se acredita una estimada) con una asignación óptima de grafo
bipartito -- misma familia de técnica que la Feature 002 del hito 1 ya
usó (`scipy.optimize.linear_sum_assignment`) para el problema análogo de
emparejar estimaciones de guitarra contra referencias, verificado en el
código fuente real de `mir_eval`, no en documentación de segunda mano.
`mir_eval.util.midi_to_hz`/`hz_to_midi` (fórmula estándar de temperamento
igual, `440 * 2**((midi-69)/12)`) cubren la conversión sin agregar
`librosa` como dependencia directa del propio proyecto (aunque
`basic-pitch` sí depende de `librosa` de forma transitiva, para su
propio pipeline interno).

**Alternatives considered**: reimplementar el emparejamiento con
`scipy.optimize.linear_sum_assignment` directamente (ya es una
dependencia del proyecto desde la Feature 002) -- descartado porque
`mir_eval` ya expone la función completa (matching + tolerancia +
offset-agnóstico) con la semántica exacta que FR-003/004/005 piden, cuya
implementación además ES la referencia de la industria que `spec.md`
pide citar -- reimplementarla en paralelo duplicaría lógica ya probada
sin ninguna ganancia real, y arriesgaría una sutil divergencia de
comportamiento respecto de la convención citada.

## 6. Fuente de audio de GuitarSet: `audio_mic`, no `audio_mix`

**Decision**: la propiedad `audio_mic` del `Track` de GuitarSet (via
`mirdata`) -- la grabación real de un micrófono de condensador Neumann
U-87 -- no `audio_mix`.

**Rationale, verificado no supuesto**: GuitarSet distribuye cuatro
señales de audio por grabación (verificado contra
`mirdata/datasets/guitarset.py` y el registro real de Zenodo, DOI
`10.5281/zenodo.3371780`): `audio_mic` (grabación real de micrófono,
mono), `audio_mix` (mezcla mono, pero **sintetizada** por downmix de las
seis señales de pastilla hexafónica), `audio_hex` (seis canales, una
pastilla por cuerda) y `audio_hex_cln` (hexafónico con bleeding
removido). `spec.md` (Assumptions) pide "la que corresponde a audio de
guitarra sola tal como llegaría de una grabación real, sin acceso a
señales por-cuerda que un sistema real no tendría" -- `audio_mic` es la
única opción que es una grabación acústica genuina; `audio_mix`, pese a
ser mono, sigue siendo una construcción sintética derivada de señales
por-cuerda que un sistema real no tendría disponibles.

## 7. Carga del dataset: `mirdata`, no parseo manual de JAMS

**Decision**: `mirdata` (BSD-3-Clause, verificado contra `LICENSE` real
del repositorio `mir-dataset-loaders/mirdata`) para cargar audio y
anotaciones de GuitarSet, en vez de parsear los archivos JAMS a mano.

**Rationale, verificado no supuesto**: el `Track` de `mirdata` para
GuitarSet ya expone `notes_all` -- un `NoteData` agregado de las seis
cuerdas con `intervals` (`[inicio, fin]` en segundos) y `values` (tono
MIDI), verificado contra el código fuente real de
`mirdata/datasets/guitarset.py` -- exactamente la forma que
`analytics.metrica_deteccion_notas` necesita como "notas de referencia"
(data-model.md), sin reimplementar el parseo del formato JAMS (namespaces
`note_midi`/`pitch_contour`) a mano. `mirdata` está mantenido
activamente (último cambio verificado: 2026-07-14).

**Alternatives considered**: parsear JAMS directamente con el paquete
`jams` -- descartado porque `mirdata` ya hace ese trabajo y además
verifica la integridad del dataset (checksums) como parte de su propio
contrato, una capa de confianza adicional sin costo de implementación
extra.

## 8. Clasificación de polifonía: solape de intervalos, generalizada a notas estimadas sin pareja

**Decision**: dos notas de referencia se consideran simultáneas si sus
intervalos `[inicio, fin]` se superponen en cualquier medida (solape
parcial cuenta). Una nota de referencia es monofónica si ningún otro
intervalo de referencia la solapa, polifónica si al menos uno lo hace.
Esta misma regla se generaliza a **cualquier** nota estimada, sea que
haya acertado o no (FR-007 exige el desglose de precisión también, no
solo exhaustividad): se evalúa cuántos intervalos de referencia solapan
el instante de inicio de la nota estimada -- 0 o 1 clasifica como
monofónica (caso degenerado incluido: una nota inventada durante un
silencio real no tiene ninguna referencia con la que ser polifónica), 2
o más como polifónica.

**Rationale**: FR-006 fija la clasificación solo para notas de
referencia explícitamente, dejando abierto (a propósito, ver `spec.md`
Assumptions "Simultaneidad para clasificar polifonía") el criterio
exacto de solape y, por construcción, el caso de una nota estimada sin
ninguna referencia que la respalde. Generalizar la misma regla de solape
(evaluada siempre contra la referencia, nunca contra lo que el sistema
detectó) es la única forma de calcular precisión por subconjunto
(FR-007) sin violar FR-006 ("nunca a partir de las notas que el propio
sistema estimó") -- la fuente de la clasificación sigue siendo
exclusivamente la anotación de referencia, evaluada en un instante
distinto según el caso.

**Alternatives considered**: dejar las notas estimadas sin pareja fuera
de cualquier bucket de polifonía (un tercer grupo "sin clasificar") --
descartado porque FR-007 exige la cifra de precisión completa en ambos
subconjuntos (mono y poli), y un tercer grupo no pedido fragmentaría el
reporte sin necesidad -- la generalización de arriba clasifica siempre,
sin dejar ningún caso sin resolver.

## 9. Cálculo por subconjunto: partir el conjunto de notas antes de evaluar

**Decision**: antes de invocar `mir_eval.transcription`, el conjunto de
notas de referencia y el de notas estimadas de una grabación se separan
en dos subconjuntos (monofónico/polifónico, según #8), y se invoca la
evaluación de `mir_eval` **una vez por subconjunto**, de forma
independiente -- nunca calculando el emparejamiento global una sola vez
y dividiendo el resultado después.

**Rationale**: `mir_eval.transcription.precision_recall_f1_overlap`
calcula precisión/exhaustividad/balance agregados sobre el conjunto que
recibe, sin exponer a qué subconjunto pertenece cada coincidencia
individual en su valor de retorno -- partir la entrada es más simple y
más verificable que extraer índices de emparejamiento internos de la
biblioteca (que no son parte de su contrato público estable).

## 10. Fallo de inferencia sobre una grabación individual: exclusión terminal

**Decision**: si el modelo falla al procesar una grabación (FR-012,
Clarifications de `spec.md`), se captura como una excepción propia y esa
grabación queda excluida con un motivo explícito -- la medición del
resto del conjunto continúa.

**Rationale**: mismo patrón, ya validado dos veces en este proyecto, que
un fallo duro por unidad de trabajo se convierte en una exclusión
terminal sin abortar la corrida completa (Feature 003, research.md #5,
`SeparacionFallidaError`; Feature 004, FR-006, motivo
`"fallo_procesamiento"`). Con ~360 grabaciones en GuitarSet, abortar todo
por una sola problemática descartaría el resto del cómputo ya válido --
el mismo argumento que motivó el patrón la primera vez.

## 11. Arquitectura: nueva capa `transcripcion`, nuevo orquestador `deteccion`

**Decision**: cuatro módulos nuevos, seleccionados para mirror exacto de
la arquitectura de 4 capas que el hito 1 ya estableció y validó:

- `ingestion/guitarset.py` -- lee una grabación y sus notas de
  referencia via `mirdata` (paralelo a `ingestion/slakh2100.py`).
- `transcripcion/` (capa nueva, paralela a `separacion/`) --
  `transcripcion/transcriptor.py` (protocolo, paralelo a
  `separacion/separador.py`) y
  `transcripcion/basic_pitch_transcriptor.py` (implementación real,
  paralelo a `separacion/demucs_separador.py`) -- único módulo que
  importa `basic_pitch`.
- `analytics/metrica_deteccion_notas.py` -- acierto, emparejamiento,
  clasificación de polifonía, agregación por subconjunto (paralelo a
  `analytics/metrica_separacion.py`).
- `deteccion/orquestador.py` (paquete nuevo, paralelo a `medicion/`) --
  agrega sobre un conjunto de grabaciones, maneja exclusiones (#10) --
  importa de las tres capas anteriores a la vez, así que se **excluye a
  propósito** del contrato `layers` de import-linter, mismo criterio que
  `medicion` (Feature 004, research.md #6).

**Rationale**: mismo argumento estructural que motivó la arquitectura de
4 capas del hito 1 -- separar "leer datos" (`ingestion`), "correr el
modelo" (`transcripcion`), "medir" (`analytics`) y "orquestar" (paquete
excluido del contrato) evita que una sola capa mezcle responsabilidades
que ya se probaron por separado exitosamente. `transcripcion` puede
importar de `analytics` e `ingestion` (nunca al revés) -- mismo orden
que `separacion → analytics → ingestion` ya establece; se agrega
`transcripcion` a la lista `layers` de `pyproject.toml`, mismo
tratamiento que cuando se agregó `separacion` (Feature 003, research.md
#8).

**Alternatives considered**: reusar el paquete `medicion` existente para
la orquestación de esta feature también -- descartado porque `medicion`
ya tiene un significado específico y cerrado (orquestación del hito 1
sobre Slakh2100, por tema) -- reusarlo para un flujo distinto (GuitarSet,
por grabación, notas en vez de SI-SDR) generaría confusión de dominio sin
ahorrar nada real.

## 12. Presupuesto de cómputo: medido en `/implement`, no estimado aquí

**Decision**: el tiempo real de inferencia de Basic Pitch sobre una
grabación de GuitarSet no se estima en este documento -- se mide durante
`/speckit-implement`, siguiendo la misma disciplina "medido, no estimado"
que la Feature 003 ya estableció (research.md #9 de 003).

**Rationale**: las grabaciones de GuitarSet son considerablemente más
cortas (~30 s, verificado contra `mirdata`) que un tema completo de
Slakh2100 (~240 s) -- es razonable esperar que el presupuesto de tiempo
total sobre las 360 grabaciones sea manejable en una sola sesión, pero
esa expectativa no reemplaza una medición real, exactamente el motivo
por el que la Feature 003 midió en vez de estimar.

## 13. Atribuciones: se extiende `docs/ATRIBUCIONES.md`, no un archivo nuevo

**Decision**: la entrada de licencia de Basic Pitch, GuitarSet, `mir_eval`
y `mirdata` se agrega como una nueva sección de `docs/ATRIBUCIONES.md`
(ya existente desde la Feature 003 para Demucs), no un archivo separado.

**Rationale**: mismo archivo, mismo propósito declarado en su propio
comentario de cabecera ("para cada componente de terceros cuyo uso no es
obvio por sí mismo... Principio IV") -- Basic Pitch aporta una entrada
más simple que la de Demucs (sin asimetría código/pesos que documentar),
pero el mismo archivo es el lugar correcto.
