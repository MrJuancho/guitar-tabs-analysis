"""Tests de integración de `deteccion.orquestador.ejecutar_deteccion`
(User Story 3, T023/T024) -- `_TranscriptorSelectivo` (variante de
`TranscriptorFalso`, T011, que falla según la ruta de audio recibida) y
`leer_grabacion` real con el índice de `mirdata` monkeypatcheado (mismo
mecanismo que T013, `tests/unit/test_guitarset.py`) -- nunca GuitarSet
real (constitución Principio IV).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from guitar_tabs_analysis.analytics.metrica_deteccion_notas import (
    NotaEstimada,
    agregar_conjunto,
)
from guitar_tabs_analysis.deteccion.orquestador import ejecutar_deteccion
from guitar_tabs_analysis.ingestion import guitarset
from guitar_tabs_analysis.transcripcion.transcriptor import TranscripcionFallidaError
from tests.fixtures.transcriptor_fixture import MODELO_FALSO

# ---------------------------------------------------------------------
# Sustitutos mínimos de mirdata -- mismo patrón que
# tests/unit/test_guitarset.py, duplicado aquí (self-contenido, no una
# dependencia nueva entre archivos de test).
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
    def __init__(self, tracks: dict[str, _TrackFalso]) -> None:
        self._tracks = tracks

    def track(self, track_id: str) -> _TrackFalso:
        if track_id not in self._tracks:
            raise ValueError(f"{track_id} is not a valid track_id in guitarset")
        return self._tracks[track_id]


def _monkeypatch_mirdata(monkeypatch: pytest.MonkeyPatch, dataset: _DatasetFalso) -> None:
    def _initialize_falso(nombre: str, data_home: str) -> _DatasetFalso:
        assert nombre == "guitarset"
        return dataset

    monkeypatch.setattr(guitarset.mirdata, "initialize", _initialize_falso)


class _TranscriptorSelectivo:
    """Un `Transcriptor` de prueba cuyo comportamiento depende de la ruta
    de audio recibida -- a diferencia de `TranscriptorFalso` (uniforme
    para todas las invocaciones), necesario para ejercitar FR-012 (una
    grabación falla, las demás no) dentro de una misma corrida."""

    def __init__(
        self,
        fallos: dict[str, Exception],
        notas: dict[str, list[NotaEstimada]],
    ) -> None:
        self.modelo_declarado = MODELO_FALSO
        self._fallos = fallos
        self._notas = notas
        self.rutas_invocadas: list[Path] = []

    def transcribir(self, ruta_audio: Path) -> list[NotaEstimada]:
        self.rutas_invocadas.append(ruta_audio)
        clave = ruta_audio.name
        if clave in self._fallos:
            raise self._fallos[clave]
        return self._notas.get(clave, [])


# ---------------------------------------------------------------------
# T024
# ---------------------------------------------------------------------


def test_ejecutar_deteccion_excluye_grabacion_con_fallo_de_transcripcion_y_sigue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    track_ok = _TrackFalso(
        audio_mic_path="/datos/rec_ok_mic.wav",
        notes_all=_NoteDataFalso(intervals=np.array([[0.0, 0.5]]), pitches=np.array([60.0])),
    )
    track_falla = _TrackFalso(
        audio_mic_path="/datos/rec_falla_mic.wav",
        notes_all=_NoteDataFalso(intervals=np.array([[0.0, 0.5]]), pitches=np.array([64.0])),
    )
    dataset = _DatasetFalso({"rec_ok": track_ok, "rec_falla": track_falla})
    _monkeypatch_mirdata(monkeypatch, dataset)

    ruta_falla = Path("/datos/rec_falla_mic.wav")
    transcriptor = _TranscriptorSelectivo(
        fallos={"rec_falla_mic.wav": TranscripcionFallidaError(ruta_falla, RuntimeError("boom"))},
        notas={"rec_ok_mic.wav": [NotaEstimada(tono_midi=60.0, inicio_s=0.01, fin_s=0.5)]},
    )

    artefacto = ejecutar_deteccion(["rec_ok", "rec_falla"], tmp_path, transcriptor)

    assert len(artefacto.exclusiones) == 1
    assert artefacto.exclusiones[0].grabacion_id == "rec_falla"
    assert "boom" in artefacto.exclusiones[0].detalle
    assert len(artefacto.resultados_por_grabacion) == 2

    resultado_ok = next(r for r in artefacto.resultados_por_grabacion if r.grabacion_id == "rec_ok")
    assert resultado_ok.exclusion is None
    assert resultado_ok.notas_referencia is not None
    assert resultado_ok.notas_estimadas is not None

    resultado_falla = next(
        r for r in artefacto.resultados_por_grabacion if r.grabacion_id == "rec_falla"
    )
    assert resultado_falla.exclusion is not None
    assert resultado_falla.notas_referencia is None
    assert resultado_falla.notas_estimadas is None

    # rec_falla queda fuera del pool: solo la nota de rec_ok participa.
    assert artefacto.global_.num_notas_referencia == 1
    assert artefacto.global_.num_notas_estimadas == 1


def test_ejecutar_deteccion_grabacion_inexistente_se_excluye_y_sigue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    track_ok = _TrackFalso(
        audio_mic_path="/datos/rec_ok_mic.wav",
        notes_all=_NoteDataFalso(intervals=np.array([[0.0, 0.5]]), pitches=np.array([60.0])),
    )
    dataset = _DatasetFalso({"rec_ok": track_ok})
    _monkeypatch_mirdata(monkeypatch, dataset)
    transcriptor = _TranscriptorSelectivo(
        fallos={},
        notas={"rec_ok_mic.wav": [NotaEstimada(tono_midi=60.0, inicio_s=0.01, fin_s=0.5)]},
    )

    artefacto = ejecutar_deteccion(["rec_ok", "rec_no_existe"], tmp_path, transcriptor)

    assert len(artefacto.exclusiones) == 1
    assert artefacto.exclusiones[0].grabacion_id == "rec_no_existe"
    assert (
        artefacto.exclusiones[0].detalle
        == "La grabación 'rec_no_existe' no existe en el índice de GuitarSet."
    )
    resultado_no_existe = next(
        r for r in artefacto.resultados_por_grabacion if r.exclusion is not None
    )
    assert resultado_no_existe.grabacion_id == "rec_no_existe"
    # nunca se invocó el transcriptor para la grabación inexistente --
    # leer_grabacion falla ANTES de llegar a transcribir().
    assert transcriptor.rutas_invocadas == [Path("/datos/rec_ok_mic.wav")]


def test_ejecutar_deteccion_pasa_el_root_dir_correcto_a_leer_grabacion(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    track_ok = _TrackFalso(
        audio_mic_path="/datos/rec_ok_mic.wav",
        notes_all=_NoteDataFalso(intervals=np.array([[0.0, 0.5]]), pitches=np.array([60.0])),
    )
    dataset = _DatasetFalso({"rec_ok": track_ok})
    llamadas_data_home: list[str] = []

    def _initialize_falso(nombre: str, data_home: str) -> _DatasetFalso:
        assert nombre == "guitarset"
        llamadas_data_home.append(data_home)
        return dataset

    monkeypatch.setattr(guitarset.mirdata, "initialize", _initialize_falso)
    transcriptor = _TranscriptorSelectivo(fallos={}, notas={})

    ejecutar_deteccion(["rec_ok"], tmp_path, transcriptor)

    assert llamadas_data_home == [str(tmp_path)]


def test_ejecutar_deteccion_fallo_de_lectura_en_medio_no_detiene_las_siguientes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """FR-012: la grabación inexistente va en el MEDIO de la lista, no al
    final -- si el bucle usara `break` en vez de `continue` al toparse con
    un fallo de lectura (mutation testing, T026), rec3 nunca llegaría a
    procesarse y ningún test lo notaría."""
    track = _TrackFalso(
        audio_mic_path="/datos/rec_mic.wav",
        notes_all=_NoteDataFalso(intervals=np.array([[0.0, 0.5]]), pitches=np.array([60.0])),
    )
    dataset = _DatasetFalso({"rec1": track, "rec3": track})
    _monkeypatch_mirdata(monkeypatch, dataset)
    transcriptor = _TranscriptorSelectivo(
        fallos={},
        notas={"rec_mic.wav": [NotaEstimada(tono_midi=60.0, inicio_s=0.01, fin_s=0.5)]},
    )

    artefacto = ejecutar_deteccion(["rec1", "rec2_no_existe", "rec3"], tmp_path, transcriptor)

    ids_procesados = {
        r.grabacion_id for r in artefacto.resultados_por_grabacion if r.exclusion is None
    }
    assert ids_procesados == {"rec1", "rec3"}
    assert [e.grabacion_id for e in artefacto.exclusiones] == ["rec2_no_existe"]


def test_ejecutar_deteccion_fallo_de_transcripcion_en_medio_no_detiene_las_siguientes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Mismo caso que arriba, pero con el fallo en `transcriptor.transcribir`
    (`TranscripcionFallidaError`) en vez de en `leer_grabacion`."""
    track1 = _TrackFalso(
        audio_mic_path="/datos/rec1_mic.wav",
        notes_all=_NoteDataFalso(intervals=np.array([[0.0, 0.5]]), pitches=np.array([60.0])),
    )
    track2 = _TrackFalso(
        audio_mic_path="/datos/rec2_falla_mic.wav",
        notes_all=_NoteDataFalso(intervals=np.array([[0.0, 0.5]]), pitches=np.array([62.0])),
    )
    track3 = _TrackFalso(
        audio_mic_path="/datos/rec3_mic.wav",
        notes_all=_NoteDataFalso(intervals=np.array([[0.0, 0.5]]), pitches=np.array([64.0])),
    )
    dataset = _DatasetFalso({"rec1": track1, "rec2_falla": track2, "rec3": track3})
    _monkeypatch_mirdata(monkeypatch, dataset)
    transcriptor = _TranscriptorSelectivo(
        fallos={
            "rec2_falla_mic.wav": TranscripcionFallidaError(
                Path("/datos/rec2_falla_mic.wav"), RuntimeError("boom")
            )
        },
        notas={
            "rec1_mic.wav": [NotaEstimada(tono_midi=60.0, inicio_s=0.01, fin_s=0.5)],
            "rec3_mic.wav": [NotaEstimada(tono_midi=64.0, inicio_s=0.01, fin_s=0.5)],
        },
    )

    artefacto = ejecutar_deteccion(["rec1", "rec2_falla", "rec3"], tmp_path, transcriptor)

    ids_procesados = {
        r.grabacion_id for r in artefacto.resultados_por_grabacion if r.exclusion is None
    }
    assert ids_procesados == {"rec1", "rec3"}
    assert [e.grabacion_id for e in artefacto.exclusiones] == ["rec2_falla"]


