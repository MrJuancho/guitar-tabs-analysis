# Quickstart: Separación de guitarra con modelo preentrenado

Valida `separar_guitarra` (ver [contracts/separacion.md](./contracts/separacion.md))
contra el spec. A diferencia de la Feature 002, esta feature sí tiene una
dependencia externa pesada (`torch`/`demucs`, research.md #7) — por eso
hay dos secciones separadas: lo que corre siempre, rápido y sin red, y lo
que ejercita el modelo real.

## Lo que corre en `just gauntlet` (rápido, sin `torch` cargado)

```bash
uv sync
just gauntlet
```

Todo esto usa un `SeparadorFalso` de prueba (`tests/fixtures/`), nunca
`DemucsSeparador` — en milisegundos, sin red:

- Frecuencia de muestreo de la mezcla igual a la del `Separador` →
  `TransformacionDeclarada(tipo="frecuencia_muestreo", aplicada=False)`
  presente en el resultado (Acceptance Scenario 1, User Story 1).
- Frecuencia de muestreo distinta → `aplicada=True`, y la entrada que
  recibe el `Separador` ya está remuestreada (Acceptance Scenario 2).
- Mezcla mono contra un `Separador` que espera 2 canales → el canal se
  duplica en la entrada, y la salida de `"guitar"` (2 canales) se colapsa a
  mono promediando ambos canales en el resultado, con las dos
  transformaciones declaradas por separado (Acceptance Scenario 3).
- El `Separador` falso no incluye la clave `"guitar"` en su salida →
  `resultado.estimaciones == []`, sin sintetizar nada (User Story 3,
  escenario 1; FR-009).
- El `Separador` falso sí incluye `"guitar"` pero con energía nula →
  `resultado.estimaciones` tiene una `Estimacion` real (no se omite ni se
  reclasifica aquí — User Story 3, escenario 2; FR-010).
- El `Separador` falso levanta una excepción arbitraria al separar →
  `SeparacionFallidaError` con el `tema_id` y la causa encadenada, sin
  reintento (Acceptance Scenario 6, User Story 1; FR-014).
- Dos llamadas a `separar_guitarra` con el mismo `Separador` falso
  determinista → mismas estimaciones dentro de tolerancia (Acceptance
  Scenario 7; FR-015) — con un falso, esto es trivialmente exacto; el caso
  no trivial (variación real de `torch`) lo cubre la sección de abajo.
- `resultado.modelo` es exactamente `separador.modelo_declarado`, sin
  transformación.

## Lo que corre con el modelo real (lento, red la primera vez)

Un único test, marcado `@pytest.mark.modelo_real`
(`tests/integration/test_demucs_separador_integracion.py`, research.md
#7), se salta automáticamente si no hay red o si la carga del modelo
falla — nunca bloquea `just gauntlet`. Para correrlo explícitamente:

```bash
uv run pytest -m modelo_real -v
```

Qué valida, sobre un clip sintético de 1-2 segundos (no un tema completo):

- `DemucsSeparador` carga `htdemucs_6s` con `device="cpu"`.
- `separador.samplerate == 44100` y `separador.audio_channels == 2`,
  leídos de la propiedad real del modelo, no hardcodeados (research.md
  #4).
- `separar_guitarra` de punta a punta con este separador real produce un
  `ResultadoSeparacionTema` con una `Estimacion` (o ninguna, si el clip no
  tiene nada reconocible como guitarra) sin lanzar ninguna excepción no
  controlada.
- Correr la separación dos veces sobre el mismo clip produce estimaciones
  cuyas muestras coinciden dentro de tolerancia numérica (FR-015,
  research.md #6) — esta es la verificación real de determinismo, no la
  trivial de la sección de arriba.

## Ejecución manual de un ejemplo end-to-end (sin modelo real)

```bash
uv run python -c "
import numpy as np
from guitar_tabs_analysis.ingestion.slakh2100 import PistaAudio
from guitar_tabs_analysis.analytics.metrica_separacion import Estimacion
from guitar_tabs_analysis.separacion.separador import (
    ModeloDeclarado, separar_guitarra,
)

sr = 44100
t = np.linspace(0, 1, sr, endpoint=False)
mezcla = PistaAudio((np.sin(2 * np.pi * 220 * t) * 1000).astype(np.int16), sr)

class SeparadorDeEjemplo:
    modelo_declarado = ModeloDeclarado(
        nombre='Demucs', variante='htdemucs_6s',
        firma='5c90dfd2', checksum_sha256_prefijo='d2a1745f0744',
        licencia_pesos='ver docs/ATRIBUCIONES.md',
    )
    samplerate = sr
    audio_channels = 2

    def separar(self, muestras):
        # Simula una salida de guitarra idéntica a la entrada (2 canales).
        return {'guitar': np.stack([muestras[0], muestras[0]])}

resultado = separar_guitarra('Track00001', mezcla, SeparadorDeEjemplo())
print('Estimaciones:', [e.identificador for e in resultado.estimaciones])
print('Transformaciones:', resultado.transformaciones)
print('Modelo:', resultado.modelo)
"
```

Resultado esperado (verificado ejecutando el ejemplo tal cual, T023):
`Estimaciones: ['guitar']`; `Transformaciones` incluye **tres** entradas
— frecuencia de muestreo de entrada (`aplicada=False`, ambas a 44100 Hz),
canales de entrada (`aplicada=True`, 1 → 2, duplicado), y canales de
salida (`aplicada=True`, 2 → 1, promedio) — no cuatro, como decía una
versión anterior de este documento nunca ejecutada contra la
implementación real.

## Verificación de la declaración de licencia (User Story 2, sin ejecutar nada)

```bash
test -f docs/ATRIBUCIONES.md && grep -q "htdemucs_6s" docs/ATRIBUCIONES.md && echo OK
```

Confirma que la declaración del modelo (FR-002/FR-004) es un archivo real
del repositorio, consultable sin correr ninguna inferencia — la
Independent Test de User Story 2.
