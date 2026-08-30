"""Compuertas de calidad sobre ARTEFACTOS de datos, no sobre el código.

ESPECÍFICO DEL DOMINIO -- esto es un esqueleto FUNCIONAL con UN gate de
ejemplo (`pct_valores_vacios`), no una lista real de compuertas. Antes de
usarlo en serio:

1. Reemplaza `GOLD_GATES` por los presupuestos reales de tu dominio. Cada
   entrada no-cero debería ser deuda documentada con `owner`/fecha (ver
   `docs/adr/`), no un umbral elegido a ojo.
2. Reemplaza `medir_metricas_calidad` por las mediciones reales sobre tu
   artefacto (Parquet, tabla, lo que sea la capa curada de tu pipeline).
3. Actualiza `main()` para leer la ruta real del artefacto -- ahora mismo
   apunta a un ejemplo (`data/gold/ejemplo.parquet`) que no existe hasta
   que corras tu propio pipeline.

`data-auditor` (`.claude/agents/data-auditor.md`) interpreta los números de
este módulo contra `docs/adr/` -- si cambias `GOLD_GATES`, revisa que ese
agente y el ADR correspondiente sigan describiendo la misma realidad.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

GOLD_GATES: dict[str, dict[str, object]] = {
    # EJEMPLO -- borra esta entrada al agregar los gates reales del dominio.
    "pct_valores_vacios": {"max": 0.05, "owner": "TODO", "trend": "decreasing"},
}


@dataclass(frozen=True)
class ResultadoGate:
    nombre: str
    valor: float
    presupuesto: dict[str, object]

    @property
    def aprueba(self) -> bool:
        maximo = self.presupuesto["max"]
        assert isinstance(maximo, int | float)
        return self.valor <= maximo

    @property
    def severity(self) -> str:
        return str(self.presupuesto.get("severity", "error"))


def medir_metricas_calidad(df: pd.DataFrame) -> dict[str, float]:
    """Calcula el valor real de cada métrica de `GOLD_GATES` a partir del
    artefacto ya persistido. EJEMPLO: `pct_valores_vacios` sobre una
    columna `valor` -- reemplaza por las mediciones reales del dominio."""
    total = len(df)
    if total == 0:
        return {"pct_valores_vacios": 0.0}
    return {"pct_valores_vacios": float((df["valor"].astype(str).str.strip() == "").sum() / total)}


def evaluar_gates(df: pd.DataFrame) -> list[ResultadoGate]:
    """Evalúa cada gate de `GOLD_GATES` contra el DataFrame dado."""
    metricas = medir_metricas_calidad(df)
    return [
        ResultadoGate(nombre, metricas[nombre], presupuesto)
        for nombre, presupuesto in GOLD_GATES.items()
        if nombre in metricas
    ]


def main() -> int:
    """CLI: evalúa los gates sobre el artefacto curado (invocada por
    `just gates`). TODO: cambia esta ruta por la de tu propio artefacto."""
    artefacto = Path("data/gold/ejemplo.parquet")
    if not artefacto.exists():
        print(f"No existe {artefacto}. Corre tu pipeline primero.", file=sys.stderr)
        return 1

    df = pd.read_parquet(artefacto)
    resultados = evaluar_gates(df)

    hubo_falla = False
    for resultado in resultados:
        if resultado.aprueba:
            estado = "PASA"
        elif resultado.severity == "warn":
            estado = "WARN"
        else:
            estado = "FALLA"
            hubo_falla = True
        maximo = resultado.presupuesto["max"]
        print(f"{resultado.nombre:35s} valor={resultado.valor!r:12} max={maximo!r:8} [{estado}]")

    return 1 if hubo_falla else 0


if __name__ == "__main__":
    sys.exit(main())
