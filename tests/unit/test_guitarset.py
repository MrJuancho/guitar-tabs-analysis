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
    IndiceMirdataAusenteError,
    LecturaGrabacion,
    NotaConPosicionReal,
    NotaReferencia,
    RaizGuitarSetInvalidaError,
    leer_grabacion,
    leer_grabacion_con_posicion_real,
    validar_indice_mirdata,
    validar_raiz_guitarset,
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
    """Sustituto mínimo de `mirdata.datasets.guitarset.Track` -- los
    atributos que `leer_grabacion`/`leer_grabacion_con_posicion_real`
    leen (`audio_mic_path`, `notes_all`, `notes`)."""

    def __init__(
        self,
        audio_mic_path: str,
        notes_all: _NoteDataFalso | None,
        notes: dict[str, _NoteDataFalso | None] | None = None,
    ) -> None:
        self.audio_mic_path = audio_mic_path
        self.notes_all = notes_all
        self.notes = notes if notes is not None else {}


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


# ---------------------------------------------------------------------
# validar_raiz_guitarset / validar_indice_mirdata (FR-015/FR-016,
# research.md #19) -- precondiciones de arranque, verificadas ANTES de
# procesar ninguna grabación. Incidente real: `root_dir` apuntando al
# repositorio en vez del dataset produjo 288 exclusiones idénticas (una
# por grabación) en vez de un solo fallo claro al arrancar.
# ---------------------------------------------------------------------


def test_validar_raiz_guitarset_con_ambos_directorios_no_falla(tmp_path: Path) -> None:
    (tmp_path / "annotation").mkdir()
    (tmp_path / "audio_mono-mic").mkdir()

    validar_raiz_guitarset(tmp_path)  # no debe lanzar nada


def test_validar_raiz_guitarset_sin_ningun_directorio_dice_ambos_faltantes(
    tmp_path: Path,
) -> None:
    with pytest.raises(RaizGuitarSetInvalidaError) as excinfo:
        validar_raiz_guitarset(tmp_path)

    assert excinfo.value.faltantes == ["annotation", "audio_mono-mic"]
    assert excinfo.value.root_dir == tmp_path
    mensaje = str(excinfo.value)
    assert str(tmp_path) in mensaje
    assert "annotation" in mensaje
    assert "audio_mono-mic" in mensaje


def test_raiz_guitarset_invalida_error_expone_root_dir_y_mensaje_completo(
    tmp_path: Path,
) -> None:
    """Comparación EXACTA del mensaje completo -- no solo `in` sobre
    palabras sueltas (mutation testing, T026: `self.root_dir = None`, el
    separador `', '.join` mutado a `'XX, XX'`, y la segunda mitad del
    mensaje ("GuitarSet debe tener...") alterada o mayusculizada
    sobrevivían a los tests existentes, que solo comprobaban que
    "annotation"/"audio_mono-mic" aparecieran en algún lado)."""
    error = RaizGuitarSetInvalidaError(tmp_path, ["annotation", "audio_mono-mic"])

    assert error.root_dir == tmp_path
    assert str(error) == (
        f"'{tmp_path}' no es una raíz de GuitarSet válida -- falta: "
        "annotation, audio_mono-mic. GuitarSet debe tener 'annotation/' "
        "(anotaciones JAMS) y 'audio_mono-mic/' (audio de micrófono) bajo esta ruta."
    )


def test_validar_raiz_guitarset_con_solo_annotation_dice_que_falta_solo_audio(
    tmp_path: Path,
) -> None:
    (tmp_path / "annotation").mkdir()

    with pytest.raises(RaizGuitarSetInvalidaError) as excinfo:
        validar_raiz_guitarset(tmp_path)

    assert excinfo.value.faltantes == ["audio_mono-mic"]


def test_validar_raiz_guitarset_rechaza_un_archivo_con_el_mismo_nombre(
    tmp_path: Path,
) -> None:
    """Un ARCHIVO llamado 'annotation' (no un directorio) no sirve para
    leer ninguna anotación real -- debe seguir contando como faltante,
    nunca colar por coincidencia de nombre."""
    (tmp_path / "annotation").write_text("no soy un directorio")
    (tmp_path / "audio_mono-mic").mkdir()

    with pytest.raises(RaizGuitarSetInvalidaError) as excinfo:
        validar_raiz_guitarset(tmp_path)

    assert excinfo.value.faltantes == ["annotation"]


def test_validar_indice_mirdata_disponible_no_falla(monkeypatch: pytest.MonkeyPatch) -> None:
    class _DatasetConIndice:
        track_ids = ["a", "b"]

    monkeypatch.setattr(guitarset.mirdata, "initialize", lambda nombre: _DatasetConIndice())

    validar_indice_mirdata()  # no debe lanzar nada


