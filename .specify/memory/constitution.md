<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0
- Fuente: docs/constitucion-fuente.md v2 (contenido acordado y ya revisado,
  trasladado a la estructura de plantilla sin reescritura de sustancia).
  Reemplaza el borrador conversacional usado para v1.0.0.
- Bump MINOR: 3 decisiones antes abiertas (DECIDIR en v1.0.0) se cierran con
  contenido real, y se añade un principio nuevo. Ninguna decisión ya tomada
  se contradice o se elimina -- no aplica MAJOR.

- Principios modificados (título viejo → título nuevo, mapeo v1.0.0 → v1.1.0):
  I.    (sin cambio)
  II.   (sin cambio)
  III.  (sin cambio)
  IV.   "El repositorio no contiene audio con derechos" (con DECIDIR de
        fuentes) → "Fuentes de audio admisibles" -- DECIDIR cerrado:
        Slakh2100 (hito 1), GuitarSet + EGFxSet (hito 2, declarados ahora),
        regla permanente de licencia CC BY 4.0 o más permisiva.
  V.    "Conjunto de evaluación intocable" (con DECIDIR de qué subconjunto)
        → reubicado y ampliado como VI. "Evaluación cuantitativa y
        verificación cualitativa son distintas" -- DECIDIR cerrado: split
        oficial de prueba de Slakh2100 como hold-out cuantitativo, más
        verificación cualitativa nueva sobre música propia (sin métrica).
  --    (nuevo) V. "Qué cuenta como 'la guitarra'" -- no existía en v1.0.0.
  VI.   "La métrica y su presupuesto" → VII. (mismo título, misma posición
        relativa tras la inserción de V). Sigue ABIERTO -- NO se rellenó,
        por regla explícita de esta sesión. Ahora con criterio de cierre
        explícito: se fija en `/plan`.
  VII.  "Determinismo" → VIII. (mismo título). Sigue ABIERTO -- NO se
        rellenó. Criterio de cierre explícito: se decide en `/plan`.
  VIII. "Datos derivados: se generan, no se leen" → IX. (renumerado, sin
        cambio de contenido).
  IX.   "Tamaño de slice y presupuesto de ventana" → X. (renumerado, sin
        cambio de contenido).
  SECTION_3 "Frontera con el arnés" → "Frontera con AGENTS.md" (contenido
        ampliado por la fuente v2 -- sigue siendo referencia pura, nunca
        duplicación, por regla 2 de esta sesión y sección XI de la fuente).

- Secciones añadidas: ninguna nueva a nivel de plantilla (Alcance y
  Frontera ya existían desde v1.0.0); dentro de Core Principles se añade
  el principio V.
- Secciones eliminadas: ninguna.

- DECIDIR/ABIERTO NO rellenados en este comando (copiados tal cual, con su
  propio criterio de cierre, según regla 1 de esta sesión):
  - VII -- Métrica principal (candidata SI-SDR). Cierra en `/plan`.
  - VII -- Presupuesto numérico. Cierra después de la primera medición
    sobre el conjunto de desarrollo, nunca antes.
  - VIII -- Política de determinismo. Cierra en `/plan`.
  Corrección respecto a v1.0.0: la Governance anterior decía que estos
  abiertos bloqueaban `/speckit-specify`. La fuente v2 dice explícitamente
  que su criterio de cierre es `/plan`, no `/specify` -- la regla de
  Governance se corrigió para no contradecir el criterio de cierre real
  que la fuente declara.

- Limpieza de formato (no de contenido): los enlaces automáticos
  `[AGENTS.md](http://AGENTS.md)` de la fuente (artefacto de renderizado,
  no una URL real) se normalizaron a la referencia en código `` `AGENTS.md` ``
  usada en el resto del repositorio.

- Ver el resumen de esta sesión (fuera de este archivo) para: qué pidió la
  plantilla que la fuente no cubre, y qué contenido de la fuente no
  encontró lugar en la estructura.
-->

# Guitar Tabs Analysis Constitution

## Core Principles

### I. El hito 1 es una línea base medida, no un modelo entrenado

El entregable es un pipeline reproducible que toma una mezcla, produce un
stem de guitarra usando un modelo preentrenado, y reporta una métrica sobre
un conjunto de evaluación fijo.

Entrenar o afinar queda fuera. Sin línea base medida, cualquier mejora
posterior es una anécdota. Con ella, afinar se vuelve una decisión con
evidencia -- y si la línea base alcanza para el uso previsto, no hay que
entrenar nada.

*Criterio de terminado:* un comando reproducible que, dado el conjunto de
evaluación, emite la métrica agregada y por pista, y una compuerta que falla
si cae por debajo del presupuesto declarado.

### II. Caminos descartados, con su razón

Un camino descartado sin razón escrita se vuelve a intentar.

**Aprendizaje reforzado.** La separación de fuentes es regresión supervisada:
existe la mezcla, existe el objetivo, y la pérdida se define sobre la
diferencia. El aprendizaje reforzado exigiría fabricar una señal de
recompensa que aquí no existe naturalmente, a cambio de nada.

