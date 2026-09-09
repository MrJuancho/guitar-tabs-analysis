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
