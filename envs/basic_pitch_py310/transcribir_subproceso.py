#!/usr/bin/env python3
"""CLI standalone, corre bajo el intérprete Python 3.10 de este proyecto
(`envs/basic_pitch_py310/`, research.md #15 de
`specs/006-deteccion-notas-guitarra-limpia/`) -- NO es parte del paquete
`guitar_tabs_analysis`, se invoca como proceso externo, nunca se importa.

uso: python transcribir_subproceso.py <ruta_audio> <ruta_salida_json>

Invoca `basic_pitch.inference.predict()` sobre `ruta_audio` y escribe un
array JSON de objetos `{"tono_midi": float, "inicio_s": float, "fin_s":
float}` -- uno por evento de nota que el modelo detecta, posiblemente un
array vacío (silencio total es un resultado legítimo) -- en
`ruta_salida_json`, con escritura atómica (temporal + `os.replace()`,
mismo mecanismo que el resto del proyecto principal usa para artefactos).
Sale con código `0` en el camino feliz.

Ante cualquier excepción real durante la inferencia, imprime el detalle
completo a stderr, sale con código distinto de cero, y NUNCA escribe
`ruta_salida_json` (ni lo deja a medio escribir) -- el adaptador del
proyecto principal (`transcripcion.basic_pitch_transcriptor.BasicPitchTranscriptor`)
trata el archivo de salida ausente, junto con el código de salida, como
la señal de fallo (`TranscripcionFallidaError`), nunca como "sin notas".

Comunicación por archivo, nunca por stdout: `basic_pitch`/sus dependencias
(TFLite, resampy) emiten advertencias y mensajes de progreso reales
durante el import y la inferencia -- mezclarlos con los datos en stdout
exigiría un protocolo de framing que un archivo de salida evita por
completo (research.md #15).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(f"uso: {argv[0]} <ruta_audio> <ruta_salida_json>", file=sys.stderr)
        return 2

    ruta_audio, ruta_salida_json = argv[1], argv[2]

    try:
        # Import diferido a propósito: si el uso es incorrecto (arriba),
        # falla rápido sin pagar el costo de cargar basic_pitch/TFLite.
        from basic_pitch.inference import predict

        _, _, note_events = predict(ruta_audio)
        notas = [
            {"tono_midi": float(tono_midi), "inicio_s": float(inicio_s), "fin_s": float(fin_s)}
            for inicio_s, fin_s, tono_midi, _velocity, _pitch_bend in note_events
        ]
    except Exception as causa:  # noqa: BLE001 -- cualquier fallo real de inferencia se reporta a stderr, nunca se escribe la salida
        print(
            f"transcribir_subproceso: fallo real durante la inferencia sobre "
            f"'{ruta_audio}': {causa!r}",
            file=sys.stderr,
        )
        return 1

    destino_dir = os.path.dirname(os.path.abspath(ruta_salida_json)) or "."
    descriptor, ruta_temporal = tempfile.mkstemp(
        dir=destino_dir, prefix=".transcribir_subproceso-", suffix=".json.tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
            json.dump(notas, archivo)
        os.replace(ruta_temporal, ruta_salida_json)
    except Exception:
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)
        raise

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
