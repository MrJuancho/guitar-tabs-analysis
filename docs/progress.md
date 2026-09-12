# Progress -- handoff entre sesiones

<!--
Este archivo se SOBRESCRIBE, no se acumula -- no es un diario ni un
changelog (eso ya vive en los ADRs y en git). Cada sesión reemplaza el
contenido de las tres secciones de abajo con el estado actual; no agrega
al final ni conserva versiones previas.

Límite duro: 40 líneas, este comentario incluido. Si no entra, resume más.

Generado una sola vez por Copier (`_skip_if_exists`) -- `copier update`
nunca vuelve a tocarlo después.
-->

## En qué quedó la última sesión

Constitución v1.10.0: Principio VII cerrado para el hito 3
(`fraccion_coincidencia=0.6186`, presupuesto `0.55`, hitos 1/2 sin
tocar). Después, ADR-0002 (`docs/adr/`): primera prueba manual de
extremo a extremo con una canción real (no Slakh2100 ni GuitarSet) --
cinco hallazgos, ninguno detectable por las métricas de los tres hitos:
(1) separación mejor de lo esperado; (2) conversión a mono descarta
panorama estéreo real (heredado de Slakh); (3) `separar_guitarra` sin
validar forma de entrada -- intento de reservar ~26 TB; (4) el modelo
de coste de digitación no penaliza altura -- mismo signo que la
asimetría de T025 (research.md #15), el más accionable; (5) el
detector confunde octava/armónico y no ve hammer-ons, invisibles con
GuitarSet. Solo documentación, sin corrección -- pedido explícito.
`just gauntlet` verde (sin cambios de código).

## Qué sigue

Decidir qué hacer con cada hallazgo de ADR-0002 es sesión aparte, cada
uno con su propia medición. El más accionable (4, altura ausente en el
modelo de coste) es el candidato más claro, junto con T025.

## Bloqueado / pendiente de decisión

Los cinco hallazgos de ADR-0002. Antes: compuerta automática del `0.70`
del hito 2; `copier update` sin commitear; licencia de Demucs sin verificar.
