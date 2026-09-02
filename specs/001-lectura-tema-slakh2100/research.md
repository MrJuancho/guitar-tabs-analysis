# Research: Lectura de un tema de Slakh2100

**Input**: [spec.md](./spec.md) | **Date**: 2026-09-01

Cada decisión resuelve un `NEEDS CLARIFICATION` del Technical Context en
`plan.md` o un supuesto técnico que el spec deja fuera de su alcance por
diseño (ver `spec.md#Assumptions`).

## 1. Biblioteca de lectura de audio

**Decision**: `soundfile` (bindings de `libsndfile`), leyendo con el
`dtype` que coincide con el `subtype` real del archivo (p. ej. `int16`
para PCM_16), en vez del `float64` reescalado que da por defecto.

**Rationale**: Slakh2100 se distribuye enteramente en `.flac`
(confirmado contra la documentación oficial del dataset — ver Sources).
`soundfile` decodifica FLAC de forma nativa y sin pérdida, devuelve
`numpy.ndarray` directamente, y expone `sf.info(path).subtype` para
conocer la codificación real del archivo. Leer con ese `dtype` exacto
evita cualquier reescalado (la normalización que FR-005 prohíbe) y hace
que SC-005 ("idéntico, muestra por muestra") sea una comparación de
enteros exacta, no una comparación de floats con tolerancia.

**Alternatives considered**:
- `librosa`: remuestrea a 22050 Hz y convierte a mono/float32 por
  defecto — viola FR-005 directamente aunque se desactiven esas
  opciones, el diseño de la biblioteca no es el contrato correcto para
  "leer tal como viene".
- `torchaudio`: trae PyTorch como dependencia solo para I/O, injustificado
  para una feature que no hace inferencia ni entrenamiento.
- `wave`/`aifc` (stdlib): no soportan FLAC; el dataset no ofrece WAV.

## 2. Parseo de metadatos

**Decision**: `PyYAML` para `metadata.yaml`.

**Rationale**: `metadata.yaml` es YAML estándar (confirmado contra
`ethman/slakh-utils`, la utilidad de referencia del propio dataset).
`PyYAML` es la biblioteca estándar de facto, sin dependencias extra, y
solo se necesita lectura (no edición con preservación de formato).

**Alternatives considered**: `ruamel.yaml` (da soporte de
round-trip/edición que esta feature no necesita, solo lee).

## 3. Regla de clasificación "es guitarra"

**Decision**: Una pista (`stem`) cuenta como guitarra si y solo si
`metadata.yaml → stems.<id>.inst_class == "Guitar"`, sin mirar
`midi_program_name`. El bajo eléctrico cae bajo `inst_class == "Bass"`,
una familia distinta, y queda excluido automáticamente por esta misma
regla.

**Rationale**: `inst_class` es el campo categórico de la taxonomía
oficial de 34 clases de instrumento de Slakh2100 — es exactamente "los
metadatos del conjunto" que el spec y la constitución (Principio V)
señalan como fuente de verdad, y su agrupación coincide con la
clasificación General MIDI: los programas de Guitarra (25–32) y de Bajo
(33–40) son familias GM distintas, y en Slakh2100 se reflejan como
valores distintos de `inst_class`. Usar este campo cierra FR-003 y
FR-004 sin heurísticas adicionales: no hace falta interpretar
`midi_program_name` para decidir si "Distortion Guitar" o "Clean
Guitar" cuentan (ambos ya son `inst_class: Guitar`).

**Alternatives considered**: Coincidencia de substring sobre
`midi_program_name` (frágil — depende de que el texto humano no cambie
de convención, y es un heurístico donde ya existe un campo categórico
autoritativo).

## 4. Pistas de guitarra no renderizadas (`audio_rendered: false`)

**Decision**: Una pista con `inst_class == "Guitar"` pero
`audio_rendered == false` en los metadatos se **excluye** de la
colección de guitarras devuelta — no dispara FR-012 (archivo ausente).

