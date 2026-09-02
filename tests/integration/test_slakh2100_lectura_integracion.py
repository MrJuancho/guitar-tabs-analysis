"""Tests de integración end-to-end para `leer_tema()` (T007-T009 de
`specs/001-lectura-tema-slakh2100/tasks.md`, User Story 1/P1).

Cada test construye un tema sintético completo (`metadata.yaml` +
`mix.flac` + `stems/*.flac`) vía `tests/fixtures/slakh2100_fixture.py` y
ejercita `leer_tema()` de punta a punta contra ese `tmp_path` -- nunca
audio real (constitución Principio IV).
"""

from __future__ import annotations

from pathlib import Path

from guitar_tabs_analysis.ingestion.slakh2100 import leer_tema
from tests.fixtures.slakh2100_fixture import EspecificacionStem, construir_tema_sintetico


def test_tema_con_una_unica_guitarra_devuelve_mezcla_y_esa_pista(tmp_path: Path) -> None:
    """spec.md Acceptance Scenario US1.1: una única pista de guitarra ->
    la colección devuelta contiene exactamente esa pista, con su
    identificador de origen correcto."""
    root_dir = construir_tema_sintetico(
        tmp_path,
        tema_id="Track00001",
        stems=(EspecificacionStem(identificador="S01", inst_class="Guitar"),),
    )

    resultado = leer_tema("Track00001", root_dir)

    assert resultado.tema_id == "Track00001"
    assert len(resultado.guitarras) == 1
    assert resultado.guitarras[0].identificador_origen == "S01"
