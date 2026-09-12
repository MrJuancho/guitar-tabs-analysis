# ADR-0002: Primera prueba manual de extremo a extremo con una canción real -- cinco hallazgos

## Estado

Aceptado -- hallazgos registrados con su evidencia. Ninguna corrección se
propone ni se implementa en este documento; qué hacer con cada uno es una
decisión posterior, con su propia medición.

## Contexto

Primera vez que el pipeline completo (separar → detectar → digitar,
hitos 1/2/3) corre encadenado a mano sobre audio que no proviene de
Slakh2100 ni de GuitarSet: ~30 segundos de una canción comercial cuya
tablatura real el usuario -- guitarrista -- conoce y toca, usada como
control independiente de cualquier dataset de este proyecto.

Los tres hitos se midieron hasta ahora exclusivamente contra sus propios
datasets (Slakh2100 sintetizado; GuitarSet, grabado con pastilla
hexafónica). Esta prueba es la primera verificación cualitativa contra
una fuente de audio y una técnica de guitarra genuinamente distintas de
las que cualquier métrica de este proyecto ya midió -- exactamente el
tipo de verificación que el Principio VI de la constitución reserva para
"detectar fallos groseros... que un buen número en [el dataset] no
revelaría", nunca productora de una cifra publicable.

## Hallazgos

### 1. La separación funcionó mejor de lo esperado

El usuario juzgó la guitarra aislada como muy limpia, con poco ruido
residual -- mejor de lo que la cifra de referencia del hito 1 (mediana
`−5.55 dB` de SI-SDR sobre el conjunto evaluable completo de Slakh2100
sintetizado, Principio VII de la constitución) hacía prever.

**Causa.** Evidencia a favor de una limitación ya declarada, no un
hallazgo nuevo: la constitución (Principio VI, "Limitación declarada")
ya advierte que la métrica del hito 1 mide separación sobre guitarras
sintetizadas desde MIDI y **no se extrapola a grabaciones reales**. En
este caso la extrapolación resultó **pesimista** -- la separación real
funcionó por encima de lo que la cifra sintetizada predecía --, dirección
opuesta a la que la limitación declarada advertía explícitamente como
riesgo (que la cifra sintetizada resultara optimista). Ambas direcciones
son consistentes con la misma limitación: la cifra sintetizada, medida
en cualquiera de las dos direcciones, no predice el caso real.

### 2. La conversión a mono descarta información

`separar_guitarra` (`src/guitar_tabs_analysis/separacion/separador.py`)
espera una mezcla de entrada mono, porque el audio de Slakh2100 -- la
única fuente contra la que este código corrió hasta ahora -- siempre lo
es (`PistaAudio.muestras` de `ingestion/slakh2100.py` es 1-D por
construcción). Antes de esta prueba, ninguna mezcla real de dos canales
había llegado nunca a este código -- alimentarlo exigió promediar a mano
la mezcla estéreo de la canción real a un solo canal antes de llamar a
`separar_guitarra`.

**Causa.** En una mezcla comercial real la guitarra suele estar
panoramizada (paneada a un lado, no centrada) -- la diferencia entre
canales izquierdo y derecho es información real sobre qué instrumento
está dónde en la imagen estéreo, señal que un separador podría
aprovechar y que el promedio a mono destruye antes de que el modelo la
vea. Es una limitación de diseño heredada por completo del formato del
dataset de entrenamiento/evaluación (Slakh2100 es mono), nunca una
decisión informada sobre qué hacer con estéreo real -- la pregunta
simplemente no se había planteado hasta que un estéreo real llegó al
código por primera vez.

### 3. `separar_guitarra` no valida la forma del arreglo de entrada

Un arreglo estéreo con los ejes transpuestos -- `(muestras, canales)` en
vez de `(canales, muestras)`, que es la convención que
`separador.audio_channels` y el resto de `separar_guitarra` asumen --
provocó un intento de reservar **~26 TB** de memoria (`np.tile`/el propio
modelo interpretando la dimensión de muestras, mucho más grande que la
de canales, como si fuera la dimensión a replicar) en vez de un mensaje
de error claro sobre la forma inesperada.

**Causa.** La convención de ejes `(canales, muestras)` ya está declarada
implícitamente en el código (es la que `PistaAudio`/`separar_guitarra`
asumen en todo momento), así que comprobar que la dimensión más chica de
un arreglo 2D de entrada es la de canales -- antes de operar sobre él --
es una verificación trivial de agregar. Nunca se agregó porque la ruta de
estéreo real **nunca se había ejercitado antes de esta prueba**: Slakh2100
es mono, así que ningún test ni ninguna corrida anterior había pasado
jamás un arreglo 2D por esta función, transpuesto o no.

### 4. El modelo de coste de digitación carece de un término de preferencia por posiciones bajas

