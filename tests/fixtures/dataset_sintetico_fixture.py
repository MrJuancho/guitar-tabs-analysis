"""Fixture de dataset sintético para `medicion` (Feature 004): construye
varios temas -- posiblemente en varios splits -- sobre el mismo `tmp_path`,
reutilizando `construir_tema_sintetico` (fixture de la Feature 001,
`tests/fixtures/slakh2100_fixture.py`) **sin modificarla**.

`construir_tema_sintetico` ya soporta un `tema_id` con `/` embebido
(`tema_dir = tmp_path / tema_id`, `mkdir(parents=True)`) -- research.md #8
de `specs/004-medicion-linea-base/`, verificado en esa sesión de
planificación. Eso es lo que permite poblar `validation/`, `train/`,
`test/` y `omitted/` del mismo dataset sintético en un solo `tmp_path`,
con identificadores de tema calificados por split
(`"validation/Track00000"`) igual que en producción (research.md #3).
"""

from __future__ import annotations

from pathlib import Path

from tests.fixtures.slakh2100_fixture import EspecificacionStem, construir_tema_sintetico


def construir_varios_temas_sinteticos(
    tmp_path: Path,
    split: str,
    cantidad: int,
    guitarras_por_tema: int | list[int] = 1,
) -> Path:
    """Construye `cantidad` temas sintéticos bajo `tmp_path/split/`, cada
    uno con `tema_id = f"{split}/Track{i:05d}"`.

    `guitarras_por_tema` como `int` aplica el mismo número de pistas de
    guitarra (`inst_class="Guitar"`, `audio_rendered=True`) a los
    `cantidad` temas; como `list[int]` de longitud `cantidad` fija un
    número distinto por tema (por ejemplo, para dejar uno sin ninguna
    guitarra -- `0` en esa posición). Devuelve `tmp_path`, la raíz que
    espera `leer_tema`/`construir_lista_temas`.
    """
    if isinstance(guitarras_por_tema, int):
        cantidades = [guitarras_por_tema] * cantidad
    else:
        cantidades = guitarras_por_tema
        if len(cantidades) != cantidad:
            raise ValueError(
                f"guitarras_por_tema tiene {len(cantidades)} elementos, pero cantidad={cantidad}."
            )

    for indice, n_guitarras in enumerate(cantidades):
        stems = tuple(
            EspecificacionStem(identificador=f"G{g:02d}", inst_class="Guitar")
            for g in range(n_guitarras)
        )
        construir_tema_sintetico(
            tmp_path,
            tema_id=f"{split}/Track{indice:05d}",
            stems=stems,
            semilla=indice,
        )

    return tmp_path
