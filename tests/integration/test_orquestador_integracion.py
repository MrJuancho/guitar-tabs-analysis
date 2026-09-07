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
    escribir_progreso_tema,
    leer_progreso_tema,
    procesar_tema,
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


def test_reanudar_no_reprocesa_temas_ya_persistidos_y_produce_artefacto_equivalente(
    tmp_path: Path,
) -> None:
    """T021, User Story 2, AS1/AS3, FR-008/FR-009: interrumpir una
    corrida (simulado persistiendo el progreso de una parte de los temas
    como si una invocación anterior ya los hubiera calculado) y
    reanudarla no reprocesa esos temas, y el artefacto final es
    equivalente al de una corrida sin interrupción sobre el mismo
    conjunto."""
    root_dir = tmp_path / "dataset"
    (root_dir / "train").mkdir(parents=True)
    guitarra = EspecificacionStem(identificador="G01", inst_class="Guitar")
    for indice in range(5):
        construir_tema_sintetico(
            root_dir, tema_id=f"validation/Track{indice:05d}", stems=(guitarra,)
        )

    temas = construir_lista_temas("conjunto_completo", root_dir)
    assert len(temas) == 5

    artefacto_sin_interrupcion = ejecutar_corrida(
        "conjunto_completo", root_dir, SeparadorFalso(), tmp_path / "trabajo_referencia"
    )

    # Simula una corrida anterior interrumpida justo después de persistir
    # los primeros 3 temas -- nunca se mata un proceso real, se deja el
    # progreso en el estado exacto en el que una interrupción lo dejaría.
    directorio_trabajo = tmp_path / "trabajo_interrumpida"
    for tema_id in temas[:3]:
        progreso = procesar_tema(tema_id, root_dir, SeparadorFalso())
        escribir_progreso_tema(directorio_trabajo / "temas", progreso)

    separador_reanudacion = SeparadorFalso()
    artefacto_reanudado = ejecutar_corrida(
        "conjunto_completo", root_dir, separador_reanudacion, directorio_trabajo
    )

    # Solo los 2 temas sin progreso previo invocaron separar().
    assert separador_reanudacion.llamadas == 2
    assert artefacto_reanudado == artefacto_sin_interrupcion


def test_reanudar_no_reintenta_un_tema_que_fallo_duro(tmp_path: Path) -> None:
    """T022, User Story 2, AS2: un tema que falló duro y quedó persistido
    como excluido no se reintenta en una reanudación, aunque el separador
    de la segunda invocación ya no esté configurado para fallar --
    aclaración de `/speckit-clarify` ("el fallo es terminal")."""
    root_dir = tmp_path / "dataset"
    (root_dir / "train").mkdir(parents=True)
    guitarra = EspecificacionStem(identificador="G01", inst_class="Guitar")
    construir_tema_sintetico(root_dir, tema_id="validation/Track00000", stems=(guitarra,))

    directorio_trabajo = tmp_path / "trabajo"
    separador_primera_corrida = SeparadorFalso(excepcion=RuntimeError("boom"))
    artefacto1 = ejecutar_corrida(
        "conjunto_completo", root_dir, separador_primera_corrida, directorio_trabajo
    )
    assert artefacto1.exclusiones[0].motivo == "fallo_procesamiento"

    separador_segunda_corrida = SeparadorFalso()  # ya no configurado para fallar
    artefacto2 = ejecutar_corrida(
        "conjunto_completo", root_dir, separador_segunda_corrida, directorio_trabajo
    )

    assert separador_segunda_corrida.llamadas == 0  # nunca se reintenta
    assert artefacto2.exclusiones == artefacto1.exclusiones


def test_conjunto_completo_excluye_test_y_omitted_via_ejecutar_corrida(tmp_path: Path) -> None:
    """T025, User Story 3, AS1, FR-014: dataset sintético con temas en los
    cuatro splits -- `ejecutar_corrida("conjunto_completo", ...)` incluye
    exactamente los de `train`/`validation` y ninguno de `test`/`omitted`,
    de punta a punta (no solo a nivel de `construir_lista_temas`, ya
    cubierto por T013)."""
    root_dir = tmp_path / "dataset"
    construir_varios_temas_sinteticos(root_dir, split="train", cantidad=2)
    construir_varios_temas_sinteticos(root_dir, split="validation", cantidad=3)
    construir_varios_temas_sinteticos(root_dir, split="test", cantidad=2)
    construir_varios_temas_sinteticos(root_dir, split="omitted", cantidad=2)

    artefacto = ejecutar_corrida(
        "conjunto_completo", root_dir, SeparadorFalso(), tmp_path / "trabajo"
    )

    assert len(artefacto.temas) == 2 + 3
    assert all(t.startswith("train/") or t.startswith("validation/") for t in artefacto.temas)
    assert not any(t.startswith("test/") for t in artefacto.temas)
    assert not any(t.startswith("omitted/") for t in artefacto.temas)


