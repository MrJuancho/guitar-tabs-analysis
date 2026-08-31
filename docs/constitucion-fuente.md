# Constitución del proyecto

> Versión 2. Tres decisiones cerradas respecto del borrador anterior (fuentes, conjunto de evaluación, licencias). Quedan dos abiertas, con criterio explícito de cuándo se cierran.

## Alcance

Sistema que, a partir de una grabación, aísla la pista de guitarra y posteriormente estima las notas para producir tablaturas ejecutables por una mano humana.

**Hito 1 (este):** aislar la pista de guitarra y medir qué tan bien se hace. **Hito 2 (fuera de alcance):** transcripción a notas y digitación.

Uso personal y educativo. No hay objetivo comercial, no se distribuyen stems ni grabaciones, no se expone como servicio.

---

## I. El hito 1 es una línea base medida, no un modelo entrenado

El entregable es un pipeline reproducible que toma una mezcla, produce un stem de guitarra usando un modelo preentrenado, y reporta una métrica sobre un conjunto de evaluación fijo.

Entrenar o afinar queda fuera. Sin línea base medida, cualquier mejora posterior es una anécdota. Con ella, afinar se vuelve una decisión con evidencia — y si la línea base alcanza para el uso previsto, no hay que entrenar nada.

*Criterio de terminado:* un comando reproducible que, dado el conjunto de evaluación, emite la métrica agregada y por pista, y una compuerta que falla si cae por debajo del presupuesto declarado.

## II. Caminos descartados, con su razón

Un camino descartado sin razón escrita se vuelve a intentar.

**Aprendizaje reforzado.** La separación de fuentes es regresión supervisada: existe la mezcla, existe el objetivo, y la pérdida se define sobre la diferencia. El aprendizaje reforzado exigiría fabricar una señal de recompensa que aquí no existe naturalmente, a cambio de nada.

**Filtrado por banda de frecuencia.** Los fundamentales de la guitarra en afinación estándar caen aproximadamente entre 82 Hz y 1.3 kHz, con armónicos hasta ~15 kHz — el mismo rango que voz, piano y bajo. Los espectros se solapan; no existe una banda que aislar. El timbre vive en la distribución de energía entre armónicos y en el transitorio de ataque, información que un filtro lineal en frecuencia no puede explotar.

## III. La guitarra no es un stem estándar

Los conjuntos y benchmarks establecidos separan cuatro fuentes: voz, batería, bajo y *otros*. La guitarra vive dentro de *otros*. Consecuencias asumidas:

- Hay mucho menos audio etiquetado con guitarra aislada que con voz o batería.
- Las cifras publicadas de separación **no son comparables** con las de este proyecto y no se citan como si lo fueran.
- Una separación mediocre puede seguir siendo útil para el hito 2, donde importa la detección de tonos, no la fidelidad perceptual.

## IV. Fuentes de audio admisibles

**Regla permanente: una fuente sin licencia identificada no es admisible.** No se usa "mientras se aclara". El criterio de cierre es el archivo de licencia de la distribución, no la solicitud de citación — pedir que te citen no otorga derechos de uso.

Toda fuente debe ser CC BY 4.0 (*Creative Commons Attribution 4.0 International*) o más permisiva. Las citas requeridas viven en un archivo de atribuciones del repositorio.

**Hito 1 — Slakh2100** (CC BY 4.0). Audio sintetizado desde MIDI, con stems por instrumento perfectamente aislados y alineados. Se elige sobre las alternativas por licencia sin cláusula no comercial, tamaño manejable, y divisiones oficiales de entrenamiento/validación/prueba.

**Hito 2 — GuitarSet y EGFxSet** (ambos CC BY 4.0). Anotación de cuerda y traste, que es la etiqueta que la tablatura necesita. GuitarSet cubre guitarra acústica; EGFxSet, eléctrica con efectos. Se declaran ahora, aunque no se usen todavía, para que el formato de datos del hito 1 no haya que rehacerlo.

**El repositorio no contiene audio.** Ni fixtures de grabaciones, ni casos de prueba. El audio vive fuera, referenciado por manifiesto con sumas de verificación; el pipeline falla con mensaje claro si no lo encuentra, nunca en silencio.

## V. Qué cuenta como "la guitarra"

Toda pista etiquetada como guitarra en los metadatos de la fuente, sin distinguir entre limpia, distorsionada o acústica.

**Excepción verificada:** el bajo eléctrico pertenece a una familia distinta en la clasificación General MIDI, pero debe confirmarse contra los metadatos reales de cada tema que no quedó agrupado con las guitarras. Incluirlo contaminaría la referencia de forma invisible para la métrica.

