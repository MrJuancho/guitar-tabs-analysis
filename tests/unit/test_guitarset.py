"""Tests unitarios de `ingestion.guitarset`: los tipos de dominio
(Foundational, T005) y `leer_grabacion()` (User Story 2, T012-T013), con el
índice/`Track` de `mirdata` reemplazado por `monkeypatch` -- NUNCA se
descarga GuitarSet real (constitución Principio IV).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest

from guitar_tabs_analysis.ingestion import guitarset
from guitar_tabs_analysis.ingestion.guitarset import (
    GrabacionNoExisteError,
    LecturaGrabacion,
    NotaReferencia,
    leer_grabacion,
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


# ---------------------------------------------------------------------
# leer_grabacion (T012-T013) -- índice/Track de mirdata reemplazados por
# monkeypatch, nunca GuitarSet real (constitución Principio IV).
# ---------------------------------------------------------------------


class _NoteDataFalso:
    """Sustituto mínimo de `mirdata.annotations.NoteData` -- solo los dos
    atributos que `leer_grabacion` lee (`intervals`, `pitches`)."""

    def __init__(self, intervals: np.ndarray, pitches: np.ndarray) -> None:
        self.intervals = intervals
        self.pitches = pitches


class _TrackFalso:
    """Sustituto mínimo de `mirdata.datasets.guitarset.Track` -- solo los
    dos atributos que `leer_grabacion` lee (`audio_mic_path`,
    `notes_all`)."""

    def __init__(self, audio_mic_path: str, notes_all: _NoteDataFalso | None) -> None:
        self.audio_mic_path = audio_mic_path
        self.notes_all = notes_all


class _DatasetFalso:
    """Sustituto mínimo de `mirdata.core.Dataset` -- solo `.track()`,
    con la misma semántica real (`ValueError` para un `track_id`
    inexistente, verificado contra `mirdata.core.Track.__init__`)."""

    def __init__(self, tracks: dict[str, _TrackFalso]) -> None:
        self._tracks = tracks

    def track(self, track_id: str) -> _TrackFalso:
        if track_id not in self._tracks:
            raise ValueError(f"{track_id} is not a valid track_id in guitarset")
        return self._tracks[track_id]


def _monkeypatch_mirdata(
    monkeypatch: pytest.MonkeyPatch, dataset: _DatasetFalso, llamadas: list[str] | None = None
) -> None:
    def _initialize_falso(nombre: str, data_home: str) -> _DatasetFalso:
        assert nombre == "guitarset"
        if llamadas is not None:
            llamadas.append(data_home)
        return dataset

    monkeypatch.setattr(guitarset.mirdata, "initialize", _initialize_falso)


def test_leer_grabacion_existente_usa_audio_mic_y_notes_all(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Postcondición 1 de contracts/deteccion.md: `ruta_audio` viene de
    `audio_mic` (nunca `audio_mix`), `notas_referencia` de `notes_all`."""
    notes_all = _NoteDataFalso(
        intervals=np.array([[1.0, 1.5], [2.0, 2.25]]),
        pitches=np.array([60.0, 64.0]),
    )
    track = _TrackFalso(
        audio_mic_path="/datos/audio_mono-mic/00_BN1-129-Eb_comp_mic.wav",
        notes_all=notes_all,
    )
    dataset = _DatasetFalso({"00_BN1-129-Eb_comp": track})
    _monkeypatch_mirdata(monkeypatch, dataset)

    lectura = leer_grabacion("00_BN1-129-Eb_comp", tmp_path)

    assert lectura.grabacion_id == "00_BN1-129-Eb_comp"
    assert lectura.ruta_audio == Path("/datos/audio_mono-mic/00_BN1-129-Eb_comp_mic.wav")
    assert lectura.notas_referencia == [
        NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.5),
        NotaReferencia(tono_midi=64.0, inicio_s=2.0, fin_s=2.25),
    ]


def test_leer_grabacion_sin_ninguna_nota_devuelve_lista_vacia(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`Track.notes_all` es `None` cuando ninguna cuerda tiene notas
    anotadas (`mirdata.datasets.guitarset.load_notes` devuelve `None`)."""
    track = _TrackFalso(audio_mic_path="/datos/audio_mono-mic/silencio_mic.wav", notes_all=None)
    dataset = _DatasetFalso({"silencio": track})
    _monkeypatch_mirdata(monkeypatch, dataset)

    lectura = leer_grabacion("silencio", tmp_path)

    assert lectura.notas_referencia == []


def test_leer_grabacion_inexistente_levanta_grabacion_no_existe_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Postcondición 2 de contracts/deteccion.md: nunca una excepción
    cruda de `mirdata` sin envolver."""
    dataset = _DatasetFalso({})
    _monkeypatch_mirdata(monkeypatch, dataset)

    with pytest.raises(GrabacionNoExisteError) as excinfo:
        leer_grabacion("99_inexistente", tmp_path)

    assert excinfo.value.grabacion_id == "99_inexistente"
    assert (
        str(excinfo.value) == "La grabación '99_inexistente' no existe en el índice de GuitarSet."
    )


def test_leer_grabacion_pasa_root_dir_como_data_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`root_dir` (la raíz local de la distribución de GuitarSet ya
    presente en disco, precondición de contracts/deteccion.md) debe
    llegar tal cual a `mirdata.initialize` -- nunca `None` ni una ruta
    distinta, que haría que `mirdata` mirara la ubicación por defecto en
    vez de los datos locales del proyecto."""
    llamadas: list[str] = []
    track = _TrackFalso(audio_mic_path="/datos/x_mic.wav", notes_all=None)
    dataset = _DatasetFalso({"grabacion": track})
    _monkeypatch_mirdata(monkeypatch, dataset, llamadas)

    leer_grabacion("grabacion", tmp_path)

    assert llamadas == [str(tmp_path)]


def test_leer_grabacion_intervals_y_pitches_de_distinta_longitud_falla(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`Track.notes_all.intervals`/`.pitches` deben tener siempre la
    misma longitud (invariante de `mirdata.annotations.NoteData`,
    verificado contra su código fuente real) -- `leer_grabacion` no debe
    emparejar en silencio un intervalo con el tono equivocado si alguna
    vez esa invariante se rompiera (`zip(..., strict=True)`)."""
    notes_all = _NoteDataFalso(
        intervals=np.array([[1.0, 1.5], [2.0, 2.25]]),
        pitches=np.array([60.0]),
    )
    track = _TrackFalso(audio_mic_path="/datos/x_mic.wav", notes_all=notes_all)
    dataset = _DatasetFalso({"grabacion": track})
    _monkeypatch_mirdata(monkeypatch, dataset)

    with pytest.raises(ValueError, match="zip"):
        leer_grabacion("grabacion", tmp_path)
