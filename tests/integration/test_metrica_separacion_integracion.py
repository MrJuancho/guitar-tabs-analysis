"""Tests de integración end-to-end para `emparejar_tema()` (T010-T015 de
`specs/002-metrica-separacion-guitarra/tasks.md`, User Story 1/P1).

Cada test construye referencias/estimaciones sintéticas vía
`tests/fixtures/metrica_separacion_fixture.py` -- nunca audio real del
dataset (constitución Principio IV) -- y ejercita `emparejar_tema()` de
punta a punta.
"""

from __future__ import annotations

import numpy as np

from guitar_tabs_analysis.analytics.metrica_separacion import emparejar_tema
from tests.fixtures.metrica_separacion_fixture import (
    estimacion_sintetica,
    onda_senoidal,
    referencia_sintetica,
    silencio,
)


def test_una_referencia_una_estimacion_que_la_aproxima() -> None:
    """spec.md Acceptance Scenario US1.1."""
    onda = onda_senoidal(n_muestras=2000, frecuencia_onda=220.0)
    ruido = np.random.default_rng(1).standard_normal(2000) * 20.0
    referencia = referencia_sintetica(identificador_origen="S01", muestras=onda)
    estimacion = estimacion_sintetica(identificador="sep_S01", muestras=onda + ruido)

    reporte = emparejar_tema([referencia], [estimacion])

    assert reporte.num_referencias == 1
    assert reporte.num_estimaciones_recibidas == 1
    assert reporte.sin_pareja == []
    assert len(reporte.emparejadas) == 1
    emparejada = reporte.emparejadas[0]
    assert emparejada.identificador_referencia == "S01"
    assert emparejada.identificador_estimacion == "sep_S01"
    assert np.isfinite(emparejada.si_sdr)


def test_varias_referencias_cada_una_emparejada_con_una_estimacion_distinta() -> None:
    """spec.md Acceptance Scenario US1.2, FR-002."""
    referencias = []
    estimaciones = []
    for identificador, frecuencia in [("S01", 220.0), ("S02", 330.0), ("S03", 440.0)]:
        onda = onda_senoidal(n_muestras=2000, frecuencia_onda=frecuencia)
        ruido = np.random.default_rng(hash(identificador) % (2**32)).standard_normal(2000) * 10.0
        referencias.append(referencia_sintetica(identificador_origen=identificador, muestras=onda))
        estimaciones.append(
            estimacion_sintetica(identificador=f"sep_{identificador}", muestras=onda + ruido)
        )

    reporte = emparejar_tema(referencias, estimaciones)

    assert reporte.sin_pareja == []
    assert len(reporte.emparejadas) == 3
    identificadores_estimacion = [e.identificador_estimacion for e in reporte.emparejadas]
    assert len(set(identificadores_estimacion)) == 3
    # Cada referencia se empareja con la estimación construida a partir de
    # su propia onda (mejor correlación por construcción, frecuencias
    # distintas entre referencias) -- confirma que la asignación óptima
    # no es una asignación arbitraria cualquiera.
    for emparejada in reporte.emparejadas:
        sufijo = emparejada.identificador_referencia
        assert emparejada.identificador_estimacion == f"sep_{sufijo}"


def test_mas_referencias_que_estimaciones_las_sobrantes_sin_pareja() -> None:
    """spec.md Acceptance Scenario US1.3, FR-003."""
    referencias = [
        referencia_sintetica(
            identificador_origen=f"S0{i}",
            muestras=onda_senoidal(n_muestras=1000, frecuencia_onda=220.0 * i),
        )
        for i in range(1, 4)
    ]
    estimacion = estimacion_sintetica(
        identificador="sep_S01", muestras=onda_senoidal(n_muestras=1000, frecuencia_onda=220.0)
    )

    reporte = emparejar_tema(referencias, [estimacion])

    assert reporte.num_referencias == 3
    assert reporte.num_estimaciones_recibidas == 1
    assert len(reporte.emparejadas) == 1
    assert len(reporte.sin_pareja) == 2
    for sin_pareja in reporte.sin_pareja:
        assert sin_pareja.motivo == "sin_estimacion_disponible"


