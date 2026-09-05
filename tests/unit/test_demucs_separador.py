"""Tests unitarios de `separacion.demucs_separador` -- solo la
declaración fija del modelo (`MODELO_DECLARADO`), consultable sin
instanciar `DemucsSeparador` ni tocar la red (User Story 2,
Independent Test de `spec.md`).

Importar este módulo sí importa `torch`/`demucs` (unos segundos de carga
de librería), pero no descarga ni carga ningún peso -- eso solo ocurre al
construir `DemucsSeparador()`, que este archivo no hace.
"""

from __future__ import annotations

from guitar_tabs_analysis.separacion.demucs_separador import MODELO_DECLARADO


def test_modelo_declarado_tiene_los_valores_verificados() -> None:
    """AS1 US2: nombre, variante, firma y checksum quedan fijos y
    consultables (FR-002), verificados en vivo contra el modelo real
    (research.md #1/#2)."""
    assert MODELO_DECLARADO.nombre == "Demucs"
    assert MODELO_DECLARADO.variante == "htdemucs_6s"
    assert MODELO_DECLARADO.firma == "5c90dfd2"
    assert MODELO_DECLARADO.checksum_sha256_prefijo == "d2a1745f0744"


def test_modelo_declarado_es_consulta_idempotente() -> None:
    """Dos importaciones sucesivas del módulo devuelven el mismo valor
    -- una declaración fija, no algo que cambie entre consultas."""
    from guitar_tabs_analysis.separacion.demucs_separador import (
        MODELO_DECLARADO as segunda_consulta,
    )

    assert MODELO_DECLARADO is segunda_consulta
