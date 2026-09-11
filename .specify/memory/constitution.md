<!--
Sync Impact Report
- Version change: 1.8.1 → 1.9.0
- Fuente: primera medición real del hito 2 (Feature 006, detección de
  notas sobre guitarra limpia -- `mediciones/deteccion_medibles.json`,
  288 grabaciones medibles de GuitarSet, Basic Pitch icassp_2022 firma
  `3db297d5`). Cierra el último `ABIERTO` que quedaba en el documento.
- Bump MINOR: cierra un `ABIERTO` con contenido real y verificado -- no
  elimina ni contradice ninguna decisión ya tomada (la reserva de VI,
  cerrada en v1.8.0, no cambia; nada del hito 1 se toca, pedido explícito
  de esta sesión), así que no aplica MAJOR; no es solo una aclaración de
  redacción -- agrega la métrica principal (F1 con precisión/
  exhaustividad obligatorias por separado, desglosadas global/mono/poli)
  y el presupuesto numérico (`0.70`) que no existían -- así que no es
  PATCH.

- Principios modificados en v1.9.0 (contenido, no título ni posición):
  VII.  "La métrica y su presupuesto" -- el bloque "Hito 2 -- detección
        de notas. ABIERTO." se reemplaza por contenido cerrado: métrica
        principal (F1, `mir_eval.transcription`, convención MIREX Note
        Tracking, ya fijada en `spec.md`/`plan.md` de la Feature 006),
        alcance de la medición (288/360 grabaciones medibles, Basic
        Pitch icassp_2022 firma `3db297d5`, backend `tflite`, Apache-2.0,
        tolerancias 50 cents/50 ms, cero exclusiones), evidencia completa
        (TP/referencia/estimadas global + monofónico + polifónico, con
        el invariante `TP(mono) + TP(poli) = TP(global)` verificado), la
        asimetría precisión/exhaustividad reportada por partición como
        parte obligatoria del resultado (no un adorno), el presupuesto
        (`0.70` sobre el F1 global, con su margen argumentado), y una
        subsección nueva de historia metodológica: dos defectos del
        mismo tipo (agrupar/clasificar antes de emparejar) encontrados y
        corregidos antes de fijar el presupuesto (FR-013, FR-014 de la
        Feature 006), registrados como evidencia sobre el método, no
        solo sobre el modelo.

- Secciones añadidas: ninguna a nivel de encabezado (todo el contenido
  nuevo vive dentro de Principio VII, ya existente, como la instancia del
  hito 2). Secciones eliminadas: ninguna. Ningún contenido del hito 1
  (Principios I-VII sección "Hito 1", VIII) se modifica -- pedido
  explícito de esta sesión.

- Governance: el checkbox "VII -- Hito 2: métrica principal y
  presupuesto numérico" pasa de `[ ]` a `[x]`, con la cifra resumida en
  la propia línea. Con este cierre, **no queda ningún `ABIERTO`
  pendiente en el documento** -- los cinco originales (tres del hito 1,
  dos del hito 2) están cerrados.

- Sesión anterior (v1.8.0 → v1.8.1), preservada por referencia histórica:
- Version change: 1.8.0 → 1.8.1
- Fuente: `/speckit-implement` de la Feature 006 (T028-T035, Fase 7 --
  CLI y filtro de la reserva) decidió el mecanismo real de la reserva de
  GuitarSet: cálculo en vivo desde la semilla, sin manifiesto
  persistido -- distinto de lo que v1.8.0 había previsto
  (`tests/holdout/guitarset_reservado_hito2.json` + hook de protección).
- Bump PATCH: corrige CÓMO se implementa un mecanismo ya decidido -- el
  número (72/360) y la semilla (`20260908`) no cambian, tampoco el
  propósito de la reserva; es una aclaración de mecanismo, no una nueva
  decisión ni la eliminación de una ya tomada.

- Principios modificados en v1.8.1 (contenido, no título ni posición):
  VI.   "Evaluación cuantitativa y verificación cualitativa son
        distintas" -- el bloque "Mecanismo" del apartado "Hito 2 --
        porción reservada de GuitarSet" se reescribe: sin manifiesto en
        `tests/holdout/`, la reserva se deriva de
        `random.Random(20260908).sample(...)` en cada invocación de
        `construir_lista_grabaciones`, con `modo="medibles"`/
        `"reservado"` complementarios por construcción.

- Secciones añadidas: ninguna. Secciones eliminadas: ninguna. Governance:
  sin cambios en ningún checkbox.

- Sesión anterior (v1.7.0 → v1.8.0), preservada por referencia histórica:
- Version change: 1.7.0 → 1.8.0
- Fuente: pedido explícito de esta sesión, cerrando documentación de la
  Feature 006 (detección de notas sobre guitarra limpia) -- tamaño y
  semilla de la porción reservada de GuitarSet, criterio de cierre que
  v1.7.0 dejó explícito para el `ABIERTO` de Principio VI.
- Bump MINOR: se cierra un `ABIERTO` con contenido real (72 grabaciones,
  semilla `20260908`) -- no se elimina ni contradice ninguna decisión ya
  tomada (el split `test` de Slakh, la generalización de v1.7.0, todo
  permanece sin cambio), así que no aplica MAJOR; no es solo una
  aclaración de redacción -- agrega un número y una semilla que no
  existían -- así que no es PATCH.

- Principios modificados en v1.8.0 (contenido, no título ni posición):
  VI.   "Evaluación cuantitativa y verificación cualitativa son
        distintas" -- el bloque "Hito 2 -- porción reservada de
        GuitarSet" deja de estar `ABIERTO`: 72 grabaciones (20% de 360),
        semilla `20260908`, con la evidencia completa (por qué 20% y no
        15%, por qué esa semilla, el mecanismo de protección) en el
        propio principio. El split `test` de Slakh2100 (hito 1) no
        cambia.

- Secciones añadidas: ninguna a nivel de encabezado. Secciones
  eliminadas: ninguna.

