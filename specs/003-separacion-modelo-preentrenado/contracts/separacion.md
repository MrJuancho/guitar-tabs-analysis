# Contrato: `separacion`

Librería (sin API HTTP ni CLI para esta feature). El contrato es la firma
pública de `separacion.separador` y el comportamiento observable descrito
en `spec.md`. Dos módulos, una sola función pública de orquestación.

## `separar_guitarra`

```python
def separar_guitarra(
    tema_id: str,
    mezcla: PistaAudio,
    separador: Separador,
) -> ResultadoSeparacionTema:
    ...
```

Módulo: `separacion.separador`. No importa `torch` ni `demucs` — solo
depende del protocolo `Separador` (data-model.md), inyectado por quien
llama. El adaptador real (`separacion.demucs_separador.DemucsSeparador`)
vive en un módulo aparte que sí los importa (research.md #7/#8).

`separador` se recibe como parámetro **a propósito** — no hay un
`_cargar_modelo()` interno por defecto: cargar `htdemucs_6s` implica
descargar/verificar pesos y construir el objeto `torch`, un costo que la
mayoría de los tests no deben pagar (research.md #7). Quien orquesta una
corrida real construye un `DemucsSeparador` una sola vez y lo reutiliza
para todos los temas.

### Precondiciones

- `mezcla.muestras` es un array de una sola dimensión (mono) — el
  contrato de `PistaAudio` de la Feature 001. `separar_guitarra` no valida
  esto explícitamente porque es una garantía del tipo de entrada, no un
  caso de error propio de esta feature.
- `separador` implementa el protocolo completo (`modelo_declarado`,
  `samplerate`, `audio_channels`, `separar`) — un `Separador` de prueba
  incompleto es un error de configuración del test, no un caso que este
  contrato documente como fallo en producción.

### Postcondiciones

1. **Verificación de formato siempre declarada (FR-005, FR-006, FR-007).**
   `resultado.transformaciones` contiene siempre una entrada
   `tipo="frecuencia_muestreo", direccion="entrada"` y una
   `tipo="canales", direccion="entrada"`, con `aplicada=False` cuando
   `mezcla.frecuencia_muestreo == separador.samplerate` (resp. cuando el
   número de canales de `mezcla` ya coincide con `separador.audio_channels`)
   y `aplicada=True` en caso contrario — nunca se omiten por no haber
   requerido cambio real.
2. **Duplicación de canal cuando el modelo espera más canales que la
   mezcla (FR-006).** Si `separador.audio_channels > 1` y `mezcla` es
   mono, la entrada que recibe `separador.separar()` tiene el canal mono
   repetido en cada uno de los `audio_channels` canales — no rellenada con
   silencio ni tomada de una sola pasada.
3. **Ausencia total de estimación (FR-009).** Si el diccionario que
   devuelve `separador.separar()` no contiene la clave `"guitar"`,
   `resultado.estimaciones == []` — nunca se sintetiza una `Estimacion`
   artificial para representar la ausencia.
4. **Estimación real, silenciosa o no (FR-010).** Si el diccionario sí
   contiene `"guitar"`, `resultado.estimaciones` tiene exactamente un
   elemento, sin importar si su audio resulta tener energía nula —
   clasificar esa situación es responsabilidad de la Feature 002
   (`emparejar_tema`), no de esta función.
5. **Colapso de salida a mono declarado (FR-006, FR-007).** Cuando se
   produce una `Estimacion` (postcondición 4), su `audio.muestras` es de
   una sola dimensión, resultado de promediar los canales de la salida del
   modelo para la fuente `"guitar"` (research.md #4) — nunca un canal
   descartado — y `resultado.transformaciones` incluye la entrada
   `tipo="canales", direccion="salida"` correspondiente.
6. **Modelo declarado, siempre presente (FR-002).** `resultado.modelo ==
   separador.modelo_declarado`, sin transformación — es un eco, no un
   cálculo.
7. **Fallo real del modelo, no silenciado (FR-014).** Si
   `separador.separar()` levanta cualquier excepción, `separar_guitarra`
   la envuelve en `SeparacionFallidaError(tema_id, ...)` encadenada
   (`raise ... from causa_original`) y la propaga — nunca la captura en
   silencio, nunca reintenta la llamada.
8. **No hay reescalado de amplitud.** Las únicas transformaciones que esta
   función aplica son las declaradas explícitamente en las postcondiciones
   2 y 5 (duplicar/colapsar canales) y, cuando aplica, remuestreo
   (postcondición 1) — ningún ajuste de ganancia ni normalización.

### Modos de fallo

| Excepción | Cuándo | Mensaje incluye |
|---|---|---|
| `SeparacionFallidaError` | `separador.separar()` levanta cualquier excepción durante la inferencia (FR-014) | `tema_id` y la causa original (encadenada, no reformulada) |

No hay una segunda excepción para "el modelo no produjo guitarra" — ese no
es un modo de fallo, es el resultado normal de la postcondición 3
(`estimaciones == []`).

## `DemucsSeparador`

Módulo: `separacion.demucs_separador`. Implementa el protocolo `Separador`
envolviendo `demucs.api.Separator(model="htdemucs_6s", device="cpu",
shifts=0)` (research.md #1, #2, #10 — `shifts=0` no es el valor por
defecto de la librería, es obligatorio para que FR-015 se cumpla, ver
postcondición 4). Expone `modelo_declarado` como la constante fija
descrita en data-model.md (`MODELO_DECLARADO`). No forma parte del
contrato probado por los tests unitarios de `separar_guitarra` (research.md
#7) — se prueba una sola vez, de punta a punta, en
`tests/integration/test_demucs_separador_integracion.py`, marcado
`@pytest.mark.modelo_real`.

### Precondiciones

- El proceso tiene acceso de red la primera vez que se construye (para
  descargar y verificar los pesos, research.md #2) o los pesos ya están en
  la caché local de `torch.hub`. Sin ninguna de las dos, la construcción
  falla — ver Modos de fallo.

### Postcondiciones

1. `device="cpu"` fijo — nunca intenta usar GPU, consistente con "sin GPU
   declarada" (Assumptions de `spec.md`).
2. `samplerate`/`audio_channels` se leen de las propiedades reales del
   `Separator` cargado (`44100`/`2` para `htdemucs_6s`, research.md #4),
   nunca hardcodeadas en este adaptador tampoco — sería la misma
   suposición que el contrato de `separar_guitarra` prohíbe un nivel más
   arriba.
3. No entrena ni ajusta ningún parámetro del modelo cargado (FR-011) — el
   modelo se usa exclusivamente en modo evaluación.
4. Dos llamadas a `separar()` con la misma entrada producen resultados
   idénticos dentro de la tolerancia de FR-015 (verificado: bit a bit
   idénticos en el backend de CPU de este proyecto) — depende
   directamente de `shifts=0`; el valor por defecto de la librería
   (`shifts=1`) viola esta postcondición por diseño (research.md #10).

### Modos de fallo

| Excepción | Cuándo |
|---|---|
| Cualquier excepción de `demucs`/`torch` (no envuelta aquí) | Fallo de carga o de inferencia — `separar_guitarra` es quien la envuelve en `SeparacionFallidaError` (postcondición 7 de arriba), este adaptador no la captura. |
