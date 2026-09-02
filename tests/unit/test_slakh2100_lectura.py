"""Tests unitarios para los tipos, excepciones y helpers de E/S del
módulo `ingestion.slakh2100` (T003, T005, T006 de
`specs/001-lectura-tema-slakh2100/tasks.md`).

No prueba `leer_tema()` en sí -- esa función (y sus tests de
clasificación guitarra/bajo, colección vacía, discrepancia de longitud)
es la Fase 3-5 (T007 en adelante) de `tasks.md`, fuera del alcance de
este archivo por ahora. Este archivo lo seguirán llenando T010/T015 en
sesiones futuras.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from guitar_tabs_analysis.ingestion.slakh2100 import (
    ArchivoAudioNoLegibleError,
    LecturaTema,
    LongitudInconsistenteError,
    PistaAudio,
    PistaGuitarra,
    TemaNoExisteError,
    _decodificar_audio,
    _leer_metadata,
)
from tests.fixtures.slakh2100_fixture import EspecificacionStem, construir_tema_sintetico

# ---------------------------------------------------------------------
# T003: PistaAudio, PistaGuitarra, LecturaTema y las tres excepciones.
# ---------------------------------------------------------------------


def test_pista_audio_expone_muestras_y_frecuencia() -> None:
    muestras = np.array([1, -1, 2], dtype=np.int16)
    pista = PistaAudio(muestras=muestras, frecuencia_muestreo=44100)
    assert pista.frecuencia_muestreo == 44100
    np.testing.assert_array_equal(pista.muestras, muestras)


def test_pista_audio_es_inmutable() -> None:
    pista = PistaAudio(muestras=np.array([1], dtype=np.int16), frecuencia_muestreo=44100)
    with pytest.raises(dataclasses.FrozenInstanceError):
        pista.frecuencia_muestreo = 22050  # type: ignore[misc]


def test_pista_guitarra_expone_identificador_y_audio() -> None:
    audio = PistaAudio(muestras=np.array([1], dtype=np.int16), frecuencia_muestreo=44100)
    pista = PistaGuitarra(identificador_origen="S01", audio=audio)
    assert pista.identificador_origen == "S01"
    assert pista.audio is audio


def test_pista_guitarra_es_inmutable() -> None:
    audio = PistaAudio(muestras=np.array([1], dtype=np.int16), frecuencia_muestreo=44100)
    pista = PistaGuitarra(identificador_origen="S01", audio=audio)
    with pytest.raises(dataclasses.FrozenInstanceError):
        pista.identificador_origen = "S02"  # type: ignore[misc]


def test_lectura_tema_agrupa_mezcla_y_guitarras() -> None:
    mezcla = PistaAudio(muestras=np.array([1, 2], dtype=np.int16), frecuencia_muestreo=44100)
    guitarra = PistaGuitarra(
        identificador_origen="S01",
        audio=PistaAudio(muestras=np.array([1, 2], dtype=np.int16), frecuencia_muestreo=44100),
    )
    lectura = LecturaTema(tema_id="Track00001", mezcla=mezcla, guitarras=[guitarra])
    assert lectura.tema_id == "Track00001"
    assert lectura.mezcla is mezcla
    assert lectura.guitarras == [guitarra]


def test_lectura_tema_acepta_coleccion_vacia_de_guitarras() -> None:
    mezcla = PistaAudio(muestras=np.array([1, 2], dtype=np.int16), frecuencia_muestreo=44100)
    lectura = LecturaTema(tema_id="Track00002", mezcla=mezcla, guitarras=[])
    assert lectura.guitarras == []


def test_lectura_tema_es_inmutable() -> None:
    mezcla = PistaAudio(muestras=np.array([1], dtype=np.int16), frecuencia_muestreo=44100)
    lectura = LecturaTema(tema_id="Track00001", mezcla=mezcla, guitarras=[])
    with pytest.raises(dataclasses.FrozenInstanceError):
        lectura.tema_id = "Track00002"  # type: ignore[misc]


def test_tema_no_existe_error_incluye_el_identificador() -> None:
    error = TemaNoExisteError("Track99999")
    assert error.tema_id == "Track99999"
    assert "Track99999" in str(error)


def test_archivo_audio_no_legible_error_incluye_tema_y_archivo() -> None:
    error = ArchivoAudioNoLegibleError("Track00001", "stems/S01.flac")
    assert error.tema_id == "Track00001"
    assert error.archivo == "stems/S01.flac"
    assert "Track00001" in str(error)
    assert "stems/S01.flac" in str(error)


def test_longitud_inconsistente_error_incluye_tema_y_pista() -> None:
    error = LongitudInconsistenteError("Track00001", "S01")
    assert error.tema_id == "Track00001"
    assert error.identificador_origen == "S01"
    assert "Track00001" in str(error)
    assert "S01" in str(error)


# ---------------------------------------------------------------------
# T005: _leer_metadata (parseo de metadata.yaml con PyYAML).
# ---------------------------------------------------------------------


def test_leer_metadata_expone_inst_class_y_audio_rendered_por_stem(tmp_path: Path) -> None:
    root_dir = construir_tema_sintetico(
        tmp_path,
        tema_id="Track00010",
        stems=(
            EspecificacionStem(identificador="S01", inst_class="Guitar", audio_rendered=True),
            EspecificacionStem(identificador="S02", inst_class="Bass", audio_rendered=False),
        ),
    )

    metadata = _leer_metadata(root_dir / "Track00010")

    assert metadata["stems"]["S01"]["inst_class"] == "Guitar"
    assert metadata["stems"]["S01"]["audio_rendered"] is True
    assert metadata["stems"]["S02"]["inst_class"] == "Bass"
    assert metadata["stems"]["S02"]["audio_rendered"] is False


def test_leer_metadata_de_tema_sin_stems_devuelve_diccionario_vacio_de_stems(
    tmp_path: Path,
) -> None:
    root_dir = construir_tema_sintetico(tmp_path, tema_id="Track00011", stems=())

    metadata = _leer_metadata(root_dir / "Track00011")

    assert metadata["stems"] == {}


def test_leer_metadata_lanza_si_el_archivo_no_existe(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        _leer_metadata(tmp_path / "TrackInexistente")


# ---------------------------------------------------------------------
# T006: _decodificar_audio (soundfile, dtype nativo, sin reescalado).
# ---------------------------------------------------------------------


def test_decodificar_audio_conserva_dtype_y_muestras_sin_reescalar(tmp_path: Path) -> None:
    muestras_originales = np.array([0, 1, -1, 32767, -32768], dtype=np.int16)
    ruta = tmp_path / "pista.flac"
    sf.write(str(ruta), muestras_originales, 44100, subtype="PCM_16")

    pista = _decodificar_audio(ruta)

    assert pista.frecuencia_muestreo == 44100
    assert pista.muestras.dtype == np.int16
    np.testing.assert_array_equal(pista.muestras, muestras_originales)


def test_decodificar_audio_respeta_la_frecuencia_de_muestreo_del_archivo(tmp_path: Path) -> None:
    muestras = np.array([1, 2, 3], dtype=np.int16)
    ruta = tmp_path / "pista_22050.flac"
    sf.write(str(ruta), muestras, 22050, subtype="PCM_16")

    pista = _decodificar_audio(ruta)

    assert pista.frecuencia_muestreo == 22050


def test_decodificar_audio_lanza_sin_traducir_si_el_archivo_no_existe(tmp_path: Path) -> None:
    with pytest.raises(sf.LibsndfileError):
        _decodificar_audio(tmp_path / "no_existe.flac")