**Rationale**: `audio_rendered: false` es un estado normal y
documentado del dataset (la pista MIDI no produjo salida audible, p. ej.
un track sin eventos, y Slakh2100 deliberadamente no escribe archivo
para ella) — no es una falla de integridad, es la ausencia esperada de
un archivo que nunca debió existir. Tratarlo como FR-012 haría fallar
lecturas de temas perfectamente válidos por una fracción arbitraria del
dataset, y confundiría "este tema no tiene esta guitarra" (un resultado
legítimo, symétrico al caso ya cubierto por FR-009/User Story 2) con
"los datos están corruptos". FR-012 queda reservado para una pista con
`audio_rendered: true` (o la mezcla) cuyo archivo, aun así, no está en
disco o no se puede leer — ahí sí hay una discrepancia real entre lo que
los metadatos prometen y lo que existe.

**Alternatives considered**: Incluir la pista y dejar que la ausencia
de archivo dispare FR-012 (rechazada — confunde "ausencia esperada" con
"fallo de integridad", exactamente la ambigüedad que la Clarification
de `spec.md` cerró para el caso de archivo *inesperadamente* ausente,
no para este caso *esperado*); fallar siempre ante cualquier guitarra no
renderizada (rechazada — violaría FR-009 si la única guitarra del tema
resulta no renderizada: el tema debe comportarse como si no tuviera
guitarras, colección vacía, sin error).

## 5. Ubicación del dataset en disco

**Decision**: La feature recibe un `root_dir: Path` explícito (o un
único valor de configuración con ese propósito) que apunta a la copia
local de Slakh2100 (el directorio que contiene `TrackXXXXX/`). No se
construye manifiesto ni verificación de checksums en esta feature.

**Rationale**: `spec.md#Assumptions` es explícito: "esta feature no
cubre su descarga ni su verificación de integridad". Un manifiesto con
sumas de verificación (Principio IV de la constitución) es
infraestructura de una feature de adquisición de datos futura, no de
esta lectura puntual. Un parámetro de ruta es el mecanismo mínimo
suficiente para lo que este spec pide.

**Alternatives considered**: Manifiesto con checksums ahora (rechazada
— fuera de alcance declarado, prematuro); ruta fija hardcodeada
(rechazada — no portable entre máquinas/CI).

## 6. Estrategia de datos de prueba

**Decision**: Ningún audio real de Slakh2100 se commitea al repositorio.
Los tests construyen, en un directorio temporal por test, una estructura
sintética `TrackXXXXX/{metadata.yaml, mix.flac, stems/*.flac}` con
formas de onda cortas generadas (p. ej. senoidales/ruido de unas pocas
centenas de muestras), nunca grabaciones reales.

**Rationale**: La constitución (Principio IV) es explícita: "El
repositorio no contiene audio. Ni fixtures de grabaciones, ni casos de
prueba." Generar la estructura en disco en tiempo de test (en vez de
mockear la capa de I/O) sigue ejercitando el decodificador FLAC real y
el parseo YAML real, que es lo que este spec necesita verificar.

**Alternatives considered**: Mockear la capa de I/O por completo
(rechazada — no detectaría bugs reales de integración con
`soundfile`/YAML); depender de una copia local real de Slakh2100 en CI
(rechazada — no portable, y los tests quedarían silenciosamente
saltados donde no exista esa copia).

## 7. Determinismo (Principio VIII de la constitución, `ABIERTO`)

**Decision**: No se cierra en este plan.

**Rationale**: Esta feature no ejecuta ninguna operación no
determinista — no hay remuestreo, no hay inferencia de modelo, no hay
semillas aleatorias; cada lectura es una decodificación pura de un
archivo inmutable, con el mismo resultado en cualquier corrida y
cualquier hardware. El propio criterio de cierre del `ABIERTO` ("cuando
estén elegidas la biblioteca y el hardware" de la operación que lo
necesita) apunta a la futura feature de separación/inferencia, no a
esta. Se documenta aquí para que el ítem de gobernanza no se salte en
silencio, no para cerrarlo prematuramente.

## 8. Métrica principal (Principio VII de la constitución, `ABIERTO`)

**Decision**: No aplica a esta feature — no se calcula ninguna métrica
aquí. Permanece abierto, a cerrar en el `/plan` de la feature de
métrica.

## Sources

- [Slakh2100 | Zenodo](https://zenodo.org/records/4599666) — formato de distribución, `.flac`, mono, 44.1kHz/16-bit.
- [slakh-utils/README.md at master · ethman/slakh-utils](https://github.com/ethman/slakh-utils/blob/master/README.md) — estructura de `metadata.yaml`, campos por stem (`inst_class`, `audio_rendered`, `midi_program_name`, etc.), layout de directorio `TrackXXXXX/`.
