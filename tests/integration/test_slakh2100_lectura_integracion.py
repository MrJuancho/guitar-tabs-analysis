"""Tests de integración end-to-end para `leer_tema()` (T007-T009, T014,
T016-T018 de `specs/001-lectura-tema-slakh2100/tasks.md`, User Story
1/P1, User Story 2/P2 y User Story 3/P3).

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


def test_tema_con_varias_guitarras_devuelve_todas_sin_fusionar(tmp_path: Path) -> None:
    """spec.md Acceptance Scenario US1.2: guitarra limpia, distorsionada y
    acústica -> las tres presentes por separado, cada una con su propio
    identificador de origen."""
    root_dir = construir_tema_sintetico(
        tmp_path,
        tema_id="Track00002",
        stems=(
            EspecificacionStem(
                identificador="S01",
                inst_class="Guitar",
                midi_program_name="Clean Electric Guitar",
            ),
            EspecificacionStem(
                identificador="S02",
                inst_class="Guitar",
                midi_program_name="Distortion Guitar",
            ),
            EspecificacionStem(
                identificador="S03",
                inst_class="Guitar",
                midi_program_name="Acoustic Guitar",
            ),
        ),
    )

    resultado = leer_tema("Track00002", root_dir)

    identificadores = {guitarra.identificador_origen for guitarra in resultado.guitarras}
    assert identificadores == {"S01", "S02", "S03"}
    assert len(resultado.guitarras) == 3


def test_tema_con_bajo_electrico_no_incluye_el_bajo_entre_las_guitarras(tmp_path: Path) -> None:
    """spec.md Acceptance Scenario US1.3 / FR-004: un bajo eléctrico
    agrupado junto a las guitarras no debe aparecer en la colección
    devuelta."""
    root_dir = construir_tema_sintetico(
        tmp_path,
        tema_id="Track00003",
        stems=(
            EspecificacionStem(identificador="S01", inst_class="Guitar"),
            EspecificacionStem(
                identificador="S02", inst_class="Bass", midi_program_name="Electric Bass"
            ),
        ),
    )

    resultado = leer_tema("Track00003", root_dir)

    identificadores = {guitarra.identificador_origen for guitarra in resultado.guitarras}
    assert identificadores == {"S01"}
    assert "S02" not in identificadores


def test_tema_sin_pistas_de_guitarra_devuelve_mezcla_y_coleccion_vacia(tmp_path: Path) -> None:
    """spec.md Acceptance Scenario US2.1 / FR-009 / SC-002: un tema sin
    ninguna pista etiquetada como guitarra en sus metadatos devuelve la
    mezcla junto con una colección vacía, sin lanzar ninguna excepción."""
    root_dir = construir_tema_sintetico(
        tmp_path,
        tema_id="Track00004",
        stems=(
            EspecificacionStem(identificador="S01", inst_class="Drums"),
            EspecificacionStem(identificador="S02", inst_class="Bass"),
        ),
    )

    resultado = leer_tema("Track00004", root_dir)

    assert resultado.tema_id == "Track00004"
    assert resultado.guitarras == []
