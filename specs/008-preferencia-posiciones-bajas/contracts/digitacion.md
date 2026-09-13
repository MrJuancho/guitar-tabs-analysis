# Contrato: preferencia por posiciones bajas en el modelo de coste

Extiende `contracts/digitacion.md` de la Feature 007 -- un campo nuevo
en la firma de `ModeloCoste`, una extensión de comportamiento en
`asignar_secuencia` (postcondición 4 de esa feature, sin cambiar su
firma), y una función nueva en `digitacion.orquestador`. Ningún
contrato ya cerrado de la Feature 007 se elimina.

## `analytics.metrica_digitacion.ModeloCoste` (campo nuevo)

```python
@dataclass(frozen=True)
class ModeloCoste:
    ...  # campos de la Feature 007, sin cambio
    peso_altura_traste: float
```

### Postcondiciones (nuevas, sobre el campo)

1. `MODELO_COSTE_POR_DEFECTO.peso_altura_traste == 0.0` (research.md
   #6) -- MUST reproducir exactamente el comportamiento de la Feature
   007 mientras no se pase un valor distinto explícitamente.

## `analytics.metrica_digitacion.asignar_secuencia` (comportamiento extendido, misma firma)

```python
def asignar_secuencia(notas: list[NotaEntrada], modelo: ModeloCoste) -> Digitacion:
    ...
```

Firma sin cambio respecto de la Feature 007. Postcondición 4 de
`contracts/digitacion.md` de esa feature se extiende:

4'. El coste de nodo de cada combinación candidata `combo` MUST ser
    `estiramiento(combo) + modelo.peso_altura_traste · altura(combo)`,
    con `altura(combo) = Σ p.traste para cada p en combo` (research.md
    #2 de esta feature) -- MUST NOT afectar el cálculo de
    `costeArista` (desplazamiento/cruce de cuerdas, sin cambio) ni el
    criterio de validez de una combinación (estiramiento máximo,
    cuerdas distintas, tolerancia de tono -- FR-004 de esta feature:
    agregar este componente al coste MUST NOT alterar qué posiciones se
    consideran válidas, solo cuánto cuestan las ya válidas).

## `digitacion.orquestador.ejecutar_barrida_peso_altura` (función nueva)

```python
def ejecutar_barrida_peso_altura(
    valores_candidatos: list[float],
    grabaciones: list[str],
    root_dir: Path,
    modelo_base: ModeloCoste = MODELO_COSTE_POR_DEFECTO,
) -> ResultadoBarrida:
    ...
```

Función nueva en `digitacion/orquestador.py` (mismo paquete que
`ejecutar_digitacion`, misma exclusión del contrato `layers` de
import-linter). Reutiliza `ingestion.guitarset.leer_grabacion_con_posicion_real`
y `analytics.metrica_digitacion.{asignar_secuencia, evaluar_coincidencia,
agregar_conjunto}` -- MUST NOT invocar `ejecutar_digitacion` en un
bucle (research.md #4: eso releería GuitarSet una vez por valor
candidato, cuando la lectura es el costo dominante y no depende del
peso).

### Precondiciones

Mismas que `ejecutar_digitacion` (contracts/digitacion.md de la Feature
007): `root_dir` es la raíz de una distribución de GuitarSet ya
presente en disco; `grabaciones` MUST ser la lista de las 288 medibles
(`construir_lista_grabaciones("medibles", ...)`) -- MUST NOT invocarse
con ninguna de las 72 reservadas (FR-011 de esta feature, Principio VI,
mismo criterio que `ejecutar_digitacion`: esta función no lo verifica
por sí misma, es responsabilidad de quien construye `grabaciones`).

### Postcondiciones

1. **Lectura única.** MUST leer las notas y la posición real de cada
   `grabacion_id` de `grabaciones` EXACTAMENTE UNA VEZ, sin importar
   cuántos valores tenga `valores_candidatos` (research.md #4) -- un
   fallo de lectura (`GrabacionNoExisteError`) excluye esa grabación de
   TODOS los puntos de la barrida por igual (mismo motivo, mismo patrón
   que `ExclusionDigitacion` de `ejecutar_digitacion`), nunca solo de
   algunos.
2. **Un punto por valor candidato.** Para cada valor de
   `valores_candidatos`, en el mismo orden, MUST construir un
   `ModeloCoste` idéntico a `modelo_base` salvo `peso_altura_traste`
   fijado a ese valor, MUST correr `asignar_secuencia` +
   `evaluar_coincidencia` sobre los datos ya leídos (postcondición 1)
   para cada grabación no excluida, MUST agregar con
   `agregar_conjunto` (mismo criterio que `ArtefactoDigitacion` de la
   Feature 007: suma de conteos, nunca promedio de fracciones), y MUST
   producir un `PuntoBarrida` con ese valor y su `ResultadoCoincidencia`.
3. **Curva completa, nunca solo el máximo (FR-008).** MUST devolver un
   único `ResultadoBarrida` con un `PuntoBarrida` por cada valor de
   `valores_candidatos`, en el mismo orden -- MUST NOT omitir ningún
   punto, sin importar su `fraccion_coincidencia` relativa a los demás.
4. **Sin elección del valor final (FR-007/FR-009).** MUST NOT comparar
   ningún `PuntoBarrida` contra ningún otro para decidir un "ganador",
   ni contra el presupuesto vigente (`0.55`) -- termina en devolver la
   curva completa, igual que `ejecutar_digitacion` termina en devolver
   el artefacto sin evaluar ningún umbral (FR-015 de la Feature 007).
5. **Punto de control (research.md #6).** El `PuntoBarrida` cuyo
   `peso_altura_traste == 0.0` MUST tener una `fraccion_coincidencia`
   idéntica a la de una corrida de `ejecutar_digitacion` con
   `MODELO_COSTE_POR_DEFECTO` sobre las mismas `grabaciones` -- si
   difiere, es evidencia de un defecto de integración del nuevo
   componente (Edge Case de `spec.md`).
