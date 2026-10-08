# Backlog priorizado — HemoVision Alert

**Product Owner:** Ruben Mora  
**Líder técnico:** Josué Desiderio  
**Fuente:** Tarea 2 (requerimientos, historias de usuario y módulos)

## Cómo leer este documento

- Los elementos están agrupados por módulo (M1 a M6) y, dentro de cada módulo, ordenados de prioridad Alta a Baja.
- Un elemento asignado a varios módulos aparece en cada uno, con la nota *también en ...*.
- **Prioridad:** Alta = necesaria para el flujo principal, la seguridad, la privacidad o la integridad de los registros. Media = complementaria para la demostración y el seguimiento. Baja = experimental o futura, sin bloquear el funcionamiento principal.
- **Historia de usuario:** la HU sin asterisco aparece listada de forma directa en la trazabilidad de la Tarea 2. La HU con asterisco (*) se relaciona por compartir el mismo código de origen (RU o RS). El guion (-) indica que no hay HU relacionada en la Tarea 2.
- **Estado:** todos los elementos inician en *Pendiente*. Se actualiza a *En progreso* o *Terminado* cuando el trabajo ocurra realmente.

## Resumen de prioridades

**Elementos únicos** (cada uno se cuenta una sola vez):

| Tipo | Total | Alta | Media | Baja |
|---|---|---|---|---|
| Requerimientos funcionales (RF) | 18 | 15 | 2 | 1 |
| Requerimientos no funcionales (RNF) | 9 | 7 | 2 | 0 |
| **Total** | **27** | **22** | **4** | **1** |

**Por módulo** (aquí un elemento compartido cuenta en cada módulo donde aparece):

| Módulo | Elementos | Alta | Media | Baja |
|---|---|---|---|---|
| M1 Gestión de pacientes y sesiones | 4 | 4 | 0 | 0 |
| M2 Captura y visión artificial | 10 | 8 | 1 | 1 |
| M3 Motor de riesgo y reglas | 5 | 4 | 1 | 0 |
| M4 Dashboard de monitoreo | 9 | 7 | 2 | 0 |
| M5 Historial, auditoría y reportes | 9 | 7 | 2 | 0 |
| M6 Seguridad y privacidad | 9 | 9 | 0 | 0 |

## Backlog por módulo

### M1 — Gestión de pacientes y sesiones

| ID | Elemento | Prioridad | Historia de usuario | Criterio de aceptación | Estado |
|---|---|---|---|---|---|
| RF-01 | Capturar video de la sesión *(también en M2)* | Alta | HU-05 | Abrir una sesión con video controlado de 10 min; comprobar marcas de tiempo y que al cierre no se generen nuevos eventos. | Pendiente |
| RF-07 | Registrar paciente mínimo | Alta | - | Crear dos códigos ficticios distintos y recuperarlos; rechazar código vacío o duplicado; no exigir nombre. | Pendiente |
| RF-08 | Gestionar sesiones | Alta | - | Iniciar, consultar y cerrar sesión; rechazar inicio en estación ocupada; conservar vínculos históricos y detener captura al cierre. | Pendiente |
| RNF-05 | Integridad de registros *(también en M5)* | Alta | HU-04* | Identificadores de evento únicos; escritura atómica de revisión con su auditoría; ningún registro referencia una sesión inexistente. | Pendiente |

### M2 — Captura y visión artificial

| ID | Elemento | Prioridad | Historia de usuario | Criterio de aceptación | Estado |
|---|---|---|---|---|---|
| RF-01 | Capturar video de la sesión *(también en M1)* | Alta | HU-05 | Abrir una sesión con video controlado de 10 min; comprobar marcas de tiempo y que al cierre no se generen nuevos eventos. | Pendiente |
| RF-02 | Detectar señales visuales | Alta | HU-05 | Probar clips positivos y negativos etiquetados por clase; verificar campos y aplicar RNF-08. Una clase sin modelo evaluado se muestra no disponible. | Pendiente |
| RF-13 | Configurar captura y diagnosticar fallos *(también en M4)* | Alta | HU-06* | Cambiar fuente y región; desconectar y reconectar y comprobar estado e incidencia según RNF-03; no mostrar video fuera de la región autorizada. | Pendiente |
| RF-14 | Transmitir eventos y evidencia mínima *(también en M5)* | Alta | HU-06* | Interrumpir conexión y reenviar el mismo ID tres veces: queda un registro; sin flujo continuo de video crudo a la nube. | Pendiente |
| RNF-02 | Privacidad de captura y acceso *(también en M5, M6)* | Alta | HU-06 | Imágenes con marcas fuera de región no se conservan; enlace sin sesión o con rol inválido: acceso denegado; se usa HTTPS. | Pendiente |
| RNF-03 | Continuidad y detección de fallos *(también en M4)* | Alta | - | En ensayo de 4 h, disponibilidad del panel ≥99 %; fuente sin fotogramas 10 s pasa a sin señal; recuperación en ≤10 s. | Pendiente |
| RNF-08 | Evaluación del detector | Alta | - | Precisión y sensibilidad ≥0,80 por clase, con ≥20 positivos y ≥20 negativos sobre clips ajenos al entrenamiento. | Pendiente |
| RNF-09 | Restricción tecnológica *(también en M4, M5, M6)* | Alta | - | Django para web; Django REST Framework para eventos; servicio local con OpenCV y YOLO; AWS S3 privado; scikit-learn para métricas. | Pendiente |
| RNF-07 | Modularidad *(también en M3, M4)* | Media | HU-06* | Sustituir la fuente por un simulador sin cambiar el panel ni el contrato de eventos. | Pendiente |
| RF-18 | Evaluar estimaciones por video | Baja | HU-05* | Con pares video-referencia autorizados, emitir resultados y error medio absoluto; sin referencia no declarar validación. | Pendiente |

