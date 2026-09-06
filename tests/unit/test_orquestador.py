"""Tests unitarios de `medicion.orquestador.procesar_tema` (T009 de
`specs/004-medicion-linea-base/tasks.md`, User Story 1/Foundational) --
los 4 casos de contracts/medicion.md, con `SeparadorFalso` (Feature 003) y
`construir_tema_sintetico` (Feature 001) sobre `tmp_path`, en milisegundos,
sin `torch`/`demucs`.
"""

from __future__ import annotations

import json
from pathlib import Path

from guitar_tabs_analysis.ingestion.slakh2100 import leer_tema
from guitar_tabs_analysis.medicion.orquestador import (
    artefacto_a_dict,
    ejecutar_corrida,
    procesar_tema,
)
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


def test_serializacion_del_artefacto_incluye_todo_lo_que_sc007_exige(tmp_path: Path) -> None:
    """T020, G1 de `/speckit-analyze`: el `dict` de `artefacto_a_dict`
    contiene modelo+firma, semilla, temas, valores por referencia,
    mediana, exclusiones con motivo, distribución de referencias por
    tema, y las transformaciones declaradas por tema -- y sobrevive un
    round-trip de `json.dumps`/`json.loads` sin perder ningún valor."""
    root_dir = tmp_path / "dataset"
    (root_dir / "train").mkdir(parents=True)
    construir_tema_sintetico(root_dir, tema_id="validation/Track00000", stems=(_GUITARRA,))
    construir_tema_sintetico(root_dir, tema_id="validation/Track00001", stems=())

    artefacto = ejecutar_corrida(
        "conjunto_completo", root_dir, SeparadorFalso(), tmp_path / "trabajo"
    )
    serializado = artefacto_a_dict(artefacto)

    claves_esperadas = {
        "modo",
        "semilla",
        "modelo",
        "temas",
        "exclusiones",
        "reportes",
        "transformaciones_por_tema",
        "mediana",
        "distribucion_referencias_por_tema",
    }
    assert claves_esperadas == set(serializado.keys())
    assert serializado["modelo"]["firma"] == SeparadorFalso().modelo_declarado.firma

    # El tema con guitarra tiene transformaciones no vacías; el excluido
    # (sin guitarra de referencia) no aporta ninguna entrada (G1).
    assert serializado["transformaciones_por_tema"]["validation/Track00000"] != []
    assert "validation/Track00001" not in serializado["transformaciones_por_tema"]

    # Round-trip: json no admite claves enteras, así que
    # `distribucion_referencias_por_tema` vuelve con claves `str` -- eso
    # no es perder información, es la única forma válida en JSON.
    recuperado = json.loads(json.dumps(serializado))
    assert recuperado["modo"] == serializado["modo"]
    assert recuperado["temas"] == serializado["temas"]
    assert recuperado["reportes"] == serializado["reportes"]
    assert recuperado["exclusiones"] == serializado["exclusiones"]
    assert recuperado["transformaciones_por_tema"] == serializado["transformaciones_por_tema"]
    assert recuperado["mediana"] == serializado["mediana"]
    distribucion_recuperada = {
        int(clave): valor
        for clave, valor in recuperado["distribucion_referencias_por_tema"].items()
    }
    assert distribucion_recuperada == artefacto.distribucion_referencias_por_tema
