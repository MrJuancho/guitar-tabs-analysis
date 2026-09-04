"""Tests unitarios para los tipos, excepciones y `si_sdr()` del módulo
`analytics.metrica_separacion` (T003, T005 de
`specs/002-metrica-separacion-guitarra/tasks.md`).

No prueba `emparejar_tema()` ni `agregar_conjunto()` -- esas funciones
(y sus tests de integración/property) son las Fases 3-4 (T010 en
adelante) de `tasks.md`, fuera del alcance de este slice.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from guitar_tabs_analysis.analytics.metrica_separacion import (
    EntradaConjunto,
    Estimacion,
    EstimacionIncompatibleError,
    Exclusion,
    ReferenciaEmparejada,
    ReferenciaEnergiaNulaError,
    ReferenciaSinPareja,
    ReporteTema,
    ResultadoAgregado,
    si_sdr,
)
from guitar_tabs_analysis.ingestion.slakh2100 import PistaAudio, PistaGuitarra
from tests.fixtures.metrica_separacion_fixture import (
    estimacion_sintetica,
    onda_senoidal,
    referencia_sintetica,
    silencio,
)

# ---------------------------------------------------------------------
# T003: Estimacion, ReferenciaEmparejada, ReferenciaSinPareja,
# ReporteTema, EntradaConjunto, Exclusion, ResultadoAgregado, y las
# excepciones EstimacionIncompatibleError / ReferenciaEnergiaNulaError.
# ---------------------------------------------------------------------


def test_estimacion_expone_identificador_y_audio() -> None:
    audio = PistaAudio(muestras=np.array([1, -1], dtype=np.int16), frecuencia_muestreo=44100)
    estimacion = Estimacion(identificador="sep_S01", audio=audio)
    assert estimacion.identificador == "sep_S01"
    assert estimacion.audio is audio


def test_estimacion_es_inmutable() -> None:
    audio = PistaAudio(muestras=np.array([1], dtype=np.int16), frecuencia_muestreo=44100)
    estimacion = Estimacion(identificador="sep_S01", audio=audio)
    with pytest.raises(dataclasses.FrozenInstanceError):
        estimacion.identificador = "sep_S02"  # type: ignore[misc]


def test_referencia_emparejada_expone_sus_campos() -> None:
    emparejada = ReferenciaEmparejada(
        identificador_referencia="S01", identificador_estimacion="sep_S01", si_sdr=12.5
    )
    assert emparejada.identificador_referencia == "S01"
    assert emparejada.identificador_estimacion == "sep_S01"
    assert emparejada.si_sdr == 12.5


def test_referencia_sin_pareja_expone_motivo() -> None:
    sin_pareja = ReferenciaSinPareja(identificador_referencia="S02", motivo="energia_nula")
    assert sin_pareja.identificador_referencia == "S02"
    assert sin_pareja.motivo == "energia_nula"


def test_reporte_tema_agrupa_emparejadas_y_sin_pareja() -> None:
    emparejada = ReferenciaEmparejada(
        identificador_referencia="S01", identificador_estimacion="sep_S01", si_sdr=8.0
    )
    sin_pareja = ReferenciaSinPareja(
        identificador_referencia="S02", motivo="sin_estimacion_disponible"
    )
    reporte = ReporteTema(
        tema_id="Track00001",
        num_referencias=2,
        num_estimaciones_recibidas=1,
        emparejadas=[emparejada],
        sin_pareja=[sin_pareja],
    )
    assert reporte.tema_id == "Track00001"
    assert reporte.num_referencias == 2
    assert reporte.num_estimaciones_recibidas == 1
    assert reporte.emparejadas == [emparejada]
    assert reporte.sin_pareja == [sin_pareja]


def test_reporte_tema_acepta_listas_vacias_por_defecto() -> None:
    reporte = ReporteTema(tema_id="Track00002", num_referencias=0, num_estimaciones_recibidas=0)
    assert reporte.emparejadas == []
    assert reporte.sin_pareja == []


def test_entrada_conjunto_expone_sus_campos() -> None:
    audio = PistaAudio(muestras=np.array([1], dtype=np.int16), frecuencia_muestreo=44100)
    referencia = PistaGuitarra(identificador_origen="S01", audio=audio)
    estimacion = Estimacion(identificador="sep_S01", audio=audio)
    entrada = EntradaConjunto(
        tema_id="Track00001",
        referencias=[referencia],
        estimaciones=[estimacion],
        es_directorio_omitido=False,
    )
    assert entrada.tema_id == "Track00001"
    assert entrada.referencias == [referencia]
    assert entrada.estimaciones == [estimacion]
    assert entrada.es_directorio_omitido is False


def test_exclusion_expone_tema_y_motivo() -> None:
    exclusion = Exclusion(tema_id="Track00003", motivo="directorio_omitido")
    assert exclusion.tema_id == "Track00003"
    assert exclusion.motivo == "directorio_omitido"


def test_resultado_agregado_expone_sus_campos() -> None:
    reporte = ReporteTema(tema_id="Track00001", num_referencias=1, num_estimaciones_recibidas=1)
    exclusion = Exclusion(tema_id="Track00002", motivo="sin_guitarra_referencia")
    resultado = ResultadoAgregado(
        mediana=5.0,
        num_temas_evaluados=1,
        distribucion_referencias_por_tema={1: 1},
        exclusiones=[exclusion],
        reportes_por_tema=[reporte],
    )
    assert resultado.mediana == 5.0
    assert resultado.num_temas_evaluados == 1
    assert resultado.distribucion_referencias_por_tema == {1: 1}
    assert resultado.exclusiones == [exclusion]
    assert resultado.reportes_por_tema == [reporte]


def test_resultado_agregado_acepta_mediana_none() -> None:
    resultado = ResultadoAgregado(
        mediana=None, num_temas_evaluados=0, distribucion_referencias_por_tema={}
    )
    assert resultado.mediana is None
    assert resultado.exclusiones == []
    assert resultado.reportes_por_tema == []


def test_resultado_agregado_es_inmutable() -> None:
    resultado = ResultadoAgregado(
        mediana=None, num_temas_evaluados=0, distribucion_referencias_por_tema={}
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        resultado.mediana = 1.0  # type: ignore[misc]


def test_estimacion_incompatible_error_incluye_identificadores_y_motivo() -> None:
    error = EstimacionIncompatibleError(
        identificador_referencia="S01",
        identificador_estimacion="sep_S01",
        motivo="distinta longitud (número de muestras)",
    )
    assert error.identificador_referencia == "S01"
    assert error.identificador_estimacion == "sep_S01"
    assert error.motivo == "distinta longitud (número de muestras)"
    assert str(error) == (
        "La estimación 'sep_S01' es incompatible con la referencia 'S01': "
        "distinta longitud (número de muestras)."
    )


def test_referencia_energia_nula_error_incluye_el_identificador() -> None:
    error = ReferenciaEnergiaNulaError(identificador_referencia="S03")
    assert error.identificador_referencia == "S03"
    assert str(error) == (
        "La referencia 'S03' tiene energía nula (silencio digital); "
        "el SI-SDR no está definido para ella."
    )


# ---------------------------------------------------------------------
# T005: si_sdr() (research.md #1, #3, #4, #5, #7 de
# specs/002-metrica-separacion-guitarra/).
# ---------------------------------------------------------------------


@pytest.mark.filterwarnings("error")
def test_si_sdr_referencia_como_su_propia_estimacion_da_infinito_exacto() -> None:
    onda = onda_senoidal(n_muestras=2000)
    referencia = referencia_sintetica(identificador_origen="S01", muestras=onda)
    # Copia bit-idéntica, no el mismo objeto -- confirma que la exactitud
    # de +inf no depende de una identidad de objeto "hecha trampa"
    # (research.md #5): num y den son la misma reducción de punto
    # flotante porque el CONTENIDO es idéntico, no porque sea el mismo
    # array en memoria.
    estimacion = estimacion_sintetica(identificador="sep_S01", muestras=onda.copy())

    assert si_sdr(referencia, estimacion) == float("inf")


def test_si_sdr_es_invariante_a_la_ganancia_de_la_estimacion() -> None:
    onda = onda_senoidal(n_muestras=2000)
    # Ruido independiente de la referencia -- la estimación NO es
    # proporcional a `onda`, así que esto ejercita la fórmula general,
    # no el caso exacto +inf/-inf de los otros tests de este archivo.
    ruido = np.random.default_rng(42).standard_normal(2000) * 50.0
    base = onda + ruido

    referencia = referencia_sintetica(muestras=onda)
    estimacion_ganancia_2 = estimacion_sintetica(muestras=base * 2.0)
    estimacion_ganancia_7 = estimacion_sintetica(muestras=base * 7.0)

    valor_ganancia_2 = si_sdr(referencia, estimacion_ganancia_2)
    valor_ganancia_7 = si_sdr(referencia, estimacion_ganancia_7)

    # Valor calculado, no exacto por construcción -- tolerancia numérica
    # declarada (research.md #6, constitución Principio VIII), no
    # igualdad bit a bit.
    assert valor_ganancia_2 == pytest.approx(valor_ganancia_7, rel=1e-9)


def test_si_sdr_con_estimacion_de_energia_nula_da_menos_infinito_por_convencion() -> None:
    referencia = referencia_sintetica(muestras=onda_senoidal(n_muestras=500))
    estimacion = estimacion_sintetica(muestras=silencio(500))

    # -inf está DEFINIDO por convención (research.md #5, hallazgo
    # 2026-09-04), no calculado -- por eso la igualdad exacta es
    # correcta aquí y no una tolerancia: es el valor que la
    # implementación devuelve directamente, no el resultado de una
    # acumulación de punto flotante.
    assert si_sdr(referencia, estimacion) == float("-inf")


def test_si_sdr_con_referencia_de_energia_nula_levanta_referencia_energia_nula_error() -> None:
    referencia = referencia_sintetica(identificador_origen="S05", muestras=silencio(300))
    estimacion = estimacion_sintetica(muestras=onda_senoidal(n_muestras=300))

    with pytest.raises(ReferenciaEnergiaNulaError) as exc_info:
        si_sdr(referencia, estimacion)
    assert exc_info.value.identificador_referencia == "S05"


def test_si_sdr_con_distinta_longitud_levanta_estimacion_incompatible_error() -> None:
    referencia = referencia_sintetica(
        identificador_origen="S06", muestras=onda_senoidal(n_muestras=500)
    )
    estimacion = estimacion_sintetica(
        identificador="sep_S06", muestras=onda_senoidal(n_muestras=400)
    )

    with pytest.raises(EstimacionIncompatibleError) as exc_info:
        si_sdr(referencia, estimacion)
    assert exc_info.value.identificador_referencia == "S06"
    assert exc_info.value.identificador_estimacion == "sep_S06"
    # Mensaje completo, no solo que los identificadores aparezcan
    # (AGENTS.md "Tests de excepciones") -- T027, mutation testing
    # encontró exactamente este hueco: .motivo mutado a None/mayúsculas
    # sobrevivía porque nada lo comparaba.
    assert exc_info.value.motivo == "distinta longitud (número de muestras)"
    assert str(exc_info.value) == (
        "La estimación 'sep_S06' es incompatible con la referencia 'S06': "
        "distinta longitud (número de muestras)."
    )


def test_si_sdr_con_distinta_frecuencia_de_muestreo_levanta_estimacion_incompatible_error() -> None:
    referencia = referencia_sintetica(
        identificador_origen="S07",
        frecuencia_muestreo=44100,
        muestras=onda_senoidal(n_muestras=500, frecuencia_muestreo=44100),
    )
    estimacion = estimacion_sintetica(
        identificador="sep_S07",
        frecuencia_muestreo=22050,
        muestras=onda_senoidal(n_muestras=500, frecuencia_muestreo=22050),
    )

    with pytest.raises(EstimacionIncompatibleError) as exc_info:
        si_sdr(referencia, estimacion)
    assert exc_info.value.identificador_referencia == "S07"
    assert exc_info.value.identificador_estimacion == "sep_S07"
    assert exc_info.value.motivo == "distinta frecuencia de muestreo"
    assert str(exc_info.value) == (
        "La estimación 'sep_S07' es incompatible con la referencia 'S07': "
        "distinta frecuencia de muestreo."
    )


def test_si_sdr_con_referencia_y_estimacion_ambas_de_energia_nula_gana_referencia() -> None:
    # Caso ambos-cero: la prioridad (gana ReferenciaEnergiaNulaError, no
    # el -inf por convención) ya era el comportamiento correcto por el
    # orden de los `if` -- este test cierra la brecha de cobertura sobre
    # ese comportamiento y lo deja explícito, no corrige un defecto
    # (AGENTS.md: la regla de test-rojo-primero no aplica al cerrar
    # cobertura sobre código ya correcto). research.md #5.
    referencia = referencia_sintetica(identificador_origen="S08", muestras=silencio(200))
    estimacion = estimacion_sintetica(identificador="sep_S08", muestras=silencio(200))

    with pytest.raises(ReferenciaEnergiaNulaError) as exc_info:
        si_sdr(referencia, estimacion)
    assert exc_info.value.identificador_referencia == "S08"


def test_si_sdr_valor_analitico_conocido_confirma_la_constante_10_de_la_formula() -> None:
    """T027, mutation testing: `10.0 * log10(...)` mutado a `11.0 * ...`
    sobrevivía -- ningún test comparaba un SI-SDR finito contra un valor
    numérico conocido (los demás tests de este archivo solo verifican
    +-inf exactos o invarianza a la ganancia, ambos insensibles a la
    constante multiplicativa).

    Construcción exacta: `s = [10, -10]`, `e = [1, 1]` son ortogonales
    (`dot(s, e) == 10 - 10 == 0` para cualquier `e = [c, c]`), así que
    `alpha == 1` exactamente y `s_target == s`, `e_noise == e` sin
    aproximación. `‖s‖² / ‖e‖² == 200 / 2 == 100`, y
    `10 * log10(100) == 20.0` exacto -- una constante de 11 daría 22.0,
    una diferencia muy por encima de cualquier tolerancia numérica."""
    s = np.array([10.0, -10.0])
    e = np.array([1.0, 1.0])
    referencia = referencia_sintetica(identificador_origen="S09", muestras=s)
    estimacion = estimacion_sintetica(identificador="sep_S09", muestras=s + e)

    assert si_sdr(referencia, estimacion) == pytest.approx(20.0, abs=1e-9)
