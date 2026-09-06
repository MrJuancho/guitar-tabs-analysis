"""Tests unitarios de `medicion.orquestador.procesar_tema` (T009 de
`specs/004-medicion-linea-base/tasks.md`, User Story 1/Foundational) --
los 4 casos de contracts/medicion.md, con `SeparadorFalso` (Feature 003) y
`construir_tema_sintetico` (Feature 001) sobre `tmp_path`, en milisegundos,
sin `torch`/`demucs`.
"""

from __future__ import annotations

from pathlib import Path

from guitar_tabs_analysis.ingestion.slakh2100 import leer_tema
from guitar_tabs_analysis.medicion.orquestador import procesar_tema
from guitar_tabs_analysis.separacion.separador import separar_guitarra
from tests.fixtures.separador_fixture import SeparadorFalso
from tests.fixtures.slakh2100_fixture import EspecificacionStem, construir_tema_sintetico

_GUITARRA = EspecificacionStem(identificador="G01", inst_class="Guitar")


def test_lectura_fallida_se_reporta_como_exclusion_terminal(tmp_path: Path) -> None:
    separador = SeparadorFalso()

    resultado = procesar_tema("TrackInexistente", tmp_path, separador)

    assert resultado.tema_id == "TrackInexistente"
    assert resultado.reporte is None
    assert resultado.exclusion is not None
    assert resultado.exclusion.motivo == "fallo_procesamiento"
    assert "TrackInexistente" in resultado.exclusion.detalle
    assert resultado.transformaciones == []
    assert separador.llamadas == 0  # nunca se intenta separar un tema que no se pudo leer


def test_sin_guitarra_de_referencia_no_invoca_al_separador(tmp_path: Path) -> None:
    construir_tema_sintetico(tmp_path, tema_id="Track00001", stems=())
    separador = SeparadorFalso()

    resultado = procesar_tema("Track00001", tmp_path, separador)

    assert resultado.reporte is None
    assert resultado.exclusion is not None
    assert resultado.exclusion.motivo == "sin_guitarra_referencia"
    assert resultado.exclusion.detalle == ""
    assert resultado.transformaciones == []
    assert separador.llamadas == 0


def test_separacion_fallida_se_reporta_como_exclusion_terminal(tmp_path: Path) -> None:
    construir_tema_sintetico(tmp_path, tema_id="Track00002", stems=(_GUITARRA,))
    causa = RuntimeError("forma de audio no soportada")
    separador = SeparadorFalso(excepcion=causa)

    resultado = procesar_tema("Track00002", tmp_path, separador)

    assert resultado.reporte is None
    assert resultado.exclusion is not None
    assert resultado.exclusion.motivo == "fallo_procesamiento"
    assert "Track00002" in resultado.exclusion.detalle
    assert resultado.transformaciones == []
    assert separador.llamadas == 1  # se intentó una vez, sin reintento


def test_camino_feliz_reporta_y_declara_las_transformaciones(tmp_path: Path) -> None:
    construir_tema_sintetico(tmp_path, tema_id="Track00003", stems=(_GUITARRA,))

    resultado = procesar_tema("Track00003", tmp_path, SeparadorFalso())

    assert resultado.exclusion is None
    assert resultado.reporte is not None
    assert resultado.reporte.tema_id == "Track00003"
    assert resultado.reporte.num_referencias == 1

    # `transformaciones` debe coincidir con lo que `separar_guitarra`
    # (Feature 003) produce para la misma mezcla -- calculado de forma
    # independiente en el test, sin duplicar la lógica de `procesar_tema`.
    lectura = leer_tema("Track00003", tmp_path)
    esperado = separar_guitarra("Track00003", lectura.mezcla, SeparadorFalso())

    assert resultado.transformaciones != []
    assert resultado.transformaciones == esperado.transformaciones
