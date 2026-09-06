"""Tests unitarios de `medicion.orquestador.construir_lista_temas` (T013
de `specs/004-medicion-linea-base/tasks.md`, Foundational)."""

from __future__ import annotations

from pathlib import Path

from guitar_tabs_analysis.ingestion.slakh2100 import leer_tema
from guitar_tabs_analysis.medicion.orquestador import construir_lista_temas
from tests.fixtures.dataset_sintetico_fixture import construir_varios_temas_sinteticos


def _dataset_con_cuatro_splits(tmp_path: Path) -> Path:
    construir_varios_temas_sinteticos(tmp_path, split="train", cantidad=3)
    construir_varios_temas_sinteticos(tmp_path, split="validation", cantidad=5)
    construir_varios_temas_sinteticos(tmp_path, split="test", cantidad=2)
    construir_varios_temas_sinteticos(tmp_path, split="omitted", cantidad=2)
    return tmp_path


def test_submuestra_hito1_es_reproducible_con_la_misma_semilla(tmp_path: Path) -> None:
    root_dir = _dataset_con_cuatro_splits(tmp_path)

    primera = construir_lista_temas("submuestra_hito1", root_dir, tamano_submuestra=3)
    segunda = construir_lista_temas("submuestra_hito1", root_dir, tamano_submuestra=3)

    assert primera == segunda
    assert len(primera) == 3
    assert all(tema.startswith("validation/") for tema in primera)


def test_conjunto_completo_incluye_train_y_validation_nunca_test_ni_omitted(
    tmp_path: Path,
) -> None:
    root_dir = _dataset_con_cuatro_splits(tmp_path)

    temas = construir_lista_temas("conjunto_completo", root_dir)

    assert len(temas) == 3 + 5  # train + validation, sin muestreo
    assert all(tema.startswith("train/") or tema.startswith("validation/") for tema in temas)
    assert not any(tema.startswith("test/") for tema in temas)
    assert not any(tema.startswith("omitted/") for tema in temas)


def test_cada_identificador_devuelto_se_puede_leer_con_leer_tema(tmp_path: Path) -> None:
    root_dir = _dataset_con_cuatro_splits(tmp_path)

    temas = construir_lista_temas("conjunto_completo", root_dir)

    for tema_id in temas:
        lectura = leer_tema(tema_id, root_dir)
        assert lectura.tema_id == tema_id
