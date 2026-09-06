"""Tests unitarios de manifiesto de corrida (T015 de
`specs/004-medicion-linea-base/tasks.md`, Foundational)."""

from __future__ import annotations

from pathlib import Path

import pytest

from guitar_tabs_analysis.medicion.orquestador import (
    ManifiestoCorrida,
    ModeloCambiadoError,
    ejecutar_corrida,
    escribir_manifiesto,
    leer_manifiesto,
)
from guitar_tabs_analysis.separacion.separador import ModeloDeclarado
from tests.fixtures.separador_fixture import SeparadorFalso


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


def test_reanudar_con_firma_de_modelo_distinta_falla_cerrado(tmp_path: Path) -> None:
    """T024, User Story 2, AS5, FR-008a: un manifiesto persistido con una
    firma de modelo distinta a la del `Separador` vigente levanta
    `ModeloCambiadoError` con ambas firmas en el mensaje, sin invocar
    `separar()` para ningún tema."""
    directorio_trabajo = tmp_path / "trabajo"
    manifiesto_viejo = ManifiestoCorrida(
        modo="conjunto_completo",
        semilla=None,
        firma_modelo="firma-vieja",
        temas=["validation/Track00000"],
    )
    escribir_manifiesto(directorio_trabajo, manifiesto_viejo)

    modelo_nuevo = ModeloDeclarado(
        nombre="ModeloFalso",
        variante="v1-prueba",
        firma="firma-nueva",
        checksum_sha256_prefijo="dummy2222",
        licencia_pesos="ninguna -- solo para tests",
    )
    separador = SeparadorFalso(modelo_declarado=modelo_nuevo)

    with pytest.raises(ModeloCambiadoError) as excinfo:
        ejecutar_corrida(
            "conjunto_completo",
            tmp_path / "dataset_nunca_tocado",
            separador,
            directorio_trabajo,
        )

    assert "firma-vieja" in str(excinfo.value)
    assert "firma-nueva" in str(excinfo.value)
    assert excinfo.value.firma_esperada == "firma-vieja"
    assert excinfo.value.firma_actual == "firma-nueva"
    assert separador.llamadas == 0
