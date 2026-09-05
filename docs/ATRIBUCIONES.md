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
