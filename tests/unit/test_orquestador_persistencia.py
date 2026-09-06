"""Tests unitarios de persistencia atómica por tema (T011 de
`specs/004-medicion-linea-base/tasks.md`, Foundational)."""

from __future__ import annotations

from pathlib import Path

from guitar_tabs_analysis.analytics.metrica_separacion import (
    ReferenciaEmparejada,
    ReferenciaSinPareja,
    ReporteTema,
)
from guitar_tabs_analysis.medicion.orquestador import (
    ExclusionMedicion,
    ResultadoProcesamientoTema,
    escribir_progreso_tema,
    leer_progreso_tema,
)
from guitar_tabs_analysis.separacion.separador import TransformacionDeclarada


def test_escribir_y_leer_un_resultado_exitoso_recupera_los_mismos_valores(tmp_path: Path) -> None:
    resultado = ResultadoProcesamientoTema(
        tema_id="validation/Track00001",
        reporte=ReporteTema(
            tema_id="validation/Track00001",
            num_referencias=2,
            num_estimaciones_recibidas=1,
            emparejadas=[
                ReferenciaEmparejada(
                    identificador_referencia="S01",
                    identificador_estimacion="guitar",
                    si_sdr=12.5,
                )
            ],
            sin_pareja=[
                ReferenciaSinPareja(
                    identificador_referencia="S02", motivo="sin_estimacion_disponible"
                )
            ],
        ),
        exclusion=None,
        transformaciones=[
            TransformacionDeclarada(
                tipo="frecuencia_muestreo",
                direccion="entrada",
                aplicada=False,
                detalle="sin cambio",
            )
        ],
    )

    escribir_progreso_tema(tmp_path, resultado)
    recuperado = leer_progreso_tema(tmp_path, "validation/Track00001")

    assert recuperado == resultado


def test_escribir_y_leer_una_exclusion_recupera_los_mismos_valores(tmp_path: Path) -> None:
    resultado = ResultadoProcesamientoTema(
        tema_id="validation/Track00002",
        reporte=None,
        exclusion=ExclusionMedicion(
            tema_id="validation/Track00002", motivo="fallo_procesamiento", detalle="boom"
        ),
        transformaciones=[],
    )

    escribir_progreso_tema(tmp_path, resultado)
    recuperado = leer_progreso_tema(tmp_path, "validation/Track00002")

    assert recuperado == resultado


def test_leer_progreso_sin_manifiesto_previo_devuelve_none(tmp_path: Path) -> None:
    assert leer_progreso_tema(tmp_path, "validation/Track00099") is None


def test_archivo_temporal_sin_renombrar_no_se_confunde_con_uno_completo(tmp_path: Path) -> None:
    """Simula una interrupción a mitad de `escribir_progreso_tema`: el
    archivo temporal existe, pero el `os.replace()` final nunca ocurrió."""
    (tmp_path / "validation__Track00003.json.tmp").write_text('{"incompleto": true')

    assert leer_progreso_tema(tmp_path, "validation/Track00003") is None
