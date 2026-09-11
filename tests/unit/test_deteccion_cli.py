"""Tests de `deteccion.cli` (T033 de `specs/006-deteccion-notas-guitarra-limpia/tasks.md`,
Fase 7): el modo se elige explícitamente, sin valor por defecto -- invocar
sin `--modo`, o con un `--modo` inválido (o sin `--root-dir`), falla ANTES
de construir ningún `BasicPitchTranscriptor` real (que invoca un
subproceso Python 3.10, research.md #15). Mismo patrón exacto que
`tests/unit/test_cli.py` del hito 1 (Feature 004, T027).
"""

from __future__ import annotations

import json
from pathlib import Path

import mirdata
import numpy as np
import pytest

from guitar_tabs_analysis.analytics.metrica_deteccion_notas import ResultadoSubconjunto
from guitar_tabs_analysis.deteccion import cli
from guitar_tabs_analysis.deteccion.orquestador import ArtefactoDeteccion
from guitar_tabs_analysis.transcripcion.transcriptor import ModeloTranscripcionDeclarado
from tests.fixtures.transcriptor_fixture import MODELO_FALSO, TranscriptorFalso


def _fallar_si_se_construye() -> None:
    raise AssertionError(
        "BasicPitchTranscriptor no debería construirse sin un --modo/--root-dir "
        "válidos -- el error de argparse tiene que ocurrir antes."
    )


def test_construir_parser_expone_prog_descripcion_y_los_dos_argumentos_completos() -> None:
    """Fija la estructura real del parser -- no solo texto cosmético de
    `--help` (mutation testing, T026: 36 mutantes sobrevivían en
    `_construir_parser`, la mayoría cambios de texto sin ningún test que
    los mirara). `--modo` sin `choices`/`required` correctos mediría el
    conjunto reservado del hito 2 por accidente (FR-004) -- no es
    decorativo."""
    parser = cli._construir_parser()

    assert parser.prog == "python -m guitar_tabs_analysis.deteccion.cli"
    assert parser.description == (
        "Detecta notas del hito 2: lee cada grabación de GuitarSet, transcribe "
        "con Basic Pitch, calcula precisión/exhaustividad/balance."
    )

    accion_modo = next(a for a in parser._actions if a.dest == "modo")
    assert accion_modo.choices == ["medibles", "reservado"]
    assert accion_modo.required is True
    assert accion_modo.help == (
        "medibles: 288 grabaciones (80% de GuitarSet), las únicas que se miden "
        "durante el desarrollo del hito 2. reservado: las 72 restantes (20%), "
        "solo para el cierre del hito 2 -- Principio VI de la constitución. "
        "Sin valor por defecto."
    )

    accion_root_dir = next(a for a in parser._actions if a.dest == "root_dir")
    assert accion_root_dir.type is Path
    assert accion_root_dir.required is True
    assert accion_root_dir.help == "Raíz de una distribución de GuitarSet ya presente en disco."


def test_sin_modo_falla_con_mensaje_claro_antes_de_construir_transcriptor(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "BasicPitchTranscriptor", _fallar_si_se_construye)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--root-dir", "/cualquier/ruta"])

    assert excinfo.value.code != 0
    mensaje = capsys.readouterr().err
    assert "--modo" in mensaje
    assert "required" in mensaje  # argparse: "the following arguments are required: --modo"


def test_modo_invalido_falla_con_mensaje_claro_antes_de_construir_transcriptor(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "BasicPitchTranscriptor", _fallar_si_se_construye)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--modo", "no_existe", "--root-dir", "/cualquier/ruta"])

    assert excinfo.value.code != 0
    mensaje = capsys.readouterr().err
    assert "--modo" in mensaje


def test_sin_root_dir_falla_con_mensaje_claro(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "BasicPitchTranscriptor", _fallar_si_se_construye)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--modo", "medibles"])

    assert excinfo.value.code != 0
    mensaje = capsys.readouterr().err
    assert "--root-dir" in mensaje


