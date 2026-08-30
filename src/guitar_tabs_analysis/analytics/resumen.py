"""EJEMPLO -- capa de analytics (nivel más alto del contrato de
import-linter en pyproject.toml). Importa de `ingestion`, nunca al revés
-- esa dirección es justo lo que el contrato `type = "layers"` verifica.
Reemplaza este módulo por las agregaciones reales de tu dominio.
"""

from __future__ import annotations

from collections import Counter

from guitar_tabs_analysis.ingestion.normalizar import normalizar_texto


def contar_valores_unicos(valores: list[str]) -> dict[str, int]:
    """Normaliza cada valor y cuenta ocurrencias -- dos valores que solo
    difieren en mayúsculas o espacios cuentan como el mismo."""
    return dict(Counter(normalizar_texto(v) for v in valores))
