# Quickstart: Lectura de un tema de Slakh2100

Valida que `leer_tema` (ver [contracts/leer_tema.md](./contracts/leer_tema.md))
cumple el spec, en dos niveles: sin dataset real (lo que corre siempre,
en CI) y con una copia local real (validación manual puntual).

## Sin dataset real — lo que corre en `just gauntlet`

Los tests de `tests/unit/`, `tests/integration/` y `tests/property/`
construyen su propia estructura `TrackXXXXX/` sintética en un
`tmp_path` (research.md #6) — no requieren nada instalado ni descargado.

```bash
uv sync
just gauntlet
```

Escenarios que deben quedar cubiertos (mapean 1:1 a las Acceptance
Scenarios de `spec.md`):

- Tema con una guitarra → mezcla + una `PistaGuitarra` con su
  `identificador_origen` correcto.
- Tema con varias guitarras (limpia/distorsionada/acústica) → todas
  presentes, sin fusionar.
- Tema con bajo eléctrico junto a guitarras → el bajo no aparece en
  `guitarras`.
- Tema con una guitarra `audio_rendered: false` → esa guitarra no
  aparece (research.md #4), y si es la única, `guitarras == []` sin
  error (mismo camino que un tema sin guitarras).
- Tema sin guitarras → `guitarras == []`, sin excepción.
- `tema_id` inexistente → `TemaNoExisteError`.
- Mezcla y una guitarra con longitudes distintas → `LongitudInconsistenteError`
  con tema + pista, sin recorte ni relleno.
- Metadatos referencian una guitarra `audio_rendered: true` cuyo
  archivo `.flac` no está en disco → `ArchivoAudioNoLegibleError` con
  tema + archivo.
- Round-trip de contenido: las muestras devueltas para un `.flac`
  sintético coinciden exactamente (comparación entera, no con
  tolerancia) con las muestras usadas para generarlo.

## Con una copia local real de Slakh2100 (validación manual, no en CI)

Prerrequisito: una copia local del dataset (descargada por fuera de
este repo, según la política de fuentes admisibles — Principio IV de la
constitución).

```bash
export SLAKH2100_ROOT=/ruta/a/tu/copia/de/slakh2100
uv run python -c "
from pathlib import Path
from guitar_tabs_analysis.ingestion.slakh2100 import leer_tema

resultado = leer_tema('Track00001', Path('$SLAKH2100_ROOT'))
print(resultado.tema_id, resultado.mezcla.frecuencia_muestreo, len(resultado.guitarras))
for g in resultado.guitarras:
    print(' ', g.identificador_origen, g.audio.muestras.shape)
"
```

Resultado esperado: sin excepción, `frecuencia_muestreo` igual a la
declarada por el conjunto (44100 en la distribución oficial), y una
línea por cada pista de guitarra real del tema. Repetir con un
`tema_id` inexistente y confirmar que el mensaje de `TemaNoExisteError`
nombra ese identificador.
