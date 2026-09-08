"""Tests unitarios de los tipos de dominio de `ingestion.guitarset`
(Foundational, `specs/006-deteccion-notas-guitarra-limpia/tasks.md`,
T005).

No prueba `leer_grabacion()` -- todavía no existe en este slice (User
Story 2, T012).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from guitar_tabs_analysis.ingestion.guitarset import (
    GrabacionNoExisteError,
    LecturaGrabacion,
    NotaReferencia,
)


def test_nota_referencia_expone_sus_campos() -> None:
    nota = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)
    assert nota.tono_midi == 60.0
    assert nota.inicio_s == 1.0
    assert nota.fin_s == 1.5


def test_nota_referencia_es_inmutable() -> None:
    nota = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)
    with pytest.raises(dataclasses.FrozenInstanceError):
        nota.tono_midi = 61.0  # type: ignore[misc]


def test_lectura_grabacion_agrupa_ruta_y_notas() -> None:
    nota = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)
    lectura = LecturaGrabacion(
        grabacion_id="00_BN1-129-Eb_comp",
        ruta_audio=Path("/datos/guitarset/audio_mic/00_BN1-129-Eb_comp_mic.wav"),
        notas_referencia=[nota],
    )
    assert lectura.grabacion_id == "00_BN1-129-Eb_comp"
    assert lectura.ruta_audio == Path("/datos/guitarset/audio_mic/00_BN1-129-Eb_comp_mic.wav")
    assert lectura.notas_referencia == [nota]


def test_lectura_grabacion_notas_referencia_vacia_por_defecto() -> None:
    lectura = LecturaGrabacion(grabacion_id="00_BN1-129-Eb_comp", ruta_audio=Path("/x.wav"))
    assert lectura.notas_referencia == []


def test_grabacion_no_existe_error_expone_mensaje_completo() -> None:
    error = GrabacionNoExisteError("99_inexistente")
    assert error.grabacion_id == "99_inexistente"
    assert str(error) == "La grabación '99_inexistente' no existe en el índice de GuitarSet."
