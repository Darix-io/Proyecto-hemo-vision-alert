# Diseño de M3: motor de riesgo y reglas

*Versión 1.1 — decisiones confirmadas por el Product Owner el 28 de octubre de 2026*

## Alcance

Cubre la lógica y los datos de RF-03 (clasificar y agrupar eventos), RF-04 (avisos explicables) y RF-12 (reglas versionadas), trabajando con entradas sintéticas. No incluye el video (M2) ni las pantallas del Dashboard (M4).

## Decisiones propuestas

| Tema | Propuesta | Quién confirma |
|---|---|---|
| Clases de evento | Una al inicio: `hemorragia` (el prototipo muestra "posible hemorragia"). Agregar otras debe ser sencillo | Product Owner |
| Valor del evento | La confianza del detector, de 0 a 100 (como el 94.2 % del prototipo) | Product Owner |
| Umbral | Valor de ejemplo: 90. Un valor menor es estado normal; igual o mayor es estado crítico | Product Owner |
| Estados de una alerta | Normal, atención y crítica, como el Dashboard del prototipo. M3 produce hoy normal y crítica; atención queda reservado hasta que el Product Owner defina cuándo aplica | Product Owner |
| Ventana | Valor de ejemplo: 60 segundos, siempre positiva. Eventos de la misma clase y la misma sesión dentro de la ventana forman una sola alerta | Product Owner |
| Repetición | Cada evento tiene un identificador único; repetir el mismo evento no crea otra alerta | Líder técnico |
| Versiones | Cada regla tiene un número de versión. Cambiar una regla crea una versión nueva y la alerta guarda la versión que usó | Líder técnico |
| Datos ausentes | Se guardan vacíos y nunca se rellenan con valores supuestos (RF-04) | Líder técnico |

Los valores 90 y 60 son de ejemplo, no vienen del backlog.

## Datos propuestos

| Tabla | Campos |
|---|---|
| Regla de riesgo | clase de evento, umbral, ventana en segundos, versión, activa |
| Evento visual | identificador único, sesión de diálisis, cámara (texto, opcional), clase, valor, hora |
| Alerta | estado, versión de la regla usada, eventos que agrupa |

El evento se vincula a la sesión de diálisis, que ya conoce al paciente y la estación.

## Decisiones confirmadas por el Product Owner

Confirmadas el 28 de octubre de 2026.

- Un evento normal genera alerta: sí. Condición: el Dashboard (M4) y el historial (M5) deben filtrar por estado.
- Al agrupar eventos, la alerta toma el estado más grave de sus eventos y no baja: sí. Condición: solo la revisión humana (RF-05) cierra una alerta crítica.
- La ventana se mide desde el evento más cercano de la misma clase y sesión.

## Condiciones para M4 y M5

- El Dashboard y el historial deben filtrar las alertas por estado: las alertas de estado "normal" no se muestran como alertas que requieren atención.
- La alerta crítica solo la cierra una revisión humana (RF-05). Cuando se construya la revisión, la alerta necesitará un campo de estado de revisión (pendiente o revisada).
- Cuando se construya la revisión, un evento nuevo no debe unirse a una alerta ya revisada: debe abrir una alerta nueva.

## Preguntas abiertas

1. ¿Qué clases de evento existen además de hemorragia?
2. ¿Cuándo corresponde el estado "atención"?
3. ¿El umbral y la ventana son iguales para todas las clases o cada clase tiene los suyos?
4. ¿Quién configura las reglas? Eso toca a M6 (RF-12).
5. ¿Debe haber un límite máximo de duración de una alerta? Hoy una alerta puede extenderse mientras sigan llegando eventos a menos de la ventana de distancia.