def test_cero_estimaciones_todas_las_referencias_sin_pareja() -> None:
    """spec.md Acceptance Scenario US1.4."""
    referencias = [
        referencia_sintetica(
            identificador_origen=f"S0{i}",
            muestras=onda_senoidal(n_muestras=500, frecuencia_onda=220.0 * i),
        )
        for i in range(1, 3)
    ]

    reporte = emparejar_tema(referencias, [])

    assert reporte.num_estimaciones_recibidas == 0
    assert reporte.emparejadas == []
    assert len(reporte.sin_pareja) == 2
    assert all(sp.motivo == "sin_estimacion_disponible" for sp in reporte.sin_pareja)


def test_verificacion_respuesta_conocida_referencia_como_su_propia_estimacion() -> None:
    """spec.md Acceptance Scenario US1.5, FR-011, SC-001 -- verificación
    completa a través de emparejar_tema(), no solo si_sdr() aislada."""
    referencias = []
    estimaciones = []
    for i in range(1, 4):
        onda = onda_senoidal(n_muestras=1500, frecuencia_onda=220.0 * i)
        referencias.append(referencia_sintetica(identificador_origen=f"S0{i}", muestras=onda))
        estimaciones.append(estimacion_sintetica(identificador=f"sep_S0{i}", muestras=onda.copy()))

    reporte = emparejar_tema(referencias, estimaciones)

    assert reporte.sin_pareja == []
    assert len(reporte.emparejadas) == 3
    for emparejada in reporte.emparejadas:
        assert emparejada.si_sdr == float("inf")


def test_referencia_de_energia_nula_entre_otras_con_energia() -> None:
    """spec.md Acceptance Scenario US1.6, FR-006, SC-006."""
    referencia_silenciosa = referencia_sintetica(
        identificador_origen="S_silenciosa", muestras=silencio(1000)
    )
    onda = onda_senoidal(n_muestras=1000, frecuencia_onda=220.0)
    referencia_normal = referencia_sintetica(identificador_origen="S_normal", muestras=onda)
    estimacion = estimacion_sintetica(identificador="sep_S_normal", muestras=onda.copy())

    reporte = emparejar_tema([referencia_silenciosa, referencia_normal], [estimacion])

    assert len(reporte.sin_pareja) == 1
    assert reporte.sin_pareja[0].identificador_referencia == "S_silenciosa"
    assert reporte.sin_pareja[0].motivo == "energia_nula"
    assert len(reporte.emparejadas) == 1
    assert reporte.emparejadas[0].identificador_referencia == "S_normal"
    assert reporte.emparejadas[0].si_sdr == float("inf")


def test_estimacion_asignada_silenciosa_se_reporta_sin_pareja_no_emparejada() -> None:
    """spec.md Acceptance Scenario US1.7, FR-016, SC-009 -- la única
    estimación disponible para esta referencia es silenciosa: la
    asignación óptima se la da igual (research.md #11), pero el reporte
    la reclasifica a sin_pareja en vez de dejarla en emparejadas con
    si_sdr == -inf."""
    referencia = referencia_sintetica(
        identificador_origen="S01", muestras=onda_senoidal(n_muestras=800, frecuencia_onda=220.0)
    )
    estimacion_silenciosa = estimacion_sintetica(
        identificador="sep_S01_silencio", muestras=silencio(800)
    )

    reporte = emparejar_tema([referencia], [estimacion_silenciosa])

    assert reporte.emparejadas == []
    assert len(reporte.sin_pareja) == 1
    assert reporte.sin_pareja[0].identificador_referencia == "S01"
    assert reporte.sin_pareja[0].motivo == "estimacion_silenciosa"
