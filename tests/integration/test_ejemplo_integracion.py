"""EJEMPLO -- test de integración: ejercita más de un módulo del esqueleto
junto (ingestion -> analytics -> quality), a diferencia de tests/unit/ que
prueba cada función aislada. TODO: reemplaza por la integración real de tu
pipeline (varias etapas encadenadas, no solo funciones puras).
"""

from __future__ import annotations

import pandas as pd

from guitar_tabs_analysis.analytics.resumen import contar_valores_unicos
from guitar_tabs_analysis.quality.gates import evaluar_gates


def test_conteo_normalizado_alimenta_el_gate_de_calidad() -> None:
    valores = ["Ejemplo", " ejemplo ", "", "Otro"]
    conteo = contar_valores_unicos(valores)
    df = pd.DataFrame({"valor": list(conteo.keys())})

    resultados = evaluar_gates(df)

    assert conteo["ejemplo"] == 2
    assert all(r.nombre == "pct_valores_vacios" for r in resultados)
