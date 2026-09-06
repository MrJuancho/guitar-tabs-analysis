"""Tests de `medicion.cli` (T027 de `specs/004-medicion-linea-base/tasks.md`,
User Story 3): el modo se elige explícitamente, sin valor por defecto --
invocar sin `--modo`, o con un `--modo` inválido, falla ANTES de construir
ningún `Separador` real (`DemucsSeparador` importa `torch`/`demucs`, que
este módulo de tests nunca debe tocar).
"""

from __future__ import annotations

import pytest

from guitar_tabs_analysis.medicion import cli


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
