# Contrato: detección de notas

Librería, sin CLI todavía (se agrega en `/speckit-tasks` de esta feature
o en una posterior, mismo criterio que el hito 1 diferenció "orquestador
puro" de "CLI real", Feature 004). El contrato es la firma pública de
cuatro módulos nuevos y el comportamiento observable descrito en
`spec.md`.

## `ingestion.guitarset.leer_grabacion`

```python
def leer_grabacion(grabacion_id: str, root_dir: Path) -> LecturaGrabacion:
    ...
```

Módulo nuevo: `ingestion/guitarset.py`. No importa `transcripcion` ni
`analytics` (capa base, mismo lugar que `ingestion/slakh2100.py`).

### Precondiciones

`root_dir` es la raíz de una distribución de GuitarSet accesible vía
`mirdata` (audio + anotaciones JAMS ya presentes en disco -- este
proyecto no descarga datos, Principio IV: "el pipeline falla con mensaje
claro si no lo encuentra, nunca en silencio").

### Postcondiciones

1. **Éxito.** Si `grabacion_id` existe en el índice de `mirdata`, MUST
   devolver `LecturaGrabacion` con `ruta_audio` apuntando al archivo real
   de `audio_mic` (research.md #6) y `notas_referencia` derivadas de
   `Track.notes_all` (research.md #7) -- nunca de `audio_mix` ni de
   ninguna señal hexafónica.
2. **Grabación inexistente o índice corrupto.** MUST levantar una
   excepción propia identificable (mismo patrón que
   `TemaNoExisteError`/`ArchivoAudioNoLegibleError` del hito 1), nunca
   una excepción cruda de `mirdata` sin envolver.

## `transcripcion.transcriptor.Transcriptor` (Protocol)

```python
class Transcriptor(Protocol):
    modelo_declarado: ModeloTranscripcionDeclarado

    def transcribir(self, ruta_audio: Path) -> list[NotaEstimada]:
        ...
```

Módulo nuevo: `transcripcion/transcriptor.py`. Recibe una **ruta de
archivo**, no muestras cargadas en memoria -- a diferencia de
`separacion.separador.Separador` (hito 1), porque `basic_pitch.inference.predict()`
solo acepta ruta de archivo, no un array en memoria (verificado contra
el código fuente real, research.md #1) -- este protocolo sigue la forma
que el modelo real exige, no la del hito 1 por inercia.

### Postcondiciones

1. **Éxito.** MUST devolver una lista de `NotaEstimada` (posiblemente
   vacía -- silencio total es un resultado válido, spec.md US2 AS3), una
   por cada evento de nota que el modelo predice, con `tono_midi` e
   `inicio_s` (y `fin_s`, conservado aunque no participe del criterio de
   acierto, FR-004).
2. **Fallo de inferencia.** Si el modelo no puede procesar el archivo
   (error real, no ausencia de notas), MUST levantar una excepción
   propia (`TranscripcionFallidaError` o equivalente) -- nunca dejar
   propagar una excepción cruda de `basic_pitch`/`onnxruntime` sin
   envolver, mismo criterio que `SeparacionFallidaError` del hito 1.

## `transcripcion.basic_pitch_transcriptor.BasicPitchTranscriptor`

Implementación real de `Transcriptor` -- único módulo de esta feature
que importa `basic_pitch`. Construye una sola vez (carga el modelo ONNX
declarado, research.md #1/#2), reutilizable entre llamadas a
`transcribir()`.

## `analytics.metrica_deteccion_notas`

```python
def clasificar_polifonia_en_instante(
    instante_s: float, notas_referencia: list[NotaReferencia]
) -> ClasificacionPolifonia:
    ...

def evaluar_grabacion(
    notas_referencia: list[NotaReferencia],
    notas_estimadas: list[NotaEstimada],
) -> tuple[ResultadoSubconjunto, ResultadoSubconjunto, ResultadoSubconjunto]:
    """Devuelve (global, monofónico, polifónico) para una grabación."""
    ...

def agregar_conjunto(
    resultados: list[ResultadoDeteccionGrabacion],
) -> tuple[ResultadoSubconjunto, ResultadoSubconjunto, ResultadoSubconjunto]:
    """Mismo cálculo que evaluar_grabacion, pero sobre el pool de todas
    las grabaciones exitosas del conjunto (nunca sobre las excluidas)."""
    ...
```

Módulo nuevo: `analytics/metrica_deteccion_notas.py`. Puede importar de
`ingestion` (para el tipo `NotaReferencia`), nunca de `transcripcion`
(orden de capas, research.md #11) -- `NotaEstimada` se define en este
mismo módulo y `transcripcion` lo importa desde aquí, mismo patrón que
`Estimacion` en la Feature 002/003 del hito 1.

### Postcondiciones

1. **Clasificación (FR-006, research.md #8).** `clasificar_polifonia_en_instante`
   MUST devolver `"polifonica"` si dos o más notas de `notas_referencia`
   solapan `instante_s`, `"monofonica"` en cualquier otro caso (incluido
   el caso degenerado de cero referencias solapando).
2. **Acierto (FR-003/FR-004/FR-005).** `evaluar_grabacion` MUST calcular
   el emparejamiento con `mir_eval.transcription`
   (`onset_tolerance=0.05`, `pitch_tolerance=50.0`, `offset_ratio=None`,
   research.md #3/#4/#5), partiendo primero el conjunto de notas en
   monofónico/polifónico (research.md #9) antes de invocar la
   evaluación, nunca calculando un emparejamiento global y dividiendo el
   resultado después.
3. **Subconjunto vacío (FR-008).** Si el subconjunto de notas de
   referencia (o de estimadas) de un grupo queda vacío, el
   `ResultadoSubconjunto` correspondiente MUST tener `exhaustividad`
   (o `precision`) en `None`, nunca una división por cero silenciosa.
4. **Agregación (FR-007).** `agregar_conjunto` MUST combinar el pool de
   notas de todas las grabaciones **no excluidas** antes de partir por
   polifonía y evaluar -- nunca promedia los resultados de
   `evaluar_grabacion` de cada grabación por separado (evitaría, por
   ejemplo, que una grabación con muchas notas pesara más que una con
   pocas, que es exactamente el comportamiento esperado de una métrica
   agregada, no promediada).

## `deteccion.orquestador`

```python
def ejecutar_deteccion(
    grabaciones: list[str],
    root_dir: Path,
    transcriptor: Transcriptor,
) -> ArtefactoDeteccion:
    ...
```

Paquete nuevo: `deteccion/orquestador.py` -- excluido a propósito del
contrato `layers` de import-linter (research.md #11), mismo criterio que
`medicion` en el hito 1: importa de `ingestion`, `transcripcion` y
`analytics` a la vez.

### Postcondiciones

1. **Por grabación (FR-012, research.md #10).** Para cada
   `grabacion_id` de `grabaciones`, MUST leerla (`ingestion.guitarset`),
   transcribirla (`transcriptor.transcribir`), y si cualquiera de los
   dos pasos falla con una excepción real, MUST registrar esa grabación
   como `ExclusionDeteccion` con el detalle del error, y MUST continuar
   con la siguiente grabación -- nunca abortar la corrida completa por
   un fallo individual.
2. **Artefacto final (FR-011).** Al completar todas las grabaciones,
   MUST devolver un único `ArtefactoDeteccion` con el modelo declarado,
   la tolerancia y ventana aplicadas, la lista de grabaciones, las
   exclusiones con su motivo, los resultados crudos por grabación, y las
   tres cifras (global/monofónico/polifónico) calculadas con
   `analytics.metrica_deteccion_notas.agregar_conjunto` sobre las
   grabaciones no excluidas.
3. **Sin umbral (FR-009).** MUST NOT comparar ninguna cifra contra
   ningún valor de aprobación -- termina en devolver el artefacto, nunca
   en un veredicto de pase/falla.
