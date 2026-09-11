"""Tests de `digitacion.cli` (T017/T023 de
`specs/007-digitacion-restriccion-mano/tasks.md`): el modo se elige
explícitamente, sin valor por defecto -- invocar sin `--modo`, o con un
`--modo` inválido (o sin `--root-dir`), falla ANTES de tocar disco.
Mismo patrón exacto que `tests/unit/test_deteccion_cli.py` del hito 2 --
sin transcriptor que mockear (research.md #2 de esta feature: ningún
modelo/subproceso externo)."""

from __future__ import annotations

import json
from pathlib import Path

import mirdata
import numpy as np
import pytest

from guitar_tabs_analysis.analytics.metrica_digitacion import (
    MODELO_COSTE_POR_DEFECTO,
    ResultadoCoincidencia,
)
from guitar_tabs_analysis.digitacion import cli
from guitar_tabs_analysis.digitacion.orquestador import ArtefactoDigitacion


def test_construir_parser_expone_prog_descripcion_y_los_dos_argumentos_completos() -> None:
    """Fija la estructura real del parser -- mismo criterio que
    `deteccion.cli` (mutation testing T026 de esa feature: texto
    cosmético de `--help` sin ningún test que lo mirara sobrevivía).
    `--modo` sin `choices`/`required` correctos mediría el conjunto
    reservado del hito 3 por accidente (Principio VI)."""
    parser = cli._construir_parser()

    assert parser.prog == "python -m guitar_tabs_analysis.digitacion.cli"
    assert parser.description == (
        "Digita el hito 3: lee la posición real de cada grabación de GuitarSet, "
        "calcula la digitación de coste mínimo y mide la coincidencia contra el uso real."
    )

    accion_modo = next(a for a in parser._actions if a.dest == "modo")
    assert accion_modo.choices == ["medibles", "reservado"]
    assert accion_modo.required is True
    assert accion_modo.help == (
        "medibles: 288 grabaciones (80% de GuitarSet), las únicas que se miden "
        "durante el desarrollo del hito 3. reservado: las 72 restantes (20%), "
        "solo para el cierre del hito 3 -- Principio VI de la constitución. "
        "Sin valor por defecto."
    )

    accion_root_dir = next(a for a in parser._actions if a.dest == "root_dir")
    assert accion_root_dir.type is Path
    assert accion_root_dir.required is True
    assert accion_root_dir.help == "Raíz de una distribución de GuitarSet ya presente en disco."