**Múltiples pistas de guitarra:** cada una es una referencia separada, no se suman. La evaluación mide contra la mejor coincidencia de cada referencia, y **reporta el número de pistas de guitarra del tema junto con la métrica**. Se espera que el rendimiento caiga con la polifonía; eso es un resultado, no un defecto a esconder.

> Alternativa registrada para el futuro: restringir el hito 1 a temas con una sola pista de guitarra y admitir múltiples después. Descartada por ahora para no ocultar el caso difícil.

## VI. Evaluación cuantitativa y verificación cualitativa son distintas

**Cuantitativa — Slakh2100.** Se usa la división oficial de prueba como conjunto reservado: no la inventamos, es comparable con trabajo publicado, y elimina la discusión de cómo partir sin fugas de datos. Ningún agente la inspecciona ni ajusta nada contra ella; se usa una vez, al cerrar el hito. El bloqueo es mecánico: la ruta se protege con el mismo hook `PreToolUse` que cubre `tests/holdout/`.

**Cualitativa — música propia.** Un conjunto pequeño de grabaciones personales, fuera del repositorio, **sin referencia aislada y por lo tanto sin métrica posible**. Sirve para detectar fallos groseros (salida en silencio, voz colada, artefactos) que un buen número en Slakh no revelaría. No produce cifras y no se publica.

**Limitación declarada:** Slakh es audio sintetizado desde MIDI; el modelo preentrenado se entrenó con audio real. La métrica del hito 1 mide separación sobre guitarras sintetizadas y **no se extrapola a grabaciones reales**. Cualquier afirmación sobre el rendimiento en canciones reales requiere evidencia que este hito no produce.

## VII. La métrica y su presupuesto

Se declara una métrica principal, un presupuesto numérico, y la evidencia que justifica ese número.

**El umbral no se recalibra para forzar un pase.** Un FALLA documentado con su razón es un resultado; un umbral movido después de ver el resultado no es nada.

> `ABIERTO` — Métrica principal. Candidata: SI-SDR (*Scale-Invariant Signal-to-Distortion Ratio*), estándar en separación de fuentes e invariante a escala, lo que evita premiar o castigar diferencias de ganancia. *Criterio de cierre:* se fija en `/plan`, cuando se sepa qué reporta la herramienta elegida.
>
> `ABIERTO` — Presupuesto. *Criterio de cierre:* se fija después de la primera medición sobre el conjunto de desarrollo, por debajo del percentil observado y con el margen justificado por escrito. Fijarlo antes sería exactamente el vicio que esta sección prohíbe.

## VIII. Determinismo

> `ABIERTO` — *Criterio de cierre:* se decide en `/plan`, cuando estén elegidas la biblioteca y el hardware. Dos opciones defendibles:
>
> **(a) Reproducibilidad exacta.** Semillas fijas más algoritmos deterministas forzados. Cuesta velocidad y no toda operación tiene implementación determinista.
>
> **(b) Tolerancia numérica declarada.** Las aserciones comparan con una tolerancia explícita en vez de igualdad exacta.
>
> Lo no defendible es no decidirlo y descubrir la respuesta cuando un test falle de forma intermitente en integración continua.

## IX. Datos derivados: se generan, no se leen

Todo artefacto derivado — manifiestos, tablas de resultados, catálogos — se produce con un script versionado y se verifica con aserciones sobre propiedades: cantidad esperada, casos frontera conocidos, invariantes. Nunca leyendo el contenido completo.

Corolario del arnés: si no se lee el código que produce el agente porque las compuertas lo verifican, tampoco se lee el dato que produce.

En audio esto es más fuerte que en datos tabulares: un espectrograma no se inspecciona en contexto. Se verifica por forma, rango, energía y casos conocidos.

## X. Tamaño de slice y presupuesto de ventana

Una tarea que contiene más de un test rojo no es una tarea.

El presupuesto real no es el reloj sino los tokens de la ventana. Una sesión cierra cuando el trabajo comprometido está en verde y el handoff escrito, no cuando se agota el presupuesto.

## XI. Frontera con [AGENTS.md](http://AGENTS.md)

[`AGENTS.md`](http://AGENTS.md) gobierna **cómo se verifica** el trabajo: compuertas, ciclo de slice, subagentes, disciplina de contexto. Es transversal y llega por actualización del template.

Esta constitución gobierna **qué se construye y bajo qué principios de producto**: alcance, caminos descartados, fuentes, métricas, política de datos.

Los dos documentos no se solapan. Si la plantilla de Spec Kit pide principios de calidad o de proceso de desarrollo, la respuesta correcta es **referenciar** [`AGENTS.md`](http://AGENTS.md) **como fuente única**, no reescribirlos aquí. Duplicar garantiza que en seis meses nadie sepa cuál manda.