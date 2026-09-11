"""Tests de integración de `digitacion.orquestador.ejecutar_digitacion`
(User Story 3, T016/T022) -- índice/`Track` de `mirdata` reemplazados
por `monkeypatch`, tanto en `ingestion.guitarset` (lectura por
grabación) como en `deteccion.orquestador` (`construir_lista_grabaciones`,
reutilizada tal cual) -- nunca GuitarSet real (constitución Principio IV).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest

from guitar_tabs_analysis.analytics.metrica_digitacion import MODELO_COSTE_POR_DEFECTO
from guitar_tabs_analysis.deteccion import orquestador as deteccion_orquestador
from guitar_tabs_analysis.deteccion.orquestador import construir_lista_grabaciones
from guitar_tabs_analysis.digitacion import orquestador as digitacion_orquestador
from guitar_tabs_analysis.digitacion.orquestador import ejecutar_digitacion
from guitar_tabs_analysis.ingestion import guitarset

# ---------------------------------------------------------------------
# Sustitutos mínimos de mirdata -- mismo patrón que
# tests/unit/test_guitarset.py y
# tests/integration/test_deteccion_orquestador_integracion.py, con
# `.notes` (por cuerda) además de `.track_ids` (para que el mismo
# dataset falso sirva tanto a `leer_grabacion_con_posicion_real` como a
# `construir_lista_grabaciones`).
# ---------------------------------------------------------------------


class _NoteDataFalso:
    def __init__(self, intervals: np.ndarray, pitches: np.ndarray) -> None:
        self.intervals = intervals
        self.pitches = pitches


class _TrackFalso:
    def __init__(self, notes: dict[str, _NoteDataFalso | None]) -> None:
        self.notes = notes


class _DatasetFalso:
    def __init__(self, tracks: dict[str, _TrackFalso]) -> None:
        self._tracks = tracks
        self.track_ids = list(tracks.keys())

    def track(self, track_id: str) -> _TrackFalso:
        if track_id not in self._tracks:
            raise ValueError(f"{track_id} is not a valid track_id in guitarset")
        return self._tracks[track_id]


def _monkeypatch_mirdata(monkeypatch: pytest.MonkeyPatch, dataset: _DatasetFalso) -> None:
    def _initialize_falso(nombre: str, data_home: str) -> _DatasetFalso:
        assert nombre == "guitarset"
        return dataset

    monkeypatch.setattr(guitarset.mirdata, "initialize", _initialize_falso)
    monkeypatch.setattr(deteccion_orquestador.mirdata, "initialize", _initialize_falso)


def _track_una_nota(cuerda: str, tono: float, inicio: float, fin: float) -> _TrackFalso:
    notes: dict[str, _NoteDataFalso | None] = dict.fromkeys(["E", "A", "D", "G", "B", "e"], None)
    notes[cuerda] = _NoteDataFalso(intervals=np.array([[inicio, fin]]), pitches=np.array([tono]))
    return _TrackFalso(notes=notes)


def test_ejecutar_digitacion_grabacion_inexistente_se_excluye_y_sigue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = _DatasetFalso({"g1": _track_una_nota("A", 47.0, 1.0, 1.5)})
    _monkeypatch_mirdata(monkeypatch, dataset)

    artefacto = ejecutar_digitacion(["g1", "99_inexistente"], tmp_path)

    assert len(artefacto.exclusiones_grabacion) == 1
    assert artefacto.exclusiones_grabacion[0].grabacion_id == "99_inexistente"
    assert len(artefacto.resultados_por_grabacion) == 2
    resultado_g1 = next(r for r in artefacto.resultados_por_grabacion if r.grabacion_id == "g1")
    assert resultado_g1.exclusion is None
    assert resultado_g1.digitacion is not None
    # El propio ResultadoDigitacionGrabacion excluido conserva su
    # grabacion_id real, no None (mutation testing T027).
    resultado_excluido = next(
        r for r in artefacto.resultados_por_grabacion if r.exclusion is not None
    )
    assert resultado_excluido.grabacion_id == "99_inexistente"


def test_ejecutar_digitacion_continua_tras_una_exclusion_no_se_detiene(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`continue`, no `break`, tras registrar una exclusión -- una
    grabación excluida al PRINCIPIO de la lista no debe detener el
    procesamiento de las siguientes (mutation testing T027: los tests
    existentes solo probaban la exclusión al FINAL de la lista, donde
    `break` y `continue` son indistinguibles -- no queda nada después
    de la última posición en ningún caso)."""
    dataset = _DatasetFalso({"g_ok": _track_una_nota("A", 47.0, 1.0, 1.5)})
    _monkeypatch_mirdata(monkeypatch, dataset)

    artefacto = ejecutar_digitacion(["g_no_existe", "g_ok"], tmp_path)

    resultado_ok = next(r for r in artefacto.resultados_por_grabacion if r.grabacion_id == "g_ok")
    assert resultado_ok.exclusion is None
    assert resultado_ok.digitacion is not None
    assert artefacto.resultado_coincidencia.num_notas_medidas == 1


