"""Tests de retención. NO visibles para agentes de código (ver AGENTS.md).

EJEMPLO -- verifica una invariante de dominio (aquí: "el gate de ejemplo
nunca reporta un porcentaje fuera de [0, 1]"), no implementación. Si un
cambio pasa tests/unit, tests/integration y tests/property pero falla
aquí, el cambio se afinó a los tests visibles en vez de resolver el
problema real -- esa es la señal que este directorio existe para atrapar.
TODO: reemplaza por las invariantes reales de tu dominio.
"""

from __future__ import annotations

import pandas as pd

from guitar_tabs_analysis.quality.gates import evaluar_gates


def test_pct_valores_vacios_esta_siempre_entre_cero_y_uno(df_sintetico: pd.DataFrame) -> None:
    resultados = evaluar_gates(df_sintetico)
    por_nombre = {r.nombre: r for r in resultados}
    assert 0.0 <= por_nombre["pct_valores_vacios"].valor <= 1.0


def test_conteo_sintetico_no_pierde_valores_no_vacios(conteo_sintetico: dict[str, int]) -> None:
    """Invariante de dominio: agrupar por valor normalizado nunca debe
    hacer desaparecer un valor no vacío -- solo puede fusionar duplicados."""
    assert sum(conteo_sintetico.values()) == 4
    assert conteo_sintetico.get("ejemplo sintetico") == 2
