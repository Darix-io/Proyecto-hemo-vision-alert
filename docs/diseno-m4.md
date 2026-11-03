# Diseño de M4: Dashboard de monitoreo

*Versión 0.1 — PROPUESTA pendiente de confirmación del Product Owner — 2 de noviembre de 2026*

## Alcance

Primera versión del Dashboard (RF-09, supervisar estaciones), con datos simulados: una pantalla con las estaciones, su estado, filtros y el detalle de cada una. Muestra las alertas que produce M3. No incluye la revisión humana de las alertas (RF-05) ni el video (M2).

## Criterio del backlog

- **RF-09:** cargar 40 estaciones simuladas con estados conocidos; comprobar identificación, filtro y detalle; "sin señal" se diferencia de "normal".
- **RNF-01:** el 95 % de 100 eventos de prueba se muestra en 5 segundos o menos, con 40 estaciones simuladas.

## Decisiones propuestas

| Tema | Propuesta | Quién confirma |
|---|---|---|
| Estación | Pasa a ser una tabla propia (código único como EST-07, sala, activa). La sesión se vincula a ella, con una migración que convierte los textos actuales | Líder técnico |
| Última señal | Cada estación guarda la fecha de su última señal | Líder técnico |
| Estados que se muestran | Sin señal, crítica, en atención y normal, como el prototipo. "En atención" queda reservado hasta que se defina cuándo aplica | Product Owner |
| Sin señal | Una estación está sin señal si nunca tuvo señal o la última supera 5 minutos (valor de ejemplo) | Product Owner |
| Estado crítico | Una estación con una alerta crítica abierta, hasta que la revisión humana la cierre (esa revisión todavía no existe) | Product Owner |
| Estado normal | Una estación con señal reciente y sin alerta crítica abierta | Product Owner |
| Contadores | Estaciones activas, normales, en atención, críticas y sin señal, como el prototipo | Product Owner |
| Filtros | Por estado y por sala, y búsqueda por código de estación o de paciente | Product Owner |
| Orden | Las críticas primero | Product Owner |
| Detalle de una estación | Paciente, sesión, cámara, hora del evento, evento detectado, confianza y tiempo transcurrido, con el aviso de que requiere revisión humana y no es un diagnóstico | Product Owner |
| Datos simulados | Un comando que carga 40 estaciones con estados conocidos, para probar y mostrar | Líder técnico |
| Condición heredada de M3 | Se filtra por estado: las alertas normales no se muestran como alertas que requieren atención | Product Owner |

## Pantallas propuestas

- Dashboard de estaciones: tarjetas, contadores y filtros.
- Detalle de una estación.

## Preguntas abiertas

1. ¿Cuántos minutos sin señal convierten una estación en "sin señal"? (ejemplo: 5)
2. Si una estación está sin señal y además tiene una alerta crítica abierta, ¿cuál se muestra?
3. ¿El Dashboard se actualiza solo cada cierto tiempo o con un botón?
4. ¿Qué usuarios ven el Dashboard? Hoy, cualquiera con sesión iniciada; los roles llegan con RF-11.
5. ¿Cuántas salas hay y cómo se llaman?
6. ¿Qué se muestra de una estación libre, sin sesión activa?