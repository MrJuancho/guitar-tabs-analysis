#!/usr/bin/env python3
"""PreToolUse (Edit|Write) -- bloquea tests/holdout/. FALLA CERRADO.

Componente de seguridad, no de conveniencia: si no se puede determinar con
certeza la ruta del archivo (JSON malformado en stdin, campo ausente, error
de cualquier tipo), se BLOQUEA por defecto en vez de dejar pasar. Es la
lección fundacional de este patrón: un hook que depende de una herramienta
ausente (originalmente `jq`) y cae a `exit 0` en silencio deja de proteger
sin que nadie se entere.
"""

from __future__ import annotations

import json
import sys


def _ruta_del_archivo() -> str | None:
    try:
        datos = json.load(sys.stdin)
    except Exception:
        return None
    tool_input = datos.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    ruta = tool_input.get("file_path")
    if not isinstance(ruta, str) or not ruta:
        return None
    return ruta


def main() -> int:
    ruta = _ruta_del_archivo()
    if ruta is None:
        print(
            "No se pudo determinar la ruta del archivo -- bloqueado por "
            "seguridad (fail-closed). Si esto es un falso positivo, revisa "
            ".claude/hooks/block_holdout.py.",
            file=sys.stderr,
        )
        return 2
    if "tests/holdout/" in ruta:
        print(
            "tests/holdout/ es zona de retencion: el agente no puede leerla "
            "ni modificarla (ver AGENTS.md).",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
