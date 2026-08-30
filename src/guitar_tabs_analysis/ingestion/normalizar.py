"""EJEMPLO -- capa de ingestion (nivel más bajo del contrato de import-linter
en pyproject.toml). Reemplaza este módulo por la lectura/limpieza real de
tu fuente de datos; conserva el patrón: ingestion no importa de analytics
ni de quality, solo produce valores que las capas de arriba consumen.
"""

from __future__ import annotations


def normalizar_texto(valor: str) -> str:
    """Recorta espacios y normaliza mayúsculas/minúsculas.

    Idempotente a propósito -- `normalizar_texto(normalizar_texto(x)) ==
    normalizar_texto(x)` para cualquier `x`, la propiedad que
    `tests/property/test_ingestion_property.py` verifica con Hypothesis.
    """
    return valor.strip().casefold()
