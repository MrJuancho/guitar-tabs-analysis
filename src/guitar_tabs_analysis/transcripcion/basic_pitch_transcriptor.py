"""Adaptador real que invoca Basic Pitch por subproceso (capa
`transcripcion`) -- este módulo NUNCA importa `basic_pitch` directamente:
es irresoluble en Python 3.12 (research.md #2 de
`specs/006-deteccion-notas-guitarra-limpia/`). En su lugar, invoca el
intérprete ya materializado de un segundo proyecto `uv`, fijado a Python
3.10 (`envs/basic_pitch_py310/`, research.md #15), corriendo
`envs/basic_pitch_py310/transcribir_subproceso.py` sobre `ruta_audio`, con
una ruta de salida JSON temporal como segundo argumento.

Implementa el protocolo `Transcriptor` de `transcripcion.transcriptor`.
Cubre T014(b) de `specs/006-deteccion-notas-guitarra-limpia/tasks.md`. Ver
research.md #15 y contracts/deteccion.md (sección `BasicPitchTranscriptor`)
para el contrato completo.

**Invocación directa del intérprete del venv, nunca `uv run` en tiempo de
llamada** (research.md #15): `uv run` sincroniza el entorno (y con él, su
`uv.lock`) implícitamente antes de ejecutar -- si este adaptador usara
`uv run`, un desincronizado real entre `pyproject.toml` y `uv.lock` de
`envs/basic_pitch_py310/` se curaría en silencio en cada llamada, y `just
doctor` nunca lo detectaría (mismo antipatrón que AGENTS.md documenta para
`uv.lock` del proyecto principal).
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from guitar_tabs_analysis.analytics.metrica_deteccion_notas import NotaEstimada
from guitar_tabs_analysis.transcripcion.transcriptor import (
    ModeloTranscripcionDeclarado,
    TranscripcionFallidaError,
)

# Resuelto de forma robusta relativa a la raíz del repo, no al directorio
# de trabajo del proceso que invoca -- este archivo vive en
# src/guitar_tabs_analysis/transcripcion/, tres niveles bajo la raíz.
# Públicos (sin guion bajo) a propósito: el test de integración
# `modelo_real` (T015) los usa para decidir si el entorno secundario está
# materializado antes de invocarlo, mismo criterio que `MODELO_DECLARADO`
# más abajo -- configuración fija del adaptador, consultable desde fuera.
RAIZ_REPO = Path(__file__).resolve().parents[3]
ENV_DIR = RAIZ_REPO / "envs" / "basic_pitch_py310"
PYTHON_ENV = ENV_DIR / ".venv" / "bin" / "python"
SCRIPT_SUBPROCESO = ENV_DIR / "transcribir_subproceso.py"

MODELO_DECLARADO = ModeloTranscripcionDeclarado(
    nombre="Basic Pitch",
    variante="icassp_2022",
    # Primeros 8 caracteres hex de sha256(nmp.tflite) -- el archivo de
    # pesos real bundleado dentro del paquete instalado
    # (envs/basic_pitch_py310/.venv/.../basic_pitch/saved_models/icassp_2022/nmp.tflite),
    # verificado en vivo contra el entorno real (`sha256sum` sobre ese
    # archivo exacto), mismo criterio que `firma="5c90dfd2"` de
    # `separacion.demucs_separador.MODELO_DECLARADO` en el hito 1: un
    # identificador corto y estable de los pesos concretos que se están
    # usando, no de la versión del paquete (que podría publicar los
    # mismos pesos bajo un número de versión distinto, o pesos distintos
    # bajo el mismo número).
    firma="3db297d5",
    backend="tflite",
    licencia="Apache-2.0 (código y pesos) -- ver docs/ATRIBUCIONES.md",
)
"""Declaración fija del modelo (data-model.md), verificada en vivo contra
el modelo real (research.md #1/#2/#15)."""


class BasicPitchTranscriptor:
    """Implementa el protocolo `Transcriptor` invocando Basic Pitch por
    subproceso en `envs/basic_pitch_py310/`."""

    modelo_declarado: ModeloTranscripcionDeclarado = MODELO_DECLARADO

    def transcribir(self, ruta_audio: Path) -> list[NotaEstimada]:
        """Invoca `transcribir_subproceso.py` sobre `ruta_audio` y
        parsea su salida JSON a `list[NotaEstimada]`.

        Trata como fallo real (`TranscripcionFallidaError`, nunca una
        lista vacía por defecto) cualquiera de tres casos: código de
        salida distinto de cero, archivo de salida ausente pese a
        código `0`, o JSON presente pero malformado -- los tres con el
        `stderr` capturado del subproceso como parte de la causa.
        """
        with tempfile.TemporaryDirectory(prefix="basic_pitch_transcriptor-") as directorio:
            ruta_salida = Path(directorio) / "notas.json"
            resultado = subprocess.run(
                [str(PYTHON_ENV), str(SCRIPT_SUBPROCESO), str(ruta_audio), str(ruta_salida)],
                capture_output=True,
                text=True,
            )

            if resultado.returncode != 0:
                raise TranscripcionFallidaError(
                    ruta_audio,
                    RuntimeError(
                        "el subproceso de Basic Pitch salió con código "
                        f"{resultado.returncode}: {resultado.stderr.strip()}"
                    ),
                )
            if not ruta_salida.exists():
                raise TranscripcionFallidaError(
                    ruta_audio,
                    RuntimeError(
                        "el subproceso de Basic Pitch salió con código 0 pero no escribió "
                        f"el archivo de salida esperado: {resultado.stderr.strip()}"
                    ),
                )
            try:
                contenido = json.loads(ruta_salida.read_text(encoding="utf-8"))
            except json.JSONDecodeError as causa:
                raise TranscripcionFallidaError(
                    ruta_audio,
                    RuntimeError(f"el archivo de salida del subproceso no es JSON válido: {causa}"),
                ) from causa

            return [
                NotaEstimada(
                    tono_midi=float(nota["tono_midi"]),
                    inicio_s=float(nota["inicio_s"]),
                    fin_s=float(nota["fin_s"]),
                )
                for nota in contenido
            ]
