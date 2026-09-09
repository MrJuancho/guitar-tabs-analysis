"""Tests unitarios de `deteccion.orquestador`: `construir_lista_grabaciones`
(T028-T029, User Story 3) y la serialización de `ArtefactoDeteccion`
(T030-T031) -- el índice de `mirdata` reemplazado por `monkeypatch`, NUNCA
se descarga GuitarSet real (constitución Principio IV).
"""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from guitar_tabs_analysis.deteccion import orquestador
from guitar_tabs_analysis.deteccion.orquestador import construir_lista_grabaciones

# ---------------------------------------------------------------------
# construir_lista_grabaciones (T028-T029) -- contracts/deteccion.md,
# postcondición 1 de `deteccion.orquestador`.
# ---------------------------------------------------------------------


class _DatasetFalsoTrackIds:
    """Sustituto mínimo de `mirdata.core.Dataset` -- solo `.track_ids`,
    el único atributo que `construir_lista_grabaciones` lee (verificado
    contra `mirdata/core.py::Dataset.track_ids`, línea 466, instalado en
    este proyecto)."""

    def __init__(self, track_ids: list[str]) -> None:
        self.track_ids = track_ids


def _monkeypatch_mirdata_track_ids(monkeypatch: pytest.MonkeyPatch, track_ids: list[str]) -> None:
    def _initialize_falso(nombre: str, data_home: str) -> _DatasetFalsoTrackIds:
        assert nombre == "guitarset"
        return _DatasetFalsoTrackIds(track_ids)

    monkeypatch.setattr(orquestador.mirdata, "initialize", _initialize_falso)


# 360 identificadores sintéticos, mismo orden de magnitud que los reales de
# GuitarSet -- deliberadamente en orden INVERSO al orden lexicográfico: si
# `construir_lista_grabaciones` no ordenara antes de muestrear, el cálculo
# independiente de este test (que sí ordena, como el contrato exige) daría
# un resultado distinto y el test lo detectaría.
_IDS_SINTETICOS_ORDENADOS = sorted(f"grabacion_{i:03d}" for i in range(360))
_IDS_SINTETICOS_DESORDENADOS = list(reversed(_IDS_SINTETICOS_ORDENADOS))


def test_medibles_nunca_incluye_ninguna_de_las_72_reservadas_recalculadas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """El test que más importa de esta fase: un filtro que excluyera 72
    arbitrarias distintas también daría `len(resultado) == 288` -- por eso
    esto recalcula, de forma independiente (sin llamar a ninguna función
    de producción para el conjunto esperado), el mismo muestreo que exige
    el contrato, y afirma que NINGUNO de esos 72 identificadores aparece
    en el resultado de `modo="medibles"`."""
    _monkeypatch_mirdata_track_ids(monkeypatch, _IDS_SINTETICOS_DESORDENADOS)

    reservados_esperados = set(random.Random(20260908).sample(_IDS_SINTETICOS_ORDENADOS, 72))

    medibles = construir_lista_grabaciones("medibles", Path("/cualquier/ruta"))

    assert reservados_esperados & set(medibles) == set()


def test_reservado_devuelve_exactamente_los_72_recalculados(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _monkeypatch_mirdata_track_ids(monkeypatch, _IDS_SINTETICOS_DESORDENADOS)

    reservados_esperados = sorted(random.Random(20260908).sample(_IDS_SINTETICOS_ORDENADOS, 72))

    reservado = construir_lista_grabaciones("reservado", Path("/cualquier/ruta"))

    assert reservado == reservados_esperados


def test_union_de_medibles_y_reservado_cubre_todos_sin_overlap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _monkeypatch_mirdata_track_ids(monkeypatch, _IDS_SINTETICOS_DESORDENADOS)

    medibles = construir_lista_grabaciones("medibles", Path("/cualquier/ruta"))
    reservado = construir_lista_grabaciones("reservado", Path("/cualquier/ruta"))

    assert set(medibles) & set(reservado) == set()
    assert set(medibles) | set(reservado) == set(_IDS_SINTETICOS_ORDENADOS)
    assert len(medibles) == 288
    assert len(reservado) == 72


def test_dos_invocaciones_con_los_mismos_parametros_dan_la_misma_lista(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _monkeypatch_mirdata_track_ids(monkeypatch, _IDS_SINTETICOS_DESORDENADOS)

    primera = construir_lista_grabaciones("medibles", Path("/cualquier/ruta"))
    segunda = construir_lista_grabaciones("medibles", Path("/cualquier/ruta"))

    assert primera == segunda


def test_semilla_reserva_distinta_cambia_por_completo_el_conjunto_reservado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fija en código, no solo en documentación, que la partición depende
    de la semilla -- dominio sintético más chico (50) para que el test sea
    legible, con una segunda semilla verificada de antemano para no
    solapar con la primera en absoluto."""
    ids_ordenados = sorted(f"rec_{i:03d}" for i in range(50))
    _monkeypatch_mirdata_track_ids(monkeypatch, list(reversed(ids_ordenados)))

    reservado_semilla_por_defecto = construir_lista_grabaciones(
        "reservado", Path("/cualquier/ruta"), tamano_reserva=5
    )
    reservado_otra_semilla = construir_lista_grabaciones(
        "reservado", Path("/cualquier/ruta"), tamano_reserva=5, semilla_reserva=2
    )

    assert set(reservado_semilla_por_defecto) & set(reservado_otra_semilla) == set()
