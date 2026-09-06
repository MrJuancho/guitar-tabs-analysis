"""Tests unitarios de manifiesto de corrida (T015 de
`specs/004-medicion-linea-base/tasks.md`, Foundational)."""

from __future__ import annotations

from pathlib import Path

from guitar_tabs_analysis.medicion.orquestador import (
    ManifiestoCorrida,
    escribir_manifiesto,
    leer_manifiesto,
)


def test_escribir_y_leer_un_manifiesto_recupera_los_mismos_campos(tmp_path: Path) -> None:
    manifiesto = ManifiestoCorrida(
        modo="submuestra_hito1",
        semilla=20260904,
        firma_modelo="5c90dfd2",
        temas=["validation/Track00001", "validation/Track00002"],
    )

    escribir_manifiesto(tmp_path, manifiesto)
    recuperado = leer_manifiesto(tmp_path)

    assert recuperado == manifiesto


def test_directorio_sin_manifiesto_devuelve_none(tmp_path: Path) -> None:
    assert leer_manifiesto(tmp_path) is None
