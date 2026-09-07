"""Tests de `medicion.compuerta.evaluar_artefacto` (T002 de
`specs/005-compuerta-metrica/tasks.md`, User Story 1) -- sobre `dict`s
sintéticos con la forma exacta de `artefacto_a_dict` (Feature 004,
data-model.md de esta feature), nunca sobre el artefacto real ni un
modelo: la compuerta no invoca ninguno de los dos (FR-001).
"""

from __future__ import annotations

from typing import Any

import pytest

from guitar_tabs_analysis.medicion.compuerta import (
    PRESUPUESTO_SI_SDR_DB,
    ArtefactoInvalidoError,
    evaluar_artefacto,
)

_MODELO = {
    "nombre": "Demucs",
    "variante": "htdemucs_6s",
    "firma": "5c90dfd2",
    "checksum_sha256_prefijo": "d2a1745f0744",
    "licencia_pesos": "ninguna -- solo para tests",
}


def _reporte(
    tema_id: str, si_sdr_emparejadas: list[float], num_sin_pareja: int = 0
) -> dict[str, Any]:
    return {
        "tema_id": tema_id,
        "num_referencias": len(si_sdr_emparejadas) + num_sin_pareja,
        "num_estimaciones_recibidas": len(si_sdr_emparejadas),
        "emparejadas": [
            {
                "identificador_referencia": f"S{i:02d}",
                "identificador_estimacion": "guitar",
                "si_sdr": valor,
            }
            for i, valor in enumerate(si_sdr_emparejadas)
        ],
        "sin_pareja": [
            {"identificador_referencia": f"X{i:02d}", "motivo": "sin_estimacion_disponible"}
            for i in range(num_sin_pareja)
        ],
    }


def _artefacto(
    reportes: list[dict[str, Any]], *, modelo: dict[str, str] | None = None
) -> dict[str, Any]:
    return {
        "modo": "submuestra_hito1",
        "semilla": 20260904,
        "modelo": modelo if modelo is not None else _MODELO,
        "temas": [r["tema_id"] for r in reportes],
        "exclusiones": [],
        "reportes": reportes,
        "transformaciones_por_tema": {},
        "mediana": None,
        "distribucion_referencias_por_tema": {},
    }


def test_mediana_por_encima_del_presupuesto_aprueba() -> None:
    artefacto = _artefacto([_reporte("Track00000", [-3.0, -2.0])])

    veredicto = evaluar_artefacto(artefacto)

    assert veredicto.aprobado is True
    assert veredicto.mediana_emparejadas == -2.5
    assert veredicto.presupuesto == PRESUPUESTO_SI_SDR_DB


def test_veredicto_incluye_todo_el_contexto_del_artefacto_sin_alterarlo() -> None:
    """Triage de mutación (T015): ningún test anterior comprobaba
    `modelo_nombre`/`modelo_variante`/`modo`/`semilla` -- solo
    `modelo_firma` (test de firma arbitraria). Cada uno debe ser el eco
    exacto de lo que trae `datos`, nunca un valor derivado (FR-009)."""
    artefacto = _artefacto([_reporte("Track00000", [-3.0, -2.0])])

    veredicto = evaluar_artefacto(artefacto)

    assert veredicto.modelo_nombre == _MODELO["nombre"]
    assert veredicto.modelo_variante == _MODELO["variante"]
    assert veredicto.modelo_firma == _MODELO["firma"]
    assert veredicto.modo == "submuestra_hito1"
    assert veredicto.semilla == 20260904


def test_mediana_exactamente_en_el_presupuesto_aprueba() -> None:
    """Límite inclusive (spec.md US1 AS3): un empate exacto es aprobación."""
    artefacto = _artefacto([_reporte("Track00000", [PRESUPUESTO_SI_SDR_DB])])

    veredicto = evaluar_artefacto(artefacto)

    assert veredicto.aprobado is True
    assert veredicto.mediana_emparejadas == PRESUPUESTO_SI_SDR_DB


