"""Lectura de una grabación de GuitarSet (capa `ingestion`, nivel más
bajo del contrato de import-linter): tipos de dominio para la anotación
de referencia de una grabación de guitarra limpia, y `leer_grabacion()`
real vía `mirdata` (User Story 2, T012).

`leer_grabacion()` usa `audio_mic` (research.md #6) -- la grabación real
de micrófono, nunca `audio_mix` (una mezcla sintetizada por downmix de
señales por-cuerda que un sistema real no tendría disponibles) -- y las
notas de referencia de `Track.notes_all` (research.md #7). Este módulo
no importa `transcripcion` ni `analytics`.

**Corrección respecto a research.md #7** (verificado contra el código
fuente real de `mirdata` 1.0.0, instalado en este proyecto): el atributo
de tono de `NoteData` es `.pitches`, no `.values` -- `mirdata.annotations.NoteData`
nunca expuso un atributo `values` en la versión instalada; `research.md`
describía una API distinta a la que realmente resuelve `mirdata>=0.3`. El
resto de la decisión (`Track.notes_all`, `intervals` en `[inicio, fin]`
segundos) sí coincide con lo verificado.

Ver `specs/006-deteccion-notas-guitarra-limpia/data-model.md` y
`specs/006-deteccion-notas-guitarra-limpia/contracts/deteccion.md` para
el contrato completo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import mirdata

# ---------------------------------------------------------------------
# Tipos de dominio (T005) -- todos inmutables: son el resultado de una
# única operación de lectura, sin ciclo de vida propio (data-model.md).
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class NotaReferencia:
    """Una nota anotada por GuitarSet (`Track.notes_all`, research.md #7).

    `tono_midi` puede ser fraccionario -- GuitarSet anota afinación real,
    no cuantizada a semitono entero. `fin_s` no participa del criterio
    de acierto (FR-004), solo de la clasificación de polifonía
    (research.md #8)."""

    tono_midi: float
    inicio_s: float
    fin_s: float


@dataclass(frozen=True)
class LecturaGrabacion:
    """El resultado devuelto por la operación de lectura para una
    grabación de GuitarSet."""

    grabacion_id: str
    ruta_audio: Path
    notas_referencia: list[NotaReferencia] = field(default_factory=list)


# ---------------------------------------------------------------------
# Excepciones del contrato (T005) -- ver contracts/deteccion.md,
# postcondición 2 de `leer_grabacion`.
# ---------------------------------------------------------------------


class GrabacionNoExisteError(Exception):
    """`grabacion_id` no existe en el índice de `mirdata`, o el índice
    está corrupto (contracts/deteccion.md, postcondición 2 de
    `leer_grabacion`) -- nunca una excepción cruda de `mirdata` sin
    envolver."""

    def __init__(self, grabacion_id: str) -> None:
        self.grabacion_id = grabacion_id
        super().__init__(f"La grabación '{grabacion_id}' no existe en el índice de GuitarSet.")


# ---------------------------------------------------------------------
# Precondiciones de arranque (FR-015/FR-016) -- verificadas UNA VEZ antes
# de procesar ninguna grabación, nunca descubiertas a mitad de una
# corrida (research.md #19). Mismo criterio que el hito 1: el pipeline
# falla con mensaje claro si no encuentra el audio, nunca en silencio y
# nunca a mitad -- acá se adelanta el mismo tipo de fallo al arranque en
# vez de esperar a la primera (o a las 288) `leer_grabacion` que lo
# habría descubierto de todos modos, una vez por grabación.
# ---------------------------------------------------------------------


class IndiceMirdataAusenteError(Exception):
    """El índice de `mirdata` para GuitarSet no está disponible (FR-016)
    -- vive en `site-packages/mirdata/datasets/indexes/`, research.md
    #19: una descarga aparte del paquete, independiente de `root_dir`,
    que `pip install`/`uv sync` no trae. Nunca se propaga la excepción
    cruda de `mirdata` (un `FileNotFoundError` con un mensaje genérico) --
    se envuelve con el comando exacto para resolverlo."""

    def __init__(self, causa: Exception) -> None:
        self.causa = causa
        super().__init__(
            "El índice de GuitarSet de mirdata no está disponible -- descargalo con: "
            'python -c "import mirdata; '
            "mirdata.initialize('guitarset').download(partial_download=['index'])\" "
            f"(causa real: {causa})."
        )


def validar_indice_mirdata() -> None:
    """Verifica, ANTES de procesar ninguna grabación (FR-016), que el
    índice de GuitarSet de `mirdata` está disponible -- independiente de
    `root_dir` (research.md #19: el índice vive en `site-packages`, no
    bajo la raíz de datos). `dataset.track_ids` es la misma propiedad que
    `construir_lista_grabaciones` ya necesita -- si el índice falta, MUST
    fallar aquí, con un mensaje que diga cómo obtenerlo, no como una
    excepción cruda de `mirdata` más adelante."""
    try:
        _ = mirdata.initialize("guitarset").track_ids
    except Exception as causa:
        raise IndiceMirdataAusenteError(causa) from causa


DIRECTORIOS_REQUERIDOS_GUITARSET = ("annotation", "audio_mono-mic")
"""Los dos directorios que `leer_grabacion` consume de `root_dir`:
`annotation/` (JAMS, `Track.jams_path` -> `notes_all`, research.md #7) y
`audio_mono-mic/` (audio real de micrófono, `Track.audio_mic_path`,
research.md #6) -- verificado contra una distribución real de GuitarSet
en disco, no supuesto por el nombre del dataset."""


class RaizGuitarSetInvalidaError(Exception):
    """`root_dir` no tiene la estructura mínima que GuitarSet debe tener
    (FR-015) -- incidente real: apuntar `--root-dir` a la raíz del
    repositorio en vez de al dataset. El fallo real reproducido
    (research.md #19) es un `FileNotFoundError` SIN ENVOLVER en la
    primera grabación (no 288 exclusiones repetidas, como se reportó de
    entrada) -- en cualquiera de las dos formas, el defecto de fondo es
    el mismo: nada valida `root_dir` antes de arrancar. Nunca una
    excepción cruda de `mirdata`/`FileNotFoundError` -- MUST decir
    explícitamente qué directorio falta."""

    def __init__(self, root_dir: Path, faltantes: list[str]) -> None:
        self.root_dir = root_dir
        self.faltantes = faltantes
        super().__init__(
            f"'{root_dir}' no es una raíz de GuitarSet válida -- falta: "
            f"{', '.join(faltantes)}. GuitarSet debe tener 'annotation/' (anotaciones "
            "JAMS) y 'audio_mono-mic/' (audio de micrófono) bajo esta ruta."
        )


def validar_raiz_guitarset(root_dir: Path) -> None:
    """Verifica, ANTES de procesar ninguna grabación (FR-015), que
    `root_dir` contiene los directorios que `leer_grabacion` consume --
    `annotation/` y `audio_mono-mic/`, ambos como DIRECTORIO (no un
    archivo suelto con ese nombre, que pasaría este chequeo sin poder
    servir ninguna grabación real). MUST NOT invocar `mirdata`: el
    objetivo es fallar sobre `root_dir` en sí, independiente de si algún
    `grabacion_id` particular existe en el índice (eso ya lo cubre
    `GrabacionNoExisteError`, por grabación)."""
    faltantes = [
        nombre for nombre in DIRECTORIOS_REQUERIDOS_GUITARSET if not (root_dir / nombre).is_dir()
    ]
    if faltantes:
        raise RaizGuitarSetInvalidaError(root_dir, faltantes)


# ---------------------------------------------------------------------
# leer_grabacion (T012) -- lectura real vía mirdata, contracts/deteccion.md.
# ---------------------------------------------------------------------


def leer_grabacion(grabacion_id: str, root_dir: Path) -> LecturaGrabacion:
    """Lee la grabación `grabacion_id` de GuitarSet bajo `root_dir` vía
    `mirdata` (contracts/deteccion.md).

    `root_dir` es la raíz de una distribución de GuitarSet ya presente en
    disco (audio + anotaciones JAMS) -- este proyecto no descarga datos
    (constitución Principio IV).

    Lanza `GrabacionNoExisteError` si `grabacion_id` no existe en el
    índice de `mirdata`, o si el índice está corrupto -- nunca deja
    propagar una excepción cruda de `mirdata` sin envolver.
    """
    dataset = mirdata.initialize("guitarset", data_home=str(root_dir))
    try:
        track: Any = dataset.track(grabacion_id)
    except Exception as causa:
        raise GrabacionNoExisteError(grabacion_id) from causa

    notes_all = track.notes_all
    if notes_all is None:
        notas_referencia: list[NotaReferencia] = []
    else:
        notas_referencia = [
            NotaReferencia(tono_midi=float(tono), inicio_s=float(inicio), fin_s=float(fin))
            for (inicio, fin), tono in zip(notes_all.intervals, notes_all.pitches, strict=True)
        ]

    return LecturaGrabacion(
        grabacion_id=grabacion_id,
        ruta_audio=Path(track.audio_mic_path),
        notas_referencia=notas_referencia,
    )


# ---------------------------------------------------------------------
# leer_grabacion_con_posicion_real (Feature 007, T018) -- posición REAL
# anotada por cuerda (`track.notes`, research.md #5 de esa feature),
# NUNCA `notes_all` (pooleada, sin cuerda -- lo que `leer_grabacion`
# usa arriba). `leer_grabacion()` no se toca.
# ---------------------------------------------------------------------

MIDI_CUERDA_ABIERTA: dict[str, int] = {"E": 40, "A": 45, "D": 50, "G": 55, "B": 59, "e": 64}
"""Mismo valor que `analytics.metrica_digitacion.ModeloCoste.midi_cuerda_abierta`
por defecto (research.md #3 de la Feature 007) -- declarado aparte, no
importado de ahí: `ingestion` no puede importar `analytics` sin invertir
las capas (research.md #11 del hito 2). La coincidencia de valor es
intencional, misma fuente real de afinación de GuitarSet -- no una copia
sin mirar."""


@dataclass(frozen=True)
class NotaConPosicionReal:
    """Una nota anotada por GuitarSet junto con la posición REAL que el
    guitarrista usó (`cuerda_real`, `traste_real`) -- fuente de verdad
    exclusiva de User Story 3 de la Feature 007, NUNCA usada para decidir
    qué posición asignar (`analytics.metrica_digitacion.asignar_secuencia`
    no la recibe: sería circular, FR-007)."""

    tono_midi: float
    inicio_s: float
    fin_s: float
    cuerda_real: str
    traste_real: int


def leer_grabacion_con_posicion_real(
    grabacion_id: str, root_dir: Path
) -> list[NotaConPosicionReal]:
    """Lee la posición real (cuerda, traste) que GuitarSet anota para
    cada nota de `grabacion_id`, vía `track.notes` (`dict[str, NoteData]`,
    una entrada por cuerda -- research.md #5 de la Feature 007,
    contracts/digitacion.md postcondición 1 de
    `leer_grabacion_con_posicion_real`).

    `traste_real` se DERIVA (`round(tono_midi - MIDI_CUERDA_ABIERTA[cuerda])`)
    -- GuitarSet no anota traste directamente. La lista final queda
    ordenada por `inicio_s`, aunque las seis listas por cuerda no vengan
    ordenadas entre sí.

    Lanza `GrabacionNoExisteError` en las mismas condiciones que
    `leer_grabacion` -- el mismo tipo, nunca una excepción cruda de
    `mirdata` sin envolver.
    """
    dataset = mirdata.initialize("guitarset", data_home=str(root_dir))
    try:
        track: Any = dataset.track(grabacion_id)
    except Exception as causa:
        raise GrabacionNoExisteError(grabacion_id) from causa

    notas: list[NotaConPosicionReal] = []
    for cuerda, note_data in track.notes.items():
        if note_data is None:
            continue
        abierta = MIDI_CUERDA_ABIERTA[cuerda]
        for (inicio, fin), tono in zip(note_data.intervals, note_data.pitches, strict=True):
            notas.append(
                NotaConPosicionReal(
                    tono_midi=float(tono),
                    inicio_s=float(inicio),
                    fin_s=float(fin),
                    cuerda_real=cuerda,
                    traste_real=round(float(tono) - abierta),
                )
            )
    notas.sort(key=lambda n: n.inicio_s)
    return notas