def test_submuestra_hito1_y_conjunto_completo_no_interfieren_entre_si(tmp_path: Path) -> None:
    """T026, User Story 3, AS3: invocar ambos modos sobre el mismo
    `root_dir`, cada uno con su propio `directorio_trabajo` (como hará el
    CLI), produce dos artefactos correctos e independientes -- el
    progreso de uno no contamina al otro."""
    root_dir = tmp_path / "dataset"
    cantidades = [1] * 40
    construir_varios_temas_sinteticos(
        root_dir, split="validation", cantidad=40, guitarras_por_tema=cantidades
    )
    construir_varios_temas_sinteticos(root_dir, split="train", cantidad=2)

    artefacto_submuestra = ejecutar_corrida(
        "submuestra_hito1", root_dir, SeparadorFalso(), tmp_path / "trabajo_submuestra"
    )
    artefacto_completo = ejecutar_corrida(
        "conjunto_completo", root_dir, SeparadorFalso(), tmp_path / "trabajo_completo"
    )

    assert len(artefacto_submuestra.temas) == 40
    assert artefacto_submuestra.semilla == 20260904
    assert len(artefacto_completo.temas) == 40 + 2
    assert artefacto_completo.semilla is None
    # Ninguno de los dos modos alteró el progreso del otro -- directorios
    # de trabajo separados, sin superposición de temas persistidos.
    assert set(artefacto_submuestra.temas) != set(artefacto_completo.temas)


@pytest.fixture
def _dataset_3_temas(tmp_path: Path) -> Path:
    """2 temas con guitarra (`ok`) + 1 sin ninguna (`excluido`), para
    fijar el formato exacto de la salida de progreso sin depender de un
    dataset grande."""
    root_dir = tmp_path / "dataset"
    (root_dir / "train").mkdir(parents=True)
    construir_varios_temas_sinteticos(
        root_dir, split="validation", cantidad=3, guitarras_por_tema=[1, 1, 0]
    )
    return root_dir


def test_ejecutar_corrida_imprime_una_linea_por_tema_recien_procesado(
    tmp_path: Path, _dataset_3_temas: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Salida de progreso (pedido explícito): una línea por tema al
    terminarlo, en el mismo punto donde ya se persiste el progreso --
    formato `[i/N] tema_id  ok  Xs  N refs` o `[i/N] tema_id  excluido:
    motivo`. Sin esto, un proceso de hasta 18h corre en silencio, sin
    forma de saber si sigue vivo (incidente real: un proceso que seguía
    agregando se dio por muerto y se relanzó encima, produciendo una
    condición de carrera)."""
    ejecutar_corrida("conjunto_completo", _dataset_3_temas, SeparadorFalso(), tmp_path / "trabajo")

    salida = capsys.readouterr().out
    lineas = salida.splitlines()
    assert "[1/3] validation/Track00000  ok  " in lineas[0]
    assert lineas[0].rstrip().endswith("1 refs")
    assert "[2/3] validation/Track00001  ok  " in lineas[1]
    assert lineas[1].rstrip().endswith("1 refs")
    assert lineas[2] == "[3/3] validation/Track00002  excluido: sin_guitarra_referencia"
    assert "agregando 3 temas" in salida
    assert "se omiten" not in salida  # nada saltado en una corrida sin progreso previo


def test_ejecutar_corrida_resumida_resume_los_temas_ya_hechos_en_una_sola_linea(
    tmp_path: Path, _dataset_3_temas: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Con los 3 temas ya persistidos de una corrida previa, reanudar NO
    debe imprimir una línea por cada uno -- con 1559 temas ya hechos, eso
    son 1559 líneas de ruido antes de empezar. Un resumen basta."""
    directorio_trabajo = tmp_path / "trabajo"
    ejecutar_corrida("conjunto_completo", _dataset_3_temas, SeparadorFalso(), directorio_trabajo)
    capsys.readouterr()  # descarta la salida de la corrida inicial

    ejecutar_corrida("conjunto_completo", _dataset_3_temas, SeparadorFalso(), directorio_trabajo)

    salida = capsys.readouterr().out
    assert salida.count("\n") == 2  # el resumen de saltados + "agregando"
    assert "3 temas ya procesados, se omiten" in salida
    assert "agregando 3 temas" in salida
    assert "[1/3]" not in salida
    assert "ok" not in salida
    assert "excluido" not in salida


def test_ejecutar_corrida_resumida_a_medias_imprime_el_resumen_antes_de_seguir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Caso intermedio, más cercano al real: algunos temas ya
    persistidos (de una corrida previa interrumpida), el resto todavía
    no -- el resumen de saltados aparece una vez, antes de retomar las
    líneas por tema de los que sí se procesan ahora."""
    root_dir = tmp_path / "dataset"
    (root_dir / "train").mkdir(parents=True)
    construir_varios_temas_sinteticos(root_dir, split="validation", cantidad=3)
    directorio_trabajo = tmp_path / "trabajo"

    temas = construir_lista_temas("conjunto_completo", root_dir)
    separador = SeparadorFalso()
    escribir_progreso_tema(
        directorio_trabajo / "temas", procesar_tema(temas[0], root_dir, separador)
    )

    ejecutar_corrida("conjunto_completo", root_dir, separador, directorio_trabajo)

    lineas = capsys.readouterr().out.splitlines()
    assert lineas[0] == "1 temas ya procesados, se omiten"
    assert lineas[1].startswith(f"[2/3] {temas[1]}  ok  ")
    assert lineas[2].startswith(f"[3/3] {temas[2]}  ok  ")
    assert lineas[3] == "agregando 3 temas"