def test_main_construye_transcriptor_y_llama_ejecutar_y_escribir_con_los_argumentos_correctos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ningún test anterior de este archivo llega a ejecutar el CUERPO
    de `main()` -- los tres de arriba fallan en `argparse`, antes de
    construir nada (mutation testing, T026: los 15 mutantes de `main`
    sobrevivían porque nada lo ejercitaba de punta a punta). `BasicPitchTranscriptor`
    se reemplaza (nunca invoca el subproceso real) y `_ejecutar_y_escribir`
    también, para capturar con qué argumentos exactos `main` la invoca,
    sin depender de mirdata ni de ningún dato real."""
    transcriptor_falso = object()
    monkeypatch.setattr(cli, "BasicPitchTranscriptor", lambda: transcriptor_falso)
    llamadas: list[tuple[object, object, object, object]] = []

    def _ejecutar_y_escribir_falso(
        modo: object, root_dir: object, transcriptor: object, ruta_artefacto: object
    ) -> int:
        llamadas.append((modo, root_dir, transcriptor, ruta_artefacto))
        return 0

    monkeypatch.setattr(cli, "_ejecutar_y_escribir", _ejecutar_y_escribir_falso)

    codigo = cli.main(["--modo", "medibles", "--root-dir", "/una/ruta"])

    assert codigo == 0
    assert llamadas == [
        (
            "medibles",
            Path("/una/ruta"),
            transcriptor_falso,
            Path("mediciones") / "deteccion_medibles.json",
        )
    ]


# ---------------------------------------------------------------------
# escribir_artefacto (T032b) -- mismo mecanismo exacto que
# medicion.cli.escribir_artefacto/EscrituraIncompletaError.
# ---------------------------------------------------------------------


_SUBCONJUNTO_VACIO = ResultadoSubconjunto(
    precision=None,
    exhaustividad=None,
    balance_f1=None,
    num_notas_referencia=0,
    num_notas_estimadas=0,
    verdaderos_positivos=0,
)


def _artefacto_de_prueba() -> ArtefactoDeteccion:
    return ArtefactoDeteccion(
        modelo=ModeloTranscripcionDeclarado(
            nombre="Basic Pitch",
            variante="icassp_2022",
            firma="3db297d5",
            backend="tflite",
            licencia="Apache-2.0 -- solo para tests",
        ),
        tolerancia_tono_cents=50.0,
        ventana_inicio_s=0.05,
        grabaciones=["00_BN1-129-Eb_comp"],
        exclusiones=[],
        resultados_por_grabacion=[],
        global_=_SUBCONJUNTO_VACIO,
        monofonico=_SUBCONJUNTO_VACIO,
        polifonico=_SUBCONJUNTO_VACIO,
    )


def test_escribir_artefacto_produce_json_valido_y_legible(tmp_path: Path) -> None:
    ruta = tmp_path / "mediciones" / "deteccion_medibles.json"
    artefacto = _artefacto_de_prueba()

    cli.escribir_artefacto(ruta, artefacto)

    contenido = json.loads(ruta.read_text())
    assert contenido["grabaciones"] == ["00_BN1-129-Eb_comp"]


def test_escribir_artefacto_crea_varios_niveles_de_directorio_ausentes(tmp_path: Path) -> None:
    """`mkdir(parents=True, ...)` (mutation testing, T026: sobrevivía
    mutado a `parents=False`/`parents=None`/omitido) -- un solo nivel de
    anidamiento (`tmp_path/mediciones/...`, el resto de los tests de este
    archivo) no lo distingue de `parents=False`, porque `tmp_path` mismo
    ya existe. Con DOS niveles ausentes (`a/b/`), `parents=False` fallaría
    con `FileNotFoundError` -- este test exige que no falle."""
    ruta = tmp_path / "a" / "b" / "deteccion_medibles.json"
    artefacto = _artefacto_de_prueba()

    cli.escribir_artefacto(ruta, artefacto)

    assert json.loads(ruta.read_text())["grabaciones"] == ["00_BN1-129-Eb_comp"]


def test_escribir_artefacto_usa_sufijo_tmp_para_el_archivo_temporal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """El nombre del archivo temporal termina en `.tmp` (mutation
    testing, T026: sobrevivía mutado a `.TMP`/vacío -- el sufijo exacto
    no afecta la atomicidad en sí, pero sí es lo que un humano vería
    listando el directorio a mitad de una escritura)."""
    ruta = tmp_path / "mediciones" / "deteccion_medibles.json"
    artefacto = _artefacto_de_prueba()
    origenes: list[Path] = []

    def _os_replace_que_registra(origen: Path, destino: Path) -> None:
        origenes.append(origen)
        os_replace_real(origen, destino)

    os_replace_real = cli.os.replace
    monkeypatch.setattr(cli.os, "replace", _os_replace_que_registra)

    cli.escribir_artefacto(ruta, artefacto)

    assert origenes == [ruta.with_name(ruta.name + ".tmp")]


def test_escribir_artefacto_es_atomico_no_deja_archivo_final_truncado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "mediciones" / "deteccion_medibles.json"
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
    ruta = tmp_path / "mediciones" / "deteccion_medibles.json"
    artefacto = _artefacto_de_prueba()

    monkeypatch.setattr(cli.os, "replace", lambda origen, destino: None)

    with pytest.raises(cli.EscrituraIncompletaError) as excinfo:
        cli.escribir_artefacto(ruta, artefacto)

    assert not ruta.exists()
    # Mensaje EXACTO, no solo el tipo de excepción (mutation testing,
    # T026: `raise EscrituraIncompletaError(None)` sobrevivía sin esto).
    assert str(excinfo.value) == (
        f"'{ruta}' no quedó legible después de escribirlo -- "
        f"[Errno 2] No such file or directory: '{ruta}'."
    )


def test_escribir_artefacto_falla_cerrado_si_deja_un_artefacto_viejo_a_medias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "mediciones" / "deteccion_medibles.json"
    ruta.parent.mkdir(parents=True)
    ruta.write_text(json.dumps({"grabaciones": []}))
    artefacto = _artefacto_de_prueba()  # grabaciones=["00_BN1-129-Eb_comp"], otra longitud

    monkeypatch.setattr(cli.os, "replace", lambda origen, destino: None)

    with pytest.raises(cli.EscrituraIncompletaError) as excinfo:
        cli.escribir_artefacto(ruta, artefacto)

    # Mensaje EXACTO -- los dos conteos que discrepan, no solo el tipo de
    # excepción (mutation testing, T026: `raise EscrituraIncompletaError(None)`
    # sobrevivía sin esto).
    assert str(excinfo.value) == (
        f"'{ruta}' no coincide con el artefacto recién calculado: "
        "0 grabaciones persistidas, 1 esperadas."
    )


# ---------------------------------------------------------------------
# _ejecutar_y_escribir (T032b) -- de punta a punta con TranscriptorFalso
# y el índice de mirdata monkeypatcheado (nunca GuitarSet real).
# ---------------------------------------------------------------------


class _NoteDataFalso:
    def __init__(self, intervals: np.ndarray, pitches: np.ndarray) -> None:
        self.intervals = intervals
        self.pitches = pitches


class _TrackFalso:
    def __init__(self, audio_mic_path: str, notes_all: _NoteDataFalso | None) -> None:
        self.audio_mic_path = audio_mic_path
        self.notes_all = notes_all


class _DatasetFalso:
    """Sustituto de `mirdata.core.Dataset` con `.track_ids` (que usa
    `construir_lista_grabaciones`) y `.track()` (que usa `leer_grabacion`)."""

    def __init__(self, tracks: dict[str, _TrackFalso]) -> None:
        self._tracks = tracks
        self.track_ids = sorted(tracks.keys())

    def track(self, track_id: str) -> _TrackFalso:
        if track_id not in self._tracks:
            raise ValueError(f"{track_id} is not a valid track_id in guitarset")
        return self._tracks[track_id]


def _monkeypatch_mirdata(monkeypatch: pytest.MonkeyPatch, dataset: _DatasetFalso) -> None:
    """Un único monkeypatch sobre el módulo `mirdata` real cubre tanto
    `deteccion.orquestador.mirdata` como `ingestion.guitarset.mirdata` --
    ambos son el mismo objeto módulo (`sys.modules['mirdata']`), así que
    parchear su atributo `initialize` una vez alcanza para las dos rutas
    de llamada (`construir_lista_grabaciones` y `leer_grabacion`)."""

    def _initialize_falso(nombre: str, data_home: str | None = None) -> _DatasetFalso:
        # `data_home=None` por defecto, como la firma real de
        # `mirdata.initialize` (`dataset_name, data_home=None, ...`) --
        # `validar_indice_mirdata` (FR-016) invoca sin `data_home` en
        # absoluto, antes de que `construir_lista_grabaciones`/
        # `leer_grabacion` lo pasen explícito.
        assert nombre == "guitarset"
        return dataset

    monkeypatch.setattr(mirdata, "initialize", _initialize_falso)


def test_ejecutar_y_escribir_produce_artefacto_en_disco(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dominio sintético de 100 identificadores (por encima de
    `tamano_reserva=72`, el default real que `_ejecutar_y_escribir` no
    sobreescribe -- mismos parámetros que usaría la CLI real) -- las 100
    comparten el mismo `_TrackFalso` (sin notas de referencia), así que
    el resultado no depende de cuáles 28 exactas caen en `"medibles"`,
    solo de que sean 100 - 72 = 28."""
    (tmp_path / "annotation").mkdir()
    (tmp_path / "audio_mono-mic").mkdir()
    track = _TrackFalso(audio_mic_path="/datos/dummy_mic.wav", notes_all=None)
    dominio = sorted(f"grabacion_{i:03d}" for i in range(100))
    dataset = _DatasetFalso(dict.fromkeys(dominio, track))
    _monkeypatch_mirdata(monkeypatch, dataset)
    transcriptor = TranscriptorFalso(modelo_declarado=MODELO_FALSO)
    ruta_artefacto = tmp_path / "mediciones" / "deteccion_medibles.json"

    codigo = cli._ejecutar_y_escribir("medibles", tmp_path, transcriptor, ruta_artefacto)

    assert codigo == 0
    contenido = json.loads(ruta_artefacto.read_text())
    assert len(contenido["grabaciones"]) == 28
    assert contenido["exclusiones"] == []
    assert contenido["modelo"]["nombre"] == "ModeloFalso"