- Governance: el checkbox "VI -- Hito 2: tamaño de la porción reservada
  de GuitarSet y su semilla de muestreo" pasa de `[ ]` a `[x]`, con la
  cifra resumida en la propia línea. El checkbox "VII -- Hito 2: métrica
  principal y presupuesto numérico" permanece `[ ]` a propósito -- su
  propio criterio de cierre (primera medición real de la Feature 006) no
  se cumplió todavía, y rellenarlo ahora sería el mismo vicio que VII ya
  prohíbe para el presupuesto.

- Sesión anterior (v1.6.0 → v1.7.0), preservada por referencia histórica:
- Version change: 1.6.0 → 1.7.0
- Fuente: pedido explícito de gobernanza de esta sesión (dos cambios, sin
  tocar presupuestos ni cifras ya cerradas).
- Bump MINOR: se generaliza la redacción de los Principios VI y VII para
  cubrir cualquier hito (antes redactados específicamente para el hito 1),
  y se agrega una decisión nueva (reserva de una porción de GuitarSet para
  el hito 2, tamaño y semilla ABIERTO) -- no se elimina ni se contradice
  ninguna decisión ya tomada (SI-SDR −8.0 dB, split `test` de Slakh, las
  dos limitaciones declaradas, todo permanece sin cambio como evidencia
  del hito 1), así que no aplica MAJOR; no es solo una aclaración de
  redacción -- agrega una regla nueva de reserva de evaluación para el
  hito 2 -- así que no es PATCH.

- Principios modificados en v1.7.0 (contenido, no título ni posición):
  VI.   "Evaluación cuantitativa y verificación cualitativa son distintas"
        -- el bloque "Cuantitativa" se reescribe: regla general primero
        (todo hito reserva una porción intocable de su conjunto de
        evaluación, usada una sola vez al cierre), luego el split `test`
        de Slakh2100 explícitamente etiquetado como la instancia del
        hito 1, no la definición. Se agrega una instancia nueva para el
        hito 2 (ABIERTO): porción de GuitarSet reservada por muestreo
        aleatorio con semilla declarada, protegida por el mismo hook
        `PreToolUse` que `tests/holdout/` -- tamaño y semilla se cierran
        en `/speckit-plan` de la Feature 006, no aquí. Las dos
        limitaciones declaradas (Slakh sintetizado; SI-SDR no predice
        transcribibilidad) se conservan sin cambio de contenido, solo
        etiquetadas "(hito 1)" para que quede explícito que son evidencia
        de ese hito, no una propiedad general del principio.
  VII.  "La métrica y su presupuesto" -- se agrega un párrafo de regla
        general al inicio (cada hito declara su propia métrica y
        presupuesto, fijado después de medir, nunca antes) y se etiqueta
        explícitamente todo el contenido de SI-SDR/−8.0 dB ya existente
        como "Hito 1 -- separación de guitarra". Se agrega un párrafo
        nuevo "Hito 2 -- detección de notas. ABIERTO": métrica y
        presupuesto sin declarar en este documento todavía, cierran tras
        la primera medición real de la Feature 006. Ningún número ni
        cifra existente cambia.

- Secciones añadidas: ninguna a nivel de encabezado (todo el contenido
  nuevo vive dentro de los Principios VI y VII, ya existentes, como
  párrafos con etiqueta de hito). Secciones eliminadas: ninguna.

- Governance: se agregan dos checkboxes `[ ]` nuevos -- VI (tamaño y
  semilla de la porción reservada de GuitarSet, hito 2) y VII (métrica
  principal y presupuesto del hito 2) --, cada uno con su propio criterio
  de cierre explícito, siguiendo la misma regla que ya rigió los tres
  `ABIERTO` originales del documento. El párrafo introductorio de esa
  subsección se actualiza para reflejar que vuelven a existir `ABIERTO`
  sin rellenar.

- Sesión anterior (v1.5.0 → v1.6.0), preservada por referencia histórica:
- Version change: 1.5.0 → 1.6.0
- Fuente: medición real sobre el conjunto evaluable completo (Feature
  004, `mediciones/conjunto_completo.json` -- 1559 temas de
  `train`+`validation`, sin muestreo, `htdemucs_6s` firma 5c90dfd2).
  Segunda medición independiente del presupuesto ya cerrado en v1.5.0,
  no una nueva decisión.
- Bump MINOR: se agrega evidencia real y verificada a Principio VII --
  el presupuesto (`−8.0 dB`) NO cambia, así que no aplica MAJOR (ninguna
  decisión ya tomada se contradice); no es solo una aclaración de
  redacción -- agrega una segunda corrida real con su propia mediana y
  su propia consecuencia metodológica -- así que no es PATCH.

- Principios modificados en v1.6.0 (contenido, no título ni posición):
  VII.  "La métrica y su presupuesto" -- se agrega la subsección
        "Evidencia adicional sobre el conjunto evaluable completo",
        después del bloque de "Presupuesto" ya cerrado en v1.5.0: la
        corrida sobre los 1559 temas sin muestreo (mediana de
        emparejadas `−5.55 dB`, margen `2.45 dB`), la comparación con la
        submuestra (`−6.95 dB`, `1.4 dB` más pesimista que el conjunto
        completo -- el riesgo real de una muestra pequeña era salir
        optimista, y no ocurrió), y la consecuencia explícita: valida el
        método de muestreo, no es motivo para recalibrar el número ya
        fijado -- recalibrar ahora sería el mismo vicio que la sección ya
        prohíbe para forzar un pase, aplicado en la dirección inversa
        (mover el umbral para que apruebe con más margen todavía).

- Secciones añadidas: ninguna a nivel de encabezado (el nuevo contenido
  vive dentro de Principio VII, ya existente). Secciones eliminadas:
  ninguna.

- Governance: sin cambios en los checkboxes -- los tres `ABIERTO`
  originales ya estaban cerrados desde v1.5.0; esta enmienda agrega
  evidencia a una decisión ya tomada, no cierra nada nuevo.

