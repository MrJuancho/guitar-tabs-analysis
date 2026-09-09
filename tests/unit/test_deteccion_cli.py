"""Tests de `deteccion.cli` (T033 de `specs/006-deteccion-notas-guitarra-limpia/tasks.md`,
Fase 7): el modo se elige explícitamente, sin valor por defecto -- invocar
sin `--modo`, o con un `--modo` inválido (o sin `--root-dir`), falla ANTES
de construir ningún `BasicPitchTranscriptor` real (que invoca un
subproceso Python 3.10, research.md #15). Mismo patrón exacto que
`tests/unit/test_cli.py` del hito 1 (Feature 004, T027).
"""

from __future__ import annotations

import json
from pathlib import Path

import mirdata
import numpy as np
import pytest

from guitar_tabs_analysis.analytics.metrica_deteccion_notas import ResultadoSubconjunto
from guitar_tabs_analysis.deteccion import cli
from guitar_tabs_analysis.deteccion.orquestador import ArtefactoDeteccion
from guitar_tabs_analysis.transcripcion.transcriptor import ModeloTranscripcionDeclarado
from tests.fixtures.transcriptor_fixture import MODELO_FALSO, TranscriptorFalso


def _fallar_si_se_construye() -> None:
    raise AssertionError(
        "BasicPitchTranscriptor no debería construirse sin un --modo/--root-dir "
        "válidos -- el error de argparse tiene que ocurrir antes."
    )


def test_sin_modo_falla_con_mensaje_claro_antes_de_construir_transcriptor(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "BasicPitchTranscriptor", _fallar_si_se_construye)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--root-dir", "/cualquier/ruta"])

    assert excinfo.value.code != 0
    mensaje = capsys.readouterr().err
    assert "--modo" in mensaje
    assert "required" in mensaje  # argparse: "the following arguments are required: --modo"


def test_modo_invalido_falla_con_mensaje_claro_antes_de_construir_transcriptor(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "BasicPitchTranscriptor", _fallar_si_se_construye)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--modo", "no_existe", "--root-dir", "/cualquier/ruta"])

    assert excinfo.value.code != 0
    mensaje = capsys.readouterr().err
    assert "--modo" in mensaje


def test_sin_root_dir_falla_con_mensaje_claro(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "BasicPitchTranscriptor", _fallar_si_se_construye)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--modo", "medibles"])

    assert excinfo.value.code != 0
    mensaje = capsys.readouterr().err
    assert "--root-dir" in mensaje


# ---------------------------------------------------------------------
# escribir_artefacto (T032b) -- mismo mecanismo exacto que
# medicion.cli.escribir_artefacto/EscrituraIncompletaError.
# ---------------------------------------------------------------------


_SUBCONJUNTO_VACIO = ResultadoSubconjunto(
    precision=None,
    exhaustividad=None,
    balance_f1=None,
    num_notas_referencia=0,
    num_notas_estimadas=0,
)


def _artefacto_de_prueba() -> ArtefactoDeteccion:
    return ArtefactoDeteccion(
        modelo=ModeloTranscripcionDeclarado(
            nombre="Basic Pitch",
            variante="icassp_2022",
            firma="3db297d5",
            backend="tflite",
            licencia="Apache-2.0 -- solo para tests",
        ),
        tolerancia_tono_cents=50.0,
        ventana_inicio_s=0.05,
        grabaciones=["00_BN1-129-Eb_comp"],
        exclusiones=[],
        resultados_por_grabacion=[],
        global_=_SUBCONJUNTO_VACIO,
        monofonico=_SUBCONJUNTO_VACIO,
        polifonico=_SUBCONJUNTO_VACIO,
    )


def test_escribir_artefacto_produce_json_valido_y_legible(tmp_path: Path) -> None:
    ruta = tmp_path / "mediciones" / "deteccion_medibles.json"
    artefacto = _artefacto_de_prueba()

    cli.escribir_artefacto(ruta, artefacto)

    contenido = json.loads(ruta.read_text())
    assert contenido["grabaciones"] == ["00_BN1-129-Eb_comp"]