def test_mediana_por_debajo_del_presupuesto_rechaza() -> None:
    artefacto = _artefacto([_reporte("Track00000", [-20.0, -15.0])])

    veredicto = evaluar_artefacto(artefacto)

    assert veredicto.aprobado is False
    assert veredicto.mediana_emparejadas == -17.5


def test_pool_se_acumula_sobre_todos_los_reportes_no_solo_el_primero() -> None:
    artefacto = _artefacto(
        [
            _reporte("Track00000", [-3.0], num_sin_pareja=1),
            _reporte("Track00001", [-1.0, 3.0], num_sin_pareja=2),
        ]
    )

    veredicto = evaluar_artefacto(artefacto)

    assert veredicto.mediana_emparejadas == -1.0
    assert veredicto.total_emparejadas == 3
    assert veredicto.total_sin_pareja == 3
    assert veredicto.fraccion_sin_pareja == 3 / 6


def test_firma_de_modelo_arbitraria_no_afecta_el_veredicto() -> None:
    """C2 de /speckit-analyze, spec.md US3 AS3: hoy `evaluar_artefacto` no
    tiene ningún código de comparación de firma -- esta es la guarda que
    falla el día que alguien agregue esa comparación sin querer, rompiendo
    el propósito de detectar regresiones al cambiar de modelo."""
    modelo_desconocido = {**_MODELO, "firma": "firma-inventada"}
    artefacto = _artefacto([_reporte("Track00000", [-3.0, -2.0])], modelo=modelo_desconocido)

    veredicto = evaluar_artefacto(artefacto)

    assert veredicto.aprobado is True
    assert veredicto.modelo_firma == "firma-inventada"


def test_artefacto_sin_clave_reportes_es_invalido() -> None:
    artefacto = _artefacto([])
    del artefacto["reportes"]

    with pytest.raises(ArtefactoInvalidoError) as excinfo:
        evaluar_artefacto(artefacto)

    assert "reportes" in str(excinfo.value)
    assert excinfo.value.motivo == str(excinfo.value)


def test_artefacto_sin_ningun_reporte_es_invalido() -> None:
    """Conjunto de referencias vacío (spec.md Edge Cases): sin ningún
    `reporte`, no hay ningún valor de `si_sdr` contra el cual comparar
    el presupuesto."""
    artefacto = _artefacto([])

    with pytest.raises(ArtefactoInvalidoError) as excinfo:
        evaluar_artefacto(artefacto)

    assert "evidencia" in str(excinfo.value)


def test_artefacto_con_reportes_pero_ninguna_referencia_emparejada_es_invalido() -> None:
    """El caso más angosto de research.md #5: `total_referencias > 0`
    (hay `sin_pareja`), pero el pool de la mediana de *emparejadas*
    queda vacío -- `statistics.median([])` levantaría `StatisticsError`
    sin control si no se valida antes."""
    artefacto = _artefacto([_reporte("Track00000", [], num_sin_pareja=3)])

    with pytest.raises(ArtefactoInvalidoError) as excinfo:
        evaluar_artefacto(artefacto)

    assert "evidencia" in str(excinfo.value)


@pytest.mark.parametrize("clave_faltante", ["modelo", "modo", "semilla"])
def test_artefacto_sin_clave_de_contexto_es_invalido(clave_faltante: str) -> None:
    """C1 de /speckit-analyze: `evaluar_artefacto` lee `datos["modelo"]`,
    `datos["modo"]` y `datos["semilla"]` además de `reportes` -- sin esta
    validación, un artefacto al que le falte cualquiera de las tres
    levantaría un `KeyError` crudo en vez de `ArtefactoInvalidoError`,
    exactamente el modo de fallo que esta feature existe para cerrar."""
    artefacto = _artefacto([_reporte("Track00000", [-3.0, -2.0])])
    del artefacto[clave_faltante]

    with pytest.raises(ArtefactoInvalidoError) as excinfo:
        evaluar_artefacto(artefacto)

    assert clave_faltante in str(excinfo.value)
