"""Tests de `medicion.compuerta.leer_artefacto` y `main` (T006/T009 de
`specs/005-compuerta-metrica/tasks.md`, User Stories 2 y 3) -- sobre
`tmp_path`, nunca sobre `mediciones/submuestra_hito1.json` real.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from guitar_tabs_analysis.medicion import compuerta
from guitar_tabs_analysis.medicion.compuerta import ArtefactoInvalidoError, leer_artefacto


def test_ruta_ausente_es_invalida(tmp_path: Path) -> None:
    with pytest.raises(ArtefactoInvalidoError) as excinfo:
        leer_artefacto(tmp_path / "no_existe.json")

    assert "no_existe.json" in str(excinfo.value)


def test_contenido_no_interpretable_es_invalido(tmp_path: Path) -> None:
    ruta = tmp_path / "corrupto.json"
    ruta.write_text("esto no es json")

    with pytest.raises(ArtefactoInvalidoError) as excinfo:
        leer_artefacto(ruta)

    assert "corrupto.json" in str(excinfo.value)


_MODELO = {
    "nombre": "Demucs",
    "variante": "htdemucs_6s",
    "firma": "5c90dfd2",
    "checksum_sha256_prefijo": "d2a1745f0744",
    "licencia_pesos": "ninguna -- solo para tests",
}


def _artefacto(
    modo: str, si_sdr_emparejadas: list[float], num_sin_pareja: int = 0
) -> dict[str, Any]:
    return {
        "modo": modo,
        "semilla": 20260904 if modo == "submuestra_hito1" else None,
        "modelo": _MODELO,
        "temas": ["validation/Track00000"],
        "exclusiones": [],
        "reportes": [
            {
                "tema_id": "validation/Track00000",
                "num_referencias": len(si_sdr_emparejadas) + num_sin_pareja,
                "num_estimaciones_recibidas": len(si_sdr_emparejadas),
                "emparejadas": [
                    {
                        "identificador_referencia": f"S{i:02d}",
                        "identificador_estimacion": "guitar",
                        "si_sdr": valor,
                    }
                    for i, valor in enumerate(si_sdr_emparejadas)
                ],
                "sin_pareja": [
                    {"identificador_referencia": f"X{i:02d}", "motivo": "sin_estimacion_disponible"}
                    for i in range(num_sin_pareja)
                ],
            }
        ],
        "transformaciones_por_tema": {},
        "mediana": None,
        "distribucion_referencias_por_tema": {},
    }


def _escribir_artefacto(
    mediciones_dir: Path, modo: str, si_sdr_emparejadas: list[float], num_sin_pareja: int = 0
) -> None:
    mediciones_dir.mkdir(parents=True, exist_ok=True)
    artefacto = _artefacto(modo, si_sdr_emparejadas, num_sin_pareja)
    (mediciones_dir / f"{modo}.json").write_text(json.dumps(artefacto))


def test_sin_modo_falla_antes_de_leer_ningun_archivo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as excinfo:
        compuerta.main([])

    assert excinfo.value.code != 0
    assert "--modo" in capsys.readouterr().err


def test_modo_invalido_falla_con_mensaje_claro(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as excinfo:
        compuerta.main(["--modo", "no_existe"])

    assert excinfo.value.code != 0
    assert "--modo" in capsys.readouterr().err


def test_solo_existe_submuestra_hito1_y_se_juzga_sin_que_el_otro_exista(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """C3 de /speckit-analyze: un solo artefacto presente -- prueba
    independencia real, no solo que cada modo lee el suyo cuando ambos
    existen (spec.md FR-008, US3 AS1). También fija el contenido del
    veredicto impreso a stdout (contracts/compuerta.md, postcondición 4
    de `main`): ningún test anterior lo comprobaba."""
    monkeypatch.chdir(tmp_path)
    _escribir_artefacto(tmp_path / "mediciones", "submuestra_hito1", [-3.0, -2.0], num_sin_pareja=1)
    assert not (tmp_path / "mediciones" / "conjunto_completo.json").exists()

    codigo = compuerta.main(["--modo", "submuestra_hito1"])

    assert codigo == 0
    salida = capsys.readouterr().out
    assert salida.startswith("APROBADO -- ")
    assert "-2.50" in salida
    assert "1/3" in salida  # total_sin_pareja/(total_emparejadas + total_sin_pareja)
    assert "5c90dfd2" in salida
    assert "submuestra_hito1" in salida


def test_solo_existe_conjunto_completo_y_se_juzga_sin_que_el_otro_exista(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Simétrico al anterior, y con una mediana que rechaza -- confirma
    que ambos modos comparan contra el mismo PRESUPUESTO_SI_SDR_DB, y fija
    la palabra "RECHAZADO" en la salida (el mismo mecanismo de impresión
    que el caso de aprobación, pero la otra rama del condicional)."""
    monkeypatch.chdir(tmp_path)
    _escribir_artefacto(tmp_path / "mediciones", "conjunto_completo", [-20.0, -15.0])
    assert not (tmp_path / "mediciones" / "submuestra_hito1.json").exists()

    codigo = compuerta.main(["--modo", "conjunto_completo"])

    assert codigo == 1
    assert capsys.readouterr().out.startswith("RECHAZADO -- ")


def test_artefacto_ausente_devuelve_codigo_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    codigo = compuerta.main(["--modo", "submuestra_hito1"])

    assert codigo == 2
    assert "submuestra_hito1.json" in capsys.readouterr().err