def test_escribir_artefacto_es_atomico_no_deja_archivo_final_truncado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "mediciones" / "deteccion_medibles.json"
    artefacto = _artefacto_de_prueba()

    def _os_replace_que_falla(origen: object, destino: object) -> None:
        raise OSError("interrupción simulada entre escribir el temporal y renombrarlo")

    monkeypatch.setattr(cli.os, "replace", _os_replace_que_falla)

    with pytest.raises(OSError):
        cli.escribir_artefacto(ruta, artefacto)

    assert not ruta.exists()


def test_escribir_artefacto_falla_cerrado_si_os_replace_no_mueve_nada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "mediciones" / "deteccion_medibles.json"
    artefacto = _artefacto_de_prueba()

    monkeypatch.setattr(cli.os, "replace", lambda origen, destino: None)

    with pytest.raises(cli.EscrituraIncompletaError):
        cli.escribir_artefacto(ruta, artefacto)

    assert not ruta.exists()


def test_escribir_artefacto_falla_cerrado_si_deja_un_artefacto_viejo_a_medias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "mediciones" / "deteccion_medibles.json"
    ruta.parent.mkdir(parents=True)
    ruta.write_text(json.dumps({"grabaciones": []}))
    artefacto = _artefacto_de_prueba()  # grabaciones=["00_BN1-129-Eb_comp"], otra longitud

    monkeypatch.setattr(cli.os, "replace", lambda origen, destino: None)

    with pytest.raises(cli.EscrituraIncompletaError):
        cli.escribir_artefacto(ruta, artefacto)


# ---------------------------------------------------------------------
# _ejecutar_y_escribir (T032b) -- de punta a punta con TranscriptorFalso
# y el índice de mirdata monkeypatcheado (nunca GuitarSet real).
# ---------------------------------------------------------------------


class _NoteDataFalso:
    def __init__(self, intervals: np.ndarray, pitches: np.ndarray) -> None:
        self.intervals = intervals
        self.pitches = pitches


class _TrackFalso:
    def __init__(self, audio_mic_path: str, notes_all: _NoteDataFalso | None) -> None:
        self.audio_mic_path = audio_mic_path
        self.notes_all = notes_all


class _DatasetFalso:
    """Sustituto de `mirdata.core.Dataset` con `.track_ids` (que usa
    `construir_lista_grabaciones`) y `.track()` (que usa `leer_grabacion`)."""

    def __init__(self, tracks: dict[str, _TrackFalso]) -> None:
        self._tracks = tracks
        self.track_ids = sorted(tracks.keys())

    def track(self, track_id: str) -> _TrackFalso:
        if track_id not in self._tracks:
            raise ValueError(f"{track_id} is not a valid track_id in guitarset")
        return self._tracks[track_id]


def _monkeypatch_mirdata(monkeypatch: pytest.MonkeyPatch, dataset: _DatasetFalso) -> None:
    """Un único monkeypatch sobre el módulo `mirdata` real cubre tanto
    `deteccion.orquestador.mirdata` como `ingestion.guitarset.mirdata` --
    ambos son el mismo objeto módulo (`sys.modules['mirdata']`), así que
    parchear su atributo `initialize` una vez alcanza para las dos rutas
    de llamada (`construir_lista_grabaciones` y `leer_grabacion`)."""

    def _initialize_falso(nombre: str, data_home: str) -> _DatasetFalso:
        assert nombre == "guitarset"
        return dataset

    monkeypatch.setattr(mirdata, "initialize", _initialize_falso)


def test_ejecutar_y_escribir_produce_artefacto_en_disco(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    track = _TrackFalso(
        audio_mic_path="/datos/grabacion_000_mic.wav",
        notes_all=_NoteDataFalso(intervals=np.array([[0.0, 0.5]]), pitches=np.array([60.0])),
    )
    dataset = _DatasetFalso({"grabacion_000": track})
    _monkeypatch_mirdata(monkeypatch, dataset)
    transcriptor = TranscriptorFalso(
        modelo_declarado=MODELO_FALSO,
    )
    ruta_artefacto = tmp_path / "mediciones" / "deteccion_medibles.json"

    codigo = cli._ejecutar_y_escribir("medibles", tmp_path, transcriptor, ruta_artefacto)

    assert codigo == 0
    contenido = json.loads(ruta_artefacto.read_text())
    assert contenido["grabaciones"] == ["grabacion_000"]
    assert contenido["modelo"]["nombre"] == "ModeloFalso"