def test_ejecutar_digitacion_agrega_resultado_coincidencia_sobre_varias_grabaciones(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # g1: A2 (MIDI 47.0) anotado; g2: D0 (MIDI 50.0) anotado. Con
    # traste_maximo=3, cada tono tiene una ÚNICA candidata posible (la
    # candidata en la cuerda más grave -- E7/E10 -- queda fuera del
    # rango), así que la digitación producida coincide con la real por
    # construcción, sin ninguna ambigüedad de DP que decidir.
    modelo = dataclasses.replace(MODELO_COSTE_POR_DEFECTO, traste_maximo=3)
    dataset = _DatasetFalso(
        {
            "g1": _track_una_nota("A", 47.0, 1.0, 1.5),
            "g2": _track_una_nota("D", 50.0, 1.0, 1.5),
        }
    )
    _monkeypatch_mirdata(monkeypatch, dataset)

    artefacto = ejecutar_digitacion(["g1", "g2"], tmp_path, modelo)

    assert artefacto.exclusiones_grabacion == []
    assert artefacto.resultado_coincidencia.num_notas_medidas == 2
    assert artefacto.resultado_coincidencia.num_notas_coincidentes == 2
    assert artefacto.resultado_coincidencia.fraccion_coincidencia == 1.0


def test_ejecutar_digitacion_no_umbral_ni_comparacion_de_aprobacion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-015: el artefacto se devuelve tal cual, sin ningún campo ni
    lógica de aprobación/umbral -- el propio tipo `ArtefactoDigitacion`
    no tiene un campo así (verificado indirectamente: no hay ningún
    atributo de umbral que consultar)."""
    dataset = _DatasetFalso({"g1": _track_una_nota("A", 47.0, 1.0, 1.5)})
    _monkeypatch_mirdata(monkeypatch, dataset)

    artefacto = ejecutar_digitacion(["g1"], tmp_path)

    assert not hasattr(artefacto, "aprobado")
    assert not hasattr(artefacto, "presupuesto")


def test_ejecutar_digitacion_reutiliza_construir_lista_grabaciones_ninguna_reservada_participa(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """US3 AS2, FR-008: ninguna de las grabaciones "reservadas" (en este
    dominio sintético, calculadas por `construir_lista_grabaciones` con
    los mismos parámetros que el hito 2) aparece en el resultado --
    reutilizando la función tal cual, sin una segunda partición."""
    ids_sinteticos = [f"grabacion_{i:02d}" for i in range(10)]
    tracks = {gid: _track_una_nota("A", 47.0, 1.0, 1.5) for gid in ids_sinteticos}
    dataset = _DatasetFalso(tracks)
    _monkeypatch_mirdata(monkeypatch, dataset)

    medibles = construir_lista_grabaciones(
        "medibles", tmp_path, tamano_reserva=3, semilla_reserva=20260908
    )
    reservados = construir_lista_grabaciones(
        "reservado", tmp_path, tamano_reserva=3, semilla_reserva=20260908
    )
    assert set(medibles) & set(reservados) == set()
    assert len(medibles) == 7

    artefacto = ejecutar_digitacion(medibles, tmp_path)

    ids_resultado = {r.grabacion_id for r in artefacto.resultados_por_grabacion}
    assert artefacto.grabaciones == medibles
    assert ids_resultado & set(reservados) == set()


def test_ejecutar_digitacion_usa_el_modelo_de_coste_declarado_por_defecto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = _DatasetFalso({"g1": _track_una_nota("A", 47.0, 1.0, 1.5)})
    _monkeypatch_mirdata(monkeypatch, dataset)

    artefacto = ejecutar_digitacion(["g1"], tmp_path)

    assert artefacto.modelo_coste == MODELO_COSTE_POR_DEFECTO


# ---------------------------------------------------------------------
# Salida de progreso -- mismo patrón que
# test_deteccion_orquestador_integracion.py del hito 2 (mutation
# testing, T027: cada rama de impresión tiene su propio print, ninguna
# cubierta por defecto por otros tests que no capturan stdout).
# ---------------------------------------------------------------------


def test_ejecutar_digitacion_imprime_una_linea_por_grabacion_y_un_aviso_al_agregar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset = _DatasetFalso(
        {"g_ok": _track_una_nota("A", 47.0, 1.0, 1.5)},
    )
    _monkeypatch_mirdata(monkeypatch, dataset)

    ejecutar_digitacion(["g_ok", "g_no_existe"], tmp_path)

    lineas = capsys.readouterr().out.splitlines()
    assert "[1/2] g_ok  ok  " in lineas[0]
    assert lineas[0].rstrip().endswith("1 posiciones")
    assert lineas[1] == (
        "[2/2] g_no_existe  excluido: La grabación 'g_no_existe' "
        "no existe en el índice de GuitarSet."
    )
    assert lineas[2] == "agregando 2 grabaciones"


def test_ejecutar_digitacion_imprime_la_duracion_resultado_de_restar_no_sumar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`duracion = time.perf_counter() - inicio`, no `+` (mutation
    testing T027, mismo patrón que la Feature 006: comparación EXACTA
    de la línea completa, no `in` -- "2.5s" es substring de "202.5s")."""
    dataset = _DatasetFalso({"g_ok": _track_una_nota("A", 47.0, 1.0, 1.5)})
    _monkeypatch_mirdata(monkeypatch, dataset)
    valores = iter([100.0, 102.5])
    monkeypatch.setattr(digitacion_orquestador.time, "perf_counter", lambda: next(valores))

    ejecutar_digitacion(["g_ok"], tmp_path)

    linea = capsys.readouterr().out.splitlines()[0]
    assert linea == "[1/1] g_ok  ok  2.5s  1 posiciones"


def test_ejecutar_digitacion_exclusion_conserva_el_grabacion_id_y_el_detalle_reales(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`ExclusionDigitacion(grabacion_id, str(causa))` -- ni el
    `grabacion_id` ni el detalle deben perderse a `None` (mutation
    testing T027)."""
    dataset = _DatasetFalso({})
    _monkeypatch_mirdata(monkeypatch, dataset)

    artefacto = ejecutar_digitacion(["g_no_existe"], tmp_path)

    assert artefacto.exclusiones_grabacion[0].grabacion_id == "g_no_existe"
    assert artefacto.exclusiones_grabacion[0].detalle == (
        "La grabación 'g_no_existe' no existe en el índice de GuitarSet."
    )
