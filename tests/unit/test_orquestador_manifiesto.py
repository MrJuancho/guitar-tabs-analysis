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


def test_escribir_manifiesto_crea_directorios_intermedios_faltantes(tmp_path: Path) -> None:
    """Triage de mutación (Polish, T031): los demás tests de este módulo
    llaman a `escribir_manifiesto` con un `directorio` que falta a lo
    sumo un nivel (su padre ya existe, por ser `tmp_path` u otro
    subdirectorio de `tmp_path`) -- ahí `mkdir(parents=True)` y
    `mkdir(parents=False)` (el default) se comportan igual, porque crear
    el nivel final no requiere crear ninguno intermedio. `directorio_trabajo`
    en uso real (`Path("data/silver/mediciones") / modo`, `medicion/cli.py`)
    sí puede faltar varios niveles a la vez."""
    directorio_trabajo = tmp_path / "silver" / "mediciones" / "submuestra_hito1"
    manifiesto = ManifiestoCorrida(
        modo="submuestra_hito1",
        semilla=20260904,
        firma_modelo="firma-cualquiera",
        temas=["validation/Track00000"],
    )

    escribir_manifiesto(directorio_trabajo, manifiesto)

    assert leer_manifiesto(directorio_trabajo) == manifiesto