### M3 — Motor de riesgo y reglas

| ID | Elemento | Prioridad | Historia de usuario | Criterio de aceptación | Estado |
|---|---|---|---|---|---|
| RF-03 | Clasificar y agrupar eventos | Alta | HU-01, HU-02 | Entradas sintéticas bajo, igual y sobre el umbral producen el estado definido por la regla; repetir el mismo evento no crea otra alerta. | Pendiente |
| RF-04 | Mostrar avisos explicables *(también en M4)* | Alta | HU-02, HU-05* | Inyectar alertas de prueba con valores conocidos y comparar cada campo y su orden temporal; no inventar valores ausentes. | Pendiente |
| RF-12 | Configurar reglas versionadas *(también en M6)* | Alta | - | Rechazar ventana no positiva y clase inexistente; aplicar regla válida a entradas de prueba; conservar versión en el evento. | Pendiente |
| RNF-01 | Tiempo de respuesta *(también en M4)* | Alta | - | El 95 % de 100 eventos de prueba se muestra en ≤5 s desde su recepción en el backend, con 40 estaciones simuladas. | Pendiente |
| RNF-07 | Modularidad *(también en M2, M4)* | Media | HU-06* | Sustituir la fuente por un simulador sin cambiar el panel ni el contrato de eventos. | Pendiente |

### M4 — Dashboard de monitoreo

| ID | Elemento | Prioridad | Historia de usuario | Criterio de aceptación | Estado |
|---|---|---|---|---|---|
| RF-04 | Mostrar avisos explicables *(también en M3)* | Alta | HU-02, HU-05* | Inyectar alertas de prueba con valores conocidos y comparar cada campo y su orden temporal; no inventar valores ausentes. | Pendiente |
| RF-05 | Registrar revisión humana *(también en M5, M6)* | Alta | HU-03 | Confirmar y descartar eventos de prueba; una cuenta sin permiso no puede validar; una observación deja pendiente el aviso. | Pendiente |
| RF-09 | Supervisar estaciones | Alta | HU-01* | Cargar 40 estaciones simuladas con estados conocidos; comprobar identificación, filtro y detalle; sin señal se diferencia de normal. | Pendiente |
| RF-13 | Configurar captura y diagnosticar fallos *(también en M2)* | Alta | HU-06* | Cambiar fuente y región; desconectar y reconectar y comprobar estado e incidencia según RNF-03; no mostrar video fuera de la región autorizada. | Pendiente |
| RNF-01 | Tiempo de respuesta *(también en M3)* | Alta | - | El 95 % de 100 eventos de prueba se muestra en ≤5 s desde su recepción en el backend, con 40 estaciones simuladas. | Pendiente |
| RNF-03 | Continuidad y detección de fallos *(también en M2)* | Alta | - | En ensayo de 4 h, disponibilidad del panel ≥99 %; fuente sin fotogramas 10 s pasa a sin señal; recuperación en ≤10 s. | Pendiente |
| RNF-09 | Restricción tecnológica *(también en M2, M5, M6)* | Alta | - | Django para web; Django REST Framework para eventos; servicio local con OpenCV y YOLO; AWS S3 privado; scikit-learn para métricas. | Pendiente |
| RNF-06 | Legibilidad y acceso al detalle | Media | HU-01*, HU-02* | En pantalla de 1366×768, el detalle se abre con una selección; prioridad indicada con texto e icono además del color. | Pendiente |
| RNF-07 | Modularidad *(también en M2, M3)* | Media | HU-06* | Sustituir la fuente por un simulador sin cambiar el panel ni el contrato de eventos. | Pendiente |

### M5 — Historial, auditoría y reportes

