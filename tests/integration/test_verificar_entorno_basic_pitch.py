"""Test de regresión de `scripts/verificar_entorno_basic_pitch.sh`
(research.md #18 de `specs/006-deteccion-notas-guitarra-limpia/`): el
chequeo del entorno secundario de Basic Pitch en `just doctor` debe pasar
(código 2, nunca `fallo`) Y reportar de forma visible cuando `.venv` no
existe todavía -- research.md #18: mismo criterio en CI que en local, ese
estado es legítimo, `just detectar`/tests `modelo_real` son quienes de
verdad necesitan el entorno -- y debe seguir verificando de VERDAD (código
1, `fallo` real) cuando el entorno SÍ existe pero está roto, o pasar
limpio (código 0) cuando existe y está sano.

Construye entornos sintéticos con `uv venv`/`uv lock` REALES (proyectos de
cero dependencias, sin red) en vez de mockear `subprocess` -- mismo
criterio que los property tests de este proyecto: probar contra el
comportamiento real de las herramientas, no una simulación de él. No
depende de -- ni toca -- el `.venv` real de `envs/basic_pitch_py310/`."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "verificar_entorno_basic_pitch.sh"
_VERSION_PYTHON = f"{sys.version_info.major}.{sys.version_info.minor}"


def _correr(ruta_entorno: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), str(ruta_entorno)],
        capture_output=True,
        text=True,
    )


def test_directorio_del_entorno_ausente_es_fallo_real(tmp_path: Path) -> None:
    """El directorio de `envs/basic_pitch_py310/` está versionado
    (pyproject.toml/uv.lock/transcribir_subproceso.py, research.md #15) --
    su ausencia es un repositorio roto, no una omisión esperada."""
    ruta = tmp_path / "no_existe"

    resultado = _correr(ruta)

    assert resultado.returncode == 1
    assert "FALTA" in resultado.stdout
    assert str(ruta) in resultado.stdout


def test_venv_ausente_pasa_y_reporta_la_omision_de_forma_visible(tmp_path: Path) -> None:
    """Estado real de CI (research.md #18): el directorio del entorno
    existe (versionado), pero nadie corrió `uv sync` ahí todavía."""
    ruta = tmp_path / "entorno"
    ruta.mkdir()
    (ruta / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.1.0"\n')

    resultado = _correr(ruta)

    assert resultado.returncode == 2
    assert "OMITIDO" in resultado.stdout
    assert ".venv" in resultado.stdout
    assert "modelo_real" in resultado.stdout


def _crear_entorno_uv(ruta: Path) -> None:
    ruta.mkdir()
    (ruta / "pyproject.toml").write_text(
        '[project]\nname = "fake-basic-pitch-env"\nversion = "0.1.0"\n'
        'requires-python = ">=3.10"\ndependencies = []\n'
    )
    subprocess.run(
        ["uv", "venv", "--python", _VERSION_PYTHON, str(ruta / ".venv")],
        check=True,
        capture_output=True,
    )
    subprocess.run(["uv", "lock"], cwd=ruta, check=True, capture_output=True)


def test_venv_presente_pero_basic_pitch_no_importa_es_fallo_real(tmp_path: Path) -> None:
    """El entorno está sano en todo lo demás (intérprete ejecutable, lock
    sincronizado) -- le falta justo lo que este chequeo existe para
    confirmar. Prueba que "existe" no basta para pasar."""
    ruta = tmp_path / "entorno"
    _crear_entorno_uv(ruta)

    resultado = _correr(ruta)

    assert resultado.returncode == 1
    assert "basic_pitch no importa" in resultado.stdout


def test_venv_presente_y_sano_verifica_completo_y_pasa(tmp_path: Path) -> None:
    ruta = tmp_path / "entorno"
    _crear_entorno_uv(ruta)
    sitepkgs = subprocess.run(
        [
            str(ruta / ".venv" / "bin" / "python"),
            "-c",
            "import site; print(site.getsitepackages()[0])",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    (Path(sitepkgs) / "basic_pitch.py").write_text("")

    resultado = _correr(ruta)

    assert resultado.returncode == 0
    assert "verificado" in resultado.stdout
