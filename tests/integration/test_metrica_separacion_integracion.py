"""Tests de integración end-to-end para `emparejar_tema()`/`agregar_conjunto()`
(T010-T024 de `specs/002-metrica-separacion-guitarra/tasks.md`, User
Story 1/P1 y User Story 2/P2).

Cada test construye referencias/estimaciones sintéticas vía
`tests/fixtures/metrica_separacion_fixture.py` -- nunca audio real del
dataset (constitución Principio IV).
"""

from __future__ import annotations

import statistics

import numpy as np

from guitar_tabs_analysis.analytics.metrica_separacion import (
    EntradaConjunto,
    agregar_conjunto,
    emparejar_tema,
    si_sdr,
)
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

    reporte = emparejar_tema("Track00001", [referencia], [estimacion])

    assert reporte.tema_id == "Track00001"
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

    reporte = emparejar_tema("Track00001", referencias, estimaciones)

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

    reporte = emparejar_tema("Track00001", referencias, [estimacion])

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

    reporte = emparejar_tema("Track00001", referencias, [])

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

    reporte = emparejar_tema("Track00001", referencias, estimaciones)

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

    reporte = emparejar_tema("Track00001", [referencia_silenciosa, referencia_normal], [estimacion])

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

    reporte = emparejar_tema("Track00001", [referencia], [estimacion_silenciosa])

    assert reporte.emparejadas == []
    assert len(reporte.sin_pareja) == 1
    assert reporte.sin_pareja[0].identificador_referencia == "S01"
    assert reporte.sin_pareja[0].motivo == "estimacion_silenciosa"


def test_tema_sin_ninguna_referencia_se_excluye_sin_guitarra_referencia() -> None:
    """spec.md AS US2.2, FR-009."""
    onda = onda_senoidal(n_muestras=500, frecuencia_onda=220.0)
    referencia = referencia_sintetica(identificador_origen="S01", muestras=onda)
    estimacion = estimacion_sintetica(identificador="sep_S01", muestras=onda.copy())

    entradas = [
        EntradaConjunto("TrackSinGuitarra", [], [], es_directorio_omitido=False),
        EntradaConjunto("TrackNormal", [referencia], [estimacion], es_directorio_omitido=False),
    ]

    resultado = agregar_conjunto(entradas)

    assert len(resultado.exclusiones) == 1
    assert resultado.exclusiones[0].tema_id == "TrackSinGuitarra"
    assert resultado.exclusiones[0].motivo == "sin_guitarra_referencia"
    assert resultado.num_temas_evaluados == 1
    assert all(r.tema_id != "TrackSinGuitarra" for r in resultado.reportes_por_tema)


def test_tema_del_directorio_omitido_se_excluye_con_o_sin_referencias() -> None:
    """spec.md AS US2.3, FR-010, research.md #10 (prioridad sobre FR-009
    cuando ambos motivos aplicarían a la vez)."""
    onda = onda_senoidal(n_muestras=500, frecuencia_onda=220.0)
    referencia = referencia_sintetica(identificador_origen="S01", muestras=onda)

    entradas = [
        # Tiene referencias -- sin es_directorio_omitido, no se excluiría
        # por FR-009. Con es_directorio_omitido=True, se excluye igual.
        EntradaConjunto("TrackOmitidoConReferencias", [referencia], [], es_directorio_omitido=True),
        # Ambos motivos aplicarían (sin referencias Y omitido) -- gana
        # "directorio_omitido" (research.md #10).
        EntradaConjunto("TrackOmitidoSinReferencias", [], [], es_directorio_omitido=True),
    ]

    resultado = agregar_conjunto(entradas)

    assert resultado.num_temas_evaluados == 0
    assert len(resultado.exclusiones) == 2
    motivos = {e.tema_id: e.motivo for e in resultado.exclusiones}
    assert motivos["TrackOmitidoConReferencias"] == "directorio_omitido"
    assert motivos["TrackOmitidoSinReferencias"] == "directorio_omitido"


def test_tema_con_referencias_pero_sin_estimaciones_permanece_evaluado() -> None:
    """spec.md AS US2.4, FR-008 -- distinto de excluir: el tema SÍ tiene
    guitarras de referencia, solo que el separador no produjo nada para
    él; sus referencias entran a la mediana como -inf, no desaparecen."""
    referencia = referencia_sintetica(
        identificador_origen="S01", muestras=onda_senoidal(n_muestras=500, frecuencia_onda=220.0)
    )

    entradas = [
        EntradaConjunto("TrackSinEstimaciones", [referencia], [], es_directorio_omitido=False)
    ]

    resultado = agregar_conjunto(entradas)

    assert resultado.exclusiones == []
    assert resultado.num_temas_evaluados == 1
    assert len(resultado.reportes_por_tema) == 1
    assert resultado.reportes_por_tema[0].sin_pareja[0].motivo == "sin_estimacion_disponible"
    assert resultado.mediana == float("-inf")