def test_ejecutar_deteccion_agrega_correctamente_sobre_el_conjunto(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # rec_a: dos notas monofónicas, bien separadas.
    track_a = _TrackFalso(
        audio_mic_path="/datos/rec_a_mic.wav",
        notes_all=_NoteDataFalso(
            intervals=np.array([[0.0, 0.5], [1.0, 1.5]]), pitches=np.array([60.0, 62.0])
        ),
    )
    # rec_b: un acorde de dos notas simultáneas -- polifónica.
    track_b = _TrackFalso(
        audio_mic_path="/datos/rec_b_mic.wav",
        notes_all=_NoteDataFalso(
            intervals=np.array([[2.0, 3.0], [2.0, 3.0]]), pitches=np.array([64.0, 67.0])
        ),
    )
    dataset = _DatasetFalso({"rec_a": track_a, "rec_b": track_b})
    _monkeypatch_mirdata(monkeypatch, dataset)

    transcriptor = _TranscriptorSelectivo(
        fallos={},
        notas={
            "rec_a_mic.wav": [
                NotaEstimada(tono_midi=60.0, inicio_s=0.01, fin_s=0.5),
                NotaEstimada(tono_midi=62.0, inicio_s=1.01, fin_s=1.5),
            ],
            "rec_b_mic.wav": [
                NotaEstimada(tono_midi=64.0, inicio_s=2.01, fin_s=3.0),
                NotaEstimada(tono_midi=67.0, inicio_s=2.01, fin_s=3.0),
            ],
        },
    )

    artefacto = ejecutar_deteccion(["rec_a", "rec_b"], tmp_path, transcriptor)

    assert artefacto.exclusiones == []
    assert artefacto.grabaciones == ["rec_a", "rec_b"]
    assert artefacto.modelo == transcriptor.modelo_declarado
    assert artefacto.tolerancia_tono_cents == 50.0
    assert artefacto.ventana_inicio_s == 0.05

    # Nunca calculado independiente de agregar_conjunto -- FR-011: el
    # artefacto debe usar exactamente esa función sobre los resultados
    # crudos por grabación, no un cálculo paralelo.
    esperado_global, esperado_mono, esperado_poli = agregar_conjunto(
        artefacto.resultados_por_grabacion
    )
    assert artefacto.global_ == esperado_global
    assert artefacto.monofonico == esperado_mono
    assert artefacto.polifonico == esperado_poli

    assert artefacto.monofonico.num_notas_referencia == 2
    assert artefacto.polifonico.num_notas_referencia == 2
    assert artefacto.global_.precision == 1.0
    assert artefacto.global_.exhaustividad == 1.0


def test_ejecutar_deteccion_grabacion_sin_notas_de_referencia_se_mide_no_se_excluye(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    track_vacio = _TrackFalso(audio_mic_path="/datos/rec_vacio_mic.wav", notes_all=None)
    dataset = _DatasetFalso({"rec_vacio": track_vacio})
    _monkeypatch_mirdata(monkeypatch, dataset)
    transcriptor = _TranscriptorSelectivo(
        fallos={},
        notas={"rec_vacio_mic.wav": [NotaEstimada(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)]},
    )

    artefacto = ejecutar_deteccion(["rec_vacio"], tmp_path, transcriptor)

    assert artefacto.exclusiones == []
    resultado = artefacto.resultados_por_grabacion[0]
    assert resultado.exclusion is None
    assert resultado.notas_referencia == []
    assert artefacto.global_.exhaustividad is None
    assert artefacto.global_.precision == 0.0


# ---------------------------------------------------------------------
# Salida de progreso (T032a) -- mismo patrón exacto que
# medicion.orquestador.ejecutar_corrida (commit "salida de progreso en
# ejecutar_corrida"), sin la parte de "ya procesados, se omiten": este
# orquestador no tiene persistencia por grabación ni reanudación.
# ---------------------------------------------------------------------


def test_ejecutar_deteccion_imprime_una_linea_por_grabacion_y_un_aviso_al_agregar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Sin esto, una corrida larga trabaja en silencio -- mismo motivo
    exacto que motivó el patrón en `medicion.orquestador.ejecutar_corrida`
    (proceso vivo confundido con muerto, condición de carrera real)."""
    track_ok = _TrackFalso(
        audio_mic_path="/datos/rec_ok_mic.wav",
        notes_all=_NoteDataFalso(intervals=np.array([[0.0, 0.5]]), pitches=np.array([60.0])),
    )
    dataset = _DatasetFalso({"rec_ok": track_ok})
    _monkeypatch_mirdata(monkeypatch, dataset)
    transcriptor = _TranscriptorSelectivo(
        fallos={},
        notas={"rec_ok_mic.wav": [NotaEstimada(tono_midi=60.0, inicio_s=0.01, fin_s=0.5)]},
    )

    ejecutar_deteccion(["rec_ok", "rec_no_existe"], tmp_path, transcriptor)

    salida = capsys.readouterr().out
    lineas = salida.splitlines()
    assert "[1/2] rec_ok  ok  " in lineas[0]
    assert lineas[0].rstrip().endswith("1 notas")
    assert (
        lineas[1] == "[2/2] rec_no_existe  excluido: La grabación 'rec_no_existe' "
        "no existe en el índice de GuitarSet."
    )
    assert lineas[2] == "agregando 2 grabaciones"
