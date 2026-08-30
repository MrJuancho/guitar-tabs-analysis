# ADR-0001: EJEMPLO -- cómo documentar un presupuesto de deuda de datos

> TODO: este ADR es un placeholder que muestra el formato esperado. Bórralo
> o reemplázalo por el primer ADR real de `Guitar Tabs Analysis` -- pero
> conserva la estructura (contexto medido, decisión, presupuesto con
> owner+fecha, cuándo se revisa) para los ADRs que documenten los gates de
> `quality/gates.py`.

## Estado

Ejemplo -- no aplica a ningún gate real todavía.

## Contexto

Un gate de `GOLD_GATES` con `max > 0` no es un umbral elegido a ojo: es la
cifra medida en una corrida de referencia real, documentada aquí con la
causa conocida. Sin este documento, `data-auditor` no tiene contra qué
comparar un número -- solo puede decir "el gate pasa o no pasa", no "esto
es deuda conocida" vs. "esto es una regresión nueva".

Ejemplo de la forma que debería tener esta sección: "El 18.79% de los
registros de la capa curada comparten una clave que debería ser única.
Diagnosticado el <fecha>: <causa raíz medida, no supuesta>."

## Decisión

Se acepta el valor medido como presupuesto de deuda temporal, con dueño y
fecha de revisión -- no se oculta subiendo silenciosamente un umbral en
`quality/gates.py` para que el gate "pase".

```python
"nombre_del_gate": {"max": <valor medido>, "owner": "<equipo/persona>", "trend": "decreasing"},
```

## Cuándo se revisa

<Condición concreta -- una fecha, un evento, o "cuando se resuelva <causa
raíz>" -- no "eventualmente".>
