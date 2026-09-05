# Research: Separación de guitarra con modelo preentrenado

**Input**: [spec.md](./spec.md) (incluye `## Clarifications`) | **Constitution**: `.specify/memory/constitution.md` v1.3.0

Todas las decisiones de abajo se verificaron contra las fuentes reales del
modelo (repositorio y paquete de PyPI), no se asumieron. Donde la
verificación fue parcial por una restricción de red del entorno de
planificación, queda dicho explícitamente (#3).

## 1. Modelo y variante: Demucs `htdemucs_6s`

**Decision**: El modelo declarado es Demucs, variante `htdemucs_6s` — la
única variante oficial de Demucs cuyo conjunto de fuentes incluye
`"guitar"` como categoría propia (`SOURCES = ["drums", "bass", "other",
"vocals", "guitar", "piano"]`). El resto de variantes de Demucs
(`htdemucs`, `htdemucs_ft`, `mdx*`) solo separan 4 fuentes y colapsarían la
guitarra dentro de `"other"`, lo cual no serviría para esta feature.

**Rationale**: Verificado en el código fuente real
(`demucs/pretrained.py`, `demucs/remote/files.txt`, README línea 244-245
del repositorio `adefossez/demucs`, que es el mismo proyecto publicado
originalmente por Meta/FAIR como `facebookresearch/demucs`): "`htdemucs_6s`:
6 sources version of `htdemucs`, with `piano` and `guitar` being added as
sources." El propio README documenta la limitación de calidad: "Quick
testing seems to show okay quality for `guitar`, but a lot of bleeding and
artifacts for the `piano` source" — se registra aquí porque es exactamente
el tipo de limitación que el Principio III de la constitución exige no
esconder ("una separación mediocre puede seguir siendo útil... eso es un
resultado, no un defecto a esconder").

**Alternatives considered**:
- `htdemucs` (4 fuentes, por defecto): descartado — la guitarra queda
  dentro de `"other"`, sin forma de aislarla del resto de instrumentos no
  clasificados.
- Otro separador preentrenado con salida de guitarra explícita (Spleeter,
  Open-Unmix): descartados por no tener, hasta donde se verificó, ninguna
  variante públicamente disponible con una fuente de guitarra propia — la
  guitarra como stem independiente es una rareza incluso entre modelos de
  separación, consistente con el Principio III ("mucho menos audio
  etiquetado con guitarra que con voz o batería").

**Hallazgo de arquitectura (no bloqueante, documentado por transparencia)**:
`htdemucs_6s` tiene una arquitectura de salida fija de 6 fuentes — el
modelo SIEMPRE produce una forma de onda para `"guitar"` en cada
inferencia, nunca "omite" la fuente. Esto significa que, con este modelo
concreto, el escenario de FR-009 (ausencia total de estimación) no ocurre
nunca en una corrida real: lo que en la práctica se observa cuando el tema
no tiene guitarra real es una salida de `"guitar"` con energía muy baja o
nula, que es exactamente el caso de FR-010 (estimación silenciosa), no el
de FR-009. FR-009 sigue siendo parte necesaria del contrato de
`separar_guitarra()` — es una garantía sobre la función para cualquier
`Separador` que se le inyecte (Key Entities de data-model.md), verificable
con un `Separador` de prueba que sí puede omitir la clave `"guitar"` — pero
no es un camino que la implementación concreta con `htdemucs_6s` dispare
por sí sola. No cambia ninguna decisión de la spec; solo aclara qué parte
del contrato prueba cada test.

## 2. Paquete, procedencia y verificación de integridad

**Decision**: Se usa el paquete `demucs` de PyPI (versión más reciente
publicada, `4.1.0` al momento de esta investigación, licencia MIT
confirmada en su metadato de PyPI y en el archivo `LICENSE` real del
repositorio). La declaración del modelo (FR-002) es: nombre `"Demucs"`,
variante `"htdemucs_6s"`, firma `5c90dfd2`, checksum SHA-256 (prefijo)
`34c22ccb`.

La verificación de integridad **no hay que implementarla**: ya la hace
`torch.hub.load_state_dict_from_url(url, check_hash=True)`, que es el
mecanismo que usa `demucs.repo.RemoteRepo.get_model()` internamente — el
nombre de archivo remoto (`5c90dfd2-34c22ccb.th`) codifica la firma y el
checksum esperado, y `torch.hub` calcula el SHA-256 del archivo descargado
y lo compara contra ese prefijo antes de cargarlo, fallando si no coincide.
Esta feature declara y expone esa firma/checksum (para que dos corridas
comparen que usan la misma versión, FR-002), no reimplementa la
verificación.

**Procedencia real de la descarga** (verificado en vivo, no solo leído):
`demucs.pretrained.get_model()` intenta primero el HuggingFace Hub
(`adefossez/HTDemucs-6s`); ese repositorio de HuggingFace está **cerrado
con acuerdo de acceso** (`gated`) — una petición HTTP directa devolvió
401. Si esa vía falla, la propia librería cae automáticamente al
repositorio legacy en `dl.fbaipublicfiles.com/demucs/`, que **sí es
público sin autenticación** (verificado: `HEAD` a
`https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/5c90dfd2-34c22ccb.th`
devuelve `200`, `content-length: 54996327` — ~55 MB, un solo archivo, no
un *bag* de varios modelos como las variantes de 4 fuentes). En la
práctica, cargar `htdemucs_6s` con la librería tal cual no requiere ninguna
credencial: el *fallback* público se usa de forma transparente.

**Rationale**: Es la única cadena de procedencia verificable sin
suposiciones — se comprobó cada tramo (metadato de PyPI, código fuente de
`pretrained.py`/`repo.py`/`hf.py`, y las URLs reales) en vez de asumir cómo
funciona la carga de pesos.

## 3. Licencia de los pesos: categoría separada del código, cita parcialmente verificada

**Decision**: Se documenta, en un archivo de atribuciones nuevo
(`docs/ATRIBUCIONES.md`, ver data-model.md), que el código de Demucs es MIT
(verificado: archivo `LICENSE` real del repositorio) y que los pesos
preentrenados se declaran bajo una restricción de uso distinta —
"provistos solo con fines científicos" —, con uso en este proyecto
limitado a lo personal y educativo (Assumptions de spec.md), consistente
con el Principio IV de la constitución tratado como categoría nueva, no
como una fuente de audio.

**Rationale y estado de verificación (transparencia explícita)**: La cita
literal ("The model weights are not covered by the MIT license, and are
provided only for scientific purposes.") la aportó el usuario del proyecto
con su fuente exacta:
<https://github.com/facebookresearch/demucs/issues/327> (comentario en el
issue). Durante esta sesión de planificación, el acceso directo a
`github.com` (fuera de `raw.githubusercontent.com` y `api.github.com`,
ambos también bloqueados) no estuvo disponible en el entorno de red
sandboxed, así que **no se pudo verificar la cita de forma independiente
leyendo el issue directamente**. Sí se encontró evidencia indirecta
consistente: el repositorio de pesos en HuggingFace está cerrado con
acuerdo de acceso (`gated`, ver #2), lo cual es compatible con que los
pesos lleven una restricción de uso adicional a la del código. Se registra
la cita como proveniente del usuario con su fuente citada, no como algo
verificado de forma independiente por este documento — la postura
práctica del proyecto (no redistribuir pesos, uso personal/educativo) no
depende de la cita exacta y se mantiene de cualquier forma.

**Alternatives considered**: Omitir la cita hasta verificarla de forma
independiente — descartada porque el usuario proveyó la fuente exacta
cuando se le preguntó, y la postura de precaución del proyecto no cambia
con o sin la cita; omitirla perdería la trazabilidad de por qué existe la
restricción.

## 4. Transformaciones: verificación programática contra el modelo, no constantes fijas

**Decision**: La frecuencia de muestreo y el número de canales que espera
el modelo se leen de las propiedades del propio objeto cargado
(`Separator.samplerate`, `Separator.audio_channels` en `demucs.api`), no se
hardcodean como `44100`/`2` en el código de esta feature, aunque en la
práctica con `htdemucs_6s` esos valores efectivamente son `44100` y `2`
(confirmado: README del repositorio, línea 221, "four stereo wav files
sampled at 44.1 kHz"). Esto es lo que hace que FR-005/FR-006 sean una
verificación real y no una suposición codificada.

- **Frecuencia de muestreo**: Slakh2100 ya está a 44.1 kHz (Feature 001,
  confirmado por lectura sin transformación); coincide con lo que el
  modelo espera. La comparación ocurre siempre; en la práctica no dispara
  ningún remuestreo, y eso se declara igual (Acceptance Scenario 1 de User
  Story 1).
- **Canales**: Slakh2100 es mono (1 canal); el modelo espera estéreo (2
  canales). La propia librería expone `demucs.audio.convert_audio_channels`,
  que para el caso mono→estéreo hace `wav.expand(*shape, channels, length)`
  (duplica el canal, no lo reescala) — esta feature aplica esa misma
  operación de forma explícita y declarada ANTES de invocar al modelo
  (FR-006), en vez de dejar que ocurra implícitamente dentro de
  `Separator.separate_tensor()` (que también la aplicaría sola si se le
  pasara audio sin convertir, vía su propio parámetro `sr`) — declarar la
  transformación nosotros mismos es lo que hace la garantía de FR-007
  auditable sin inspeccionar el código de la librería.
- **Colapso de salida a mono**: la salida de guitarra del modelo es
  estéreo (2 canales) porque el modelo siempre opera en estéreo
  internamente. El colapso a mono se hace promediando ambos canales
  (`(L + R) / 2`), no descartando uno de los dos — descartar un canal
  perdería la mitad de la señal separada; promediar es la operación
  inversa razonable de la duplicación de entrada.

**Rationale**: Verificado contra el código fuente real de `demucs/audio.py`
y `demucs/api.py`, no contra la documentación de alto nivel solamente.

**Alternatives considered**: Fijar `44100`/`2` como constantes en el código
de esta feature — descartado explícitamente: el propio input de la feature
exige que el punto "quede cerrado por verificación, no por suposición", y
una constante hardcodeada sería exactamente esa suposición aunque el valor
resulte coincidir.

## 5. Fallo de inferencia: excepción propia, sin reintento (FR-014)

**Decision**: Cualquier excepción que levante `demucs.api.Separator` o el
propio `torch` durante `separate_tensor()` (incluidas `LoadModelError`
si la carga del modelo falla, o cualquier `RuntimeError` de `torch` ante
una forma de tensor inesperada) se captura una sola vez en el punto de
llamada de esta feature y se re-levanta como una excepción propia
(`SeparacionFallidaError`, ver data-model.md) con el `tema_id` y la causa
original encadenada (`raise ... from causa_original`) — nunca silenciada,
nunca reintentada automáticamente.

**Rationale**: Cerrado con el usuario en `/speckit-clarify` (Session
2026-09-04). Sigue el mismo patrón que Feature 001 ya estableció para
archivos ilegibles: fallar con mensaje claro que identifica el caso
específico, en vez de coercionar el error a un resultado parcial.
Reintentar automáticamente (alternativa descartada en la pregunta de
clarificación) escondería un fallo determinista bajo una apariencia de
recuperación, y esta feature no tiene ninguna razón para esperar que un
reintento cambie el resultado (no hay red de por medio en la inferencia
misma, solo en la descarga de pesos la primera vez).

## 6. Determinismo: tolerancia numérica, extendiendo el Principio VIII (FR-015)

**Decision**: Dos corridas de inferencia sobre la misma mezcla con el
mismo modelo declarado deben coincidir dentro de una tolerancia numérica
explícita (no igualdad bit a bit), aplicada sobre las muestras de audio de
cada `Estimacion` resultante.

**Rationale**: Cerrado con el usuario en `/speckit-clarify`. Se verificó
que el modelo se carga siempre en modo evaluación (`bag.eval()` en
`demucs/hf.py`, y equivalente para el repositorio legacy vía
`load_model()`), así que no hay `dropout` ni normalización por lotes con
estadísticas variables de por medio — la única fuente real de variación
entre corridas es el orden de acumulación de punto flotante de las
operaciones de `torch` sobre CPU, exactamente la misma categoría de riesgo
que el Principio VIII ya resolvió para SI-SDR en la Feature 002. Extender
la misma política evita una segunda regla de determinismo en el proyecto.

**Alternatives considered**: Determinismo estricto bit a bit — descartado
por las mismas razones que en 002 (no hay semilla que fijar, y exigir
bit-exactitud entre builds de BLAS/`torch` distintos sería frágil sin
aportar garantía real adicional).

## 7. Estrategia de tests frente al presupuesto de cómputo sin GPU

**Decision**: Los tests unitarios de esta feature **no cargan el modelo
real**. Se define un protocolo `Separador` (ver data-model.md) con las
propiedades/métodos mínimos que el código de esta feature necesita
(`samplerate`, `audio_channels`, `separar(wav) -> dict[str, ndarray]`); los
tests unitarios inyectan un `SeparadorFalso` de prueba (sin `torch` ni
`demucs` importados) que puede simular cualquier escenario — coincidencia
o no de formato, ausencia de la clave `"guitar"` (FR-009), estimación
silenciosa (FR-010), y una excepción arbitraria (FR-014) — en
milisegundos.

Un único test de integración carga el `htdemucs_6s` real
(`demucs.api.Separator(model="htdemucs_6s", device="cpu")`) y separa un
clip sintético de 1-2 segundos (no un tema completo de varios minutos),
suficiente para probar que el cableado real (carga del modelo, conversión
de formato, llamada a `separate_tensor`, extracción del stem `"guitar"`)
funciona de punta a punta. Se marca con un marcador nuevo de pytest,
`modelo_real` (a añadir a `markers` en `pyproject.toml` junto al ya
existente `holdout`), y se salta (`pytest.skip`, no falla) si la carga del
modelo no se completa — por falta de red la primera vez que se descargan
los pesos, o por cualquier error de carga — en vez de bloquear todo el
guantelete por una dependencia externa no disponible.

**Rationale**: Es la misma distinción que AGENTS.md ya documenta para los
cuatro disparadores del guantelete ("qué falla cerrado y qué falla
abierto"): este test es de **conveniencia** (prueba cableado real, no un
invariante de dominio que deba bloquear el trabajo si la red no está
disponible), así que falla ABIERTO (se salta) ante la ausencia del
recurso externo, igual que el hook de `ruff` en `PostToolUse` se salta si
falta `uv`. Los invariantes de dominio en sí (qué hace la función ante
cada forma de resultado del separador) sí se prueban de forma estricta,
solo que contra el `Separador` falso, no contra la red.

**Compute/tamaño verificado**: la rueda de `torch` por defecto de PyPI
para CPython 3.12 en Linux pesa ~555 MB porque incluye runtimes de CUDA
aunque no haya GPU; el índice dedicado de PyTorch para CPU
(`download.pytorch.org/whl/cpu`) publica una rueda `+cpu` para el mismo
intérprete de ~187 MB, sin las dependencias de CUDA. Dado que el Principio
de entorno de esta feature es explícitamente "sin GPU declarada", la
instalación de esta feature usa el índice CPU-only (configuración de
`uv` con una fuente adicional para el paquete `torch`, decisión de
implementación en `/speckit-tasks`, no de este documento) en vez de la
rueda por defecto — ahorra ~370 MB de descarga e instalación que nunca se
usarían.

**Alternatives considered**: Mockear `demucs` por completo y no tener
ningún test que cargue el modelo real — descartado: perdería la única
prueba de que la integración con la librería real (nombres de argumentos,
forma de los tensores, nombres de los stems) sigue siendo válida si
`demucs` cambia de versión. Correr el test de integración real sobre un
tema completo de Slakh2100 en cada `just gauntlet` — descartado
explícitamente por el input de la feature (cientos de temas, sin GPU,
minutos por tema).

## 8. Arquitectura: nueva capa `separacion`, por encima de `analytics`

**Decision**: El código de esta feature vive en una capa nueva,
`guitar_tabs_analysis.separacion`, que se agrega **por encima** de
`analytics` en el contrato de capas de `import-linter`
(`pyproject.toml::[tool.importlinter]`):

```
guitar_tabs_analysis.separacion   (nueva -- produce Estimacion)
guitar_tabs_analysis.analytics    (ya existe -- define Estimacion, mide)
guitar_tabs_analysis.ingestion    (ya existe -- define PistaAudio, lee)
```

**Rationale**: Esta feature necesita construir objetos `Estimacion`, que
ya está definido en `analytics.metrica_separacion` (Feature 002) y no se
redefine (ver data-model.md, Key Entities de spec.md). Import-linter con
`type = "layers"` exige que cada capa solo importe de las capas debajo de
ella en la lista — como `separacion` necesita importar de `analytics`
(para `Estimacion`) y de `ingestion` (para `PistaAudio`), debe quedar por
encima de ambas. `analytics` no necesita saber nada de `separacion` (no
hay import en la dirección contraria), así que no se rompe la regla ya
existente de que `analytics` -> `ingestion` es de una sola vía. El
contrato de `quality` (transversal, prohibido depender de `analytics`) no
se ve afectado por esta capa nueva.

**Alternatives considered**: Poner el código de separación dentro de
`analytics` mismo — descartado porque mezclaría "calcular una métrica
sobre datos ya existentes" con "invocar un modelo pesado con sus propias
dependencias externas (`torch`)"; son responsabilidades y presupuestos de
recursos claramente distintos, y el spec ya declara ambas features como
alcances separados (FR-012 de esta feature: no calcula métrica).