| ID | Elemento | Prioridad | Historia de usuario | Criterio de aceptación | Estado |
|---|---|---|---|---|---|
| RF-05 | Registrar revisión humana *(también en M4, M6)* | Alta | HU-03 | Confirmar y descartar eventos de prueba; una cuenta sin permiso no puede validar; una observación deja pendiente el aviso. | Pendiente |
| RF-14 | Transmitir eventos y evidencia mínima *(también en M2)* | Alta | HU-06* | Interrumpir conexión y reenviar el mismo ID tres veces: queda un registro; sin flujo continuo de video crudo a la nube. | Pendiente |
| RF-16 | Registrar auditoría *(también en M6)* | Alta | - | Ejecutar una acción de cada tipo y contrastar el registro; un intento de edición ordinaria es rechazado; no guardar contraseñas ni video. | Pendiente |
| RF-17 | Aplicar retención de evidencias *(también en M6)* | Alta | - | Con plazo abreviado y reloj controlado, la evidencia vencida deja de ser accesible; la revisión conserva su referencia y constancia. | Pendiente |
| RNF-02 | Privacidad de captura y acceso *(también en M2, M6)* | Alta | HU-06 | Imágenes con marcas fuera de región no se conservan; enlace sin sesión o con rol inválido: acceso denegado; se usa HTTPS. | Pendiente |
| RNF-05 | Integridad de registros *(también en M1)* | Alta | HU-04* | Identificadores de evento únicos; escritura atómica de revisión con su auditoría; ningún registro referencia una sesión inexistente. | Pendiente |
| RNF-09 | Restricción tecnológica *(también en M2, M4, M6)* | Alta | - | Django para web; Django REST Framework para eventos; servicio local con OpenCV y YOLO; AWS S3 privado; scikit-learn para métricas. | Pendiente |
| RF-06 | Consultar historial | Media | HU-04 | Cada filtro y combinación devuelve solo coincidencias y muestra mensaje si no hay resultados. | Pendiente |
| RF-15 | Exportar registros y métricas | Media | - | Exportar una consulta conocida; filas y totales coinciden; tiempo de revisión = fecha de decisión menos fecha de aviso; pendientes sin tiempo inventado. | Pendiente |

### M6 — Seguridad y privacidad

| ID | Elemento | Prioridad | Historia de usuario | Criterio de aceptación | Estado |
|---|---|---|---|---|---|
| RF-05 | Registrar revisión humana *(también en M4, M5)* | Alta | HU-03 | Confirmar y descartar eventos de prueba; una cuenta sin permiso no puede validar; una observación deja pendiente el aviso. | Pendiente |
| RF-10 | Autenticar y cerrar acceso | Alta | HU-03*, HU-07* | Credenciales válidas abren sesión, inválidas no; tras cerrar no se consultan datos; verificar negativas por rol y ámbito. | Pendiente |
| RF-11 | Administrar cuentas y roles | Alta | - | Desactivar cuenta bloquea nuevos accesos; cambio de rol restringe la siguiente petición; TI y administrador sin permiso clínico no validan alertas. | Pendiente |
| RF-12 | Configurar reglas versionadas *(también en M3)* | Alta | - | Rechazar ventana no positiva y clase inexistente; aplicar regla válida a entradas de prueba; conservar versión en el evento. | Pendiente |
| RF-16 | Registrar auditoría *(también en M5)* | Alta | - | Ejecutar una acción de cada tipo y contrastar el registro; un intento de edición ordinaria es rechazado; no guardar contraseñas ni video. | Pendiente |
| RF-17 | Aplicar retención de evidencias *(también en M5)* | Alta | - | Con plazo abreviado y reloj controlado, la evidencia vencida deja de ser accesible; la revisión conserva su referencia y constancia. | Pendiente |
| RNF-02 | Privacidad de captura y acceso *(también en M2, M5)* | Alta | HU-06 | Imágenes con marcas fuera de región no se conservan; enlace sin sesión o con rol inválido: acceso denegado; se usa HTTPS. | Pendiente |
| RNF-04 | Protección de credenciales | Alta | HU-03*, HU-07* | Sin contraseñas legibles; hash de contraseñas del framework; secretos fuera del código y del repositorio. | Pendiente |
| RNF-09 | Restricción tecnológica *(también en M2, M4, M5)* | Alta | - | Django para web; Django REST Framework para eventos; servicio local con OpenCV y YOLO; AWS S3 privado; scikit-learn para métricas. | Pendiente |

## Historias de usuario de referencia

Los criterios Dado-Cuando-Entonces completos están en la Tarea 2.

| HU | Nombre | Prioridad | Módulos |
|---|---|---|---|
| HU-01 | Supervisar estaciones | Alta | M4 |
| HU-02 | Recibir avisos explicables | Alta | M3, M4 |
| HU-03 | Revisar alertas | Alta | M4, M5, M6 |
| HU-04 | Consultar el historial | Media | M5 |
| HU-05 | Distinguir las señales | Alta | M2 |
| HU-06 | Proteger la información | Alta | M2, M5, M6 |
| HU-07 | Acceder según el rol | Alta | M6 |