**Filtrado por banda de frecuencia.** Los fundamentales de la guitarra en
afinación estándar caen aproximadamente entre 82 Hz y 1.3 kHz, con armónicos
hasta ~15 kHz -- el mismo rango que voz, piano y bajo. Los espectros se
solapan; no existe una banda que aislar. El timbre vive en la distribución de
energía entre armónicos y en el transitorio de ataque, información que un
filtro lineal en frecuencia no puede explotar.

### III. La guitarra no es un stem estándar

Los conjuntos y benchmarks establecidos separan cuatro fuentes: voz, batería,
bajo y *otros*. La guitarra vive dentro de *otros*. Consecuencias asumidas:

- Hay mucho menos audio etiquetado con guitarra aislada que con voz o
  batería.
- Las cifras publicadas de separación **no son comparables** con las de este
  proyecto y no se citan como si lo fueran.
- Una separación mediocre puede seguir siendo útil para el hito 2, donde
  importa la detección de tonos, no la fidelidad perceptual.

### IV. Fuentes de audio admisibles

**Regla permanente: una fuente sin licencia identificada no es admisible.**
No se usa "mientras se aclara". El criterio de cierre es el archivo de
licencia de la distribución, no la solicitud de citación -- pedir que te
citen no otorga derechos de uso.

Toda fuente debe ser CC BY 4.0 (*Creative Commons Attribution 4.0
International*) o más permisiva. Las citas requeridas viven en un archivo de
atribuciones del repositorio.

**Hito 1 -- Slakh2100** (CC BY 4.0). Audio sintetizado desde MIDI, con stems
por instrumento perfectamente aislados y alineados. Se elige sobre las
alternativas por licencia sin cláusula no comercial, tamaño manejable, y
divisiones oficiales de entrenamiento/validación/prueba.

**Hito 2 -- GuitarSet y EGFxSet** (ambos CC BY 4.0). Anotación de cuerda y
traste, que es la etiqueta que la tablatura necesita. GuitarSet cubre
guitarra acústica; EGFxSet, eléctrica con efectos. Se declaran ahora, aunque
no se usen todavía, para que el formato de datos del hito 1 no haya que
rehacerlo.

**El repositorio no contiene audio.** Ni fixtures de grabaciones, ni casos de
prueba. El audio vive fuera, referenciado por manifiesto con sumas de
verificación; el pipeline falla con mensaje claro si no lo encuentra, nunca
en silencio.

### V. Qué cuenta como "la guitarra"

Toda pista etiquetada como guitarra en los metadatos de la fuente, sin
distinguir entre limpia, distorsionada o acústica.

**Excepción verificada:** el bajo eléctrico pertenece a una familia distinta
en la clasificación General MIDI, pero debe confirmarse contra los metadatos
reales de cada tema que no quedó agrupado con las guitarras. Incluirlo
contaminaría la referencia de forma invisible para la métrica.

**Múltiples pistas de guitarra:** cada una es una referencia separada, no se
suman. La evaluación mide contra la mejor coincidencia de cada referencia, y
**reporta el número de pistas de guitarra del tema junto con la métrica**. Se
espera que el rendimiento caiga con la polifonía; eso es un resultado, no un
defecto a esconder.

> Alternativa registrada para el futuro: restringir el hito 1 a temas con una
> sola pista de guitarra y admitir múltiples después. Descartada por ahora
> para no ocultar el caso difícil.

### VI. Evaluación cuantitativa y verificación cualitativa son distintas

**Cuantitativa -- Slakh2100.** Se usa la división oficial de prueba como
conjunto reservado: no la inventamos, es comparable con trabajo publicado, y
elimina la discusión de cómo partir sin fugas de datos. Ningún agente la
inspecciona ni ajusta nada contra ella; se usa una vez, al cerrar el hito. El
bloqueo es mecánico: la ruta se protege con el mismo hook `PreToolUse` que
cubre `tests/holdout/`.

**Cualitativa -- música propia.** Un conjunto pequeño de grabaciones
personales, fuera del repositorio, **sin referencia aislada y por lo tanto
sin métrica posible**. Sirve para detectar fallos groseros (salida en
silencio, voz colada, artefactos) que un buen número en Slakh no revelaría.
No produce cifras y no se publica.

**Limitación declarada:** Slakh es audio sintetizado desde MIDI; el modelo
preentrenado se entrenó con audio real. La métrica del hito 1 mide separación
sobre guitarras sintetizadas y **no se extrapola a grabaciones reales**.
Cualquier afirmación sobre el rendimiento en canciones reales requiere
evidencia que este hito no produce.

### VII. La métrica y su presupuesto

Se declara una métrica principal, un presupuesto numérico, y la evidencia que
justifica ese número.

**El umbral no se recalibra para forzar un pase.** Un FALLA documentado con
su razón es un resultado; un umbral movido después de ver el resultado no es
nada.

