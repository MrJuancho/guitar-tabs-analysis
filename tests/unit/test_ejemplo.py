"""EJEMPLO -- tests unitarios del esqueleto de dominio (`ingestion`,
`analytics`, `quality`). Bórralos junto con el código de ejemplo cuando
implementes tu dominio real; hasta entonces mantienen `just gauntlet`
(cobertura >=90%) en verde sobre este template recién generado.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from guitar_tabs_analysis.analytics.resumen import contar_valores_unicos
from guitar_tabs_analysis.ingestion.normalizar import normalizar_texto
from guitar_tabs_analysis.quality.determinismo import verificar_determinismo
from guitar_tabs_analysis.quality.gates import (
    GOLD_GATES,
    evaluar_gates,
    main,
    medir_metricas_calidad,
)


def test_normalizar_texto_recorta_y_normaliza_mayusculas() -> None:
    assert normalizar_texto("  Ejemplo  ") == "ejemplo"


def test_normalizar_texto_es_idempotente_en_un_caso_concreto() -> None:
    valor = "  Ejemplo  "
    assert normalizar_texto(normalizar_texto(valor)) == normalizar_texto(valor)


def test_contar_valores_unicos_agrupa_por_valor_normalizado() -> None:
    conteo = contar_valores_unicos(["Ejemplo", " ejemplo ", "Otro"])
    assert conteo == {"ejemplo": 2, "otro": 1}


def test_medir_metricas_calidad_sobre_dataframe_vacio() -> None:
    df = pd.DataFrame({"valor": []})
    assert medir_metricas_calidad(df)["pct_valores_vacios"] == 0.0


def test_evaluar_gates_aprueba_dentro_del_presupuesto() -> None:
    df = pd.DataFrame({"valor": ["a", "b", "c", "d"]})
    resultados = evaluar_gates(df)
    por_nombre = {r.nombre: r for r in resultados}
    assert por_nombre["pct_valores_vacios"].aprueba is True
    assert set(por_nombre) == set(GOLD_GATES)


def test_evaluar_gates_reprueba_fuera_del_presupuesto() -> None:
    df = pd.DataFrame({"valor": ["", "", "", "d"]})
    resultados = evaluar_gates(df)
    por_nombre = {r.nombre: r for r in resultados}
    assert por_nombre["pct_valores_vacios"].aprueba is False


def test_verificar_determinismo_detecta_columnas_distintas() -> None:
    a = pd.DataFrame({"x": [1, 2]})
    b = pd.DataFrame({"y": [1, 2]})
    resultado = verificar_determinismo(a, b)
    assert resultado.es_determinista is False
    assert "columnas distintas" in resultado.diferencias[0]


def test_verificar_determinismo_ignora_timestamps() -> None:
    a = pd.DataFrame({"x": [1, 2], "timestamp_generacion": ["t1", "t1"]})
    b = pd.DataFrame({"x": [1, 2], "timestamp_generacion": ["t2", "t2"]})
    assert verificar_determinismo(a, b).es_determinista is True


def test_verificar_determinismo_detecta_contenido_distinto() -> None:
    a = pd.DataFrame({"x": [1, 2]})
    b = pd.DataFrame({"x": [1, 3]})
    resultado = verificar_determinismo(a, b)
    assert resultado.es_determinista is False
    assert "contenido distinto" in resultado.diferencias[0]


def test_main_falla_si_no_existe_el_artefacto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert main() == 1


def test_main_evalua_el_artefacto_de_ejemplo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    gold = tmp_path / "data" / "gold"
    gold.mkdir(parents=True)
    pd.DataFrame({"valor": ["a", "b", "c"]}).to_parquet(gold / "ejemplo.parquet")
    monkeypatch.chdir(tmp_path)
    assert main() == 0
    assert "pct_valores_vacios" in capsys.readouterr().out


def test_main_reporta_falla_cuando_el_gate_se_excede(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    gold = tmp_path / "data" / "gold"
    gold.mkdir(parents=True)
    pd.DataFrame({"valor": ["", "", "a"]}).to_parquet(gold / "ejemplo.parquet")
    monkeypatch.chdir(tmp_path)
    assert main() == 1
    assert "[FALLA]" in capsys.readouterr().out