Sobre el fragmento de la canción real, la digitación que produjo la
Feature 007 usa trastes **11-18** repartidos sobre **cinco cuerdas**,
donde la tablatura real de la canción (la que el usuario efectivamente
toca) usa trastes **1-6** sobre **una sola cuerda**.

**Causa.** El modelo de coste declarado (`spec.md`/`research.md` de la
Feature 007) penaliza el MOVIMIENTO de la mano -- desplazamiento en
trastes y cruce de cuerdas entre instantes consecutivos -- pero no tiene
ningún término que penalice la ALTURA en sí de una posición sobre el
mástil. Quedarse arriba del mástil, lejos de donde un guitarrista real
tocaría, puede ser perfectamente óptimo según el propio criterio del
modelo si desde ahí los desplazamientos subsiguientes resultan baratos --
el modelo no tiene ninguna razón declarada para preferir volver abajo.

Esto es consistente con la asimetría ya medida con evidencia real en
`specs/007-digitacion-restriccion-mano/research.md` #15 (T025): sobre los
desacuerdos de la corrida real contra GuitarSet, `Δcuerda` se mantiene
chico y acotado mientras `Δtraste` está mucho más disperso -- el modelo
evita cruzar cuerdas más de lo que lo hace un guitarrista real, y se
desplaza por el mástil más de lo que lo hace un guitarrista real. Ese
hallazgo ya estaba registrado como hipótesis con evidencia, sin
recalibrar (Principio VII de la constitución, v1.10.0); esta prueba
manual aporta un caso concreto, observable a simple vista, de la misma
asimetría de fondo -- no un defecto nuevo y distinto.

**Es el hallazgo más accionable de los cinco** -- a diferencia de los
otros cuatro (limitaciones de dataset o de modelos externos), este es un
término ausente en un modelo de coste que el propio proyecto declara y
controla por completo.

### 5. El detector falla en dos formas que la medición del hito 2 no podía revelar

- **Notas en el tempo correcto con el tono equivocado**, en un patrón
  compatible con confusión de octava o de armónico. GuitarSet -- la única
  fuente contra la que el hito 2 se midió -- se grabó con pastilla
  hexafónica (una señal eléctrica por cuerda, capturada por separado),
  condición en la que esa ambigüedad de octava/armónico casi no aparece:
  la fuente de evaluación del hito 2 no puede exhibir un modo de fallo que
  depende de justamente la información que esa fuente preserva sin
  ambigüedad por construcción.
- **Hammer-ons no detectados.** Sin un nuevo ataque (transitorio de
  cuerda pulsada), el detector ve un solo evento de nota donde la
  ejecución real produjo dos. Limitación conocida de Basic Pitch
  (entrenado sobre música general, no sobre técnica de guitarra
  específicamente) -- no un defecto de la integración de este proyecto.

**Consecuencia metodológica, mismo patrón que la limitación ya declarada
sobre SI-SDR (Principio VI/VII).** El F1 de `0.7394` medido sobre
GuitarSet (Feature 006, Principio VII) era una cifra correcta y no
predecía ninguno de los dos modos de fallo -- exactamente el mismo tipo
de brecha que la constitución ya documenta para SI-SDR ("esta cifra no
predice si la separación es suficiente para transcribir"), ahora
verificada de nuevo un hito más adelante en el pipeline: una métrica
correcta sobre su propio conjunto de evaluación no garantiza nada sobre
un modo de fallo que ese conjunto no puede exhibir.

## Hallazgo metodológico

**Ninguno de los cinco hallazgos era detectable por las métricas de los
tres hitos.** SI-SDR (hito 1), F1 (hito 2) y `fraccion_coincidencia`
(hito 3) midieron, cada una, exactamente lo que estaban diseñadas para
medir, sobre exactamente los conjuntos de evaluación que este proyecto ya
tiene -- y ninguna de las tres podía, por construcción, exhibir una
mezcla estéreo real, una técnica de hammer-on, o una preferencia humana
por posiciones bajas del mástil, porque ninguno de esos conjuntos de
evaluación (Slakh2100 sintetizado, GuitarSet hexafónico) contiene esa
condición.

Los cinco hallazgos los encontró un guitarrista, escuchando la guitarra
separada y leyendo la tablatura resultante contra una canción que ya
sabe tocar -- verificación cualitativa, sin ninguna métrica de por medio,
exactamente la que el Principio VI de la constitución ya contempla y
reserva para esto ("detectar fallos groseros... que un buen número...
no revelaría"). Este ADR es esa verificación funcionando como está
diseñada: encontrar lo que ninguna cifra podía, no una cifra alternativa
más severa.

## Cuándo se revisa

No hay ninguna fecha ni corrección comprometida en este documento --
pedido explícito de la sesión que lo generó: este ADR documenta lo
observado, no decide qué hacer con ello. Se revisa cuando una sesión
futura decida abordar alguno de los cinco hallazgos puntualmente, con su
propia medición de que el cambio propuesto mejora lo que dice mejorar
-- nunca "eventualmente", y nunca como efecto colateral de otro trabajo.
