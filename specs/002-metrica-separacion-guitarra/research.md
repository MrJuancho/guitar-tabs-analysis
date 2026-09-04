# Research: Métrica de separación de guitarra

**Input**: [spec.md](./spec.md) | **Date**: 2026-09-04

Cada decisión resuelve un `NEEDS CLARIFICATION` del Technical Context en
`plan.md`, uno de los dos `ABIERTO` de la constitución que le corresponden
a esta feature (Principios VII y VIII), o un supuesto técnico que el spec
deja fuera de su alcance por diseño (ver `spec.md#Assumptions`).

## 1. Fórmula de SI-SDR (cierra Principio VII de la constitución)

**Decision**: SI-SDR según Le Roux et al., 2019 ("SDR – Half-baked or Well
Done?"). Para una referencia `s` y una estimación `ŝ`, ambas en `float64`:

```
α          = <ŝ, s> / <s, s>
s_target   = α · s
e_noise    = ŝ − s_target
SI-SDR(s, ŝ) = 10 · log10( ‖s_target‖² / ‖e_noise‖² )
```

**Rationale**: Es la definición estándar de la literatura de separación de
fuentes citada por la constitución ("estándar en separación de fuentes e
invariante a escala"). El paso de proyección (`α`) es exactamente lo que
hace la métrica invariante a escala: no reescala la señal de entrada, sino
que encuentra la mejor aproximación escalada de `s` dentro de `ŝ` antes de
medir el residuo. Esto cierra formalmente el `ABIERTO` del Principio VII en
su mitad de "métrica principal".

**Alternatives considered**:
- SDR clásico (Vincent et al., 2006, BSS Eval): no es invariante a escala
  — penaliza o premia diferencias de ganancia entre estimación y
  referencia, justo lo que la constitución pide evitar explícitamente.
- SI-SNR: mismo nombre histórico para la misma fórmula en parte de la
  literatura de separación de voz; se usa el nombre "SI-SDR" en todo el
  spec y el código para no introducir un sinónimo sin necesidad
  (Terminología y Consistencia).

## 2. Biblioteca para el emparejamiento óptimo (FR-002/FR-003)

**Decision**: `scipy.optimize.linear_sum_assignment` sobre una matriz de
costos `C[i,j] = -SI-SDR(referencia_i, estimación_j)` (negativo porque la
función minimiza costo y FR-002 pide maximizar la aproximación).

**Rationale**: Resuelve el problema de asignación óptima (algoritmo
húngaro/Jonker-Volgenant) y **soporta matrices rectangulares de forma
nativa** — exactamente el caso de FR-003 (menos estimaciones que
referencias), sin necesitar rellenar la matriz a mano ni escribir
combinatoria propia. Es la práctica estándar para evaluación invariante a
permutación en separación de fuentes (el mismo enfoque que usan `mir_eval`
y `museval` para el "mejor permutación" entre fuentes estimadas y de
referencia). Se añade `scipy` como dependencia nueva del proyecto.

**Alternatives considered**:
- Fuerza bruta (`itertools.permutations`): correcta para conteos pequeños
  (Slakh2100 rara vez supera 3–4 guitarras por tema), pero de complejidad
  factorial y sin soporte directo para matrices rectangulares (habría que
  rellenar la matriz con filas/columnas ficticias a mano) — complejidad
  innecesaria frente a una función ya resuelta y probada.
- Reimplementar el algoritmo húngaro a mano: reinventa código ya
  ampliamente probado en `scipy`, sin ninguna ventaja para este dominio.
- Asignación voraz (cada referencia toma su mejor estimación disponible en
  orden arbitrario): puede quedar atrapada en un óptimo local peor que la
  asignación global — ya descartada explícitamente en `spec.md#Assumptions`
  a favor de la asignación óptima.

## 3. Aritmética: cast a `float64`, sin reescalado de amplitud

**Decision**: Antes de cualquier operación de SI-SDR, las muestras de la
referencia y de la estimación se convierten a `float64` (`.astype(np.float64)`).
No se aplica ningún reescalado, normalización, ni conversión de rango.

**Rationale**: Slakh2100 (vía Feature 001) devuelve muestras en el `dtype`
nativo del archivo (p. ej. `int16`), sin reescalar (FR-005 de Feature 001).
Elevar al cuadrado y sumar sobre un array `int16` puede desbordar o perder
precisión; `float64` lo evita sin alterar el resultado matemático. No hace
falta llevar la referencia y la estimación a la misma escala de amplitud
antes de calcular SI-SDR — la invarianza a escala **es la fórmula misma**
(el paso `α` de research.md #1 ya absorbe cualquier diferencia de
ganancia), no una normalización previa. Añadir una normalización adicional
sería redundante y, peor, ocultaría un bug si el paso de proyección
tuviera un error — la propiedad de invarianza a escala del sistema debe
verse en el resultado de la fórmula, no enmascararse antes de que la
fórmula corra.

**Alternatives considered**: Normalizar ambas señales a `[-1.0, 1.0]` o a
energía unitaria antes de calcular SI-SDR (rechazada — innecesaria dado
que la fórmula ya es invariante a escala, y violaría el principio de "sin
transformación" ya establecido para el audio en Feature 001).

## 4. Energía nula de la referencia (FR-006) — definición exacta

**Decision**: Una referencia tiene "energía nula" si y solo si
`Σ (muestras.astype(np.float64))² == 0` exactamente — sin umbral ni
epsilon arbitrario. Se verifica antes de calcular `α` (research.md #1),
para cualquier candidato de estimación, no una vez por par.

**Rationale**: "Silencio digital" (el término exacto que usa `spec.md`)
significa, literalmente, que todas las muestras son cero — no "muy
silencioso". Introducir un umbral (p. ej. "energía menor a X dB") sería
exactamente el tipo de constante numérica arbitraria que la Feature 002 ya
rechazó explícitamente para el sentinel de FR-008 (ver Clarifications de
`spec.md`); la misma razón aplica aquí. Con energía exactamente cero, `α`
es matemáticamente `0/0` (indefinido) — se detecta con esta comprobación
antes de intentar la división, nunca capturando la excepción/advertencia
que produciría calcularla de todos modos.

**Alternatives considered**: Umbral relativo (p. ej. energía menor a
`1e-10`) — rechazado por ser una constante arbitraria sin justificación
de dominio, exactamente lo que `spec.md#Assumptions` ya evitó para FR-008.

## 5. Los infinitos son resultados exactos, no casos especiales que evitar

**Decision**: Cuando una estimación es bit-idéntica a la referencia
(`e_noise` es el vector cero exacto), `SI-SDR = +∞` — resultado exacto de
la fórmula (división por cero de un numerador positivo), no una
aproximación numérica grande.

**La razón exacta, no la intuitiva.** No es que el error de redondeo
acumulado en `⟨ŝ,s⟩` y `⟨s,s⟩` sea "suficientemente pequeño" — a 10⁷
muestras esa intuición es falsa en general y no debe usarse como
justificación. La razón real es más estricta: cuando `ŝ` es una copia
bit-idéntica de `s`, `⟨ŝ,s⟩` y `⟨s,s⟩` son **la misma reducción de punto
flotante sobre los mismos valores**, así que producen el mismo resultado
redondeado — sea cual sea ese redondeo, es idéntico en numerador y
denominador. Y la división de IEEE754 garantiza `x / x == 1.0` para
cualquier `x` finito y distinto de cero, **sin importar cuánto error de
redondeo tenga `x` en sí** — la garantía es sobre la operación de
división, no sobre la exactitud de `x`. Por eso `α == 1.0` bit a bit, y
`s_target = 1.0 · s == s` exacto (multiplicar por `1.0` en IEEE754 es
siempre exacto), y `e_noise = s − s = 0` bit a bit.

**Verificado, no solo razonado** (2026-09-04, mismo entorno que CI —
NumPy sobre OpenBLAS 0.3.34, `DYNAMIC_ARCH`): se corrió exactamente el
cálculo de `si_sdr()` (dos llamadas separadas a `np.dot`, no una
reutilizada — el peor caso realista, no el mejor caso artificial) con
ruido gaussiano en `float32` y `float64`, para 1000, 10,000,000 y
10,652,672 muestras (la longitud de pista real de Slakh2100 vista en
Feature 001). En los seis casos: `⟨ŝ,s⟩ == ⟨s,s⟩` exacto, `α == 1.0`
exacto, `e_noise` es el vector cero exacto, `SI-SDR == inf`. El tamaño de
la reducción no rompió la igualdad porque nunca dependió de que el
redondeo fuera pequeño.

Del mismo modo, una estimación totalmente silenciosa (todo ceros) frente
a una referencia con energía produce `SI-SDR = -∞` exacto (`‖s_target‖² /
0`) — un resultado matemáticamente válido y distinto del sentinel `−∞` de
FR-008 (que se *asigna* a una referencia sin pareja, no se *calcula*),
aunque numéricamente coincidan.

La implementación usa `numpy.errstate(divide="ignore", invalid="ignore")`
alrededor de esta división: los `RuntimeWarning` de NumPy por división
entre cero son la señal esperada de este resultado, no un error a
silenciar con una corrección artificial (p. ej. sumar un epsilon al
denominador, que rompería la exactitud de +∞/−∞ que este mismo punto
describe).

**Rationale**: Evita el error más común al implementar SI-SDR — añadir un
epsilon de "estabilidad numérica" al denominador "por las dudas". Ese
epsilon convertiría el `+∞` exacto de SC-001 en un número grande pero
finito, y el criterio de aceptación dejaría de poder verificarse con
igualdad exacta, degradando la verificación de respuesta conocida a una
tolerancia arbitraria — justo lo que FR-011 no pide.

**Límite de esta garantía (no ampliar sin volver a verificar).** La
igualdad exacta depende de que `np.dot` sea determinista entre dos
llamadas con los mismos operandos — cierto para BLAS estándar (la
reducción no se aleatoriza entre llamadas idénticas), y confirmado
empíricamente arriba sobre el backend real del proyecto. No está
verificado bajo un backend BLAS distinto ni bajo paralelismo con
partición de hilos no determinista entre llamadas; si el proyecto cambia
de backend numérico, este punto debe volver a correrse, no asumirse.

**Alternatives considered**: Sumar un epsilon fijo al denominador (patrón
común en implementaciones de referencia de otras métricas) — rechazado
porque rompe la exactitud de SC-001 sin ninguna ganancia: esta feature ya
resuelve la única división por cero genuinamente indefinida (energía nula
de la referencia, research.md #4) de forma explícita antes de llegar aquí.

## 6. Determinismo (cierra Principio VIII de la constitución)

**Decision**: Opción (b) — tolerancia numérica declarada, aplicada
selectivamente:

- Los **valores de SI-SDR calculados** (no los exactos por construcción)
  se comparan en tests con tolerancia (`math.isclose`/`pytest.approx`),
  nunca con igualdad bit a bit.
- Los **dos valores exactos por construcción** — `+∞` (FR-011) y el
  sentinel `−∞` (FR-008) — se comparan con igualdad exacta, porque no son
  el resultado de una acumulación de punto flotante sujeta a orden de
  operaciones: son identidades matemáticas (`e_noise` idénticamente cero,
  o un valor asignado por definición, no calculado).
- Todo lo **discreto** (conteos, qué referencia quedó sin pareja y por
  qué, qué par se emparejó, la distribución de referencias por tema) se
  compara con igualdad exacta — son decisiones combinatorias, no
  resultados de aritmética de punto flotante.

**Rationale**: Esta feature no tiene ninguna fuente de aleatoriedad (sin
semillas, sin inferencia de modelo, sin muestreo) — el único riesgo de
no-determinismo es el orden de acumulación de punto flotante en sumas
(`Σ`) que, en teoría, podría diferir en el último bit entre builds
distintos de BLAS/NumPy en máquinas distintas. El criterio de cierre del
`ABIERTO` ("cuando estén elegidas la biblioteca y el hardware") ya se
cumple: la biblioteca es NumPy/SciPy sobre el mismo entorno Linux/CI que
usa el resto del proyecto. Elegir tolerancia en vez de exigir
reproducibilidad bit a bit evita tests frágiles ante una variación de
build de BLAS que no representa ningún error real del sistema — el mismo
motivo por el que la constitución ofrece la opción (b) en primer lugar.

**Alternatives considered**: Opción (a), reproducibilidad exacta forzada
(semillas fijas, algoritmos deterministas forzados) — rechazada porque no
hay ninguna semilla que fijar (no hay aleatoriedad) y forzar igualdad bit
a bit sobre sumas de punto flotante sería frágil ante builds de BLAS sin
aportar ninguna garantía adicional real.

## 7. Compatibilidad de forma entre referencia y estimación candidata

**Decision**: Antes de calcular SI-SDR sobre un par `(referencia,
estimación)`, se verifica que ambas tengan la misma longitud (número de
muestras) y la misma frecuencia de muestreo. Si no coinciden, el sistema
levanta `EstimacionIncompatibleError` con el tema, la referencia y la
estimación afectadas — nunca intenta recortar, rellenar, o remuestrear
para forzar la comparación.

**Rationale**: `spec.md#Assumptions` fija que esta feature recibe
colecciones ya cargadas y no valida de dónde vienen las estimaciones — pero
no dice que deba asumir ciegamente que son compatibles. Una estimación de
longitud o frecuencia de muestreo distinta a la referencia con la que se
compara no tiene una comparación SI-SDR bien definida (los vectores no
son directamente comparables muestra a muestra). Fallar explícitamente,
en vez de recortar/rellenar/remuestrear en silencio, es el mismo criterio
que Feature 001 ya adoptó para la mezcla y sus guitarras (FR-011 de esa
feature) — coherencia de dominio, no una regla nueva inventada aquí.

**Alternatives considered**: Excluir en silencio el par incompatible de la
matriz de costos (tratarlo como si no existiera esa estimación candidata)
— rechazada porque enmascara un problema real de datos (un separador que
devuelve audio de longitud equivocada) detrás de un resultado que
simplemente parece "peor emparejamiento", sin ninguna señal de que algo
está mal formado.

## 8. Persistencia del reporte

**Decision**: No aplica — esta feature no persiste nada en disco. Devuelve
estructuras de datos en memoria (`ReporteTema`, `ResultadoAgregado`, ver
`data-model.md`).

**Rationale**: `spec.md` describe qué se "reporta", no dónde se guarda; no
hay ningún requisito de persistencia. Si una feature futura de compuerta
de calidad necesita leer este resultado como artefacto persistido, seguirá
el mismo patrón que ya usa `quality/gates.py` (lee un Parquet ya
persistido, nunca importa `analytics` directamente — el contrato de
import-linter "quality es transversal: no depende de analytics" lo
prohíbe) — decisión de esa feature futura, no de esta.

## 9. Representación de la distribución de referencias por tema (FR-015)

**Decision**: `dict[int, int]` — clave es el número de referencias de un
tema, valor es cuántos temas del conjunto evaluado tienen exactamente ese
número. No un histograma con binning.

**Rationale**: El dominio (número de pistas de guitarra por tema) es un
entero pequeño y discreto, no una magnitud continua — un `dict` exacto es
más simple y más preciso que cualquier esquema de bins, y es trivialmente
verificable (`sum(distribucion.values()) == num_temas_evaluados`, la
invariante que cubre `tests/property/`).

## 10. Motivo de exclusión cuando ambos criterios aplican

**Decision**: Si un tema pertenece al directorio `omitted` **y** además no
tiene ninguna pista de guitarra de referencia, se reporta con motivo
`"directorio_omitido"` (FR-010), no con ambos motivos ni con
`"sin_guitarra_referencia"`. El chequeo de directorio se evalúa primero.

**Rationale**: Son dos condiciones independientes por diseño (`spec.md`
las declara como dos exclusiones separadas con conteos separados), pero
`Exclusion` (data-model.md) modela un motivo por tema, no una lista — un
tema excluido aparece exactamente una vez en el reporte de exclusiones
(SC-005: "el 100% de los temas excluidos... aparecen contados", no
"contados dos veces"). El directorio `omitted` es una propiedad del origen
del tema (dónde vive en el dataset), independiente de cuántas guitarras de
referencia tenga — evaluarlo primero evita que la ausencia de referencias
(una condición sobre el *contenido* del tema) oscurezca el motivo real
(una decisión de los autores del dataset sobre el *tema completo*).

**Alternatives considered**: Reportar ambos motivos cuando ambos aplican
(rechazada — `spec.md` pide un conteo por motivo, no una taxonomía de
motivos combinados; SC-005 se lee más naturalmente como una partición).

## Sources

- Le Roux, J., Wisdom, S., Erdogan, H., & Hershey, J. R. (2019). *SDR –
  Half-baked or Well Done?* ICASSP 2019 — definición de SI-SDR usada en
  research.md #1.
- [`scipy.optimize.linear_sum_assignment` — SciPy documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html) — soporte de matrices de costo rectangulares (research.md #2).
- `specs/001-lectura-tema-slakh2100/research.md` #1 — confirma que
  Slakh2100 se lee sin reescalar (`dtype` nativo), base de research.md #3
  de este documento.
