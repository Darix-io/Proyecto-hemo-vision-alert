# Documentación de módulos — HemoVision Alert

*Versión 1.1 — refleja el código de la rama `develop` al 21 de octubre de 2026*

## 1. Resumen

Los requisitos (RF) y su asignación a módulos salen de `docs/backlog.md`. El estado describe lo que existe hoy en el código.

| Módulo | App | Requisitos | Estado |
|---|---|---|---|
| M1 Pacientes y sesiones | `pacientes` | RF-07, RF-08 | Implementado |
| M2 Captura y visión | No existe todavía | RF-01, RF-02, RF-13, RF-14, RF-18 | Pendiente |
| M3 Motor de riesgo y reglas | `riesgo` | RF-03, RF-04, RF-12 | Lógica y datos implementados, sin pantallas |
| M4 Dashboard de monitoreo | `monitoreo` | RF-04, RF-05, RF-09, RF-13 | Solo estructura base |
| M5 Historial | `historial` | RF-05, RF-06, RF-14, RF-15, RF-16, RF-17 | Solo estructura base |
| M6 Seguridad | `seguridad` | RF-05, RF-10, RF-11, RF-12, RF-16, RF-17 | Parcial: RF-10 implementado |

## 2. M1 Pacientes y sesiones (`pacientes`)

**Propósito:** registrar pacientes con los datos mínimos y gestionar sus sesiones de diálisis.

**Requisitos:** RF-07 (registrar paciente mínimo) y RF-08 (gestionar sesiones).

### Datos

| Tabla | Campos |
|---|---|
| Paciente | Código (único, máximo 30 caracteres) |
| Sesión | Paciente, estación (texto), inicio, fin |

### Pantallas

| Dirección | Función |
|---|---|
| `/pacientes/` | Lista de pacientes |
| `/pacientes/registrar/` | Registrar un paciente (solo el código) |
| `/pacientes/sesiones/` | Sesiones activas y cerradas |
| `/pacientes/sesiones/iniciar/` | Iniciar una sesión de diálisis |
| `/pacientes/sesiones/<id>/cerrar/` | Cerrar una sesión (solo desde su botón) |

### Reglas que el sistema aplica

| Regla | Requisito |
|---|---|
| El código del paciente es obligatorio y no se repite | RF-07 |
| No se exige el nombre del paciente | RF-07 |
| No se inicia una sesión en una estación ocupada | RF-08 |
| Un paciente no puede tener dos sesiones activas a la vez (decisión del Product Owner) | RF-08 |
| Cerrar una sesión guarda la hora de fin y no la borra | RF-08 |
| Un paciente con sesiones no se puede borrar, para conservar el vínculo histórico | RF-08 |
| Todas las pantallas exigen haber iniciado sesión | RF-10 |

### Pruebas

16 pruebas automáticas.

### Limitaciones y pendientes

- La estación es un texto libre: `EST-03` y `E-03` se tratan como estaciones distintas. Se resolverá con una tabla de estaciones cuando M4 lo requiera.
- "Detener captura al cierre" (RF-08) depende de M2, que todavía no existe.
- Los datos del paciente se limitan al código; el formulario del prototipo en Figma pide más datos que RF-07.

## 3. M2 Captura y visión

**Estado:** pendiente. No existe una app en el código.

**Requisitos:** RF-01 (capturar video de la sesión), RF-02 (detectar señales visuales), RF-13 (configurar captura y diagnosticar fallos), RF-14 (transmitir eventos y evidencia mínima) y RF-18 (evaluar estimaciones por video).

## 4. M3 Motor de riesgo y reglas (`riesgo`)

**Propósito:** clasificar eventos según reglas de riesgo y agruparlos en alertas.

**Requisitos:** RF-03 (clasificar y agrupar eventos), RF-04 (avisos explicables, la parte de datos) y RF-12 (reglas versionadas, la parte de datos).

**Estado:** lógica y datos implementados, trabajando con entradas sintéticas (datos de prueba). No tiene pantallas.

**Diseño:** `docs/diseno-m3.md`.

### Datos

| Tabla | Campos |
|---|---|
| Regla de riesgo | Clase de evento, umbral, ventana en segundos, versión, activa |
| Evento visual | Identificador único, sesión, cámara (opcional), clase, valor (opcional, de 0 a 100), hora, alerta |
| Alerta | Sesión, clase, estado, regla usada, fecha de creación y de actualización |

### Reglas que el sistema aplica

| Regla | Requisito |
|---|---|
| La ventana de una regla debe ser positiva y la clase de evento debe existir (hoy solo "hemorragia") | RF-12 |
| Una regla nueva es una versión nueva: la anterior se desactiva y no se borra | RF-12 |
| La alerta conserva la versión de la regla que usó | RF-12 |
| Un valor menor que el umbral da estado normal; igual o mayor, crítica (umbral de ejemplo: 90) | RF-03 |
| Repetir un evento con el mismo identificador no crea otra alerta | RF-03 |
| Los eventos de la misma sesión y clase dentro de la ventana (ejemplo: 60 segundos) comparten alerta | RF-03 |
| La alerta toma el estado más grave de sus eventos y no baja (propuesta por confirmar) | RF-03 |
| Un evento sin valor se guarda sin inventar nada y no genera alerta | RF-04 |
| Un evento sin regla activa se guarda sin alerta | RF-03 |

### Pruebas

16 pruebas automáticas.

### Limitaciones y pendientes

- No hay pantallas ni datos iniciales para crear reglas: sin una regla activa, los eventos se guardan sin alerta. Se resolverá con M4 y M6.
- El estado "atención" existe, pero todavía no se usa.
- El umbral (90) y la ventana (60 segundos) son valores de ejemplo confirmados por el Product Owner.
- Tres decisiones de diseño siguen por confirmar con el Product Owner: si un evento normal genera alerta, si la alerta toma el estado más grave y desde dónde se mide la ventana.
- Las pantallas de avisos (RF-04) corresponden a M4, y la configuración de reglas (RF-12) a M6.

## 5. M4 Dashboard de monitoreo (`monitoreo`)

**Estado:** solo estructura base.

**Requisitos pendientes:** RF-09 (supervisar estaciones), RF-04 (avisos explicables), RF-05 (registrar revisión humana) y RF-13 (configurar captura y diagnosticar fallos).

## 6. M5 Historial (`historial`)

**Estado:** solo estructura base.

**Requisitos pendientes:** RF-05, RF-06 (consultar historial), RF-14, RF-15 (exportar registros y métricas), RF-16 (registrar auditoría) y RF-17 (aplicar retención de evidencias).

## 7. M6 Seguridad (`seguridad`)

**Propósito:** controlar quién entra al sistema.

**Implementado (RF-10, autenticar y cerrar acceso):**

| Dirección | Función |
|---|---|
| `/login/` | Pantalla de inicio de sesión. Si las credenciales fallan, muestra "Credenciales incorrectas." |
| `/logout/` | Cierra la sesión (solo desde su botón) |

- Una cuenta inactiva no puede entrar.
- Tras iniciar sesión, el sistema lleva a la lista de pacientes.
- Tras cerrar sesión, no se pueden consultar datos.
- 5 pruebas automáticas.

**Pendiente:** RF-11 (administrar cuentas y roles), RF-12, RF-16, RF-17 y RF-05 (permisos de validación). Todavía no existen roles ni permisos por tipo de usuario.

## 8. Cómo ejecutar las pruebas

```bash
python manage.py test
```

Estado actual: 37 pruebas, todas correctas.
