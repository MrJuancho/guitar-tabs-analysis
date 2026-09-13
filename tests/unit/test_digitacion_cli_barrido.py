"""Tests de `digitacion.cli_barrido` (Feature 008, T006/T008): la barrida
del peso de altura de traste sobre las 288 grabaciones medibles -- sin
`--modo` (siempre medibles, Principio VI) y sin ningún argumento para el
conjunto de valores candidatos (research.md #5 de la Feature 008: MUST
NOT poder pasarse por línea de comandos, para que no se pueda "ajustar
el rango después de ver la curva"). Mismo patrón exacto que
`tests/unit/test_digitacion_cli.py` de la Feature 007.
"""

from __future__ import annotations

import json
from pathlib import Path

import mirdata
import pytest

from guitar_tabs_analysis.analytics.metrica_digitacion import (
    MODELO_COSTE_POR_DEFECTO,
    PuntoBarrida,
    ResultadoBarrida,
    ResultadoCoincidencia,
)
from guitar_tabs_analysis.digitacion import cli_barrido


def test_construir_parser_expone_prog_descripcion_y_solo_root_dir() -> None:
    """El conjunto de valores candidatos NO es un argumento del parser
    (research.md #5) -- las únicas acciones son `--help` (agregada por
    `argparse`) y `--root-dir`."""
    parser = cli_barrido._construir_parser()

    assert parser.prog == "python -m guitar_tabs_analysis.digitacion.cli_barrido"
    assert parser.description == (
        "Barre el peso de altura de traste del modelo de coste de digitación "
        "sobre las 288 grabaciones medibles de GuitarSet, con el conjunto de "
        "valores candidatos ya declarado en código, y mide fraccion_coincidencia "
        "para cada uno."
    )
    destinos = {a.dest for a in parser._actions}
    assert destinos == {"help", "root_dir"}

    accion_root_dir = next(a for a in parser._actions if a.dest == "root_dir")
    assert accion_root_dir.type is Path
    assert accion_root_dir.required is True
    assert accion_root_dir.help == "Raíz de una distribución de GuitarSet ya presente en disco."