def test_ejecutar_y_escribir_pasa_el_mismo_root_dir_a_ambas_llamadas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`root_dir` (el parámetro de `_ejecutar_y_escribir`) MUST llegar
    igual a `construir_lista_grabaciones` y a `ejecutar_deteccion` --
    mutation testing, T026: `construir_lista_grabaciones(modo, None)` y
    `ejecutar_deteccion(grabaciones, None, transcriptor)` sobrevivían sin
    ningún test que mirara qué `root_dir` recibía cada llamada."""
    (tmp_path / "annotation").mkdir()
    (tmp_path / "audio_mono-mic").mkdir()
    track = _TrackFalso(audio_mic_path="/datos/dummy_mic.wav", notes_all=None)
    dominio = sorted(f"grabacion_{i:03d}" for i in range(100))
    dataset = _DatasetFalso(dict.fromkeys(dominio, track))
    llamadas_data_home: list[str | None] = []

    def _initialize_falso(nombre: str, data_home: str | None = None) -> _DatasetFalso:
        assert nombre == "guitarset"
        llamadas_data_home.append(data_home)
        return dataset

    monkeypatch.setattr(mirdata, "initialize", _initialize_falso)
    transcriptor = TranscriptorFalso(modelo_declarado=MODELO_FALSO)
    ruta_artefacto = tmp_path / "salida" / "deteccion_medibles.json"

    cli._ejecutar_y_escribir("medibles", tmp_path, transcriptor, ruta_artefacto)

    # `validar_indice_mirdata` (FR-016) invoca sin `data_home` a propósito
    # (research.md #19) -- se descarta esa llamada; todas las demás
    # (`construir_lista_grabaciones`, una por `leer_grabacion`) deben
    # llevar exactamente `root_dir`, nunca `None` ni otra ruta.
    llamadas_con_root_dir = [v for v in llamadas_data_home if v is not None]
    assert len(llamadas_con_root_dir) >= 2
    assert all(v == str(tmp_path) for v in llamadas_con_root_dir)


def test_ejecutar_y_escribir_devuelve_dos_y_el_mensaje_si_la_escritura_falla(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Camino de `EscrituraIncompletaError` a través de
    `_ejecutar_y_escribir` (no `escribir_artefacto` llamado directo,
    como el resto de sus tests) -- mutation testing, T026: el código de
    salida `2`, y el mensaje impreso en `stderr`, no tenían ningún test
    que pasara por ESTE camino en particular."""
    (tmp_path / "annotation").mkdir()
    (tmp_path / "audio_mono-mic").mkdir()
    track = _TrackFalso(audio_mic_path="/datos/dummy_mic.wav", notes_all=None)
    dominio = sorted(f"grabacion_{i:03d}" for i in range(100))
    dataset = _DatasetFalso(dict.fromkeys(dominio, track))
    _monkeypatch_mirdata(monkeypatch, dataset)
    transcriptor = TranscriptorFalso(modelo_declarado=MODELO_FALSO)
    ruta_artefacto = tmp_path / "salida" / "deteccion_medibles.json"
    monkeypatch.setattr(cli.os, "replace", lambda origen, destino: None)

    codigo = cli._ejecutar_y_escribir("medibles", tmp_path, transcriptor, ruta_artefacto)

    assert codigo == 2
    assert capsys.readouterr().err.strip() == (
        f"'{ruta_artefacto}' no quedó legible después de escribirlo -- "
        f"[Errno 2] No such file or directory: '{ruta_artefacto}'."
    )


