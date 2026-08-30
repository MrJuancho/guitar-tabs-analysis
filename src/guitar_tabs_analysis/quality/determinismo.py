"""Verificación de determinismo del pipeline (gate `pipeline_es_determinista`).

ESPECÍFICO DEL DOMINIO -- esqueleto FUNCIONAL genérico: compara dos
DataFrames que deberían ser dos corridas completas del mismo pipeline sobre
la misma entrada. Si cualquier columna difiere en algo que no sea un
timestamp de generación, el pipeline no es reproducible y ninguna cifra
publicada con él es confiable.

TODO: si tu pipeline tiene un orquestador propio (un `pipeline.py`,
`main.py`), la orquestación de "correr dos veces y comparar" debería vivir
ahí o en el `justfile` (recipe `determinismo`), NO aquí -- este módulo solo
debería poder LEER artefactos, no importar el orquestador. Si lo hiciera,
y el orquestador importa `analytics`, este módulo terminaría dependiendo
transitivamente de `analytics` -- prohibido por el contrato de
import-linter "quality es transversal" en pyproject.toml (import-linter
sí sigue cadenas de imports, no solo directos).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

_COLUMNAS_IGNORADAS = {"timestamp_generacion", "timestamp_ejecucion"}


@dataclass(frozen=True)
class ResultadoDeterminismo:
    es_determinista: bool
    diferencias: list[str] = field(default_factory=list)


def verificar_determinismo(
    corrida_a: pd.DataFrame, corrida_b: pd.DataFrame
) -> ResultadoDeterminismo:
    """Compara dos corridas del mismo artefacto. Solo se ignoran columnas de
    timestamp -- cualquier otra diferencia significa que el pipeline no es
    reproducible."""
    if list(corrida_a.columns) != list(corrida_b.columns):
        return ResultadoDeterminismo(es_determinista=False, diferencias=["columnas distintas"])

    columnas = [c for c in corrida_a.columns if c not in _COLUMNAS_IGNORADAS]
    if not corrida_a[columnas].equals(corrida_b[columnas]):
        return ResultadoDeterminismo(
            es_determinista=False,
            diferencias=["contenido distinto (excluyendo timestamps)"],
        )
    return ResultadoDeterminismo(es_determinista=True)
