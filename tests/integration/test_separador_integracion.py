"""Integration tests de User Story 3 (`spec.md`): distinguir ausencia
total de estimación (FR-009) de una estimación real que resulta
silenciosa (FR-010). Sin tareas de implementación propias -- ambos
caminos ya los produce `separar_guitarra` (US1, T011) por construcción;
ver nota de alcance de la Fase 7 en tasks.md.
"""

from __future__ import annotations

import numpy as np

from guitar_tabs_analysis.separacion.separador import separar_guitarra
from tests.fixtures.separador_fixture import SeparadorFalso, mezcla_sintetica


def test_ausencia_total_de_estimacion_da_coleccion_vacia() -> None:
    """AS1 US3: el separador no produce ninguna salida de guitarra ->
    colección vacía, nunca una estimación sintética (FR-009)."""
    mezcla = mezcla_sintetica(n_muestras=100)
    separador = SeparadorFalso(omitir_guitarra=True)

    resultado = separar_guitarra("Track00001", mezcla, separador)

    assert resultado.estimaciones == []


def test_estimacion_silenciosa_se_entrega_intacta_no_se_omite() -> None:
    """AS2 US3: el separador SÍ produce una salida de guitarra, pero es
    silencio digital -> se entrega como Estimacion real (FR-010); esta
    feature no la reclasifica, eso es responsabilidad de la Feature 002
    (emparejar_tema)."""
    mezcla = mezcla_sintetica(n_muestras=10)
    silencio = np.zeros(10)
    separador = SeparadorFalso(audio_channels=1, salida={"guitar": silencio})

    resultado = separar_guitarra("Track00001", mezcla, separador)

    assert len(resultado.estimaciones) == 1
    (estimacion,) = resultado.estimaciones
    np.testing.assert_array_equal(estimacion.audio.muestras, silencio)
