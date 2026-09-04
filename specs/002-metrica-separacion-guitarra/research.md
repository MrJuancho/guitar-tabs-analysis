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

## 5. Los infinitos: uno es exacto por cálculo, el otro es una convención explícita

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

**Corrección (2026-09-04): una estimación totalmente silenciosa NO da
`-∞` por cálculo — es NaN, y no hay forma de arreglarlo tomando un
límite.** La primera versión de este punto afirmaba, sin verificarlo,
que una estimación de energía nula producía `-∞` exacto (`‖s_target‖² /
0`). Es falso: si `ŝ = 0`, entonces `α = ⟨ŝ,s⟩/⟨s,s⟩ = 0` exacto, así
que `s_target = 0 · s = 0` también — **el numerador se anula junto con
el denominador**, no solo el denominador. El resultado real es `0/0`,
NaN, verificado numéricamente:

```
s = 1000·sin(2π·220·t), n=1000; ŝ = vector cero
⟨ŝ,s⟩ = 0.0  ⟨s,s⟩ = 500000.99...  α = 0.0
‖s_target‖² = 0.0   ‖e_noise‖² = 0.0   →  SI-SDR = nan
```

Y no es un caso "casi bien" que un límite arregle: el límite de SI-SDR
cuando `ŝ → 0` a lo largo de una dirección fija `w` (`ŝ_ε = ε·w`)
**depende de `w`**, no converge a un único valor — por la misma
invarianza a escala de este punto, `si_sdr(s, ε·w) = si_sdr(s, w)` para
todo `ε > 0`, así que el límite es `si_sdr(s, w)`: da `+∞` si `w = s`,
da `-∞` si `w` es ortogonal a `s`, y cualquier valor intermedio para
otras direcciones. `ŝ = 0` es una singularidad genuina, no una
discontinuidad evitable — no existe un valor "natural" que asignarle.