# ---------------------------------------------------------------------
# Precondiciones de arranque (FR-015/FR-016, research.md #19) -- deben
# fallar ANTES de procesar ninguna grabación, nunca a mitad de la
# corrida. Incidente real: `--root-dir` apuntando al repositorio en vez
# del dataset -- reproducido en research.md #19 como un
# `FileNotFoundError` sin envolver en la primera grabación (no como 288
# exclusiones idénticas, la forma en que se reportó de entrada); en
# cualquiera de las dos formas, nada validaba `root_dir` antes de
# arrancar.
# ---------------------------------------------------------------------


def test_root_dir_sin_estructura_de_guitarset_falla_antes_de_procesar_nada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`tmp_path` no tiene ni 'annotation/' ni 'audio_mono-mic/' -- si la
    validación no corriera ANTES de `construir_lista_grabaciones`, este
    dataset falso de una sola grabación procesaría igual (mirdata está
    mockeado, no hay ningún archivo real que lo detenga)."""
    track = _TrackFalso(audio_mic_path="/datos/dummy_mic.wav", notes_all=None)
    dataset = _DatasetFalso({"grabacion_000": track})
    _monkeypatch_mirdata(monkeypatch, dataset)
    transcriptor = TranscriptorFalso(modelo_declarado=MODELO_FALSO)
    ruta_artefacto = tmp_path / "salida" / "deteccion_medibles.json"

    codigo = cli._ejecutar_y_escribir("medibles", tmp_path, transcriptor, ruta_artefacto)

    assert codigo == 1
    assert transcriptor.llamadas == 0  # nunca se llegó a transcribir nada
    assert not ruta_artefacto.exists()
    mensaje = capsys.readouterr().err
    assert "annotation" in mensaje
    assert "audio_mono-mic" in mensaje
    assert str(tmp_path) in mensaje


def test_indice_mirdata_ausente_falla_antes_de_procesar_nada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`root_dir` tiene la estructura correcta (FR-015 no es el problema
    aquí) pero el índice de `mirdata` no está disponible (FR-016) --
    debe fallar antes de invocar `construir_lista_grabaciones`, con un
    mensaje que diga cómo descargarlo."""
    (tmp_path / "annotation").mkdir()
    (tmp_path / "audio_mono-mic").mkdir()

    def _initialize_sin_indice(nombre: str, data_home: str | None = None) -> None:
        assert nombre == "guitarset"
        raise FileNotFoundError("Dataset index for guitarset was expected but not found.")

    monkeypatch.setattr(mirdata, "initialize", _initialize_sin_indice)
    transcriptor = TranscriptorFalso(modelo_declarado=MODELO_FALSO)
    ruta_artefacto = tmp_path / "salida" / "deteccion_medibles.json"

    codigo = cli._ejecutar_y_escribir("medibles", tmp_path, transcriptor, ruta_artefacto)

    assert codigo == 1
    assert transcriptor.llamadas == 0
    assert not ruta_artefacto.exists()
    mensaje = capsys.readouterr().err
    assert "download" in mensaje
    assert "index" in mensaje
