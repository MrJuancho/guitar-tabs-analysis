"""Tests del propio helper de fixtures (T004 de
`specs/001-lectura-tema-slakh2100/tasks.md`), no de `leer_tema()`.

Verifica que `construir_tema_sintetico` puede construir tanto el camino
feliz como los tres casos de fallo/exclusión que las fases futuras
(T007+) de `tasks.md` necesitan: una pista de guitarra con longitud
distinta a la mezcla, un stem prometido por los metadatos
(`audio_rendered: true`) pero sin archivo escrito, y un stem
`audio_rendered: false` coherentemente sin archivo -- sin invocar
`leer_tema` en ningún caso, esa función todavía no existe en este slice.
"""

from __future__ import annotations

from pathlib import Path

import soundfile as sf
import yaml

from tests.fixtures.slakh2100_fixture import EspecificacionStem, construir_tema_sintetico


def test_construye_estructura_basica_con_mezcla_y_un_stem_de_guitarra(tmp_path: Path) -> None:
    root_dir = construir_tema_sintetico(
        tmp_path,
        tema_id="Track00001",
        stems=(EspecificacionStem(identificador="S01", inst_class="Guitar"),),
    )

    tema_dir = root_dir / "Track00001"
    assert (tema_dir / "mix.flac").is_file()
    assert (tema_dir / "stems" / "S01.flac").is_file()

    metadata = yaml.safe_load((tema_dir / "metadata.yaml").read_text())
    assert metadata["stems"]["S01"]["inst_class"] == "Guitar"
    assert metadata["stems"]["S01"]["audio_rendered"] is True


def test_permite_stem_no_renderizado_coherentemente_sin_archivo(tmp_path: Path) -> None:
    root_dir = construir_tema_sintetico(
        tmp_path,
        tema_id="Track00002",
        stems=(EspecificacionStem(identificador="S02", inst_class="Guitar", audio_rendered=False),),
    )

    tema_dir = root_dir / "Track00002"
    metadata = yaml.safe_load((tema_dir / "metadata.yaml").read_text())
    assert metadata["stems"]["S02"]["audio_rendered"] is False
    assert not (tema_dir / "stems" / "S02.flac").exists()


def test_permite_stem_rendered_true_sin_archivo_escrito_en_disco(tmp_path: Path) -> None:
    root_dir = construir_tema_sintetico(
        tmp_path,
        tema_id="Track00003",
        stems=(
            EspecificacionStem(
                identificador="S03",
                inst_class="Guitar",
                audio_rendered=True,
                escribir_archivo=False,
            ),
        ),
    )

    tema_dir = root_dir / "Track00003"
    metadata = yaml.safe_load((tema_dir / "metadata.yaml").read_text())
    assert metadata["stems"]["S03"]["audio_rendered"] is True
    assert not (tema_dir / "stems" / "S03.flac").exists()


def test_permite_longitud_de_stem_distinta_a_la_de_la_mezcla(tmp_path: Path) -> None:
    root_dir = construir_tema_sintetico(
        tmp_path,
        tema_id="Track00004",
        n_muestras_mezcla=200,
        stems=(EspecificacionStem(identificador="S04", inst_class="Guitar", n_muestras=150),),
    )

    tema_dir = root_dir / "Track00004"
    info_mezcla = sf.info(str(tema_dir / "mix.flac"))
    info_stem = sf.info(str(tema_dir / "stems" / "S04.flac"))
    assert info_mezcla.frames == 200
    assert info_stem.frames == 150


def test_permite_omitir_el_archivo_de_mezcla(tmp_path: Path) -> None:
    root_dir = construir_tema_sintetico(tmp_path, tema_id="Track00005", escribir_mix=False)

    tema_dir = root_dir / "Track00005"
    assert tema_dir.is_dir()
    assert not (tema_dir / "mix.flac").exists()


def test_distingue_bajo_electrico_de_guitarra_en_los_metadatos(tmp_path: Path) -> None:
    root_dir = construir_tema_sintetico(
        tmp_path,
        tema_id="Track00006",
        stems=(
            EspecificacionStem(identificador="S01", inst_class="Guitar"),
            EspecificacionStem(identificador="S02", inst_class="Bass"),
        ),
    )

    tema_dir = root_dir / "Track00006"
    metadata = yaml.safe_load((tema_dir / "metadata.yaml").read_text())
    assert metadata["stems"]["S01"]["inst_class"] == "Guitar"
    assert metadata["stems"]["S02"]["inst_class"] == "Bass"