def test_distribucion_y_mediana_ponderada_por_referencia_no_por_tema() -> None:
    """spec.md AS US2.6/US2.7, FR-007, FR-015 -- la mediana pesa cada
    referencia individualmente; un tema con más referencias influye
    proporcionalmente más, no se colapsa primero a un solo valor por
    tema."""
    rng = np.random.default_rng(7)

    def par(
        id_ref: str, id_est: str, n: int, ruido_amplitud: float
    ) -> tuple[object, object, float]:
        onda = onda_senoidal(n_muestras=n, frecuencia_onda=220.0)
        ruido = rng.standard_normal(n) * ruido_amplitud
        referencia = referencia_sintetica(identificador_origen=id_ref, muestras=onda)
        estimacion = estimacion_sintetica(identificador=id_est, muestras=onda + ruido)
        valor = si_sdr(referencia, estimacion)
        return referencia, estimacion, valor

    ref1, est1, v1 = par("A01", "sepA01", 1000, 5.0)
    ref2a, est2a, v2a = par("B01", "sepB01", 1000, 20.0)
    ref2b, est2b, v2b = par("B02", "sepB02", 1000, 40.0)
    ref3a, est3a, v3a = par("C01", "sepC01", 1000, 60.0)
    ref3b, est3b, v3b = par("C02", "sepC02", 1000, 80.0)
    ref3c, est3c, v3c = par("C03", "sepC03", 1000, 100.0)

    entradas = [
        EntradaConjunto("TrackA", [ref1], [est1], es_directorio_omitido=False),
        EntradaConjunto("TrackB", [ref2a, ref2b], [est2a, est2b], es_directorio_omitido=False),
        EntradaConjunto(
            "TrackC", [ref3a, ref3b, ref3c], [est3a, est3b, est3c], es_directorio_omitido=False
        ),
    ]

    resultado = agregar_conjunto(entradas)

    assert resultado.distribucion_referencias_por_tema == {1: 1, 2: 1, 3: 1}

    pool_plano = [v1, v2a, v2b, v3a, v3b, v3c]
    assert resultado.mediana == statistics.median(pool_plano)

    # La alternativa incorrecta (mediana de medianas por tema) da un
    # número distinto -- confirma que la agregación no colapsa primero
    # cada tema a un solo valor (spec.md#Assumptions, ponderación).
    mediana_por_tema_incorrecta = statistics.median(
        [statistics.median([v1]), statistics.median([v2a, v2b]), statistics.median([v3a, v3b, v3c])]
    )
    assert resultado.mediana != mediana_por_tema_incorrecta


def test_pool_par_con_inf_y_menos_inf_como_valores_centrales_no_produce_nan() -> None:
    """Regresión (T027, hallada por Hypothesis sobre
    test_incluir_tema_completamente_sin_emparejar_nunca_mejora_la_mediana
    durante `just mutation`, 2026-09-04): un tema con una referencia
    igual bit a bit a su propia estimación (+inf exacto, research.md #5)
    y un segundo tema completamente sin emparejar (-inf, FR-008) arman
    un pool de 2 elementos cuyos dos valores centrales son +inf y -inf.
    `statistics.median` promedia esos dos valores (`(inf + -inf) / 2`),
    y esa suma es NaN en IEEE754 -- rompe la premisa de FR-007/FR-008 de
    que la mediana aquí es un estadístico de orden puro, insensible a la
    magnitud. `agregar_conjunto` nunca debe devolver NaN: entre los dos
    valores centrales que producirían NaN al promediarse, se resuelve al
    más bajo (política pesimista, consistente con FR-008/Principio V) en
    vez de dejar escapar el artefacto de punto flotante."""
    onda = onda_senoidal(n_muestras=50, frecuencia_onda=220.0)
    referencia = referencia_sintetica(identificador_origen="R00", muestras=onda)
    estimacion = estimacion_sintetica(identificador="E00", muestras=onda.copy())
    referencia_extra = referencia_sintetica(identificador_origen="Extra_R00", muestras=onda.copy())

    entradas_base = [
        EntradaConjunto("TrackConEstimacionExacta", [referencia], [estimacion], False)
    ]
    tema_extra = EntradaConjunto("TrackExtraTodoSinEmparejar", [referencia_extra], [], False)

    resultado_sin = agregar_conjunto(entradas_base)
    resultado_con = agregar_conjunto([*entradas_base, tema_extra])

    assert resultado_sin.mediana == float("inf")
    assert resultado_con.mediana == float("-inf")
    assert resultado_con.mediana <= resultado_sin.mediana


def test_conjunto_vacio_y_conjunto_completamente_excluido_dan_mediana_none() -> None:
    """FR-014 -- la mediana de nada no existe; se reporta explícitamente
    como conjunto vacío evaluado, nunca como error ni como 0.0."""
    resultado_vacio = agregar_conjunto([])
    assert resultado_vacio.mediana is None
    assert resultado_vacio.num_temas_evaluados == 0
    assert resultado_vacio.exclusiones == []
    assert resultado_vacio.reportes_por_tema == []
    assert resultado_vacio.distribucion_referencias_por_tema == {}

    referencia = referencia_sintetica(
        identificador_origen="S01", muestras=onda_senoidal(n_muestras=500, frecuencia_onda=220.0)
    )
    entradas_todas_excluidas = [
        EntradaConjunto("TrackSinGuitarra", [], [], es_directorio_omitido=False),
        EntradaConjunto("TrackOmitido", [referencia], [], es_directorio_omitido=True),
    ]

    resultado_excluido = agregar_conjunto(entradas_todas_excluidas)

    assert resultado_excluido.mediana is None
    assert resultado_excluido.num_temas_evaluados == 0
    assert len(resultado_excluido.exclusiones) == 2
    assert resultado_excluido.reportes_por_tema == []
