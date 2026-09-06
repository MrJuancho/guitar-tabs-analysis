"""Tests de `medicion.cli` (T027 de `specs/004-medicion-linea-base/tasks.md`,
User Story 3): el modo se elige explícitamente, sin valor por defecto --
invocar sin `--modo`, o con un `--modo` inválido, falla ANTES de construir
ningún `Separador` real (`DemucsSeparador` importa `torch`/`demucs`, que
este módulo de tests nunca debe tocar).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from guitar_tabs_analysis.medicion import cli
from guitar_tabs_analysis.medicion.orquestador import ArtefactoMedicion
from guitar_tabs_analysis.separacion.separador import ModeloDeclarado
from tests.fixtures.separador_fixture import SeparadorFalso
from tests.fixtures.slakh2100_fixture import EspecificacionStem, construir_tema_sintetico


def _fallar_si_se_construye() -> None:
    raise AssertionError(
        "DemucsSeparador no debería construirse sin un --modo válido -- "
        "el error de argparse tiene que ocurrir antes."
    )


def test_sin_modo_falla_con_mensaje_claro_antes_de_construir_separador(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "DemucsSeparador", _fallar_si_se_construye)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--root-dir", "/cualquier/ruta"])

    assert excinfo.value.code != 0
    mensaje = capsys.readouterr().err
    assert "--modo" in mensaje
    assert "required" in mensaje  # argparse: "the following arguments are required: --modo"


def test_modo_invalido_falla_con_mensaje_claro_antes_de_construir_separador(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "DemucsSeparador", _fallar_si_se_construye)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--modo", "no_existe", "--root-dir", "/cualquier/ruta"])

    assert excinfo.value.code != 0
    mensaje = capsys.readouterr().err
    assert "--modo" in mensaje


def test_sin_root_dir_falla_con_mensaje_claro(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "DemucsSeparador", _fallar_si_se_construye)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--modo", "submuestra_hito1"])

    assert excinfo.value.code != 0
    mensaje = capsys.readouterr().err
    assert "--root-dir" in mensaje


_GUITARRA = EspecificacionStem(identificador="G01", inst_class="Guitar")


def _artefacto_de_prueba() -> ArtefactoMedicion:
    return ArtefactoMedicion(
        modo="submuestra_hito1",
        semilla=20260904,
        modelo=ModeloDeclarado(
            nombre="ModeloDePrueba",
            variante="v0",
            firma="firma0000",
            checksum_sha256_prefijo="checksum00",
            licencia_pesos="ninguna -- solo para tests",
        ),
        temas=["validation/Track00000"],
        exclusiones=[],
        reportes=[],
        transformaciones_por_tema={},
        mediana=None,
        distribucion_referencias_por_tema={},
    )


def test_escribir_artefacto_produce_json_valido_y_legible(tmp_path: Path) -> None:
    ruta = tmp_path / "mediciones" / "submuestra_hito1.json"
    artefacto = _artefacto_de_prueba()

    cli.escribir_artefacto(ruta, artefacto)

    contenido = json.loads(ruta.read_text())
    assert contenido["modo"] == "submuestra_hito1"
    assert contenido["temas"] == ["validation/Track00000"]


def test_escribir_artefacto_es_atomico_no_deja_archivo_final_truncado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simula una interrupción exactamente entre "escribir el archivo
    temporal" y "renombrarlo al nombre final" (`os.replace`) -- el mismo
    mecanismo que `escribir_progreso_tema`/`escribir_manifiesto`
    (research.md #5). Si `os.replace` falla, la ruta final NUNCA debe
    existir -- nunca un artefacto a medio escribir que parezca válido."""
    ruta = tmp_path / "mediciones" / "submuestra_hito1.json"
    artefacto = _artefacto_de_prueba()

    def _os_replace_que_falla(origen: object, destino: object) -> None:
        raise OSError("interrupción simulada entre escribir el temporal y renombrarlo")

    monkeypatch.setattr(cli.os, "replace", _os_replace_que_falla)

    with pytest.raises(OSError):
        cli.escribir_artefacto(ruta, artefacto)

    assert not ruta.exists()


def test_ejecutar_y_escribir_produce_artefacto_en_disco(tmp_path: Path) -> None:
    root_dir = tmp_path / "dataset"
    (root_dir / "train").mkdir(parents=True)
    construir_tema_sintetico(root_dir, tema_id="validation/Track00000", stems=(_GUITARRA,))
    ruta_artefacto = tmp_path / "mediciones" / "conjunto_completo.json"

    codigo = cli._ejecutar_y_escribir(
        "conjunto_completo",
        root_dir,
        SeparadorFalso(),
        tmp_path / "trabajo",
        ruta_artefacto,
    )

    assert codigo == 0
    contenido = json.loads(ruta_artefacto.read_text())
    assert contenido["modo"] == "conjunto_completo"
    assert contenido["temas"] == ["validation/Track00000"]


def test_ejecutar_y_escribir_con_firma_distinta_no_escribe_artefacto(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """FR-008a: si `ejecutar_corrida` levanta `ModeloCambiadoError`, el
    CLI la deja propagar como fallo visible y NO escribe ningún
    artefacto -- nunca silencia el error ni reanuda de todos modos
    (contracts/medicion.md, CLI postcondición 3)."""
    root_dir = tmp_path / "dataset"
    (root_dir / "train").mkdir(parents=True)
    construir_tema_sintetico(root_dir, tema_id="validation/Track00000", stems=(_GUITARRA,))
    directorio_trabajo = tmp_path / "trabajo"

    # Primera corrida con un modelo de firma "vieja".
    modelo_viejo = SeparadorFalso()
    cli._ejecutar_y_escribir(
        "conjunto_completo",
        root_dir,
        modelo_viejo,
        directorio_trabajo,
        tmp_path / "mediciones" / "conjunto_completo.json",
    )

    # Segunda corrida con un separador de firma distinta.
    modelo_nuevo = SeparadorFalso(
        modelo_declarado=ModeloDeclarado(
            nombre="Otro",
            variante="v1",
            firma="firma-nueva",
            checksum_sha256_prefijo="otro00",
            licencia_pesos="ninguna",
        )
    )
    ruta_artefacto = tmp_path / "mediciones" / "conjunto_completo_v2.json"

    codigo = cli._ejecutar_y_escribir(
        "conjunto_completo", root_dir, modelo_nuevo, directorio_trabajo, ruta_artefacto
    )

    assert codigo != 0
    assert not ruta_artefacto.exists()
    assert "firma" in capsys.readouterr().err