def test_validar_indice_mirdata_ausente_da_mensaje_con_como_descargarlo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nunca la excepción cruda de `mirdata` sin envolver -- el mensaje
    debe decir el comando exacto para resolverlo (research.md #19).
    Comparación EXACTA del mensaje completo (no solo `in` sobre palabras
    sueltas, mutation testing T026: alterar el texto fijo del mensaje o
    envolver con `IndiceMirdataAusenteError(None)` en vez de la causa
    real sobrevivía a un chequeo por substrings -- ninguno de "download"/
    "index"/"no está disponible" cambia con esas mutaciones)."""

    def _initialize_sin_indice(nombre: str) -> None:
        raise FileNotFoundError(
            "Dataset index for guitarset was expected but not found. Did you run .download()?"
        )

    monkeypatch.setattr(guitarset.mirdata, "initialize", _initialize_sin_indice)

    with pytest.raises(IndiceMirdataAusenteError) as excinfo:
        validar_indice_mirdata()

    assert str(excinfo.value) == (
        "El índice de GuitarSet de mirdata no está disponible -- descargalo con: "
        'python -c "import mirdata; '
        "mirdata.initialize('guitarset').download(partial_download=['index'])\" "
        "(causa real: Dataset index for guitarset was expected but not found. "
        "Did you run .download()?)."
    )


def test_indice_mirdata_ausente_error_expone_causa_y_mensaje_completo() -> None:
    causa = FileNotFoundError("boom")

    error = IndiceMirdataAusenteError(causa)

    assert error.causa is causa
    assert str(error) == (
        "El índice de GuitarSet de mirdata no está disponible -- descargalo con: "
        'python -c "import mirdata; '
        "mirdata.initialize('guitarset').download(partial_download=['index'])\" "
        "(causa real: boom)."
    )


# ---------------------------------------------------------------------
# leer_grabacion_con_posicion_real (Feature 007, T013) -- posición REAL
# anotada por cuerda (track.notes, research.md #5 de esa feature), no la
# lectura pooleada (notes_all) que leer_grabacion ya usa. NUNCA GuitarSet
# real descargado en un test (Principio IV).
# ---------------------------------------------------------------------


def test_leer_grabacion_con_posicion_real_fusiona_las_seis_cuerdas(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Una entrada por cada nota anotada, en CUALQUIERA de las seis
    cuerdas de `track.notes` -- `cuerda_real` es la clave del
    diccionario, `traste_real = round(tono_midi - MIDI_CUERDA_ABIERTA[cuerda])`
    (research.md #5/#3 de la Feature 007, contracts/digitacion.md
    postcondición 1)."""
    notes = {
        "A": _NoteDataFalso(intervals=np.array([[1.0, 1.5]]), pitches=np.array([47.0])),
        "e": _NoteDataFalso(intervals=np.array([[0.5, 0.9]]), pitches=np.array([64.0])),
        "E": None,
        "D": None,
        "G": None,
        "B": None,
    }
    track = _TrackFalso(audio_mic_path="/x_mic.wav", notes_all=None, notes=notes)
    dataset = _DatasetFalso({"grabacion": track})
    _monkeypatch_mirdata(monkeypatch, dataset)

    notas = leer_grabacion_con_posicion_real("grabacion", tmp_path)

    assert notas == [
        NotaConPosicionReal(
            tono_midi=64.0, inicio_s=0.5, fin_s=0.9, cuerda_real="e", traste_real=0
        ),
        NotaConPosicionReal(
            tono_midi=47.0, inicio_s=1.0, fin_s=1.5, cuerda_real="A", traste_real=2
        ),
    ]


def test_leer_grabacion_con_posicion_real_ordena_por_inicio_aunque_las_cuerdas_no_lo_esten(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Las seis listas por cuerda no vienen ordenadas ENTRE SÍ -- la
    lista final se ordena explícitamente por `inicio_s`, no se asume ya
    ordenada por venir de un diccionario en orden E/A/D/G/B/e."""
    notes = {
        "E": _NoteDataFalso(intervals=np.array([[5.0, 5.4]]), pitches=np.array([41.0])),
        "B": _NoteDataFalso(intervals=np.array([[0.1, 0.4]]), pitches=np.array([60.0])),
        "A": None,
        "D": None,
        "G": None,
        "e": None,
    }
    track = _TrackFalso(audio_mic_path="/x_mic.wav", notes_all=None, notes=notes)
    dataset = _DatasetFalso({"grabacion": track})
    _monkeypatch_mirdata(monkeypatch, dataset)

    notas = leer_grabacion_con_posicion_real("grabacion", tmp_path)

    assert [n.cuerda_real for n in notas] == ["B", "E"]
    assert [n.inicio_s for n in notas] == [0.1, 5.0]


def test_leer_grabacion_con_posicion_real_inexistente_levanta_grabacion_no_existe_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dataset = _DatasetFalso({})
    _monkeypatch_mirdata(monkeypatch, dataset)

    with pytest.raises(GrabacionNoExisteError) as excinfo:
        leer_grabacion_con_posicion_real("99_inexistente", tmp_path)

    assert excinfo.value.grabacion_id == "99_inexistente"


def test_leer_grabacion_con_posicion_real_intervals_y_pitches_de_distinta_longitud_falla(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Mismo invariante que `leer_grabacion` (`zip(..., strict=True)`)
    -- a diferencia de las combinaciones de `itertools.product` en
    `analytics.metrica_digitacion` (donde la igualdad de longitud está
    garantizada por construcción), `intervals`/`pitches` de una cuerda
    son dos arrays independientes leídos de `mirdata`, sin esa garantía
    estructural: un `strict=True` real aquí (mutation testing T027)."""
    notes = {
        "A": _NoteDataFalso(
            intervals=np.array([[1.0, 1.5], [2.0, 2.25]]),
            pitches=np.array([47.0]),
        ),
        "E": None,
        "D": None,
        "G": None,
        "B": None,
        "e": None,
    }
    track = _TrackFalso(audio_mic_path="/x_mic.wav", notes_all=None, notes=notes)
    dataset = _DatasetFalso({"grabacion": track})
    _monkeypatch_mirdata(monkeypatch, dataset)

    with pytest.raises(ValueError, match="zip"):
        leer_grabacion_con_posicion_real("grabacion", tmp_path)