> `ABIERTO` -- Métrica principal. Candidata: SI-SDR (*Scale-Invariant
> Signal-to-Distortion Ratio*), estándar en separación de fuentes e
> invariante a escala, lo que evita premiar o castigar diferencias de
> ganancia. *Criterio de cierre:* se fija en `/plan`, cuando se sepa qué
> reporta la herramienta elegida.
>
> `ABIERTO` -- Presupuesto. *Criterio de cierre:* se fija después de la
> primera medición sobre el conjunto de desarrollo, por debajo del percentil
> observado y con el margen justificado por escrito. Fijarlo antes sería
> exactamente el vicio que esta sección prohíbe.

### VIII. Determinismo

> `ABIERTO` -- *Criterio de cierre:* se decide en `/plan`, cuando estén
> elegidas la biblioteca y el hardware. Dos opciones defendibles:
>
> **(a) Reproducibilidad exacta.** Semillas fijas más algoritmos
> deterministas forzados. Cuesta velocidad y no toda operación tiene
> implementación determinista.
>
> **(b) Tolerancia numérica declarada.** Las aserciones comparan con una
> tolerancia explícita en vez de igualdad exacta.
>
> Lo no defendible es no decidirlo y descubrir la respuesta cuando un test
> falle de forma intermitente en integración continua.

### IX. Datos derivados: se generan, no se leen

Todo artefacto derivado -- manifiestos, tablas de resultados, catálogos -- se
produce con un script versionado y se verifica con aserciones sobre
propiedades: cantidad esperada, casos frontera conocidos, invariantes. Nunca
leyendo el contenido completo.

Corolario del arnés: si no se lee el código que produce el agente porque las
compuertas lo verifican, tampoco se lee el dato que produce.

En audio esto es más fuerte que en datos tabulares: un espectrograma no se
inspecciona en contexto. Se verifica por forma, rango, energía y casos
conocidos.

### X. Tamaño de slice y presupuesto de ventana

Una tarea que contiene más de un test rojo no es una tarea.

El presupuesto real no es el reloj sino los tokens de la ventana. Una sesión
cierra cuando el trabajo comprometido está en verde y el handoff escrito, no
cuando se agota el presupuesto.

## Alcance

Sistema que, a partir de una grabación, aísla la pista de guitarra y
posteriormente estima las notas para producir tablaturas ejecutables por una
mano humana.

**Hito 1 (este):** aislar la pista de guitarra y medir qué tan bien se hace.
**Hito 2 (fuera de alcance):** transcripción a notas y digitación.

Uso personal y educativo. No hay objetivo comercial, no se distribuyen stems
ni grabaciones, no se expone como servicio.

## Frontera con AGENTS.md

`AGENTS.md` gobierna **cómo se verifica** el trabajo: compuertas, ciclo de
slice, subagentes, disciplina de contexto. Es transversal y llega por
actualización del template.

Esta constitución gobierna **qué se construye y bajo qué principios de
producto**: alcance, caminos descartados, fuentes, métricas, política de
datos.

Los dos documentos no se solapan. Si la plantilla de Spec Kit pide principios
de calidad o de proceso de desarrollo, la respuesta correcta es
**referenciar** `AGENTS.md` **como fuente única**, no reescribirlos aquí.
Duplicar garantiza que en seis meses nadie sepa cuál manda.

## Governance

Esta constitución tiene precedencia sobre cualquier otra práctica del
proyecto para las decisiones de producto que gobierna (alcance, métricas,
política de datos); `AGENTS.md` tiene la misma precedencia para las
decisiones de proceso (ver "Frontera con AGENTS.md" arriba).

**Enmiendas.** Se hacen corriendo `/speckit-constitution` de nuevo, nunca
editando el archivo a mano -- así el Sync Impact Report queda registrado.
Versionado semántico sobre el documento mismo: MAJOR para eliminar o
redefinir un principio de forma incompatible con decisiones ya tomadas
(specs/plans existentes), MINOR para añadir un principio o cerrar un
`ABIERTO` con contenido real, PATCH para aclaraciones sin cambio de sentido.
`Ratified` es la fecha de la adopción inicial (v1.0.0) y no cambia en
enmiendas futuras; `Last Amended` sí.

**Revisión de cumplimiento.** `/speckit-plan` carga este archivo y llena su
propia sección "Constitution Check" contra estos principios, antes y después
del diseño -- no hace falta un paso manual adicional aquí.

**Los `ABIERTO` no se rellenan por adelantado.** Cada uno de los tres
puntos que siguen tiene su propio criterio de cierre, declarado en el
principio correspondiente -- no se completan antes de que ese criterio se
cumpla, y no se completan aquí como parte de un futuro `/speckit-constitution`
"para no dejar cabos sueltos": eso es exactamente el vicio que VII prohíbe
para el presupuesto, y se aplica igual a los otros dos.

- [ ] VII -- Métrica principal (candidata SI-SDR). Cierra en `/plan`.
- [ ] VII -- Presupuesto numérico. Cierra después de la primera medición
      sobre el conjunto de desarrollo, nunca antes.
- [ ] VIII -- Política de determinismo. Cierra en `/plan`.

**Version**: 1.1.0 | **Ratified**: 2026-08-30 | **Last Amended**: 2026-08-31
