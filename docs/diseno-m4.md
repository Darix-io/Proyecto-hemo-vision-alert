# Diseño de M4: Dashboard de monitoreo

## Decisiones técnicas confirmadas (líder técnico)

## Alcance

Primera versión del Dashboard (RF-09, supervisar estaciones), con datos simulados: una pantalla con las estaciones, su estado, filtros y el detalle de cada una. Muestra las alertas que produce M3. No incluye la revisión humana de las alertas (RF-05) ni el video (M2).

## Criterio del backlog

- **RF-09:** cargar 40 estaciones simuladas con estados conocidos; comprobar identificación, filtro y detalle; "sin señal" se diferencia de "normal".
- **RNF-01:** el 95 % de 100 eventos de prueba se muestra en 5 segundos o menos, con 40 estaciones simuladas.
- **RNF-03:** una fuente sin fotogramas durante 10 segundos pasa a sin señal; la recuperación es en 10 segundos o menos.

## Decisiones confirmadas por el Product Owner

Confirmadas el 3 de noviembre de 2026.

1. **Sin señal:** una estación con paciente está sin señal si nunca tuvo señal o pasan más de 10 segundos sin fotogramas, y se recupera en 10 segundos o menos (RNF-03).
2. **Sin señal y alerta crítica a la vez:** la estación se muestra como crítica, con una marca visible de "sin señal". Una alerta crítica abierta nunca se oculta. En los contadores se cuenta una sola vez, en "críticas".
3. **Actualización:** el Dashboard se actualiza solo cada 3 segundos, tiene un botón para actualizar a mano, muestra la hora de la última actualización y un aviso visible si deja de actualizarse (valor de ejemplo: más de 10 segundos sin lograr actualizar).
4. **Quién lo ve:** por ahora, cualquier usuario con sesión iniciada, de forma temporal. Condición: cuando se construya RF-11, el Dashboard se restringe a los roles con permiso clínico. El Dashboard muestra solo códigos de paciente, nunca datos personales.
5. **Salas:** dos salas simuladas, Sala A (EST-01 a EST-20) y Sala B (EST-21 a EST-40), con 20 estaciones cada una. Pendiente de la aprobación del líder técnico.
6. **Estaciones libres:** se muestran siempre, en estilo neutro (gris claro, con la palabra "Libre"), al final del orden y con un contador "Libres". Una estación libre no se evalúa como "sin señal". Condición futura: cuando exista M2, una estación libre con señal activa muestra un aviso de posible sesión sin iniciar.

## Decisiones técnicas propuestas (líder técnico)

| Tema | Propuesta |
|---|---|
| Estación | Pasa a ser una tabla propia (código único como EST-07, sala, activa). La sesión se vincula a ella, con una migración que convierte los textos actuales |
| Última señal | Cada estación guarda la fecha de su última señal |
| Datos simulados | Un comando que carga las 40 estaciones con estados conocidos, para probar y mostrar |
| Página de inicio | La dirección raíz (`/`) lleva al Dashboard; hoy muestra "no encontrado" |

## Estados y orden

- Estados que se muestran: sin señal, crítica, en atención y normal, además de "libre". "En atención" queda reservado hasta que se defina cuándo aplica.
- Orden: las críticas primero; las libres al final.
- Contadores: estaciones activas, normales, en atención, críticas, sin señal y libres.
- Filtros: por estado y por sala, y búsqueda por código de estación o de paciente.
- Condición heredada de M3: las alertas normales no se muestran como alertas que requieren atención.

## Detalle de una estación

Paciente (código), sesión, cámara, hora del evento, evento detectado, confianza y tiempo transcurrido, con el aviso de que requiere revisión humana y no es un diagnóstico.

## Datos de prueba propuestos

| Estado | Estaciones | Cantidad |
|---|---|---|
| Crítica | EST-07 (Sala A) y EST-28 (Sala B) | 2 |
| Crítica y además sin señal | EST-12 (Sala A) | 1 |
| Sin señal | EST-19 (Sala A), EST-33 y EST-40 (Sala B) | 3 |
| Libres | EST-16, EST-17 y EST-18 (Sala A); EST-37, EST-38 y EST-39 (Sala B) | 6 |
| Normal | Las 28 restantes | 28 |
| En atención | Ninguna | 0 |

Contadores esperados: 34 activas, 28 normales, 3 críticas, 3 sin señal y 6 libres.

## Preguntas abiertas

1. ¿Cuándo corresponde el estado "en atención"?
2. ¿Debe haber un límite máximo de duración de una alerta? (heredada de M3)