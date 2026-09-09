"""Tests unitarios de `transcripcion.basic_pitch_transcriptor` -- con
`subprocess.run` reemplazado por `monkeypatch`, nunca el entorno Python
3.10 real (research.md #15 de
`specs/006-deteccion-notas-guitarra-limpia/`). Rápidos, corren en `just
gauntlet` -- el test que sí invoca el subproceso real es
`tests/integration/test_basic_pitch_modelo_real_integracion.py`, marcado
`modelo_real`.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from guitar_tabs_analysis.analytics.metrica_deteccion_notas import NotaEstimada
from guitar_tabs_analysis.transcripcion import basic_pitch_transcriptor
from guitar_tabs_analysis.transcripcion.basic_pitch_transcriptor import (
    MODELO_DECLARADO,
    BasicPitchTranscriptor,
)
from guitar_tabs_analysis.transcripcion.transcriptor import TranscripcionFallidaError


def _completado(
    returncode: int, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def test_codigo_de_salida_distinto_de_cero_levanta_transcripcion_fallida(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def _run_falso(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return _completado(returncode=1, stderr="fallo real de inferencia")

    monkeypatch.setattr(basic_pitch_transcriptor.subprocess, "run", _run_falso)
    ruta_audio = tmp_path / "clip.wav"
    transcriptor = BasicPitchTranscriptor()

    with pytest.raises(TranscripcionFallidaError) as excinfo:
        transcriptor.transcribir(ruta_audio)

    assert str(ruta_audio) in str(excinfo.value)
    assert excinfo.value.ruta_audio == ruta_audio


def test_archivo_de_salida_ausente_pese_a_codigo_cero_levanta_transcripcion_fallida(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def _run_falso(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        # returncode 0 pero nunca escribe el archivo de salida -- simula
        # una falla a medio escribir que el código de salida por sí solo
        # no distingue.
        return _completado(returncode=0)

    monkeypatch.setattr(basic_pitch_transcriptor.subprocess, "run", _run_falso)
    ruta_audio = tmp_path / "clip.wav"
    transcriptor = BasicPitchTranscriptor()

    with pytest.raises(TranscripcionFallidaError) as excinfo:
        transcriptor.transcribir(ruta_audio)

    assert excinfo.value.ruta_audio == ruta_audio


def test_json_malformado_levanta_transcripcion_fallida(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def _run_falso(
        args: list[str], capture_output: bool, text: bool
    ) -> subprocess.CompletedProcess[str]:
        ruta_salida = Path(args[3])
        ruta_salida.write_text("esto no es JSON válido{", encoding="utf-8")
        return _completado(returncode=0)

    monkeypatch.setattr(basic_pitch_transcriptor.subprocess, "run", _run_falso)
    ruta_audio = tmp_path / "clip.wav"
    transcriptor = BasicPitchTranscriptor()

    with pytest.raises(TranscripcionFallidaError) as excinfo:
        transcriptor.transcribir(ruta_audio)

    assert excinfo.value.ruta_audio == ruta_audio


def test_camino_feliz_devuelve_notas_estimadas_y_limpia_el_temporal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    rutas_de_salida_usadas: list[Path] = []

    def _run_falso(
        args: list[str], capture_output: bool, text: bool
    ) -> subprocess.CompletedProcess[str]:
        ruta_salida = Path(args[3])
        rutas_de_salida_usadas.append(ruta_salida)
        ruta_salida.write_text(
            json.dumps(
                [
                    {"tono_midi": 60.0, "inicio_s": 0.1, "fin_s": 0.5},
                    {"tono_midi": 64.0, "inicio_s": 0.6, "fin_s": 1.0},
                ]
            ),
            encoding="utf-8",
        )
        return _completado(returncode=0)

    monkeypatch.setattr(basic_pitch_transcriptor.subprocess, "run", _run_falso)
    ruta_audio = tmp_path / "clip.wav"
    transcriptor = BasicPitchTranscriptor()

    notas = transcriptor.transcribir(ruta_audio)

    assert notas == [
        NotaEstimada(tono_midi=60.0, inicio_s=0.1, fin_s=0.5),
        NotaEstimada(tono_midi=64.0, inicio_s=0.6, fin_s=1.0),
    ]
    assert len(rutas_de_salida_usadas) == 1
    assert not rutas_de_salida_usadas[0].exists(), (
        "el archivo/directorio temporal debe quedar limpiado tras el camino feliz"
    )


def test_modelo_declarado_tiene_los_valores_verificados() -> None:
    assert MODELO_DECLARADO.nombre == "Basic Pitch"
    assert MODELO_DECLARADO.variante == "icassp_2022"
    assert MODELO_DECLARADO.backend == "tflite"
    assert MODELO_DECLARADO.licencia == "Apache-2.0 (código y pesos) -- ver docs/ATRIBUCIONES.md"


def test_basic_pitch_transcriptor_expone_el_modelo_declarado() -> None:
    transcriptor = BasicPitchTranscriptor()
    assert transcriptor.modelo_declarado is MODELO_DECLARADO
