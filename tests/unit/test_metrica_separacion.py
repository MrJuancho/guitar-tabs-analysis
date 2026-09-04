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
)

from guitar_tabs_analysis.ingestion.slakh2100 import PistaAudio, PistaGuitarra

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
