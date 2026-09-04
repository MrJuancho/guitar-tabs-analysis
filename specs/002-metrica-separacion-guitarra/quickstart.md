# Quickstart: Métrica de separación de guitarra

Valida que `si_sdr` / `emparejar_tema` / `agregar_conjunto` (ver
[contracts/metrica_separacion.md](./contracts/metrica_separacion.md))
cumplen el spec. A diferencia de Feature 001, esta feature no lee nada de
disco — todo corre con audio sintético construido en memoria, así que no
hay una sección separada "con dataset real": los mismos escenarios corren
siempre, en CI.

## Lo que corre en `just gauntlet`

```bash
uv sync
just gauntlet
```

Escenarios que deben quedar cubiertos (mapean 1:1 a las Acceptance
Scenarios de `spec.md`):

### `si_sdr` (unidad)

- Una referencia senoidal pasada como su propia estimación → `si_sdr(...)
  == float("inf")` exacto (research.md #5) — no `pytest.approx`.
- Una referencia senoidal contra una estimación que es puro silencio
  (vector cero) → `si_sdr(...) == float("-inf")` exacto.
- Una referencia con energía nula (silencio digital) → `ReferenciaEnergiaNulaError`,
  sin excepción numérica no controlada (sin `RuntimeWarning` sin capturar).
- Una referencia y una estimación de distinta longitud, o de distinta
  frecuencia de muestreo → `EstimacionIncompatibleError` con ambos
  identificadores.
- Una referencia y una estimación con una relación de escala/ganancia
  conocida (p. ej. la estimación es la referencia multiplicada por 3) →
  el mismo `si_sdr` que sin esa ganancia — confirma la invarianza a
  escala (research.md #1/#3) sin depender de la implementación interna.

### `emparejar_tema` (User Story 1)

- Una referencia, una estimación que la aproxima → una `ReferenciaEmparejada`,
  `sin_pareja == []`, conteos de 1 y 1.
- Varias referencias, igual o más estimaciones → cada referencia
  emparejada con una estimación distinta (ningún `identificador_estimacion`
  repetido).
- Más referencias que estimaciones → las referencias sobrantes en
  `sin_pareja` con `motivo == "sin_estimacion_disponible"`, sin excepción.
- Cero estimaciones → todas las referencias en `sin_pareja`, `num_estimaciones_recibidas == 0`.
- Una referencia con energía nula entre otras con energía → esa referencia
  en `sin_pareja` con `motivo == "energia_nula"`, distinta de las que
  faltan por escasez de estimaciones; el resto del tema se calcula con
  normalidad.
- Verificación de respuesta conocida completa (FR-011/SC-001): pasar cada
  referencia de un tema sintético multi-guitarra como su propia
  estimación (con identificadores coincidentes) → todas terminan en
  `emparejadas` con `si_sdr == float("inf")`, sin necesidad de ningún
  separador real.

### `agregar_conjunto` (User Story 2)

- Conjunto de temas con y sin pistas de referencia → los que no tienen
  ninguna quedan en `exclusiones` con `motivo == "sin_guitarra_referencia"`,
  no aparecen en `reportes_por_tema`.
- Conjunto con un tema `es_directorio_omitido=True` → excluido con
  `motivo == "directorio_omitido"`, incluso si además tiene referencias.
- Conjunto con un tema sin estimaciones (`estimaciones == []`) pero con
  referencias → **permanece evaluado** (no en `exclusiones`), sus
  referencias entran a la mediana como `-inf`.
- El mismo conjunto agregado dos veces, con y sin un tema de referencias
  sin pareja → la mediana con ese tema nunca es mejor (SC-004) — comparar
  ambos resultados numéricamente.
- Conjunto con temas de distinto número de referencias (1, 2, 3) →
  `distribucion_referencias_por_tema` refleja el conteo exacto por tema, y
  la mediana pesa cada referencia individualmente, no cada tema por igual
  (User Story 2, escenario 6 de `spec.md`) — verificable construyendo el
  conjunto a mano y calculando la mediana esperada fuera del sistema para
  comparar.
- Lista de entradas vacía, o donde todas quedan excluidas → `mediana is
  None`, `num_temas_evaluados == 0`, sin excepción (FR-014).

## Ejecución manual de un ejemplo end-to-end

No requiere ningún dataset ni separador real — construye todo en memoria:

```bash
uv run python -c "
import numpy as np
from guitar_tabs_analysis.ingestion.slakh2100 import PistaAudio, PistaGuitarra
from guitar_tabs_analysis.analytics.metrica_separacion import (
    Estimacion, EntradaConjunto, emparejar_tema, agregar_conjunto,
)

sr = 44100
t = np.linspace(0, 1, sr, endpoint=False)
onda = (np.sin(2 * np.pi * 220 * t) * 1000).astype(np.int16)

referencia = PistaGuitarra('S01', PistaAudio(onda, sr))
estimacion_perfecta = Estimacion('sep_S01', PistaAudio(onda, sr))

reporte = emparejar_tema('Track00001', [referencia], [estimacion_perfecta])
print('SI-SDR (referencia == estimación):', reporte.emparejadas[0].si_sdr)  # inf

resultado = agregar_conjunto([
    EntradaConjunto('Track00001', [referencia], [estimacion_perfecta], es_directorio_omitido=False),
    EntradaConjunto('Track00002', [], [], es_directorio_omitido=False),
])
print('Mediana:', resultado.mediana)
print('Exclusiones:', resultado.exclusiones)
print('Distribución:', resultado.distribucion_referencias_por_tema)
"
```

Resultado esperado: `SI-SDR (referencia == estimación): inf`; `Track00002`
aparece en `Exclusiones` con motivo `sin_guitarra_referencia` y no en la
mediana; `Distribución` es `{1: 1}` (un solo tema evaluado, con una
referencia).