def test_sin_root_dir_falla_con_mensaje_claro_antes_de_tocar_disco(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli_barrido.main([])

    assert excinfo.value.code != 0
    assert "--root-dir" in capsys.readouterr().err


def test_main_llama_ejecutar_y_escribir_con_el_root_dir_correcto(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llamadas: list[tuple[object, object]] = []

    def _ejecutar_y_escribir_falso(root_dir: object, ruta_artefacto: object) -> int:
        llamadas.append((root_dir, ruta_artefacto))
        return 0

    monkeypatch.setattr(cli_barrido, "_ejecutar_y_escribir", _ejecutar_y_escribir_falso)

    codigo = cli_barrido.main(["--root-dir", "/una/ruta"])

    assert codigo == 0
    assert llamadas == [(Path("/una/ruta"), Path("mediciones") / "barrido_altura_traste.json")]


def test_valores_candidatos_son_una_constante_del_modulo_no_un_argumento() -> None:
    """research.md #5/#3 de la Feature 008: el conjunto declarado antes
    de correr la barrida, fijo en código."""
    assert cli_barrido.VALORES_CANDIDATOS_ALTURA_TRASTE == (
        0.0,
        0.01,
        0.03,
        0.1,
        0.3,
        1.0,
        3.0,
        10.0,
        30.0,
        100.0,
    )


# ---------------------------------------------------------------------
# escribir_resultado_barrida -- mismo mecanismo atómico exacto que
# `digitacion.cli.escribir_artefacto`.
# ---------------------------------------------------------------------


def _resultado_de_prueba() -> ResultadoBarrida:
    return ResultadoBarrida(
        valores_candidatos=[0.0, 1.0],
        puntos=[
            PuntoBarrida(
                peso_altura_traste=0.0,
                resultado_coincidencia=ResultadoCoincidencia(
                    fraccion_coincidencia=None, num_notas_medidas=0, num_notas_coincidentes=0
                ),
            ),
            PuntoBarrida(
                peso_altura_traste=1.0,
                resultado_coincidencia=ResultadoCoincidencia(
                    fraccion_coincidencia=None, num_notas_medidas=0, num_notas_coincidentes=0
                ),
            ),
        ],
    )


def test_escribir_resultado_barrida_produce_json_valido_y_legible(tmp_path: Path) -> None:
    ruta = tmp_path / "mediciones" / "barrido_altura_traste.json"
    resultado = _resultado_de_prueba()

    cli_barrido.escribir_resultado_barrida(ruta, resultado)

    contenido = json.loads(ruta.read_text())
    assert contenido["valores_candidatos"] == [0.0, 1.0]
    assert len(contenido["puntos"]) == 2


def test_escribir_resultado_barrida_crea_varios_niveles_de_directorio_ausentes(
    tmp_path: Path,
) -> None:
    """`mkdir(parents=True, ...)` -- con un solo nivel faltante,
    `parents=False` también funcionaría (mutation testing: sobrevivía
    hasta agregar este caso con DOS niveles ausentes, donde solo
    `parents=True` los crea a ambos)."""
    ruta = tmp_path / "a" / "b" / "barrido_altura_traste.json"
    resultado = _resultado_de_prueba()

    cli_barrido.escribir_resultado_barrida(ruta, resultado)

    assert json.loads(ruta.read_text())["valores_candidatos"] == [0.0, 1.0]


def test_escribir_resultado_barrida_usa_sufijo_tmp_para_el_archivo_temporal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "mediciones" / "barrido_altura_traste.json"
    resultado = _resultado_de_prueba()
    origenes: list[Path] = []
    os_replace_real = cli_barrido.os.replace

    def _os_replace_que_registra(origen: Path, destino: Path) -> None:
        origenes.append(origen)
        os_replace_real(origen, destino)

    monkeypatch.setattr(cli_barrido.os, "replace", _os_replace_que_registra)

    cli_barrido.escribir_resultado_barrida(ruta, resultado)

    assert origenes == [ruta.with_name(ruta.name + ".tmp")]


def test_escribir_resultado_barrida_falla_cerrado_si_os_replace_no_mueve_nada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "mediciones" / "barrido_altura_traste.json"
    resultado = _resultado_de_prueba()

    monkeypatch.setattr(cli_barrido.os, "replace", lambda origen, destino: None)

    with pytest.raises(cli_barrido.EscrituraIncompletaError):
        cli_barrido.escribir_resultado_barrida(ruta, resultado)

    assert not ruta.exists()


def test_escribir_resultado_barrida_falla_cerrado_si_deja_un_resultado_viejo_a_medias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "mediciones" / "barrido_altura_traste.json"
    ruta.parent.mkdir(parents=True)
    ruta.write_text(json.dumps({"puntos": []}))
    resultado = _resultado_de_prueba()

    monkeypatch.setattr(cli_barrido.os, "replace", lambda origen, destino: None)

    with pytest.raises(cli_barrido.EscrituraIncompletaError) as excinfo:
        cli_barrido.escribir_resultado_barrida(ruta, resultado)

    assert str(excinfo.value) == (
        f"'{ruta}' no coincide con el resultado recién calculado: "
        "0 puntos persistidos, 2 esperados."
    )


# ---------------------------------------------------------------------
# _ejecutar_y_escribir -- de punta a punta con el índice de mirdata
# monkeypatcheado (nunca GuitarSet real, Principio IV).
# ---------------------------------------------------------------------


class _NoteDataFalso:
    def __init__(self, intervals: object, pitches: object) -> None:
        self.intervals = intervals
        self.pitches = pitches


class _TrackFalso:
    def __init__(self, notes: dict[str, _NoteDataFalso | None]) -> None:
        self.notes = notes


class _DatasetFalso:
    def __init__(self, tracks: dict[str, _TrackFalso]) -> None:
        self._tracks = tracks
        self.track_ids = sorted(tracks.keys())

    def track(self, track_id: str) -> _TrackFalso:
        if track_id not in self._tracks:
            raise ValueError(f"{track_id} is not a valid track_id in guitarset")
        return self._tracks[track_id]


def _track_sin_notas() -> _TrackFalso:
    return _TrackFalso(notes=dict.fromkeys(["E", "A", "D", "G", "B", "e"], None))


def _monkeypatch_mirdata(monkeypatch: pytest.MonkeyPatch, dataset: _DatasetFalso) -> None:
    def _initialize_falso(nombre: str, data_home: str | None = None) -> _DatasetFalso:
        assert nombre == "guitarset"
        return dataset

    monkeypatch.setattr(mirdata, "initialize", _initialize_falso)


def test_ejecutar_y_escribir_produce_resultado_barrida_en_disco(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "annotation").mkdir()
    (tmp_path / "audio_mono-mic").mkdir()
    dominio = sorted(f"grabacion_{i:03d}" for i in range(100))
    dataset = _DatasetFalso({gid: _track_sin_notas() for gid in dominio})
    _monkeypatch_mirdata(monkeypatch, dataset)
    ruta_artefacto = tmp_path / "mediciones" / "barrido_altura_traste.json"

    codigo = cli_barrido._ejecutar_y_escribir(tmp_path, ruta_artefacto)

    assert codigo == 0
    contenido = json.loads(ruta_artefacto.read_text())
    assert len(contenido["puntos"]) == len(cli_barrido.VALORES_CANDIDATOS_ALTURA_TRASTE)
    assert contenido["valores_candidatos"] == list(cli_barrido.VALORES_CANDIDATOS_ALTURA_TRASTE)


def test_ejecutar_y_escribir_pasa_el_mismo_root_dir_a_ambas_llamadas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`root_dir` MUST llegar sin cambios tanto a
    `construir_lista_grabaciones` como a `ejecutar_barrida_peso_altura`
    -- mismo patrón que `test_digitacion_cli.py` de la Feature 007."""
    (tmp_path / "annotation").mkdir()
    (tmp_path / "audio_mono-mic").mkdir()
    dominio = sorted(f"grabacion_{i:03d}" for i in range(100))
    dataset = _DatasetFalso({gid: _track_sin_notas() for gid in dominio})
    llamadas_data_home: list[str | None] = []

    def _initialize_falso(nombre: str, data_home: str | None = None) -> _DatasetFalso:
        assert nombre == "guitarset"
        llamadas_data_home.append(data_home)
        return dataset

    monkeypatch.setattr(mirdata, "initialize", _initialize_falso)
    ruta_artefacto = tmp_path / "salida" / "barrido_altura_traste.json"

    cli_barrido._ejecutar_y_escribir(tmp_path, ruta_artefacto)

    llamadas_con_root_dir = [v for v in llamadas_data_home if v is not None]
    assert len(llamadas_con_root_dir) >= 2
    assert all(v == str(tmp_path) for v in llamadas_con_root_dir)


def test_root_dir_sin_estructura_de_guitarset_falla_antes_de_procesar_nada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset = _DatasetFalso({"grabacion_000": _track_sin_notas()})
    _monkeypatch_mirdata(monkeypatch, dataset)
    ruta_artefacto = tmp_path / "salida" / "barrido_altura_traste.json"

    codigo = cli_barrido._ejecutar_y_escribir(tmp_path, ruta_artefacto)

    assert codigo == 1
    assert not ruta_artefacto.exists()
    mensaje = capsys.readouterr().err
    assert "annotation" in mensaje
    assert "audio_mono-mic" in mensaje


def test_indice_mirdata_ausente_falla_antes_de_procesar_nada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "annotation").mkdir()
    (tmp_path / "audio_mono-mic").mkdir()

    def _initialize_sin_indice(nombre: str, data_home: str | None = None) -> None:
        assert nombre == "guitarset"
        raise FileNotFoundError("Dataset index for guitarset was expected but not found.")

    monkeypatch.setattr(mirdata, "initialize", _initialize_sin_indice)
    ruta_artefacto = tmp_path / "salida" / "barrido_altura_traste.json"

    codigo = cli_barrido._ejecutar_y_escribir(tmp_path, ruta_artefacto)

    assert codigo == 1
    assert not ruta_artefacto.exists()
    mensaje = capsys.readouterr().err
    assert "download" in mensaje
    assert "index" in mensaje


def test_ejecutar_y_escribir_devuelve_dos_y_el_mensaje_si_la_escritura_falla(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "annotation").mkdir()
    (tmp_path / "audio_mono-mic").mkdir()
    dominio = sorted(f"grabacion_{i:03d}" for i in range(100))
    dataset = _DatasetFalso({gid: _track_sin_notas() for gid in dominio})
    _monkeypatch_mirdata(monkeypatch, dataset)
    ruta_artefacto = tmp_path / "salida" / "barrido_altura_traste.json"
    monkeypatch.setattr(cli_barrido.os, "replace", lambda origen, destino: None)

    codigo = cli_barrido._ejecutar_y_escribir(tmp_path, ruta_artefacto)

    assert codigo == 2
    assert capsys.readouterr().err.strip() == (
        f"'{ruta_artefacto}' no quedó legible después de escribirlo -- "
        f"[Errno 2] No such file or directory: '{ruta_artefacto}'."
    )


def test_modelo_coste_por_defecto_usado_como_base_de_la_barrida() -> None:
    """FR-002 de la Feature 008: la barrida no toca
    `peso_desplazamiento`/`peso_cruce_cuerdas` -- sigue partiendo de
    `MODELO_COSTE_POR_DEFECTO` para todo lo que no sea
    `peso_altura_traste`."""
    assert MODELO_COSTE_POR_DEFECTO.peso_desplazamiento == 1.0
    assert MODELO_COSTE_POR_DEFECTO.peso_cruce_cuerdas == 1.0
