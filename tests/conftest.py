"""Conftest raíz de `tests/` -- por ahora, un único mecanismo: que un
test marcado `modelo_real` que termina saltado nunca pase desapercibido
(T017 de `specs/003-separacion-modelo-preentrenado/tasks.md`).

`modelo_real` (research.md #7 de esa feature) es el único test que
ejercita el sistema completo con el modelo real de punta a punta; los
`addopts` del proyecto (`-q --strict-markers`) no imprimen el motivo de
un salto por defecto, así que sin este hook un salto real sería
indistinguible de "todo pasó" -- el mismo patrón de "compuerta que pasa
sin haber examinado nada" que `AGENTS.md` ya documenta (el hook de `jq`
ausente, el orden de `uv lock --check`).

`pytest_plugins = ["pytester"]` habilita el fixture `pytester` que el
test de regresión de este mismo mecanismo usa
(`tests/unit/test_conftest_modelo_real.py`) -- pytest exige declarar
plugins de este tipo en el conftest de nivel más alto del árbol de
tests, no en uno anidado; este archivo es ese conftest de nivel más
alto (no hay ninguno por encima de `tests/`).
"""

from __future__ import annotations

from typing import Any

pytest_plugins = ["pytester"]


def pytest_terminal_summary(terminalreporter: Any, exitstatus: int, config: Any) -> None:
    saltados = terminalreporter.stats.get("skipped", [])
    saltados_modelo_real = [reporte for reporte in saltados if "modelo_real" in reporte.keywords]
    if not saltados_modelo_real:
        return

    terminalreporter.write_sep("=", "MODELO REAL: tests saltados", red=True, bold=True)
    terminalreporter.write_line(
        f"{len(saltados_modelo_real)} test(s) marcado(s) 'modelo_real' se saltaron -- "
        "es el ÚNICO test que ejercita el sistema completo de punta a punta con el "
        "modelo real. Saltarlo sin red/pesos cacheados es razonable; que pase "
        "desapercibido no lo es."
    )
    for reporte in saltados_modelo_real:
        motivo = reporte.longrepr[-1] if isinstance(reporte.longrepr, tuple) else reporte.longrepr
        terminalreporter.write_line(f"  - {reporte.nodeid}: {motivo}")