def test_sin_modo_falla_con_mensaje_claro_antes_de_tocar_disco(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--root-dir", "/cualquier/ruta"])

    assert excinfo.value.code != 0
    mensaje = capsys.readouterr().err
    assert "--modo" in mensaje
    assert "required" in mensaje


def test_modo_invalido_falla_con_mensaje_claro(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--modo", "no_existe", "--root-dir", "/cualquier/ruta"])

    assert excinfo.value.code != 0
    assert "--modo" in capsys.readouterr().err


def test_sin_root_dir_falla_con_mensaje_claro(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--modo", "medibles"])

    assert excinfo.value.code != 0
    assert "--root-dir" in capsys.readouterr().err


def test_main_llama_ejecutar_y_escribir_con_los_argumentos_correctos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llamadas: list[tuple[object, object, object]] = []

    def _ejecutar_y_escribir_falso(modo: object, root_dir: object, ruta_artefacto: object) -> int:
        llamadas.append((modo, root_dir, ruta_artefacto))
        return 0

    monkeypatch.setattr(cli, "_ejecutar_y_escribir", _ejecutar_y_escribir_falso)

    codigo = cli.main(["--modo", "medibles", "--root-dir", "/una/ruta"])

    assert codigo == 0
    assert llamadas == [
        ("medibles", Path("/una/ruta"), Path("mediciones") / "digitacion_medibles.json")
    ]


# ---------------------------------------------------------------------
# escribir_artefacto -- mismo mecanismo exacto que
# deteccion.cli.escribir_artefacto/EscrituraIncompletaError.
# ---------------------------------------------------------------------


def _artefacto_de_prueba() -> ArtefactoDigitacion:
    return ArtefactoDigitacion(
        modelo_coste=MODELO_COSTE_POR_DEFECTO,
        grabaciones=["00_BN1-129-Eb_comp"],
        exclusiones_grabacion=[],
        resultados_por_grabacion=[],
        resultado_coincidencia=ResultadoCoincidencia(
            fraccion_coincidencia=None, num_notas_medidas=0, num_notas_coincidentes=0
        ),
    )


def test_escribir_artefacto_produce_json_valido_y_legible(tmp_path: Path) -> None:
    ruta = tmp_path / "mediciones" / "digitacion_medibles.json"
    artefacto = _artefacto_de_prueba()

    cli.escribir_artefacto(ruta, artefacto)

    contenido = json.loads(ruta.read_text())
    assert contenido["grabaciones"] == ["00_BN1-129-Eb_comp"]


def test_escribir_artefacto_crea_varios_niveles_de_directorio_ausentes(tmp_path: Path) -> None:
    ruta = tmp_path / "a" / "b" / "digitacion_medibles.json"
    artefacto = _artefacto_de_prueba()

    cli.escribir_artefacto(ruta, artefacto)

    assert json.loads(ruta.read_text())["grabaciones"] == ["00_BN1-129-Eb_comp"]


def test_escribir_artefacto_usa_sufijo_tmp_para_el_archivo_temporal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "mediciones" / "digitacion_medibles.json"
    artefacto = _artefacto_de_prueba()
    origenes: list[Path] = []
    os_replace_real = cli.os.replace

    def _os_replace_que_registra(origen: Path, destino: Path) -> None:
        origenes.append(origen)
        os_replace_real(origen, destino)

    monkeypatch.setattr(cli.os, "replace", _os_replace_que_registra)

    cli.escribir_artefacto(ruta, artefacto)

    assert origenes == [ruta.with_name(ruta.name + ".tmp")]


def test_escribir_artefacto_es_atomico_no_deja_archivo_final_truncado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "mediciones" / "digitacion_medibles.json"
    artefacto = _artefacto_de_prueba()

    def _os_replace_que_falla(origen: object, destino: object) -> None:
        raise OSError("interrupción simulada entre escribir el temporal y renombrarlo")

    monkeypatch.setattr(cli.os, "replace", _os_replace_que_falla)

    with pytest.raises(OSError):
        cli.escribir_artefacto(ruta, artefacto)

    assert not ruta.exists()


def test_escribir_artefacto_falla_cerrado_si_os_replace_no_mueve_nada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "mediciones" / "digitacion_medibles.json"
    artefacto = _artefacto_de_prueba()

    monkeypatch.setattr(cli.os, "replace", lambda origen, destino: None)

    with pytest.raises(cli.EscrituraIncompletaError) as excinfo:
        cli.escribir_artefacto(ruta, artefacto)

    assert not ruta.exists()
    assert str(excinfo.value) == (
        f"'{ruta}' no quedó legible después de escribirlo -- "
        f"[Errno 2] No such file or directory: '{ruta}'."
    )


def test_escribir_artefacto_falla_cerrado_si_deja_un_artefacto_viejo_a_medias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "mediciones" / "digitacion_medibles.json"
    ruta.parent.mkdir(parents=True)
    ruta.write_text(json.dumps({"grabaciones": []}))
    artefacto = _artefacto_de_prueba()

    monkeypatch.setattr(cli.os, "replace", lambda origen, destino: None)

    with pytest.raises(cli.EscrituraIncompletaError) as excinfo:
        cli.escribir_artefacto(ruta, artefacto)

    assert str(excinfo.value) == (
        f"'{ruta}' no coincide con el artefacto recién calculado: "
        "0 grabaciones persistidas, 1 esperadas."
    )


# ---------------------------------------------------------------------
# _ejecutar_y_escribir -- de punta a punta con el índice de mirdata
# monkeypatcheado (nunca GuitarSet real, Principio IV).
# ---------------------------------------------------------------------


class _NoteDataFalso:
    def __init__(self, intervals: np.ndarray, pitches: np.ndarray) -> None:
        self.intervals = intervals
        self.pitches = pitches


class _TrackFalso:
    def __init__(self, notes: dict[str, _NoteDataFalso | None]) -> None:
        self.notes = notes


class _DatasetFalso:
    """Sustituto de `mirdata.core.Dataset` con `.track_ids` (que usa
    `construir_lista_grabaciones`) y `.track()` (que usa
    `leer_grabacion_con_posicion_real`)."""

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
    """Un único monkeypatch sobre el módulo `mirdata` real cubre
    `deteccion.orquestador.mirdata` e `ingestion.guitarset.mirdata` --
    ambos son el mismo objeto módulo, mismo criterio que
    `test_deteccion_cli.py`."""

    def _initialize_falso(nombre: str, data_home: str | None = None) -> _DatasetFalso:
        assert nombre == "guitarset"
        return dataset

    monkeypatch.setattr(mirdata, "initialize", _initialize_falso)


def test_ejecutar_y_escribir_produce_artefacto_en_disco(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "annotation").mkdir()
    (tmp_path / "audio_mono-mic").mkdir()
    dominio = sorted(f"grabacion_{i:03d}" for i in range(100))
    dataset = _DatasetFalso({gid: _track_sin_notas() for gid in dominio})
    _monkeypatch_mirdata(monkeypatch, dataset)
    ruta_artefacto = tmp_path / "mediciones" / "digitacion_medibles.json"

    codigo = cli._ejecutar_y_escribir("medibles", tmp_path, ruta_artefacto)

    assert codigo == 0
    contenido = json.loads(ruta_artefacto.read_text())
    assert len(contenido["grabaciones"]) == 28
    assert contenido["exclusiones_grabacion"] == []


def test_ejecutar_y_escribir_pasa_el_mismo_root_dir_a_ambas_llamadas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    ruta_artefacto = tmp_path / "salida" / "digitacion_medibles.json"

    cli._ejecutar_y_escribir("medibles", tmp_path, ruta_artefacto)

    llamadas_con_root_dir = [v for v in llamadas_data_home if v is not None]
    assert len(llamadas_con_root_dir) >= 2
    assert all(v == str(tmp_path) for v in llamadas_con_root_dir)


def test_ejecutar_y_escribir_devuelve_dos_y_el_mensaje_si_la_escritura_falla(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "annotation").mkdir()
    (tmp_path / "audio_mono-mic").mkdir()
    dominio = sorted(f"grabacion_{i:03d}" for i in range(100))
    dataset = _DatasetFalso({gid: _track_sin_notas() for gid in dominio})
    _monkeypatch_mirdata(monkeypatch, dataset)
    ruta_artefacto = tmp_path / "salida" / "digitacion_medibles.json"
    monkeypatch.setattr(cli.os, "replace", lambda origen, destino: None)

    codigo = cli._ejecutar_y_escribir("medibles", tmp_path, ruta_artefacto)

    assert codigo == 2
    assert capsys.readouterr().err.strip() == (
        f"'{ruta_artefacto}' no quedó legible después de escribirlo -- "
        f"[Errno 2] No such file or directory: '{ruta_artefacto}'."
    )


def test_root_dir_sin_estructura_de_guitarset_falla_antes_de_procesar_nada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset = _DatasetFalso({"grabacion_000": _track_sin_notas()})
    _monkeypatch_mirdata(monkeypatch, dataset)
    ruta_artefacto = tmp_path / "salida" / "digitacion_medibles.json"

    codigo = cli._ejecutar_y_escribir("medibles", tmp_path, ruta_artefacto)

    assert codigo == 1
    assert not ruta_artefacto.exists()
    mensaje = capsys.readouterr().err
    assert "annotation" in mensaje
    assert "audio_mono-mic" in mensaje
    assert str(tmp_path) in mensaje


def test_indice_mirdata_ausente_falla_antes_de_procesar_nada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "annotation").mkdir()
    (tmp_path / "audio_mono-mic").mkdir()

    def _initialize_sin_indice(nombre: str, data_home: str | None = None) -> None:
        assert nombre == "guitarset"
        raise FileNotFoundError("Dataset index for guitarset was expected but not found.")

    monkeypatch.setattr(mirdata, "initialize", _initialize_sin_indice)
    ruta_artefacto = tmp_path / "salida" / "digitacion_medibles.json"

    codigo = cli._ejecutar_y_escribir("medibles", tmp_path, ruta_artefacto)

    assert codigo == 1
    assert not ruta_artefacto.exists()
    mensaje = capsys.readouterr().err
    assert "download" in mensaje
    assert "index" in mensaje
