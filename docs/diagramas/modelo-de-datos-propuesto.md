# Modelo de datos propuesto — HemoVision Alert

*Versión 1.0 — PROPUESTA: no está implementado ni acordado por el equipo*

## Descripción

Propone las tablas que el prototipo y el backlog parecen necesitar y que todavía no existen en el código. Sirve de base para que el líder técnico y el Product Owner decidan el modelo definitivo. Lo que ya está programado se encuentra en `modelo-de-datos-actual.md`.

## Diagrama

```mermaid
erDiagram
    ESTACION ||--o{ CAMARA : "tiene"
    ESTACION ||--o{ SESION : "aloja"
    PACIENTE ||--o{ SESION : "tiene"
    SESION ||--o{ ALERTA : "genera"
    CAMARA ||--o{ ALERTA : "registra"
    ALERTA ||--o{ REVISION : "recibe"
    USUARIO ||--o{ REVISION : "realiza"

    PACIENTE {
        int id PK
        string codigo UK "ya existe"
    }
    SESION {
        int id PK
        int paciente_id FK "ya existe"
        int estacion_id FK "hoy es texto"
        string codigo_sesion "ej. S-2045, por decidir"
        datetime inicio "ya existe"
        datetime fin "ya existe"
    }
    ESTACION {
        int id PK
        string codigo UK "ej. EST-07"
        string sala "ej. Sala A"
        string estado "por definir"
    }
    CAMARA {
        int id PK
        string codigo UK "ej. CAM-07"
        int estacion_id FK
    }
    ALERTA {
        int id PK
        int sesion_id FK
        int camara_id FK
        datetime hora_evento
        string evento_detectado "ej. posible hemorragia"
        float confianza "ej. 94.2"
        string estado "por definir"
        string version_regla "RF-12"
    }
    REVISION {
        int id PK
        int alerta_id FK
        int usuario_id FK
        string decision "confirmar, descartar u observar"
        string observacion
        datetime hora_registro
    }
    USUARIO {
        int id PK
        string rol "por definir con M6"
    }
```

## De dónde sale cada entidad

| Entidad | Fuente | Qué muestra el prototipo |
|---|---|---|
| Estación | Prototipo y RF-09 | Código (EST-07), sala, estado: normal, en atención, crítica o sin señal |
| Cámara | Prototipo | "Cámara asociada: CAM-07" dentro del detalle de una estación |
| Alerta | Prototipo, RF-03 y RF-04 | Hora, evento detectado, confianza del algoritmo (94.2 %) |
| Revisión | Prototipo y RF-05 | Observación, quién registró, hora, estado "Revisada" |
| Usuario | RF-10 y RF-11 | Cuentas con roles, usuario "Dr. F. Aranda" |

## Qué no se incluye, a propósito

- **Datos personales del paciente** (nombre, edad, peso, diagnóstico). El prototipo los muestra, pero RF-07 pide un registro mínimo y dice "no exigir nombre".
- **Evidencia visual y su retención** (RF-14, RF-17), **auditoría** (RF-16) y **reglas versionadas** como tabla propia (RF-12). Todavía no hay información para modelarlas.

## Preguntas abiertas

1. ¿La estación pasa a ser una tabla propia? Hoy es un texto dentro de la sesión.
2. ¿Se guarda un código de sesión como "S-2045"? El modelo actual no lo tiene.
3. ¿Una alerta puede tener varias revisiones? RF-05 dice que una observación deja el aviso pendiente, lo que sugiere que sí.
4. ¿Qué estados tiene una alerta? El prototipo solo muestra "Revisada".
5. ¿El estado de una estación se guarda o se calcula a partir de sus alertas?
6. ¿Cómo se representan los roles de usuario? Depende del módulo de seguridad (M6).