- Sesión anterior (v1.4.0 → v1.5.0), preservada por referencia histórica:
- Version change: 1.4.0 → 1.5.0
- Fuente: primera medición real del hito 1 (Feature 004,
  `mediciones/submuestra_hito1.json` -- submuestra_hito1, semilla
  20260904, 40 temas de `validation`, `htdemucs_6s` firma 5c90dfd2).
  Cierra el último `ABIERTO` de la constitución: el número del
  presupuesto de Principio VII.
- Bump MINOR: se cierra un `ABIERTO` con contenido real y verificado --
  no se elimina ni se contradice ninguna decisión ya tomada (el alcance
  de la medición, cerrado en v1.4.0, no cambia), así que no aplica
  MAJOR; no es solo una aclaración de redacción -- agrega el número del
  presupuesto que no existía -- así que no es PATCH.

- Principios modificados en v1.5.0 (contenido, no título ni posición):
  VI.   "Evaluación cuantitativa y verificación cualitativa son
        distintas" -- se agrega una segunda limitación declarada, junto
        a la de Slakh sintetizado: SI-SDR mide fidelidad de forma de
        onda, no contenido tonal, y esta cifra no predice si la
        separación alcanza para transcribir (verificación cualitativa
        sobre una salida real de la Feature 004).
  VII.  "La métrica y su presupuesto" -- el bloque `ABIERTO` de
        "Presupuesto" se reemplaza por el valor cerrado (`−8.0 dB`)
        sobre la mediana de referencias emparejadas, con la evidencia
        completa de la corrida: 40 temas/0 exclusiones, 110 referencias
        (40 emparejadas/70 sin pareja), mediana global `−∞` explicada
        como aritmética forzosa (no defecto), mediana de emparejadas
        `−6.95 dB` (rango `−49.29` a `3.12`), y la comparación
        mono/poli (`−8.55` vs `−6.15`) que descarta que la cifra esté
        dominada por comparar una estimación mono contra referencia
        polifónica. Se agrega la regla de reporte obligatorio de la
        proporción de referencias sin pareja junto a cualquier cifra de
        esta métrica.

- Secciones añadidas: ninguna a nivel de encabezado (el nuevo contenido
  vive dentro de los Principios VI y VII, ya existentes). Secciones
  eliminadas: ninguna.

- Governance: el checkbox de VII (presupuesto numérico) pasa de `[ ]` a
  `[x]` -- pedido explícito de esta sesión, con la cifra y su evidencia
  resumidas en la propia línea del checkbox. Los tres `ABIERTO`
  originales de la constitución quedan cerrados; el párrafo introductorio
  de esa subsección se actualiza para reflejarlo.

- Sesión anterior (v1.3.0 → v1.4.0), preservada por referencia histórica:
- Version change: 1.3.0 → 1.4.0
- Fuente: hallazgo real de reloj (research.md #9 de
  `specs/003-separacion-modelo-preentrenado/`) durante
  `/speckit-implement` T016 de esa feature -- medición real, no
  estimada, de cuánto tarda una inferencia con `htdemucs_6s` en CPU
  sobre un tema completo de Slakh2100.
