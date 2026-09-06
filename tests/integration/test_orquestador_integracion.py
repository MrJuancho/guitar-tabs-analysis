"""Integration tests de `medicion.orquestador.ejecutar_corrida` (User
Story 1, T016/T017 de `specs/004-medicion-linea-base/tasks.md`) --
`SeparadorFalso` (Feature 003) y datasets sintéticos (Feature 001/T007),
sin `torch`/`demucs` ni red.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy.typing as npt
import pytest

from guitar_tabs_analysis.analytics.metrica_separacion import (
    calcular_distribucion_referencias,
    calcular_mediana_agregada,
)
from guitar_tabs_analysis.medicion.orquestador import (
    construir_lista_temas,
    ejecutar_corrida,
    leer_progreso_tema,
)
from guitar_tabs_analysis.separacion.separador import ModeloDeclarado
from tests.fixtures.dataset_sintetico_fixture import construir_varios_temas_sinteticos
from tests.fixtures.separador_fixture import SeparadorFalso
from tests.fixtures.slakh2100_fixture import EspecificacionStem, construir_tema_sintetico


@pytest.fixture
def _dataset_40_temas(tmp_path: Path) -> Path:
    root_dir = tmp_path / "dataset"
    # 39 temas con una guitarra, uno sin ninguna -- ejercita la exclusión
    # "sin_guitarra_referencia" dentro de la misma corrida (AS1/AS4).
    cantidades = [1] * 39 + [0]
    construir_varios_temas_sinteticos(
        root_dir, split="validation", cantidad=40, guitarras_por_tema=cantidades
    )
    return root_dir


def test_ejecutar_corrida_submuestra_hito1_produce_artefacto_consistente(
    tmp_path: Path, _dataset_40_temas: Path
) -> None:
    root_dir = _dataset_40_temas

    artefacto1 = ejecutar_corrida(
        "submuestra_hito1", root_dir, SeparadorFalso(), tmp_path / "trabajo1"
    )
    artefacto2 = ejecutar_corrida(
        "submuestra_hito1", root_dir, SeparadorFalso(), tmp_path / "trabajo2"
    )

    assert artefacto1.temas == construir_lista_temas("submuestra_hito1", root_dir)
    assert len(artefacto1.exclusiones) + len(artefacto1.reportes) == 40
    # dos invocaciones sucesivas, sin progreso previo cada vez, resuelven
    # a la misma lista de temas (AS4).
    assert artefacto1.temas == artefacto2.temas


def test_mediana_y_distribucion_coinciden_con_calculo_independiente(
    tmp_path: Path, _dataset_40_temas: Path
) -> None:
    root_dir = _dataset_40_temas

    artefacto = ejecutar_corrida(
        "submuestra_hito1", root_dir, SeparadorFalso(), tmp_path / "trabajo"
    )

    assert artefacto.mediana == calcular_mediana_agregada(artefacto.reportes)
    assert artefacto.distribucion_referencias_por_tema == calcular_distribucion_referencias(
        artefacto.reportes
    )


class _SeparadorFallaPorLongitud:
    """Envuelve un `SeparadorFalso` real, pero falla únicamente cuando la
    mezcla recibida tiene una longitud específica -- así el fallo se
    dispara por CONTENIDO del tema, no por conteo de invocaciones, y el
    resultado no depende del orden de iteración interno de
    `ejecutar_corrida` (G2 de `/speckit-analyze`)."""

    def __init__(self, longitud_que_falla: int, delegado: SeparadorFalso) -> None:
        self._longitud_que_falla = longitud_que_falla
        self._delegado = delegado
        self.modelo_declarado: ModeloDeclarado = delegado.modelo_declarado

    @property
    def samplerate(self) -> int:
        return self._delegado.samplerate

    @property
    def audio_channels(self) -> int:
        return self._delegado.audio_channels

    def separar(self, muestras: npt.NDArray[Any]) -> dict[str, npt.NDArray[Any]]:
        if len(muestras) == self._longitud_que_falla:
            raise RuntimeError("fallo simulado para este tema")
        return self._delegado.separar(muestras)


def test_fallo_duro_a_mitad_de_la_corrida_no_detiene_los_temas_restantes(tmp_path: Path) -> None:
    """G2 de `/speckit-analyze`, SC-004: un fallo duro en el tema 3 de 5
    no detiene el procesamiento de los temas 4 y 5 dentro de la MISMA
    invocación de `ejecutar_corrida` -- garantía central para una corrida
    de hasta 25 horas."""
    root_dir = tmp_path / "dataset"
    (root_dir / "train").mkdir(parents=True)  # conjunto_completo también lista train/
    guitarra = EspecificacionStem(identificador="G01", inst_class="Guitar")
    longitud_que_falla = 999
    for indice in range(5):
        n_muestras = longitud_que_falla if indice == 2 else 200
        construir_tema_sintetico(
            root_dir,
            tema_id=f"validation/Track{indice:05d}",
            n_muestras_mezcla=n_muestras,
            stems=(guitarra,),
        )

    separador = _SeparadorFallaPorLongitud(longitud_que_falla, SeparadorFalso())
    directorio_trabajo = tmp_path / "trabajo"

    artefacto = ejecutar_corrida("conjunto_completo", root_dir, separador, directorio_trabajo)

    tema_fallido = "validation/Track00002"
    exclusiones_por_tema = {e.tema_id: e for e in artefacto.exclusiones}
    assert exclusiones_por_tema[tema_fallido].motivo == "fallo_procesamiento"

    # Los temas posteriores al fallo siguieron procesándose DENTRO de esta
    # misma invocación -- se verifica el progreso persistido, no solo el
    # artefacto final, para confirmar que de verdad se calcularon y no
    # que la corrida los alcanzó por casualidad.
    for indice in (3, 4):
        tema_id = f"validation/Track{indice:05d}"
        progreso = leer_progreso_tema(directorio_trabajo / "temas", tema_id)
        assert progreso is not None
        assert progreso.reporte is not None

    assert len(artefacto.exclusiones) + len(artefacto.reportes) == 5
