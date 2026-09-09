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
que el modelo real exige, no la del hito 1 por inercia. Esta forma no
cambió con research.md #15 (subprocess): `ruta_audio` es exactamente lo
que el adaptador reenvía al subproceso.

### Postcondiciones

1. **Éxito.** MUST devolver una lista de `NotaEstimada` (posiblemente
   vacía -- silencio total es un resultado válido, spec.md US2 AS3), una
   por cada evento de nota que el modelo predice, con `tono_midi` e
   `inicio_s` (y `fin_s`, conservado aunque no participe del criterio de
   acierto, FR-004).
2. **Fallo de inferencia.** Si el modelo no puede procesar el archivo
   (error real, no ausencia de notas), MUST levantar una excepción
   propia (`TranscripcionFallidaError` o equivalente) -- nunca dejar
   propagar una excepción cruda sin envolver, mismo criterio que
   `SeparacionFallidaError` del hito 1. Para `BasicPitchTranscriptor`
   (research.md #15), "el modelo no puede procesar el archivo" cubre
   tres casos concretos del subproceso, los tres tratados igual (nunca
   una lista vacía por defecto): código de salida distinto de cero,
   archivo de salida JSON ausente, o JSON presente pero malformado.

## `transcripcion.basic_pitch_transcriptor.BasicPitchTranscriptor`

Implementación real de `Transcriptor` -- **corregido en
`/speckit-implement` (research.md #15): NO importa `basic_pitch`
directamente.** `basic-pitch` es irresoluble en Python 3.12 (research.md
#2); esta clase invoca por subproceso el intérprete de un entorno Python
3.10 aparte (`envs/basic_pitch_py310/.venv/bin/python`, invocado
directamente, nunca vía `uv run` -- research.md #15) corriendo
`envs/basic_pitch_py310/transcribir_subproceso.py` sobre `ruta_audio`,
con una ruta de salida JSON temporal como segundo argumento. Ningún
módulo del proyecto principal (`src/guitar_tabs_analysis/`) importa
`basic_pitch` -- vive enteramente en el entorno secundario, que `just
doctor` verifica por separado.

## `envs/basic_pitch_py310/transcribir_subproceso.py` (fuera de `src/`, entorno Python 3.10 aparte)

```text
uso: python transcribir_subproceso.py <ruta_audio> <ruta_salida_json>
```

No es un módulo del paquete `guitar_tabs_analysis` -- corre bajo un
intérprete distinto (research.md #15), invocado como proceso externo,
nunca importado.

### Postcondiciones

1. **Éxito.** MUST escribir en `ruta_salida_json` un array JSON de
   objetos `{"tono_midi": float, "inicio_s": float, "fin_s": float}` (un
   objeto por evento de nota que `basic_pitch.inference.predict()`
   devuelve, posiblemente un array vacío -- silencio total es válido) y
   MUST salir con código `0`.
2. **Fallo.** Ante cualquier excepción real durante la inferencia, MUST
   imprimir el detalle en stderr, MUST salir con código distinto de
   cero, y MUST NOT escribir `ruta_salida_json` (ni dejarlo a medio
   escribir) -- el archivo de salida ausente es, junto con el código de
   salida, la señal de fallo que el adaptador (`BasicPitchTranscriptor`)
   traduce a `TranscripcionFallidaError`.

## `analytics.metrica_deteccion_notas`

```python
def evaluar_subconjunto(
    notas_referencia: list[NotaReferencia],
    notas_estimadas: list[NotaEstimada],
) -> ResultadoSubconjunto:
    """Acierto/emparejamiento vía mir_eval.transcription sobre un
    conjunto de notas SIN partir por polifonía -- el bloque que
    evaluar_grabacion/agregar_conjunto invocan una vez por subconjunto
    (global, monofónico, polifónico)."""
    ...

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
`Estimacion` en la Feature 002/003 del hito 1. `ExclusionDeteccion` y
`ResultadoDeteccionGrabacion` (data-model.md) **también** se definen
aquí, no en `deteccion/orquestador.py`: `agregar_conjunto` las necesita
en su propia firma pública, y `analytics` no puede importar de
`deteccion` sin crear una dependencia circular (research.md #11,
corrección de la sesión de `/speckit-tasks`) -- `deteccion` importa
ambos tipos desde aquí.

### Postcondiciones

1. **Acierto sobre un conjunto sin partir (FR-003/FR-004/FR-005).**
   `evaluar_subconjunto` MUST calcular el emparejamiento con
   `mir_eval.transcription` (`onset_tolerance=0.05`, `pitch_tolerance=50.0`,
   `offset_ratio=None`, research.md #3/#4/#5) sobre las listas que recibe
   tal cual, sin ninguna partición por polifonía -- esa partición es
   responsabilidad exclusiva de quien la invoca (`evaluar_grabacion`/
   `agregar_conjunto`, postcondición 3 más abajo), nunca de esta función.
2. **Subconjunto vacío (FR-008).** Si `notas_referencia` está vacía,
   `evaluar_subconjunto` MUST devolver `exhaustividad=None` (nunca una
   división por cero); si `notas_estimadas` está vacía, MUST devolver
   `precision=None`; si ambas condiciones aplican, ambos campos (y
   `balance_f1`) son `None`. Este guard ocurre **antes** de invocar
   `mir_eval`, sin depender de cómo se comporte esa librería ante una
   entrada vacía (a verificar contra su código fuente real en
   `/speckit-implement`, no supuesto aquí).
3. **Clasificación (FR-006, research.md #8).** `clasificar_polifonia_en_instante`
   MUST devolver `"polifonica"` si dos o más notas de `notas_referencia`
   solapan `instante_s`, `"monofonica"` en cualquier otro caso (incluido
   el caso degenerado de cero referencias solapando).
4. **Partición por polifonía (FR-003/FR-004/FR-005, research.md #9).**
   `evaluar_grabacion` MUST partir primero el conjunto de notas
   (referencia y estimadas) en monofónico/polifónico vía
   `clasificar_polifonia_en_instante` (postcondición 3), y llamar
   `evaluar_subconjunto` (postcondición 1) **una vez por subconjunto**
   -- global (sin partir), monofónico, polifónico -- nunca calculando un
   emparejamiento global y dividiendo el resultado después.
5. **Agregación (FR-007).** `agregar_conjunto` MUST combinar el pool de
   notas de todas las grabaciones **no excluidas** antes de partir por
   polifonía y evaluar -- clasificando las notas de cada grabación contra
   las referencias de esa misma grabación (nunca cruzando grabaciones),
   acumulando en tres pools (global/mono/poli) a través de todas las
   grabaciones, e invocando `evaluar_subconjunto` una vez por pool --
   nunca promedia los resultados de `evaluar_grabacion` calculados por
   grabación (evitaría, por ejemplo, que una grabación con muchas notas
   pesara más que una con pocas, que es exactamente el comportamiento
   esperado de una métrica agregada, no promediada).

## `deteccion.orquestador`

```python
def construir_lista_grabaciones(
    modo: Literal["medibles", "reservado"],
    root_dir: Path,
    *,
    tamano_reserva: int = 72,
    semilla_reserva: int = 20260908,
) -> list[str]:
    ...

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

1. **Reserva derivada de la semilla, nunca de una lista persistida
   (Principio VI, research.md #14/#15).** `construir_lista_grabaciones`
   MUST calcular `random.Random(semilla_reserva).sample(<todos los
   identificadores ordenados>, tamano_reserva)` en cada invocación --
   MUST NOT leer ni escribir ningún archivo de manifiesto. Con
   `modo="reservado"` MUST devolver esa muestra; con `modo="medibles"`
   MUST devolver el complemento exacto (`todos` menos la muestra) --
   ambos derivados del mismo cálculo, de forma que su unión sea siempre
   `todos` y su intersección siempre vacía, nunca dos cálculos
   independientes que podrían divergir.
2. **Por grabación (FR-012, research.md #10).** Para cada
   `grabacion_id` de `grabaciones` (la lista que `ejecutar_deteccion`
   recibe de su llamador -- típicamente el resultado de
   `construir_lista_grabaciones("medibles", ...)`, pero esta función no
   lo impone ni lo verifica), MUST leerla (`ingestion.guitarset`),
   transcribirla (`transcriptor.transcribir`), y si cualquiera de los
   dos pasos falla con una excepción real, MUST registrar esa grabación
   como `ExclusionDeteccion` con el detalle del error, y MUST continuar
   con la siguiente grabación -- nunca abortar la corrida completa por
   un fallo individual.
3. **Artefacto final (FR-011).** Al completar todas las grabaciones,
   MUST devolver un único `ArtefactoDeteccion` con el modelo declarado,
   la tolerancia y ventana aplicadas, la lista de grabaciones, las
   exclusiones con su motivo, los resultados crudos por grabación, y las
   tres cifras (global/monofónico/polifónico) calculadas con
   `analytics.metrica_deteccion_notas.agregar_conjunto` sobre las
   grabaciones no excluidas.
4. **Sin umbral (FR-009).** MUST NOT comparar ninguna cifra contra
   ningún valor de aprobación -- termina en devolver el artefacto, nunca
   en un veredicto de pase/falla.
