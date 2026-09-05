"""Verifica que `docs/ATRIBUCIONES.md` declara lo que FR-003/FR-004
exigen -- sin ejecutar ninguna inferencia (User Story 2, Independent Test
de `spec.md`)."""

from __future__ import annotations

from pathlib import Path

_RUTA = Path(__file__).resolve().parents[2] / "docs" / "ATRIBUCIONES.md"


def _contenido() -> str:
    return _RUTA.read_text(encoding="utf-8")


def test_archivo_existe() -> None:
    assert _RUTA.is_file(), f"{_RUTA} no existe"


def test_declara_licencia_mit_del_codigo() -> None:
    assert "MIT" in _contenido()


def test_declara_la_variante_del_modelo() -> None:
    assert "htdemucs_6s" in _contenido()


def test_declara_uso_personal_y_educativo() -> None:
    contenido = _contenido().lower()
    assert "personal" in contenido
    assert "educativo" in contenido


def test_cita_la_fuente_de_la_restriccion_de_los_pesos() -> None:
    assert "facebookresearch/demucs#327" in _contenido()
