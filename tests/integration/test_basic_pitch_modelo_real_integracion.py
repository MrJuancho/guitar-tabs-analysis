"""Único test de esta feature marcado `@pytest.mark.modelo_real`
(research.md #15 de `specs/006-deteccion-notas-guitarra-limpia/`):
ejercita `BasicPitchTranscriptor` real de punta a punta, subproceso real
incluido -- nunca mockeado -- sobre un clip sintético corto. Se salta,
con motivo específico, si `envs/basic_pitch_py310/` no existe o no está
sincronizado (sin `just doctor` corrido antes) -- el hook de
`tests/conftest.py` hace que ese salto nunca pase desapercibido, mismo
patrón que `tests/integration/test_demucs_separador_integracion.py`
(hito 1).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from guitar_tabs_analysis.transcripcion.basic_pitch_transcriptor import (
    PYTHON_ENV,
    BasicPitchTranscriptor,
)


@pytest.fixture(scope="module")
def transcriptor_real() -> Iterator[BasicPitchTranscriptor]:
    if not PYTHON_ENV.exists():
        pytest.skip(
            f"El entorno Python 3.10 de Basic Pitch no existe todavía en '{PYTHON_ENV}' -- "
            "correr 'uv sync' dentro de envs/basic_pitch_py310/ (o 'just doctor')."
        )
    yield BasicPitchTranscriptor()


def _audio_sintetico(tmp_path: Path, frecuencia_hz: float = 440.0, duracion_s: float = 1.0) -> Path:
    """Un seno corto -- no un clip de GuitarSet real (constitución
    Principio IV, mismo criterio que `mezcla_sintetica` del hito 1)."""
    frecuencia_muestreo = 22050
    t = np.arange(int(frecuencia_muestreo * duracion_s), dtype=np.float64) / frecuencia_muestreo
    muestras = 0.5 * np.sin(2 * np.pi * frecuencia_hz * t)
    ruta = tmp_path / "clip-prueba.wav"
    sf.write(str(ruta), muestras, frecuencia_muestreo)
    return ruta


@pytest.mark.modelo_real
def test_transcribir_de_punta_a_punta_sin_excepcion(
    transcriptor_real: BasicPitchTranscriptor, tmp_path: Path
) -> None:
    """AS1 US2: `BasicPitchTranscriptor.transcribir()` real produce una
    lista de `NotaEstimada` (o vacía, US2 AS3) sin lanzar ninguna
    excepción no controlada -- subproceso real incluido."""
    ruta_audio = _audio_sintetico(tmp_path)

    notas = transcriptor_real.transcribir(ruta_audio)

    assert isinstance(notas, list)
    for nota in notas:
        assert isinstance(nota.tono_midi, float)
        assert isinstance(nota.inicio_s, float)
        assert isinstance(nota.fin_s, float)


@pytest.mark.modelo_real
def test_transcribir_un_seno_de_440hz_detecta_la9_o_no_detecta_nada(
    transcriptor_real: BasicPitchTranscriptor, tmp_path: Path
) -> None:
    """Caso de respuesta conocida (research.md #15, verificado en la
    sesión anterior): un seno de 440 Hz produce, si el modelo detecta
    algo, un evento cercano al tono MIDI 69 (A4) -- pero el modelo puede
    legítimamente no detectar nada sobre un tono puro sintético
    (silencio real de su perspectiva, US2 AS3), así que la lista vacía
    también es un resultado válido de este test."""
    ruta_audio = _audio_sintetico(tmp_path, frecuencia_hz=440.0)

    notas = transcriptor_real.transcribir(ruta_audio)

    if not notas:
        pytest.skip("el clip sintético no produjo ninguna nota detectada en esta corrida")
    tonos = [nota.tono_midi for nota in notas]
    assert any(abs(tono - 69.0) <= 1.0 for tono in tonos)
