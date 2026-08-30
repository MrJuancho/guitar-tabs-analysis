"""Fixtures del hold-out. NO visible para agentes de código (ver AGENTS.md
y .claude/hooks/block_holdout.py -- ese hook es la barrera real).

EJEMPLO -- genera datos 100% sintéticos en memoria, sin depender de
tests/fixtures/ (que sí es visible/editable) para que la construcción del
caso de prueba en sí no pueda "afinarse" junto con el código bajo prueba.
TODO: si tu dominio real tiene un pipeline con más pasos, constrúyelo aquí
end-to-end (ver el comentario de `verificar_determinismo` en
quality/determinismo.py sobre por qué esa orquestación no vive en
quality/).
"""

from __future__ import annotations

import pandas as pd
import pytest

from guitar_tabs_analysis.analytics.resumen import contar_valores_unicos


@pytest.fixture(scope="session")
def conteo_sintetico() -> dict[str, int]:
    valores = ["Ejemplo Sintetico", " ejemplo sintetico ", "Otro Sintetico", ""]
    return contar_valores_unicos(valores)


@pytest.fixture(scope="session")
def df_sintetico(conteo_sintetico: dict[str, int]) -> pd.DataFrame:
    return pd.DataFrame({"valor": list(conteo_sintetico.keys())})