- Bump MINOR: se agrega contenido real y verificado a Principio VII
  (alcance de la medición: submuestra de 40 temas de `validation`,
  semilla fija `20260904`, con su distribución de polifonía verificada)
  -- el `ABIERTO` del presupuesto numérico en sí permanece sin cerrar a
  propósito, porque su propio criterio de cierre ("primera medición
  real") no se cumplió todavía; no se inventa un número. No se elimina
  ni se contradice ninguna decisión ya tomada -- no aplica MAJOR. No es
  solo una aclaración de redacción -- cambia qué evidencia respalda el
  principio -- así que no es PATCH.

- Principios modificados en v1.4.0 (contenido, no título ni posición):
  VII.  "La métrica y su presupuesto" -- se agrega la subsección
        "Alcance de la medición" (nueva, con evidencia real de tiempo y
        memoria, la submuestra declarada, su distribución de polifonía
        verificada, y la razón para descartar el criterio alfabético
        anterior). El bloque `ABIERTO` de "Presupuesto" se reescribe
        para aclarar que ahora es específicamente sobre el NÚMERO, no
        sobre el alcance -- sigue sin contenido numérico, por diseño.

- Secciones añadidas: ninguna a nivel de encabezado (la nueva
  subsección vive dentro de Principio VII, ya existente). Secciones
  eliminadas: ninguna.

- Governance: el checkbox de VII (presupuesto numérico) permanece `[ ]`
  -- pedido explícito de esta sesión ("El checkbox del presupuesto en
  Governance sigue [ ]") -- con una nota ampliada que distingue el
  alcance (ya fijado) del número (todavía no).

- Sesión anterior (v1.2.0 → v1.3.0), preservada por referencia histórica:
- Version change: 1.2.0 → 1.3.0
- Fuente: hallazgo G1 de `/speckit-analyze` sobre
  `specs/002-metrica-separacion-guitarra/` -- Principio X, en su redacción
  literal ("una tarea que contiene más de un test rojo no es una tarea"),
  entra en conflicto con la práctica real del proyecto, ejercitada dos
  veces (001/T003, 002/T015), no con un caso nuevo.
- Bump MINOR: se aclara/redefine el criterio de tamaño de tarea con
  contenido real (de "una función de test" a "un cambio de código
  independiente") -- cambia qué cuenta como cumplimiento, no es una
  PATCH de solo redacción, pero no elimina ni invierte el límite de
  tamaño que el principio impone, así que no aplica MAJOR.

- Principios modificados en v1.3.0 (contenido, no título ni posición):
  X.    "Tamaño de slice y presupuesto de ventana" -- se reemplaza "una
        tarea que contiene más de un test rojo no es una tarea" por un
        criterio operativo: una tarea es un cambio de implementación
        cohesivo; varias funciones de test que verifican la MISMA unidad
        desde distintos escenarios cuentan como una sola tarea, mecanismos
        genuinamente separados empaquetados juntos no. El párrafo de
        presupuesto de ventana (tokens, no reloj) queda sin cambio.

- Secciones añadidas: ninguna. Secciones eliminadas: ninguna.

- Governance: sin cambios en los checkboxes de `ABIERTO` (siguen siendo
  los mismos dos de VII/VIII cerrados, uno de VII pendiente).

- Sesión anterior (v1.1.0 → v1.2.0), preservada por referencia histórica:
- Version change: 1.1.0 → 1.2.0
- Fuente: specs/002-metrica-separacion-guitarra/plan.md y research.md
  (decisiones ya tomadas y verificadas empíricamente durante `/speckit-plan`
  de la feature 002-metrica-separacion-guitarra), trasladadas a la
  constitución sin reescritura de sustancia -- este comando solo cierra
  los `ABIERTO` que esos documentos ya resolvieron, no inventa contenido.
- Bump MINOR: 2 de los 3 `ABIERTO` de v1.1.0 se cierran con contenido real
  y verificado (Principio VII, mitad "métrica principal"; Principio VIII,
  completo). El tercero (VII, presupuesto numérico) permanece `ABIERTO` a
  propósito -- su propio criterio de cierre ("después de la primera
  medición real") no se ha cumplido, y rellenarlo ahora sería exactamente
  el vicio que ese mismo principio prohíbe. Ninguna decisión ya tomada se
  contradice o se elimina -- no aplica MAJOR.

- Principios modificados en v1.2.0 (contenido, no título ni posición):
  VII.  "La métrica y su presupuesto" -- el bloque `ABIERTO` de "Métrica
        principal" se reemplaza por SI-SDR (Le Roux et al. 2019) cerrado,
        con la verificación de respuesta conocida (+∞ exacto) documentada
        con su razón matemática y su evidencia empírica. El bloque
        `ABIERTO` de "Presupuesto" queda literalmente igual -- no se tocó.
  VIII. "Determinismo" -- el bloque `ABIERTO` se reemplaza por la opción
        (b) (tolerancia numérica declarada) cerrada, aplicada de forma
        selectiva: tolerancia para valores calculados, igualdad exacta
        para valores exactos por construcción y para todo resultado
        discreto. La opción (a) queda registrada como descartada para
        esta feature, con su razón, no borrada del historial de la
        decisión.

- Secciones añadidas: ninguna. Secciones eliminadas: ninguna.

- Governance: los checkboxes de VII (métrica principal) y VIII se marcan
  `[x]`, cada uno con una nota de una línea señalando dónde se cerraron.
  El checkbox de VII (presupuesto numérico) permanece `[ ]`, sin cambio.

- Sesión anterior (v1.0.0 → v1.1.0), preservada por referencia histórica:

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

**Cuantitativa -- regla general.** Todo hito reserva una porción de su
conjunto de evaluación que ningún agente inspecciona ni ajusta contra ella,
usada una sola vez al cerrar el hito para confirmar que la cifra medida no
es sobreajuste al propio procedimiento de desarrollo. El bloqueo es
mecánico: la ruta se protege con el mismo hook `PreToolUse` que cubre
`tests/holdout/`.

**Hito 1 -- split `test` de Slakh2100.** Se usa la división oficial de
prueba del dataset como conjunto reservado: no la inventamos, es comparable
con trabajo publicado, y elimina la discusión de cómo partir sin fugas de
datos. Es la instancia de este principio para el hito 1, no su definición.

**Hito 2 -- porción reservada de GuitarSet.** Cerrado con la Feature 006
(detección de notas sobre guitarra limpia): **72 grabaciones (20% de las
360 de GuitarSet)**, seleccionadas por muestreo aleatorio con semilla
declarada **`20260908`** sobre los 360 identificadores de grabación
ordenados -- mismo criterio que la submuestra del hito 1 (Principio VII):
reproducible, sin que el orden del identificador correlacione con nada
del proceso de grabación.

- **Por qué 20% y no 15%.** GuitarSet es chico en términos absolutos
  (360 grabaciones) comparado con Slakh2100 (1710 temas) -- una fracción
  fija en el extremo bajo del rango considerado (15% = 54) da una N
  pequeña para la confirmación de cierre. El propósito generalizado de
  este principio (v1.7.0) es confirmar que la cifra medida no es
  sobreajuste al propio procedimiento de desarrollo, no solo protegerse
  de selección de modelo entre varios candidatos -- una N mayor (72) da
  una confirmación más creíble sin sacrificar capacidad real de
  medición, porque esta feature no entrena ni afina (quedan 288
  grabaciones, 80%, disponibles para medir).
- **Mecanismo -- corregido en `/speckit-implement` de la Feature 006
  (T028-T035): sin manifiesto persistido.** La reserva se deriva en vivo
  de la semilla en cada invocación de `construir_lista_grabaciones`
  (`deteccion/orquestador.py`):
  `random.Random(20260908).sample(<identificadores ordenados>, 72)`.
  `modo="reservado"` da esas 72; `modo="medibles"` da el complemento
  (288) -- ambos derivados del mismo cálculo, complementarios por
  construcción. Un manifiesto cacheado en disco tendría una fuente de
  verdad separada del código: si alguien cambiara la semilla, el archivo
  no cambiaría solo, y la partición efectiva quedaría desincronizada de
  la que el código dice usar. Con cálculo en vivo, cambiar la semilla
  cambia la partición completa de forma automática y visible en el
  propio diff -- sin necesidad de ningún archivo ni hook de protección
  adicional para esta reserva en particular. La CLI
  (`deteccion/cli.py`) expone esto como `--modo {medibles,reservado}`,
  sin valor por defecto -- un default que apuntara a `"reservado"`
  mediría el conjunto que este principio prohíbe tocar.
- Ningún agente inspecciona esas 72 grabaciones durante el desarrollo del
  hito 2; se usan una sola vez al cerrarlo, para confirmar que la cifra
  medida sobre las 288 restantes no fue sobreajuste al procedimiento.

**Cualitativa -- música propia.** Un conjunto pequeño de grabaciones
personales, fuera del repositorio, **sin referencia aislada y por lo tanto
sin métrica posible**. Sirve para detectar fallos groseros (salida en
silencio, voz colada, artefactos) que un buen número en Slakh no revelaría.
No produce cifras y no se publica.

**Limitación declarada (hito 1):** Slakh es audio sintetizado desde MIDI; el
modelo preentrenado se entrenó con audio real. La métrica del hito 1 mide
separación sobre guitarras sintetizadas y **no se extrapola a grabaciones
reales**. Cualquier afirmación sobre el rendimiento en canciones reales
requiere evidencia que este hito no produce.

**Segunda limitación declarada (hito 1), verificada sobre la primera
medición real (Feature 004):** SI-SDR mide fidelidad de forma de onda, no
contenido tonal. La verificación cualitativa sobre una salida real de esa
corrida muestra una guitarra reconocible y con tono perceptible, con ruido
residual apreciable -- consistente con una mediana de `−6.95 dB` sobre las
referencias emparejadas (Principio VII). Para el hito 2 lo que importa es si
el contenido tonal alcanza para transcribir, no la fidelidad de forma de
onda: **esta cifra no predice si la separación es suficiente para
transcribir**. Esa validación es un hito 2 propio, no una consecuencia
automática de un buen SI-SDR.

### VII. La métrica y su presupuesto

**Regla general.** Cada hito declara una métrica principal y un presupuesto
numérico sobre ella, con la evidencia que lo justifica. El presupuesto se
fija DESPUÉS de la primera medición real de ese hito, con la evidencia
observada y el margen justificado por escrito -- nunca antes, y nunca
inventado.

**El umbral no se recalibra para forzar un pase.** Un FALLA documentado con
su razón es un resultado; un umbral movido después de ver el resultado no es
nada. La regla corre en las dos direcciones: mover un umbral que ya
aprobaba para que apruebe con más margen todavía es el mismo vicio que
moverlo para forzar un pase que no se dio.

**Hito 1 -- separación de guitarra.**

**Métrica principal: SI-SDR** (*Scale-Invariant Signal-to-Distortion
Ratio*, Le Roux, Wisdom, Erdogan & Hershey, 2019, "SDR -- Half-baked or
Well Done?", ICASSP 2019). Invariante a escala por construcción -- la
fórmula proyecta la referencia sobre la estimación con un factor de
escala calculado, no por normalizar la amplitud de las señales de
entrada, así que ninguna diferencia de ganancia entre estimación y
referencia se premia ni se castiga. Cerrado en `/plan` de la feature
002-metrica-separacion-guitarra
(`specs/002-metrica-separacion-guitarra/research.md` #1).

**Verificación de respuesta conocida.** Pasar una referencia como su
propia estimación produce SI-SDR = +∞ exacto -- no una aproximación
grande. La razón: cuando la estimación es una copia bit a bit de la
referencia, el numerador y el denominador del factor de escala son la
misma reducción de punto flotante sobre los mismos datos, y la división
de IEEE754 garantiza `x / x == 1.0` para cualquier `x` finito no nulo,
sin importar cuánto error de redondeo tenga `x` en sí -- por eso el
residuo resulta el vector cero bit a bit, no "suficientemente pequeño".
Verificado empíricamente, no solo razonado: confirmado sobre arrays de
hasta 10.652.672 muestras (la longitud real de pista de Slakh2100 vista
en la feature 001) en `float32` y `float64`, sobre el backend BLAS real
del proyecto (research.md #5).

**Alcance de la medición, cerrado con evidencia de reloj real.**
Cerrado en `/plan`/`/implement` de la feature
003-separacion-modelo-preentrenado
(`specs/003-separacion-modelo-preentrenado/research.md` #9).

- **Medido, no estimado:** `htdemucs_6s` en CPU tarda 53.4 s de
  inferencia sobre un tema real de 241.6 s de audio (10.652.672
  muestras), con un pico de memoria de 2.3 GB.
- **Extrapolación:** el conjunto evaluable completo (1710 temas, sin el
  directorio `omitted`) son ~25.4 horas de cómputo secuencial -- cruza
  el umbral de lo repetible en una sesión de trabajo. Una medición que
  no se puede repetir deja de ser una herramienta de trabajo, no solo
  una corrida lenta.
- **Decisión:** el hito 1 se mide sobre una submuestra de 40 temas del
  split `validation`, elegidos por muestreo aleatorio con semilla fija
  y declarada `20260904` -- nunca del split `test`, el conjunto
  reservado del Principio VI.
- **La submuestra ejercita el caso polifónico, verificado, no
  supuesto:** 31 de los 40 temas tienen más de una pista de guitarra,
  hasta 6 en un solo tema (`{1: 9, 2: 13, 3: 6, 4: 7, 5: 1, 6: 4}`) --
  el Principio V exige no esconder el caso difícil, y esta muestra no
  lo esconde.
- **Por qué semilla declarada y no los primeros N alfabéticos:** la
  primera versión de esta submuestra tomaba los primeros 40 `tema_id`
  en orden alfabético. Se descartó por el criterio en sí, no por su
  resultado -- esa muestra tampoco había salido degenerada (13
  monofónicos, 27 polifónicos). La razón del cambio es que el orden de
  `tema_id` no tiene ninguna garantía de no correlacionar con el
  proceso de generación del dataset (lote de render, sesión de
  composición); una semilla aleatoria declarada da la misma
  reproducibilidad exacta sin cargar con ese riesgo.
- **Consecuencia obligatoria:** toda cifra del hito 1 se reporta como
  medida sobre esta submuestra de 40 temas, nunca sobre el conjunto
  completo. Extrapolar esa cifra al conjunto completo exige evidencia
  que este hito no produce -- mismo criterio que la limitación ya
  declarada en el Principio VI sobre no extrapolar de Slakh sintetizado
  a grabaciones reales.

**Presupuesto: −8.0 dB, cerrado con la primera medición real sobre la
submuestra declarada arriba** (`submuestra_hito1`, semilla `20260904`,
`htdemucs_6s` firma `5c90dfd2`; artefacto versionado en
`mediciones/submuestra_hito1.json`, Feature 004).

- **Evidencia.** 40 temas procesados, 0 exclusiones. 110 referencias de
  guitarra en total: 40 emparejadas, 70 sin pareja, todas por
  `sin_estimacion_disponible` -- el modelo devuelve exactamente una
  estimación de guitarra por tema, y 31 de los 40 temas son polifónicos
  (Principio V: cada pista de guitarra es una referencia separada).
- **Por qué el presupuesto se fija sobre la mediana de las referencias
  EMPAREJADAS, no sobre la mediana global.** La mediana global de esta
  corrida es `−∞`: 70 de 110 valores son el sentinel de "sin pareja", así
  que el punto medio del conjunto ordenado cae ahí necesariamente -- es
  aritmética forzosa, no un defecto de esta corrida en particular. Una
  compuerta sobre una mediana estructuralmente `−∞` no podría fallar
  nunca, y una compuerta que no puede fallar es un modo de fallo que este
  proyecto ya encontró varias veces antes. La mediana sobre las 40
  referencias emparejadas es `−6.95 dB`, con rango finito observado de
  `−49.29` a `3.12 dB`.
- **Verificación de que la cifra no está artificialmente deprimida por
  comparar una estimación mono contra una referencia polifónica.** Los 9
  temas monofónicos dan una mediana de `−8.55 dB`; los 31 polifónicos dan
  `−6.15 dB`. Los monofónicos NO salen mejor -- si la cifra global
  estuviera dominada por el caso "una sola estimación de guitarra contra
  varias referencias reales", se esperaría lo contrario. Esto no descarta
  el efecto de la polifonía en sí (sigue siendo la explicación más simple
  de por qué 70 referencias quedan sin pareja), pero sí descarta que sea
  la única causa de una mediana baja.
- **Valor: −8.0 dB**, con margen por debajo de los `−6.95 dB` observados
  sobre las referencias emparejadas.
- **Reporte obligatorio de la proporción sin pareja.** Toda cifra de esta
  métrica se reporta junto con la fracción de referencias sin estimación
  (70/110 en esta corrida) -- la mediana de las emparejadas, sola, oculta
  que el modelo dejó más de la mitad de las referencias sin ninguna
  estimación con la que compararlas. Publicar el número sin esa
  proporción es tan engañoso como el problema que el punto anterior
  descarta para la mediana global.
- **El umbral no se recalibra para forzar un pase** (regla de esta misma
  sección, ya vigente): si una corrida futura sobre esta submuestra cae
  por debajo de `−8.0 dB`, el resultado es un FALLA documentado, no una
  ocasión para mover el número.

**Evidencia adicional sobre el conjunto evaluable completo -- el
presupuesto no cambia, verificado independientemente sin muestreo**
(`conjunto_completo`, `htdemucs_6s` firma `5c90dfd2`, sin semilla porque
este modo no muestrea; artefacto versionado en
`mediciones/conjunto_completo.json`).

- **Evidencia.** 1559 temas (`train`+`validation`, sin muestreo), 1557
  reportes, 2 exclusiones (`sin_guitarra_referencia`). Mediana sobre las
  1557 referencias emparejadas: `−5.55 dB` (margen de `2.45 dB` sobre el
  presupuesto), sobre un total de 4055 referencias (2498 sin pareja).
- **La submuestra resultó pesimista, no optimista, respecto del
  conjunto completo.** La mediana de la submuestra de 40 temas
  (`−6.95 dB`) es `1.4 dB` más baja que la del conjunto completo -- el
  riesgo real de fijar un presupuesto sobre una muestra pequeña era que
  saliera optimista (que aprobara con margen artificial y luego el
  conjunto completo cayera por debajo), y ocurrió lo contrario.
- **Consecuencia sobre el método de muestreo, no sobre el número.** El
  muestreo aleatorio con semilla declarada (más arriba en esta sección)
  capturó la población razonablemente bien, y fijar el presupuesto sobre
  la muestra pequeña fue la decisión conservadora, no una apuesta. Esto
  valida el método -- no es una razón para recalibrar el presupuesto
  ahora que hay una cifra más favorable disponible: hacerlo sería
  exactamente el vicio que esta misma sección prohíbe arriba ("el umbral
  no se recalibra para forzar un pase" aplica igual de fuerte a mover un
  umbral que ya aprobaba, para que apruebe con más margen todavía).
- **El presupuesto de `−8.0 dB` queda validado por las dos mediciones
  independientes**, no reemplazado por ninguna: la submuestra aprueba
  con margen de `1.05 dB`, el conjunto completo con `2.45 dB`. El número
  sigue siendo `−8.0 dB`.

**Hito 2 -- detección de notas sobre guitarra limpia.**

**Métrica principal: F1** (medida F armónica de precisión y
exhaustividad sobre el criterio de acierto tono+inicio, FR-003/FR-004 --
`mir_eval.transcription`, convención MIREX Note Tracking). Ya fijada en
`spec.md`/`plan.md` de la Feature 006; se cierra aquí con la primera
medición real. **Precisión y exhaustividad se reportan siempre por
separado, nunca solo el balance** -- son asimétricas (una nota inventada
estorba más que una faltante al tocar una tablatura), y esa asimetría es
parte del resultado, no un adorno (ver evidencia abajo). Toda cifra se
reporta además desglosada global/monofónico/polifónico (FR-006/FR-007),
nunca solo la global.

**Alcance de la medición, cerrado con la primera corrida real** (Feature
006, `mediciones/deteccion_medibles.json`).

- 288 de las 360 grabaciones de GuitarSet (las medibles -- el
  complemento de las 72 reservadas del Principio VI, semilla `20260908`).
  0 exclusiones.
- Modelo: Basic Pitch, variante `icassp_2022`, firma `3db297d5`, backend
  `tflite`, Apache-2.0 en código y pesos (Principio IV).
- Tolerancias: 50 cents de tono, ventana de inicio de 50 ms -- los
  defaults reales de `mir_eval.transcription.precision_recall_f1_overlap`
  (convención MIREX), citados, no inventados. La duración se ignora a
  propósito (FR-004): acertar tono e inicio ya produce algo tocable.
- Emparejamiento siempre dentro de una grabación (FR-013), agregación
  por SUMA de conteos entre grabaciones -- nunca por pool de notas crudas
  ni por promedio de resultados por grabación.

**Presupuesto: 0.70 sobre el F1 GLOBAL**, con margen por debajo del
`0.7394` observado.

- **Evidencia.** Global: precisión `0.7322`, exhaustividad `0.7468`, F1
  `0.7394` -- 49538 notas de referencia, 50524 estimadas, 36995
  verdaderos positivos. Monofónico: precisión `0.7267`, exhaustividad
  `0.8212`, F1 `0.7710` -- 15280 referencias, 17268 estimadas, 12548 TP.
  Polifónico: precisión `0.7351`, exhaustividad `0.7136`, F1 `0.7242` --
  34258 referencias, 33256 estimadas, 24447 TP. Invariante verificado:
  `TP(mono) + TP(poli) = TP(global)` = 36995 exacto
  (`12548 + 24447 = 36995`, FR-014).
- **La asimetría precisión/exhaustividad es distinta entre particiones,
  y esa diferencia es el resultado, no ruido.** En monofónico el modelo
  sobreestima: 17268 notas estimadas contra 15280 de referencia (+13.0%)
  -- encuentra casi todo (exhaustividad `0.8212`) pero inventa de más
  (precisión `0.7267`, la más baja de las tres particiones). En
  polifónico se invierte: 33256 estimadas contra 34258 de referencia
  (−2.9%) -- precisión (`0.7351`) por encima de exhaustividad (`0.7136`):
  el modelo deja más acordes sin cubrir de lo que inventa. Publicar solo
  el F1 ocultaría que el tipo de error que más estorba al tocar una
  tablatura (una nota inventada) es más frecuente justamente en el caso
  monofónico, no en el polifónico, donde se esperaría más ambigüedad.
- **Por qué 0.70.** Margen de `~0.04` (F1), `~5.3%` relativo, por debajo
  de lo observado -- ni ajustado al mínimo que hoy mismo aprobaría (esta
  sección lo prohíbe arriba) ni tan amplio que pierda su función de
  compuerta. Mismo criterio general que el hito 1 aplicó sobre su propia
  cifra observada (margen documentado por escrito, nunca cero) -- la
  proporción exacta no se traslada mecánicamente entre una escala
  logarítmica (dB) y una razón acotada en `[0, 1]`, pero el criterio sí:
  suficiente margen para que una remedición futura sobre este mismo
  conjunto no repruebe por casualidad de redondeo, sin ser tan laxo que
  una regresión real del método de detección pase inadvertida.
- **El umbral no se recalibra para forzar un pase** (regla general de
  esta sección, ya vigente): si una corrida futura sobre este conjunto
  cae por debajo de `0.70`, el resultado es un FALLA documentado, no una
  ocasión para mover el número.

**Historia metodológica: dos defectos del mismo tipo, encontrados y
corregidos antes de fijar el presupuesto -- evidencia sobre el método, no
solo sobre el modelo.**

La primera versión de este cálculo producía cifras inválidas por dos
defectos de la misma familia, ninguno detectado por `spec`, `plan`,
`clarify` ni `analyze` -- ambos encontrados con evidencia medida y
corregidos con test rojo primero, antes de que esta sección se cerrara:

- **Agrupar antes de emparejar (FR-013).** La primera versión de
  `agregar_conjunto` pooleaba las notas de las 288 grabaciones en dos
  listas únicas antes de emparejar -- permitía que una nota de una
  grabación se acreditara contra la de otra grabación sin relación
  temporal alguna, si sus instantes de inicio relativos coincidían por
  azar dentro de la ventana de 50 ms. Dos grabaciones sin ningún acierto
  propio podían dar precisión `0.5` por esta vía -- además de un fallo
  real de memoria (matrices densas N×M sobre el pool completo). Corregido:
  el emparejamiento ocurre siempre dentro de una única grabación, la
  agregación suma conteos ya resueltos entre grabaciones.
- **Clasificar antes de emparejar (FR-014).** La partición monofónico/
  polifónico reclasificaba cada nota estimada por su propio instante y
  volvía a emparejar de forma independiente dentro de cada subconjunto
  ya partido. Esto destruyó `7313` aciertos legítimos de `36995`
  (`19.8%` del total) -- y no de forma uniforme entre particiones: la
  polifónica era la más castigada. Corregido: un único emparejamiento
  por grabación, cada par hereda la clasificación de su nota de
  referencia.
- **El principio general detrás de ambos.** Agrupar o clasificar
  entidades ANTES de resolver el emparejamiento que las relaciona
  destruye pares legítimos que cruzan la frontera de la agrupación o
  clasificación elegida -- sin importar si esa frontera es "grabación" o
  "clase de polifonía". Cualquier partición futura de esta métrica (o de
  cualquier otra que emparejamiento resuelva primero y clasifique
  después) debe heredar la clasificación del par ya resuelto, nunca
  reclasificar ni reemparejar cada lado por separado.

### VIII. Determinismo

**Cerrado: opción (b), tolerancia numérica declarada -- aplicada de forma
selectiva, no uniforme.** Cerrado en `/plan` de la feature
002-metrica-separacion-guitarra
(`specs/002-metrica-separacion-guitarra/research.md` #6), la primera
feature del proyecto con aritmética de punto flotante sujeta a este
criterio.

- Un valor que es el resultado de una acumulación de punto flotante (p.
  ej. un SI-SDR calculado sobre audio real) se compara con tolerancia
  numérica explícita, nunca con igualdad bit a bit. No hay ninguna fuente
  de aleatoriedad en el sistema (sin semillas, sin inferencia de modelo);
  el único riesgo de no-determinismo es el orden de acumulación de punto
  flotante entre builds distintos de BLAS, y exigir bit-exactitud contra
  ese riesgo sería frágil sin aportar ninguna garantía real adicional.
- **Excepción -- lo exacto por construcción se compara exacto.** Un valor
  que es una identidad matemática o un sentinel asignado por definición,
  no el resultado de una acumulación, se compara con igualdad exacta. El
  `+∞` de la verificación de respuesta conocida (Principio VII) es el
  ejemplo: no converge a infinito, es la consecuencia exacta de que el
  residuo es el vector cero bit a bit.
- Todo resultado discreto (conteos, qué elemento se emparejó con cuál, en
  qué categoría cayó un caso) se compara con igualdad exacta, por ser una
  decisión combinatoria, no aritmética de punto flotante.

La opción (a) (reproducibilidad exacta forzada) queda descartada para
esta feature, no borrada del historial de la decisión: no hay ninguna
semilla que fijar ni ninguna operación no determinista que forzar, así
que forzar bit-exactitud no compraría ninguna garantía que la opción (b)
no dé ya. Lo no defendible sigue siendo no decidir esto y descubrir la
respuesta cuando un test falle de forma intermitente en integración
continua.

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

Una tarea es un cambio de implementación cohesivo, verificado por los
escenarios de prueba que hacen falta para fijar su comportamiento -- no,
literalmente, una función de test por tarea. El criterio: si un mismo
cambio de código hace pasar todos los tests de la tarea a la vez, son una
sola tarea; si hacen falta cambios independientes para que cada uno pase,
son tareas distintas, aunque compartan archivo o tema superficial. Varias
funciones de test que verifican la misma unidad -- el mismo tipo, la misma
función, el mismo mecanismo -- desde distintos escenarios de entrada
cuentan como una sola tarea; requisitos o mecanismos genuinamente
separados, empaquetados juntos por conveniencia o para evitar renumerar,
no.

*Aclaración (v1.3.0):* la redacción original -- "una tarea que contiene
más de un test rojo no es una tarea" -- se leía como un límite literal de
un test por tarea, más estricto que la práctica real del proyecto desde
la primera feature (`001-lectura-tema-slakh2100`, T003 agrupó varias
funciones de test bajo una sola tarea para fijar el mismo conjunto de
tipos) y ejercitada de nuevo en `002-metrica-separacion-guitarra` (T015,
dos escenarios sobre el mismo mecanismo de reclasificación de motivos).
`/speckit-analyze` señaló la brecha entre el principio escrito y la
práctica ya ejercitada dos veces; esta aclaración cierra esa brecha
describiendo el criterio que el proyecto ya aplicaba, no uno nuevo -- no
relaja el límite de tamaño de tarea, lo hace coincidir con lo que
"tamaño" mide de verdad: cuántos cambios de código independientes hacen
falta, no cuántas funciones de test hay.

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

**Los `ABIERTO` no se rellenan por adelantado.** Cada uno tiene su propio
criterio de cierre, declarado en el principio correspondiente -- no se
completa antes de que ese criterio se cumpla, y no se completa como parte
de un `/speckit-constitution` posterior "para no dejar cabos sueltos": eso
es exactamente el vicio que VII prohíbe para el presupuesto. Los tres
`ABIERTO` originales del hito 1 ya se cerraron -- con contenido real y, en
los casos de VIII y del presupuesto de VII, verificado empíricamente, no
solo razonado -- cada uno cuando su propio criterio de cierre se cumplió:
los dos primeros en `/plan` de 002-metrica-separacion-guitarra, el tercero
tras la primera medición real sobre la submuestra declarada (Feature 004,
`mediciones/submuestra_hito1.json`). La generalización de los Principios
VI/VII a cualquier hito (v1.7.0) abrió dos `ABIERTO` nuevos, específicos
del hito 2 -- no una reapertura de los tres ya cerrados del hito 1. El de
VI (tamaño y semilla de la porción reservada de GuitarSet) cerró en
v1.8.0; el de VII (métrica y presupuesto del hito 2) cerró en v1.9.0, con
la primera medición real de la Feature 006. **No queda ningún `ABIERTO`
pendiente en este documento.**

- [x] VII -- Métrica principal: SI-SDR (Le Roux et al., 2019). Hito 1.
      Cerrado en `/plan` de 002-metrica-separacion-guitarra.
- [x] VII -- Presupuesto numérico: `−8.0 dB` sobre la mediana de
      referencias emparejadas, con la proporción sin pareja como parte
      obligatoria del reporte. Hito 1. Cerrado con la primera medición
      real sobre la submuestra declarada (Feature 004,
      `mediciones/submuestra_hito1.json`), y validado independientemente
      con una segunda medición sobre el conjunto evaluable completo sin
      muestreo (`mediciones/conjunto_completo.json`, v1.6.0) -- ver
      Principio VII para la evidencia completa.
- [x] VIII -- Política de determinismo: opción (b), tolerancia numérica
      declarada con excepción para valores exactos por construcción.
      Cerrado en `/plan` de 002-metrica-separacion-guitarra.
- [x] VI -- Hito 2: tamaño de la porción reservada de GuitarSet y su
      semilla de muestreo. 72 grabaciones (20% de 360), semilla
      `20260908`. Cerrado con la Feature 006 (detección de notas sobre
      guitarra limpia) -- ver Principio VI para la evidencia completa.
- [x] VII -- Hito 2: métrica principal y presupuesto numérico. F1
      (precisión/exhaustividad siempre por separado, desglosadas
      global/mono/poli); presupuesto `0.70` sobre el F1 global, sobre
      `0.7394` observado. Cerrado con la primera medición real de la
      Feature 006 (288 grabaciones medibles,
      `mediciones/deteccion_medibles.json`) -- ver Principio VII para la
      evidencia completa, incluida la historia metodológica de los dos
      defectos corregidos antes del cierre (FR-013, FR-014).

**Version**: 1.9.0 | **Ratified**: 2026-08-30 | **Last Amended**: 2026-09-10
