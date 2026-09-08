"""Lectura de una grabación de GuitarSet (capa `ingestion`, nivel más
bajo del contrato de import-linter): tipos de dominio para la anotación
de referencia de una grabación de guitarra limpia.

Este módulo, en su estado actual (T005 de
`specs/006-deteccion-notas-guitarra-limpia/tasks.md`), cubre solo los
tipos que User Story 1 necesita (`NotaReferencia`, `LecturaGrabacion`,
`GrabacionNoExisteError`) -- todavía SIN la función `leer_grabacion()`
real vía `mirdata` (User Story 2, T012). Este módulo no importa
`transcripcion` ni `analytics`.

Ver `specs/006-deteccion-notas-guitarra-limpia/data-model.md` y
`specs/006-deteccion-notas-guitarra-limpia/contracts/deteccion.md` para
el contrato completo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

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
