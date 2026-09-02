# Contrato: `leer_tema`

Este proyecto es una librería (no expone API HTTP ni CLI para esta
feature), así que el contrato es la firma pública de la función de
`ingestion` y el comportamiento observable descrito en `spec.md`.

## Firma

```python
def leer_tema(tema_id: str, root_dir: Path) -> LecturaTema:
    ...
```

- `tema_id`: identificador nativo del tema en el conjunto (nombre de
  directorio, p. ej. `"Track00001"`).
- `root_dir`: raíz local de la distribución de Slakh2100 (contiene los
  directorios `TrackXXXXX/`) — ver `research.md` #5.
- Retorna: `LecturaTema` (ver `data-model.md`).

## Precondiciones

- `root_dir` existe y es legible (fuera del alcance de esta feature
  verificar más que eso — spec.md Assumptions).

## Postcondiciones (éxito)

Para cualquier invocación que no falle:

1. `resultado.tema_id == tema_id`.
2. `resultado.mezcla` tiene el contenido exacto de `mix.flac` para ese
   tema, sin remuestreo/conversión de canales/normalización (FR-005,
   SC-005).
3. `resultado.guitarras` contiene exactamente una entrada por cada stem
   con `inst_class == "Guitar"` y `audio_rendered == true` en
   `metadata.yaml`, ni una más ni una menos (FR-002, FR-003, FR-004,
   SC-001, SC-003). Un stem `inst_class == "Guitar"` con
   `audio_rendered == false` se excluye por **FR-013** — no cuenta para
   este "ni una más ni una menos", y no aparece en la tabla de fallos de
   abajo.
4. Cada `PistaGuitarra` en `resultado.guitarras` comparte longitud y
   frecuencia de muestreo con `resultado.mezcla` (FR-006), y esa
   frecuencia coincide con la declarada por el conjunto para el tema
   (FR-007).
5. Todas las muestras devueltas (mezcla y guitarras) están dentro del
   rango representable por su formato de origen, sin `NaN`/`inf`
   (FR-008).
6. Si el tema no tiene ninguna pista de guitarra elegible,
   `resultado.guitarras == []` y la llamada retorna normalmente, sin
   excepción (FR-009, SC-002).

## Modos de fallo (la llamada lanza, no retorna un resultado parcial)

| Condición | Excepción | Mensaje debe incluir |
|---|---|---|
| `tema_id` no corresponde a ningún directorio del conjunto | `TemaNoExisteError` | el `tema_id` solicitado (FR-010) |
| El tema existe, pero `mix.flac` o un stem con `audio_rendered == true` referenciado en los metadatos está ausente o no se puede decodificar | `ArchivoAudioNoLegibleError` | el `tema_id` y el archivo/stem afectado (FR-012) |
| La mezcla y una pista de guitarra del mismo tema tienen distinta longitud (número de muestras) | `LongitudInconsistenteError` | el `tema_id` y el `identificador_origen` de la pista afectada (FR-011) — ninguno de los dos audios se recorta ni se rellena para forzar coincidencia |

Ninguna de estas condiciones se señaliza devolviendo `None`, una
colección con valores centinela, o un resultado silenciosamente
truncado — siempre es una excepción con la información de arriba.

**Explícitamente NO es un fallo**: un stem `inst_class == "Guitar"` con
`audio_rendered == false` no tiene archivo, pero eso no dispara
`ArchivoAudioNoLegibleError` — la fila de arriba solo aplica a un stem
con `audio_rendered == true` (o a la mezcla). Ese caso es una exclusión
silenciosa de `resultado.guitarras`, gobernada por FR-013, no un modo de
fallo de esta tabla.

## Fuera de este contrato

- Verificación de integridad/descarga del dataset (spec.md Assumptions).
- Qué temas se usan para evaluación / filtrado de temas sin guitarra
  (spec.md "Fuera de alcance").
- Cualquier conversión de formato (resampleo, mono↔estéreo,
  normalización) — explícitamente prohibida, no solo fuera de alcance.
