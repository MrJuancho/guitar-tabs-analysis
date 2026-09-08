# Atribuciones

<!--
Este archivo declara, para cada componente de terceros cuyo uso no es
obvio por sí mismo (no una dependencia de PyPI cualquiera, sino un
modelo preentrenado con pesos), la licencia real y las restricciones de
uso -- verificadas donde fue posible, citadas con su fuente donde no.
Constitución, Principio IV: "una fuente sin licencia identificada no es
admisible".
-->

## Demucs (separación de guitarra, Feature 003)

**Código**: [Demucs](https://github.com/facebookresearch/demucs)
(paquete `demucs` en PyPI, versión `4.1.0` al momento de esta
declaración). Licencia **MIT** -- verificada contra el archivo `LICENSE`
real del repositorio (copyright Meta Platforms, Inc.), no solo contra el
metadato de PyPI.

**Modelo usado**: `htdemucs_6s` -- la única variante de Demucs cuyo
conjunto de fuentes incluye `"guitar"` como categoría propia (además de
`drums`, `bass`, `other`, `vocals`, `piano`). Documentada por sus propios
autores como experimental, con calidad limitada para `piano` (no afecta
a esta feature, que solo usa la fuente `guitar`).

**Pesos del modelo -- licencia distinta de la del código.** Los pesos
preentrenados de Demucs **no** están cubiertos por la licencia MIT del
código: se declaran provistos únicamente con fines científicos. Esta
restricción se cita del comentario de un mantenedor del repositorio
oficial, `facebookresearch/demucs#327`
(<https://github.com/facebookresearch/demucs/issues/327>): "The model
weights are not covered by the MIT license, and are provided only for
scientific purposes."

**Nota de verificación (honestidad explícita, no un detalle menor)**:
esta cita fue aportada por quien dirige este proyecto, con su fuente
exacta. Durante la sesión de planificación de la Feature 003, el acceso
a `github.com` (fuera de `raw.githubusercontent.com` y `api.github.com`,
también bloqueado) no estuvo disponible en el entorno de red del agente,
así que **no se pudo leer el comentario del issue de forma
independiente** para confirmar la cita palabra por palabra. Sí se
encontró evidencia indirecta consistente: al pedir la página del
repositorio de pesos en HuggingFace (`adefossez/HTDemucs-6s`) con una
petición HTTP anónima simple, la respuesta fue `401` (acceso cerrado con
acuerdo) -- compatible con que los pesos lleven una restricción de uso
adicional a la del código, aunque la descarga real con la herramienta
oficial (`huggingface_hub`) sí funcionó sin credenciales explícitas
(ver `specs/003-separacion-modelo-preentrenado/research.md`, sección 2).
La postura práctica de este proyecto (ver siguiente párrafo) no depende
de que esta cita se confirme palabra por palabra: se aplica la misma
precaución de todos modos.

**Consecuencia práctica para este proyecto**: los pesos de `htdemucs_6s`
**no se redistribuyen** dentro de este repositorio -- se descargan y se
cachean fuera de él (caché estándar de HuggingFace Hub o de `torch.hub`,
según la vía de descarga), referenciados por la declaración de
`ModeloDeclarado` (nombre, variante, firma, checksum -- ver
`src/guitar_tabs_analysis/separacion/demucs_separador.py`), nunca como
archivo versionado. El uso de estos pesos en este proyecto es
**personal y educativo**, sin objetivo comercial (ver `spec.md` de la
Feature 003 y "Alcance" en `.specify/memory/constitution.md`), consistente
con la restricción declarada arriba.

El Principio IV de la constitución ("toda fuente debe ser CC BY 4.0 o
más permisiva") se escribió para fuentes de **audio** (Slakh2100,
GuitarSet, EGFxSet); los pesos de un modelo preentrenado son una
categoría distinta que ese principio no contempla todavía. Esta
declaración resuelve el caso concreto de esta feature de forma explícita,
sin asumir que la regla de audio le aplica automáticamente.

## Basic Pitch (detección de notas, Feature 006, hito 2)

**Código y pesos -- sin asimetría, a diferencia de Demucs**: [Basic
Pitch](https://github.com/spotify/basic-pitch) (paquete `basic-pitch` en
PyPI, versión `0.4.0` al momento de esta declaración). Licencia
**Apache License 2.0** -- verificada contra el archivo `LICENSE` real del
repositorio (copyright Spotify AB), que cubre tanto el código como los
pesos preentrenados (`basic_pitch/saved_models/icassp_2022/`): a
diferencia de Demucs, el propio `README.md` de Basic Pitch no distingue
ninguna licencia separada para los pesos.

**Modelo usado**: variante `icassp_2022`, backend `onnx` (nunca
`tensorflow`, research.md #2 de
`specs/006-deteccion-notas-guitarra-limpia/`).

**Nota de bloqueo (sesión de `/speckit-implement`, T001-T009)**: pese a
la licencia limpia, `basic-pitch` **no se instaló** en este slice --
verificado contra su `pyproject.toml` real (rama `main` de
`github.com/spotify/basic-pitch`, idéntico a la versión `0.4.0` publicada
en PyPI): su dependencia base -- fuera de cualquier extra -- incluye
`tensorflow>=2.4.1,<2.15.1; platform_system != 'Darwin' and
python_version >= '3.11'`, y esa franja de `tensorflow` no publica
ninguna rueda para `cp312` (confirmado contra PyPI: `tensorflow 2.15.0`
solo trae `cp39`/`cp310`/`cp311`) -- instalar `basic-pitch[onnx]` es
irresoluble en este proyecto (`requires-python = ">=3.12"`) sin importar
qué extra se elija. Ver `pyproject.toml` y
`specs/006-deteccion-notas-guitarra-limpia/tasks.md` (T002) para el
detalle completo; la instalación real de `basic-pitch` (User Story 2,
T010 en adelante) queda pendiente de que se resuelva este bloqueo.

## GuitarSet (detección de notas, Feature 006, hito 2)

[GuitarSet](https://zenodo.org/records/3371780) (DOI
`10.5281/zenodo.3371780`), licencia **CC BY 4.0** -- ya admitida por el
Principio IV de la constitución para fuentes de audio, misma categoría
que Slakh2100. Cargado vía `mirdata`, señal `audio_mic` (research.md #6
de `specs/006-deteccion-notas-guitarra-limpia/`), nunca `audio_mix` ni
ninguna señal hexafónica.

## `mir_eval` (métrica de detección de notas, Feature 006, hito 2)

[`mir_eval`](https://github.com/craffel/mir_eval) (paquete `mir_eval` en
PyPI). Licencia **MIT** -- verificada contra el archivo `LICENSE` real
del repositorio y contra el metadato del paquete instalado
(`License :: OSI Approved :: MIT License`). Usado para el emparejamiento
óptimo y el cálculo de precisión/exhaustividad/balance
(`mir_eval.transcription.precision_recall_f1_overlap`), y para la
conversión MIDI→Hz (`mir_eval.util.midi_to_hz`) -- research.md #3/#4/#5
de `specs/006-deteccion-notas-guitarra-limpia/`.

## `mirdata` (carga de GuitarSet, Feature 006, hito 2)

[`mirdata`](https://github.com/mir-dataset-loaders/mirdata) (paquete
`mirdata` en PyPI). Licencia **BSD-3-Clause** -- verificada contra el
archivo `LICENSE` real del repositorio y contra el metadato del paquete
instalado (`License :: OSI Approved :: BSD License`). Usado para cargar
audio y anotaciones de GuitarSet sin parsear JAMS a mano -- research.md
#7 de `specs/006-deteccion-notas-guitarra-limpia/`.
