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

Bug reportado: `just medir conjunto_completo` terminaba exit 0 con los
1559 progresos de tema persistidos pero sin artefacto agregado.
Diagnóstico exhaustivo: `ejecutar_corrida`, `construir_lista_temas`
(1289 train + 270 validation = 1559, sin truncar, verificado) y
`escribir_artefacto` funcionan bien -- no se reprodujo la causa exacta
(el hueco de 16 min entre el último progreso y el artefacto sugiere que
el proceso original seguía corriendo). Se cerró la clase de fallo:
`escribir_artefacto` relee la ruta tras `os.replace()`, levanta
`EscrituraIncompletaError` si no coincide -- nunca exit 0 sin artefacto
real. Test rojo antes del arreglo. `semilla=None` tolerado en artefacto
y compuerta. `conjunto_completo.json` real ya existe (sin commitear):
1557 reportes, mediana `-5.55 dB`, aprueba. `gauntlet` verde: 172 tests.

## Qué sigue

Decidir si versionar `conjunto_completo.json` (evidencia sobre el
conjunto completo, no solo la submuestra) -- no commiteado, no fue
parte del pedido. Decidir el hito 2 (transcripción).

## Bloqueado / pendiente de decisión

Ninguno. Feature 001: dtype en `_decodificar_audio` -- diferido a hito 2.
Licencia de pesos de Demucs (research.md #3 de 003): cita del usuario, no
verificada de forma independiente (`github.com` bloqueado).
