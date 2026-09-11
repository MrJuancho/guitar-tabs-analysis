# Research: Detección de notas sobre guitarra limpia

## 1. Modelo preentrenado: Basic Pitch (Spotify)

**Decision**: `basic-pitch` (Spotify, paquete `basic-pitch` en PyPI).

**Corrección (sesión de `/speckit-implement`, T010-T015): "instalado con
el extra `[onnx]`" ya NO aplica.** Ver #15 más abajo -- `basic-pitch` se
instala sin ningún extra, en un entorno Python 3.10 aparte, donde
resuelve a backend TFLite. La elección del modelo en sí (Basic Pitch,
licencia Apache-2.0 sin asimetría) no cambia -- lo que cambió es CÓMO se
instala y CON QUÉ backend corre, no CUÁL modelo.

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

## 2. Backend de inferencia -- SUPERADO por #15: `tflite`, no `onnx`

**Este apartado queda como registro histórico de la decisión original de
`/speckit-plan`; #15 documenta la decisión real, verificada en
`/speckit-implement`, que lo reemplaza.**

**Decision original (`/plan`, incorrecta -- ver #15)**: instalar
`basic-pitch[onnx]` explícitamente, sin el extra `[tf]`, y confirmar en
`/implement` que `onnxruntime` queda como único backend disponible.

**Por qué era incorrecta, verificado en `/speckit-implement` (T002 de
`tasks.md`, sesión de T001-T009): `basic-pitch[onnx]` es irresoluble en
Python 3.12** -- la dependencia BASE de `basic-pitch` (fuera de
cualquier extra) incluye `tensorflow>=2.4.1,<2.15.1; python_version >=
'3.11'`, y esa franja de TensorFlow no publica rueda `cp312`. Reabrir
el modelo en Python 3.10 (research.md #15) tampoco salva la elección de
`onnx`: `onnxruntime` (`v1.24.3`, la única versión disponible al
verificar) tampoco publica rueda `cp310` -- verificado empíricamente
(`uv add "basic-pitch[onnx]"` sobre un proyecto Python 3.10 falla con
"doesn't have a source distribution or wheel for the current platform").
El backend real y único disponible en 3.10 es **TFLite**
(`tflite-runtime`), que la dependencia base de `basic-pitch` SÍ instala
sin ningún extra cuando `python_version < '3.11'` -- verificado
importando `basic_pitch` en ese entorno y confirmando
`TFLITE_PRESENT=True`, `TF_PRESENT=ONNX_PRESENT=CT_PRESENT=False`.

**El argumento original de research.md #2 (nunca la CUDA/GPU-oriented
TensorFlow completa, un framework más liviano para CPU) sigue vigente,
solo que TFLite -- no ONNX -- es la opción que lo satisface en la única
versión de Python donde `basic-pitch` resuelve limpio.** TFLite es en sí
mismo un runtime liviano orientado a inferencia (no a entrenamiento),
consistente con el mismo espíritu que motivó evitar TensorFlow completo.

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

## 8. Clasificación de polifonía: solape de intervalos, generalizada a notas estimadas sin pareja -- ALCANCE CORREGIDO por #17

**Decision**: dos notas de referencia se consideran simultáneas si sus
intervalos `[inicio, fin]` se superponen en cualquier medida (solape
parcial cuenta). Una nota de referencia es monofónica si ningún otro
intervalo de referencia la solapa, polifónica si al menos uno lo hace.
Esta misma regla se generaliza a cualquier nota estimada que NO se
acredite contra ninguna referencia (FR-007 exige el desglose de
precisión también, no solo exhaustividad, y un falso positivo debe
contar en el denominador de algún subconjunto): se evalúa cuántos
intervalos de referencia solapan el instante de inicio de la nota
estimada -- 0 o 1 clasifica como monofónica (caso degenerado incluido:
una nota inventada durante un silencio real no tiene ninguna referencia
con la que ser polifónica), 2 o más como polifónica. **Corrección de
#17: esta regla NO aplica a una nota estimada que sí se acredita contra
una referencia** -- esa hereda la clasificación de la referencia con la
que empareja (FR-014). La redacción original de esta decisión (research
del `/speckit-plan` inicial) decía "cualquier nota estimada, sea que
haya acertado o no"; `data-model.md` ya decía correctamente "sin
pareja" desde el principio -- la implementación de `/speckit-implement`
siguió la redacción de aquí, no la de `data-model.md`, y ahí nació el
defecto que #17 diagnostica y corrige.

**Rationale**: FR-006 fija la clasificación solo para notas de
referencia explícitamente, dejando abierto (a propósito, ver `spec.md`
Assumptions "Simultaneidad para clasificar polifonía") el criterio
exacto de solape y, por construcción, el caso de una nota estimada sin
ninguna referencia que la respalde. Generalizar la misma regla de solape
(evaluada siempre contra la referencia, nunca contra lo que el sistema
detectó) es la única forma de calcular precisión por subconjunto
(FR-007) sin violar FR-006 ("nunca a partir de las notas que el propio
sistema estimó") para el caso de un falso positivo -- la fuente de la
clasificación sigue siendo exclusivamente la anotación de referencia,
evaluada en un instante distinto según el caso. Para una nota estimada
que SÍ empareja, en cambio, ya existe una referencia concreta de la cual
heredar (la que la acreditó) -- evaluarla de nuevo por su propio instante
es una segunda fuente de clasificación independiente de la primera, y
#17 muestra que ambas fuentes discrepan con frecuencia suficiente para
romper la aritmética de la agregación.

**Alternatives considered**: dejar las notas estimadas sin pareja fuera
de cualquier bucket de polifonía (un tercer grupo "sin clasificar") --
descartado porque FR-007 exige la cifra de precisión completa en ambos
subconjuntos (mono y poli), y un tercer grupo no pedido fragmentaría el
reporte sin necesidad -- la generalización de arriba clasifica siempre,
sin dejar ningún caso sin resolver.

## 9. Cálculo por subconjunto: partir el conjunto de notas antes de evaluar -- SUPERADO por #17

**Decision** (superada, ver #17): antes de invocar
`mir_eval.transcription`, el conjunto de notas de referencia y el de
notas estimadas de una grabación se separan en dos subconjuntos
(monofónico/polifónico, según #8), y se invoca la evaluación de
`mir_eval` **una vez por subconjunto**, de forma independiente -- nunca
calculando el emparejamiento global una sola vez y dividiendo el
resultado después.

**Rationale** (obsoleto desde #16): `mir_eval.transcription.precision_recall_f1_overlap`
calcula precisión/exhaustividad/balance agregados sobre el conjunto que
recibe, sin exponer a qué subconjunto pertenece cada coincidencia
individual en su valor de retorno -- partir la entrada parecía más
simple y más verificable que extraer índices de emparejamiento internos
de la biblioteca. Esta razón dejó de aplicar desde #16: `evaluar_subconjunto`
pasó a llamar `mir_eval.transcription.match_notes` **directamente**, que
SÍ devuelve los índices `(ref_idx, est_idx)` de cada par emparejado como
parte de su contrato público estable -- la premisa que motivaba partir
antes de emparejar ya no era cierta para el código real desde ese
momento, y #9 nunca se revisó a la luz de ese cambio hasta #17.

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

**Corrección (sesión de `/speckit-tasks`, antes de `/speckit-implement`):
`ExclusionDeteccion` y `ResultadoDeteccionGrabacion` NO se definen en
`deteccion/orquestador.py`.** La primera redacción de esta decisión (y el
diagrama de `plan.md#Project Structure` que la reflejaba) las situaba ahí
-- error detectado al escribir `contracts/deteccion.md`: la firma pública
de `analytics.metrica_deteccion_notas.agregar_conjunto` recibe
`list[ResultadoDeteccionGrabacion]` (que a su vez contiene
`ExclusionDeteccion | None`), y `analytics` no puede importar de
`deteccion` sin crear una dependencia circular -- `deteccion` es, por
diseño, el paquete que importa de las tres capas de abajo (`ingestion`,
`transcripcion`, `analytics`), nunca al revés. Ambos tipos se definen en
`analytics/metrica_deteccion_notas.py`; `deteccion/orquestador.py` los
importa desde ahí, igual que importa `NotaReferencia`/`NotaEstimada`.
`plan.md` y `data-model.md` se corrigieron para reflejar esto -- mismo
tipo de hallazgo que C1 de `/speckit-analyze` en la Feature 004 (una
decisión que vivía solo en un artefacto de diseño y contradecía otro).

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

## 14. Reserva de GuitarSet para el cierre del hito 2 (Principio VI, constitución v1.8.0)

**Decision**: 72 grabaciones (20% de las 360 de GuitarSet), seleccionadas
por muestreo aleatorio con semilla declarada `20260908` sobre los 360
identificadores de grabación ordenados -- reservadas como conjunto
intocable del hito 2, nunca medidas por esta feature durante su
desarrollo. Quedan 288 grabaciones (80%) disponibles para medir.

**Rationale**: la constitución v1.7.0 generalizó el Principio VI (antes
específico del split `test` de Slakh2100, hito 1) a que todo hito reserve
una porción de su conjunto de evaluación, usada una sola vez al cerrar
ese hito. Esta feature (la primera del hito 2) fija esa instancia. El
tamaño elegido -- el extremo superior del rango 15-20% considerado, no el
inferior -- responde a que GuitarSet es chico en términos absolutos (360)
comparado con Slakh2100 (1710): una fracción fija en el extremo bajo
(15% = 54 grabaciones) da una N pequeña para la confirmación de cierre.
El propósito generalizado del principio es confirmar que la cifra medida
no es sobreajuste al propio procedimiento de desarrollo -- no solo
protegerse de elegir el mejor de varios modelos candidatos (que no es el
caso de esta feature, un único modelo ya declarado por licencia en #1) --
una N mayor (72) da una confirmación más creíble sin sacrificar capacidad
real de medición, porque esta feature no entrena ni afina. La semilla
`20260908` sigue el mismo formato AAAAMMDD que `20260904` (submuestra del
hito 1, Feature 004) -- la fecha de la decisión, no un valor con ningún
significado adicional.

**Mecanismo -- corregido en `/speckit-implement` (T028, Fase 7): SIN
manifiesto persistido.** La decisión original de este apartado preveía
un archivo `tests/holdout/guitarset_reservado_hito2.json` protegido por
el hook `PreToolUse`. Se descarta a favor de algo más fuerte, pedido
explícito de esa sesión: **la reserva se deriva de la semilla en cada
invocación, nunca se lee de una lista escrita a mano ni cacheada en
disco**. `construir_lista_grabaciones(modo, root_dir, *,
tamano_reserva=72, semilla_reserva=20260908)`
(`deteccion/orquestador.py`) enumera los identificadores reales de
GuitarSet vía `mirdata`, ordenados, y calcula
`random.Random(semilla_reserva).sample(todos, tamano_reserva)` -- ese
mismo cálculo, con `modo="reservado"`, da las 72; con
`modo="medibles"`, da el complemento (288). Un manifiesto estático
tendría un defecto real: si alguien cambiara `semilla_reserva` en el
código, un archivo cacheado en disco NO cambiaría solo, y la partición
efectiva (la que el archivo describe) quedaría desincronizada de la que
el código dice usar -- exactamente el tipo de fuente-de-verdad-doble que
este proyecto evita en otros lados (p. ej. por qué `uv.lock` se verifica
contra `pyproject.toml` en vez de asumirse). Con cálculo en vivo, cambiar
la semilla cambia la partición completa de forma automática y visible en
el diff del propio código -- no hace falta ningún hook de protección de
archivo para esta reserva en particular (el hook de `tests/holdout/`
sigue existiendo para lo que ya protegía, esto no lo toca).

**Alternatives considered**: partir GuitarSet por intérprete (GuitarSet
distribuye grabaciones de 6 guitarristas, un criterio de partición común
en la literatura de transcripción para medir generalización entre
intérpretes) -- descartado para esta decisión porque el pedido explícito
de esta sesión fija el criterio de muestreo aleatorio con semilla, mismo
patrón que la submuestra del hito 1 (no un split por intérprete, que
mediría una pregunta distinta -- generalización entre guitarristas, no
sobreajuste al procedimiento de desarrollo). Queda registrado como
alternativa para una decisión futura si esa pregunta se vuelve relevante.

## 15. `basic-pitch` real: entorno Python 3.10 aparte, invocado por subproceso

**Decision**: un segundo proyecto `uv`, `envs/basic_pitch_py310/`, fijado
a Python 3.10 (`requires-python = "==3.10.*"`), con su propio
`pyproject.toml`/`uv.lock` versionados -- **nunca** se baja el
`requires-python` del proyecto principal (`>=3.12`). Dependencias de ese
proyecto, las tres verificadas necesarias, no solo `basic-pitch` solo:

- `basic-pitch` (sin ningún extra -- research.md #2 corregido: la base
  ya resuelve a TFLite en 3.10, sin extra que pedir).
- `numpy<2` -- **pin necesario, no cosmético**: `tflite-runtime==2.14.0`
  (que `basic-pitch` arrastra) es una extensión compilada contra la ABI
  C de NumPy 1.x; con NumPy 2.x (lo que resuelve por defecto sin este
  pin) falla en tiempo de ejecución con `AttributeError: _ARRAY_API not
  found` al construir el intérprete de TFLite -- verificado
  reproduciendo el error y confirmando que desaparece con el pin.
- `setuptools<81` -- **pin necesario, no cosmético**: `resampy`
  (dependencia transitiva de `basic-pitch` vía `librosa`) importa
  `pkg_resources` en tiempo de import: `setuptools>=81` lo eliminó por
  completo (no solo lo deprecó) -- verificado reproduciendo
  `ModuleNotFoundError: No module named 'pkg_resources'` con
  `setuptools==84.0.0` (el que resuelve sin pin) y confirmando que
  `setuptools==80.10.2` sí lo incluye (con warning de deprecación, no
  error).

**Verificado de punta a punta, no solo que resuelve**: un audio
sintético de 1s a 440 Hz, corrido a través de `basic_pitch.inference.predict()`
en este entorno exacto, produce un evento de nota con `pitch_midi=69`
(A4, la nota correcta) -- la cadena de dependencias no solo instala, la
inferencia real funciona.

**Comunicación por archivos, no por stdout**: el adaptador
(`transcripcion/basic_pitch_transcriptor.py`, entorno principal, Python
3.12) invoca un script (`envs/basic_pitch_py310/transcribir_subproceso.py`)
pasándole la ruta del audio y una ruta de salida para el JSON de notas --
nunca stdin/stdout para los datos. Razón, verificada empíricamente:
`basic_pitch`/sus dependencias emiten advertencias reales durante el
import y la inferencia (`WARNING:root:Coremltools is not installed...`,
`WARNING:root:onnxruntime is not installed...`, y el propio
`UserWarning` de `pkg_resources`) -- mezclarlas con la salida de datos en
stdout exigiría un protocolo de framing que un archivo de salida evita
por completo.

**Invocación directa del intérprete del venv, nunca `uv run` en tiempo
de llamada.** El adaptador ejecuta
`envs/basic_pitch_py310/.venv/bin/python transcribir_subproceso.py ...`
directamente -- no `uv run --project envs/basic_pitch_py310 ...`.
Razón: `uv run` sincroniza el entorno (y con él, su lock) implícitamente
antes de ejecutar, exactamente el mismo antipatrón que AGENTS.md ya
documenta para `uv.lock` del proyecto principal ("un chequeo de estado
va antes de cualquier comando que pueda repararlo") -- si el adaptador
usara `uv run`, un desincronizado real entre `pyproject.toml` y
`uv.lock` de ese entorno secundario se curaría en silencio en cada
invocación, y `just doctor` (más abajo) nunca lo detectaría. Invocar el
intérprete del venv ya materializado hace que un entorno desincronizado
falle con un error real (módulo ausente o versión equivocada) en vez de
autorepararse.

**`just doctor` verifica el entorno secundario, en el mismo orden que ya
usa para el principal** (chequeo de estado ANTES de cualquier `uv run`
que pueda sincronizar): primero `uv lock --check` dentro de
`envs/basic_pitch_py310/` (falla si el lock no corresponde al
`pyproject.toml` de ese proyecto, sin tocar el entorno), y solo después
`uv run --project envs/basic_pitch_py310 python -c "import basic_pitch"`
(que si `uv lock --check` ya pasó, no tiene nada que sincronizar en
silencio) para confirmar que el intérprete 3.10 existe y `basic_pitch`
importa ahí de verdad -- "un componente no verificado en el entorno real
es un componente que no existe" (AGENTS.md).

**Fallo cerrado en el script del subproceso.** El script escribe el JSON
de salida SOLO en el camino feliz; ante cualquier excepción, imprime el
detalle a stderr, sale con código distinto de cero, y **no** escribe (ni
deja a medio escribir) el archivo de salida -- una lista vacía de notas
es un resultado legítimo (silencio real, spec.md US2 AS3) y nunca puede
confundirse con un fallo. El adaptador trata como fallo real (envuelto en
`TranscripcionFallidaError`, nunca dejado crudo) cualquiera de: código de
salida distinto de cero, archivo de salida ausente, o JSON malformado --
nunca asume "sin notas" por defecto ante cualquiera de esos tres casos.

**Pesos ya incluidos en el paquete, sin descarga aparte** (confirmado
consistente con research.md #1): `predict()` resuelve su modelo por
defecto a un archivo `.tflite` dentro del propio paquete instalado
(`.../site-packages/basic_pitch/saved_models/icassp_2022/nmp.tflite`).

**Alternatives considered**: un proceso persistente (servidor local que
mantiene el modelo cargado entre invocaciones) -- descartado por ahora,
no por costo conocido sino por falta de evidencia: recargar el modelo
por grabación podría ser barato o caro sobre 288 grabaciones, y esa
optimización se mide antes de construirse (mismo principio "medido, no
estimado" de research.md #12), no se asume. Relajar `requires-python`
del proyecto principal a `>=3.10` para evitar un segundo entorno --
descartado explícitamente por esta sesión: el proyecto principal no baja
de 3.12.

## 16. `agregar_conjunto` no debe emparejar notas crudas pooleadas -- corrección de #9, con evidencia real de OOM

**Contexto real, no hipotético**: `just detectar medibles <root_dir>`
sobre las 288 grabaciones reales de GuitarSet fue matado por el kernel
(OOM, señal 9) dos veces, consumiendo del orden de 61 GB. Diagnóstico
completo en la sesión de `/speckit-implement` correspondiente, medido
antes de tocar código (AGENTS.md, "Regla: primero el test rojo... /
Una afirmación cuantitativa se verifica numéricamente").

**Lo que el diagnóstico DESCARTÓ, con medición, no solo lectura de
código**: instrumentar `leer_grabacion`+`BasicPitchTranscriptor.transcribir`
sobre 25 grabaciones reales, midiendo RSS del proceso padre después de
cada una, dio una curva CHATA (151 MB inicial, sube a ~220 MB en la
primera iteración por imports, se mantiene en 220-232 MB durante las 24
restantes) -- ninguna acumulación por grabación. Confirmado además
leyendo el código fuente real instalado de `mirdata` (`Dataset.track()`
construye un `Track` nuevo cada vez, sin cachear nada a nivel de
`Dataset`; `Track.audio_mic` es una `@property` común, no
`@cached_property`; `leer_grabacion` nunca la toca, solo usa
`audio_mic_path` -- un string -- y `notes_all`, anotaciones, no audio).
`ResultadoDeteccionGrabacion` nunca guardó la lectura completa, solo las
listas de notas ya extraídas (verificado, no solo diseñado así).

**La causa real, medida**: `agregar_conjunto` pooleaba las notas de
referencia y estimadas de las 288 grabaciones en dos listas únicas
(hasta ~57.600 notas de referencia) y llamaba
`analytics.metrica_deteccion_notas.evaluar_subconjunto` (research.md #9,
T009) **una sola vez** sobre ese pool -- para el subconjunto global, y
de nuevo para monofónico y polifónico. Adentro,
`mir_eval.transcription.match_notes` (research.md #5) construye
matrices densas N×M vía `np.subtract.outer` (distancias de onset, de
tono, y las máscaras booleanas resultantes) -- memoria **cuadrática** en
el tamaño del pool. Confirmado escalando `evaluar_subconjunto` con notas
sintéticas, midiendo `resource.getrusage().ru_maxrss`:

```
N_ref= 1000  N_est=  900   delta=   22.2 MB
N_ref= 3000  N_est= 2700   delta=  172.9 MB   (~8x por 3x más notas)
N_ref= 6000  N_est= 5400   delta=  581.5 MB   (~26x por 6x más notas)
N_ref=12000  N_est=10800   delta= 2320.9 MB   (~104x por 12x más notas)
```

Extrapolando la tendencia cuadrática a la escala real (~57.600 notas de
referencia pooleadas) da del orden de ~53 GB solo para la matriz global
-- consistente con los ~61 GB observados, sumando monofónico/polifónico.

**El defecto no es solo de memoria -- es de corrección de la métrica,
más grave.** Emparejar notas pooleadas de grabaciones distintas permite
que una nota de la grabación A se acredite contra una de la grabación B
si sus instantes de inicio relativos caen dentro de los 50 ms de
tolerancia -- coincidencia estructuralmente probable entre clips de
~30 s con onsets independientes, no un caso de laboratorio raro. Esos
aciertos son espurios: no dicen nada sobre si el modelo detectó bien esa
nota, solo que dos clips sin relación tuvieron un reloj relativo
parecido. Las cifras que el diseño pooled habría producido (si hubiera
tenido memoria suficiente para terminar) estaban infladas por este
efecto -- FR-013 de `spec.md` fija esto como requisito explícito de
corrección, no como optimización de rendimiento.

**Decision**: emparejar SIEMPRE dentro de una única grabación
(`evaluar_grabacion`, ya lo hacía correctamente desde T019 -- el defecto
estaba únicamente en `agregar_conjunto`), acumulando los **conteos** ya
resueltos (`verdaderos_positivos`, `num_notas_referencia`,
`num_notas_estimadas`) por grabación, y derivar precisión/exhaustividad/
balance de la SUMA de esos conteos entre grabaciones -- nunca de un
pool de notas crudas. `evaluar_subconjunto` (T009) se extiende para
exponer `verdaderos_positivos` en `ResultadoSubconjunto` -- antes
calculaba precisión/exhaustividad/balance con
`mir_eval.transcription.precision_recall_f1_overlap` (que descarta el
conteo de aciertos, solo devuelve las tres razones ya divididas más
`avg_overlap_ratio`, que este proyecto tampoco usa); ahora llama
`mir_eval.transcription.match_notes` directamente (research.md #5: sigue
siendo mir_eval quien resuelve el emparejamiento, no una reimplementación
propia) y deriva las tres razones con la misma fórmula exacta que
`precision_recall_f1_overlap` usa internamente
(`precision=TP/num_est`, `exhaustividad=TP/num_ref`,
`balance_f1=mir_eval.util.f_measure(precision, exhaustividad)` --
verificado línea por línea contra el código fuente real de
`precision_recall_f1_overlap`, mismo resultado exacto, ahora con el
conteo intermedio expuesto). `mir_eval.transcription.validate(...)` se
llama explícitamente antes de `match_notes` (antes la hacía
`precision_recall_f1_overlap` por dentro) para no perder la validación
de intervalos/formas que ya existía.

Con este diseño, cada llamada a `match_notes` opera sobre las notas de
UNA grabación (del orden de 100-500 notas de referencia, matrices de
~500×500 ≈ 2 MB) -- la memoria deja de escalar con el tamaño del
conjunto agregado, escala con el tamaño de la grabación más grande, que
research.md #9 ya fijó en un orden de magnitud manejable.

## 17. La partición mono/poli pierde verdaderos positivos -- corrección de #8/#9, con evidencia real sobre `mediciones/deteccion_medibles.json`

**Contexto real, no hipotético**: la primera corrida completa sobre las
288 grabaciones medibles dio `balance_f1` GLOBAL (0.7394) mayor que el
de AMBAS particiones (monofónico 0.6094, polifónico 0.5835) -- imposible
si las particiones cubren el conjunto sin solape ni resto, que es
justamente el caso: `num_notas_referencia` de mono (15280) + poli
(34258) suma exacto el global (49538), igual `num_notas_estimadas`
(22559 + 27965 = 50524). Solo `verdaderos_positivos` no suma: mono
(11529, derivado de `precision × num_notas_estimadas`, verificado
igual vía `exhaustividad × num_notas_referencia`) + poli (18153) = 29682,
contra 36995 del global -- una diferencia de 7313 (19.8% del total
global).

**Diagnóstico medido, no supuesto**: se reprodujo `evaluar_grabacion`
sobre las notas crudas de cada una de las 288 grabaciones que
`mediciones/deteccion_medibles.json` ya guarda en
`resultados_por_grabacion` (sin volver a transcribir), y además se
recalculó el emparejamiento GLOBAL de cada grabación explícitamente con
`mir_eval.transcription.match_notes` para inspeccionar cada par
`(ref_idx, est_idx)` uno por uno. De los 36995 pares emparejados en el
global, 7329 tienen `clasificar_polifonia_en_instante(ref.inicio_s, ...)
!= clasificar_polifonia_en_instante(est.inicio_s, ...)` -- prácticamente
el mismo orden de magnitud que la diferencia observada (7329 vs 7313; la
pequeña discrepancia es el efecto de segundo orden de que cada
subconjunto reempareja con un pool más chico, que a veces encuentra
pareja nueva para una nota huérfana). Confirma la causa con dos
mediciones independientes que coinciden.

**La causa real**: `_particionar_por_polifonia` (T019) clasificaba cada
nota ESTIMADA por su propio `inicio_s` contra la densidad de referencia
en ese instante (research.md #8, tal como estaba redactado antes de esta
sesión) -- **incluyendo** las que sí empataban con una referencia.
`mir_eval.transcription.match_notes` tolera hasta 50 ms de diferencia de
onset (research.md #3) entre una referencia y su estimada acreditada:
si la referencia cae en un instante con 2+ notas solapando (polifónica)
pero la estimada que la empareja tiene su propio onset unos milisegundos
antes o después, en un punto donde esa densidad ya no llega a 2
(monofónica), el par queda partido -- la referencia va al subconjunto
polifónico, la estimada al monofónico. Como además `evaluar_grabacion`
(research.md #9) volvía a invocar `match_notes` de forma independiente
dentro de cada subconjunto ya partido, ese acierto no tiene ninguna
oportunidad de recuperarse: la referencia y la estimada que en el global
formaban un par ya no están en la misma lista de candidatos en ningún
subconjunto. El resultado es un acierto real que existe en el global y
desaparece de ambos parciales -- mismo defecto que #16 (agrupar/clasificar
antes de emparejar en vez de después), aquí en su variante de
clasificación en lugar de pooling entre grabaciones.

**Decision**: `evaluar_grabacion` pasa a emparejar **una sola vez** por
grabación (la misma llamada que ya calculaba el resultado global,
reutilizada), y clasifica cada par `(ref_idx, est_idx)` devuelto por
`match_notes` con la clasificación de **la referencia de ese par**
(`clasificar_polifonia_en_instante(notas_referencia[ref_idx].inicio_s,
notas_referencia)`) -- la estimada emparejada HEREDA esa clasificación,
nunca se reevalúa por su propio instante. Cada nota de referencia sigue
clasificándose por su propio instante exactamente como antes (FR-006,
sin cambios: eso nunca fue el defecto, los conteos de referencia ya
sumaban exacto). Cada nota estimada que **no** aparece en ningún par del
matching (un falso positivo) se clasifica por la regla general de #8
-- su propio instante contra la densidad de referencia -- porque no hay
ninguna referencia de la cual heredar; ese caso no cambia. FR-014
(`spec.md`) fija este requisito.

Con este diseño, por construcción, cada par emparejado contribuye a
exactamente un subconjunto (nunca a ninguno, nunca a dos) -- la suma de
`verdaderos_positivos` de mono y poli es SIEMPRE igual a la del global,
sin excepción, porque ambas cifras se derivan de particionar el mismo
conjunto fijo de pares, no de dos emparejamientos que puedan discrepar
entre sí. `evaluar_subconjunto` (T009, research.md #16) no cambia --
sigue siendo el único punto que invoca `match_notes`, ahora llamado una
vez por grabación en vez de tres.

**Alternatives considered**: clasificar la nota estimada emparejada
por SU PROPIO instante pero además arrastrar el par completo a ambos
subconjuntos si las clasificaciones discrepan (contarlo dos veces) --
descartado: rompería SC-002 (cada acierto es de una MISMA grabación,
pero además debe ser de un subconjunto bien definido, nunca de dos a la
vez) y produciría `verdaderos_positivos` de un subconjunto mayores que
sus propias `num_notas_referencia`/`num_notas_estimadas`, un resultado
sin sentido. Promediar o interpolar entre las dos clasificaciones --
descartado por la misma razón que #8 ya fijó: la fuente de la
clasificación es la anotación de referencia, no un cálculo derivado que
mezcle ambos lados.

**Alternatives considered**: mantener el pool pero acotar su tamaño (p.
ej. lotes de N grabaciones) -- descartado porque no resuelve el defecto
de corrección (dos grabaciones del mismo lote seguirían pudiendo
emparejarse entre sí), solo lo reduce en magnitud; el rediseño por
conteos lo elimina por completo, no lo mitiga.