**Decisión de producto (no matemática), confirmada 2026-09-04**: `si_sdr()`
detecta `⟨ŝ,ŝ⟩ == 0` (energía nula de la estimación, mismo chequeo sin
epsilon que research.md #4 usa para la referencia) y **define** el
resultado como `-∞` — por convención, no por cálculo, exactamente el
mismo patrón que FR-008 ya usa para el sentinel de una referencia sin
pareja: "no hay señal reconstruida" es un caso degenerado con
significado de producto claro (el separador no produjo nada para ese
candidato), aunque el límite matemático general no exista. La referencia
con energía nula (research.md #4) sigue siendo un caso distinto: ahí ni
siquiera se puede formar la proyección, así que `si_sdr()` lanza
`ReferenciaEnergiaNulaError` en vez de devolver un valor — la estimación
silenciosa sí tiene una proyección bien definida (`s_target = 0`
exacto), solo que el cociente resultante es indeterminado, y ahí es
donde entra la convención.

**Caso ambos-cero: referencia y estimación con energía nula a la vez —
decisión explícita, no accidente de orden.** `si_sdr()` calcula las dos
energías (`⟨s,s⟩` y `⟨ŝ,ŝ⟩`) antes de ramificar, y comprueba primero la
de la referencia: si ambas son cero, **gana `ReferenciaEnergiaNulaError`**,
nunca el `-∞` por convención. Razón: la energía nula de la referencia es
la falla más fundamental — sin ella no existe ninguna proyección posible,
independientemente de qué tan mala sea la estimación (research.md #4). La
convención `-∞` de la estimación silenciosa presupone que la referencia
sí tiene una proyección bien definida sobre la cual medir el residuo; si
la referencia también es silencio, esa premisa no se cumple, así que no
hay ninguna base para aplicar la convención. El código hace esta
prioridad visible con un comentario en el punto de la rama, no solo con
el orden de los `if` — un lector no debería tener que inferir la
decisión de qué comprobación quedó escrita primero.

La implementación usa `numpy.errstate(divide="ignore", invalid="ignore")`
alrededor de la división final: los `RuntimeWarning` de NumPy por
división entre cero (el caso `+∞` de bit-idéntico) son la señal esperada
de ese resultado, no un error a silenciar con una corrección artificial
(p. ej. sumar un epsilon al denominador, que rompería su exactitud). El
caso de estimación silenciosa nunca llega a esa división: se resuelve
antes, por la comprobación explícita de energía.

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

**Alternatives considered**:
- Sumar un epsilon fijo al denominador (patrón común en implementaciones
  de referencia de otras métricas) — rechazado porque rompe la exactitud
  de SC-001 sin ninguna ganancia: los dos casos genuinamente
  indeterminados de esta fórmula (energía nula de la referencia,
  research.md #4; energía nula de la estimación, arriba) ya se resuelven
  de forma explícita antes de llegar a la división final.
- Para la estimación silenciosa, levantar una excepción simétrica a
  `ReferenciaEnergiaNulaError` (p. ej. `EstimacionEnergiaNulaError`) —
  considerada y **rechazada** (decisión de producto, no de esta sección):
  obligaría a `emparejar_tema()` (T017) a decidir qué hacer con una
  estimación candidata silenciosa durante el emparejamiento en vez de
  simplemente asignarle el peor valor posible y dejar que la asignación
  óptima la evite naturalmente si hay mejores candidatas — más superficie
  de diseño de la que este punto necesita resolver.

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

## 11. Estimación silenciosa asignada: reclasificar después de emparejar, no excluir antes (FR-016)

**Decision**: `emparejar_tema()` NO excluye las estimaciones de energía
nula de la matriz de costos antes de correr la asignación óptima —
participan como candidatas normales, exactamente como cualquier otra
estimación (con su valor `-∞` por convención, research.md #5). Después de
obtener la asignación de `linear_sum_assignment`, cada par asignado se
revisa: si la estimación de ese par tiene energía nula, la referencia se
mueve a `sin_pareja` con `motivo == "estimacion_silenciosa"` en vez de
agregarse a `emparejadas` (FR-016).

**Rationale**: Excluir las estimaciones silenciosas *antes* de construir
la matriz de costos parecía la alternativa simétrica a cómo se tratan las
referencias de energía nula (research.md #4) — pero rompe en cuanto hay
una mezcla de estimaciones útiles e inútiles: si sobran referencias
respecto a las estimaciones *útiles*, ¿qué referencia específica "pierde"
por culpa de una estimación silenciosa en vez de por escasez genuina? No
hay una respuesta no arbitraria sin re-implementar parte de la lógica de
asignación a mano. Dejar que el optimizador considere las estimaciones
silenciosas como candidatas (son, después de todo, la peor opción posible
por construcción — research.md #5) resuelve esto gratis: `linear_sum_assignment`
ya elige la mejor asignación global, así que solo asigna una estimación
silenciosa a una referencia cuando no hay ninguna opción mejor disponible
para *ella* — exactamente la semántica que se quiere. Reclasificar
después es una operación de una sola pasada sobre el resultado ya
decidido, sin tocar la optimización.

Este reclasificado es puramente de reporte: numéricamente, `-∞` en
`emparejadas` (si no se reclasificara) y `-∞` como sentinel de `sin_pareja`
(FR-008) ya coinciden — la mediana agregada (FR-007) no cambia. La
ganancia es exclusivamente diagnóstica (FR-016, SC-009): un lector del
reporte puede distinguir "no había estimación" de "había una estimación,
y era silencio" sin tener que inspeccionar manualmente qué tan grande es
cada `si_sdr` negativo.

**Alternatives considered**:
- Excluir las estimaciones silenciosas de la matriz de costos antes de
  optimizar (rechazada — el problema de "a quién culpar" de arriba, sin
  una respuesta principiada).
- No reclasificar; dejar la referencia en `emparejadas` con `si_sdr == -inf`
  (rechazada — es lo que hacía la implementación antes de este punto, y
  es exactamente lo que `spec.md` FR-016 ahora prohíbe explícitamente:
  un valor en `emparejadas` debe representar una medición real, y `-∞`
  por convención no lo es).

## 12. SC-004 solo es demostrable para un tema completamente sin emparejar, no para "algún" tema con referencias sin pareja

**Decision**: La garantía de SC-004/AS US2.5 ("incluir el tema nunca
mejora la mediana") se acota a un tema donde **ninguna** referencia
quedó emparejada — el caso que originó la garantía ("el separador no
produjo nada para ese tema"). No se generaliza a cualquier tema que
tenga *alguna* referencia sin pareja.

**Verificado, no solo razonado** (2026-09-05): un tema con 4 referencias
— 1 sin pareja, 3 emparejadas con `si_sdr = 1000` (excelente) — agregado
a un conjunto base de mediana 5 sube la mediana a 1000:

```
pool_sin = [5]                              -> mediana = 5
pool_con = [5, -inf, 1000, 1000, 1000]      -> mediana = 1000  (1000 > 5)
```

La versión general de SC-004 (tal como estaba redactada antes de esta
sesión) es matemáticamente falsa — un contraejemplo de cinco números
basta para refutarla, no hacía falta un caso de dataset real.

**Por qué la versión acotada SÍ es demostrable**: insertar en un pool
solo copias del valor mínimo posible (`-∞`, el sentinel de FR-008) nunca
puede subir la mediana — es un hecho de estadística de orden: `-∞` es
`≤` cualquier valor ya presente, así que cada copia insertada se ubica
en la posición 0 del pool ordenado, empujando todo lo demás hacia
índices mayores; el valor en la posición de la mediana resultante es o
bien un `-∞` recién insertado, o bien un valor que ya estaba en el pool
original en una posición igual o anterior a la mediana original — nunca
puede ser mayor que la mediana original. Un tema con **todas** sus
referencias sin pareja contribuye *solo* copias de `-∞` al pool, así que
cae exactamente en este caso. Un tema mixto no: sus referencias
emparejadas pueden contribuir cualquier valor, incluido uno mayor que
todo lo que ya había, rompiendo la garantía (contraejemplo arriba).

**Rationale**: La garantía general "sonaba" cierta porque la motivación
original (`spec.md`, descripción de la feature) es exactamente el caso
acotado: "un tema donde el separador no produjo nada". Al generalizar la
Acceptance Scenario/Success Criterion a "un tema con referencias sin
pareja" (sin exigir que sean *todas*) durante la redacción del spec,
nadie volvió a verificar si la propiedad seguía siendo cierta en el caso
general — no lo es. Acotarla a la propiedad real y demostrable es mejor
que dejar una garantía falsa en el documento que gobierna qué debe
probar `T024`.

**Alternatives considered**: Mantener la garantía general y documentar
que es "esperada empíricamente" (los fallos de un separador real suelen
estar correlacionados dentro de un mismo tema, así que el contraejemplo
adversarial es improbable en la práctica) — rechazada explícitamente: es
exactamente el patrón que este proyecto ya evita en otros puntos (FR-008,
research.md #4/#5) de dejar una propiedad numérica sin verificar
descansando en una intuición sobre "cómo se ve normalmente el dato real"
en vez de en una prueba. Una propiedad de un `Success Criteria` debe ser
cierta siempre, no "cierta salvo que alguien construya el contraejemplo".

## Sources

- Le Roux, J., Wisdom, S., Erdogan, H., & Hershey, J. R. (2019). *SDR –
  Half-baked or Well Done?* ICASSP 2019 — definición de SI-SDR usada en
  research.md #1.
- [`scipy.optimize.linear_sum_assignment` — SciPy documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html) — soporte de matrices de costo rectangulares (research.md #2).
- `specs/001-lectura-tema-slakh2100/research.md` #1 — confirma que
  Slakh2100 se lee sin reescalar (`dtype` nativo), base de research.md #3
  de este documento.
