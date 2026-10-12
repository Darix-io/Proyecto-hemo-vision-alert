# Manual de flujo de trabajo — HemoVision Alert
*Versión 1.0 — 12 de octubre de 2026*

## 1. Propósito y alcance

Este manual explica cómo trabaja el equipo con Git y GitHub en el proyecto HemoVision Alert (materia Construcción de Software, UNEMI): cómo preparar el entorno, cómo realizar y subir una tarea, qué reglas se respetan y cómo resolver los problemas más frecuentes.

## 2. Roles del equipo

| Integrante | Rol |
|---|---|
| Ruben Dario Mora Jiménez | Product Owner y desarrollador |
| Josué Miguel Desiderio Delgado | Líder técnico y desarrollador |
| Deyvi Matheus Torres Morales | Desarrollador y calidad |
| Ruth Noemi Román Gamarra | Documentación |
| Bily Dilson Crespo Ayala | Documentación y diagramas |

## 3. Ramas del repositorio

| Rama | Uso |
|---|---|
| `master` | Versión estable. No se trabaja directo en ella. [Por definir con el líder técnico] |
| `develop` | Rama de integración. Recibe el trabajo ya revisado. |
| `feature/...` | Una tarea de código. Se crea desde `develop`. |
| `docs/...` | Una tarea de documentación. Se crea desde `develop`. |

## 4. Preparar el entorno (primera vez)

```bash
git clone https://github.com/Darix-io/Proyecto-hemo-vision-alert.git
cd Proyecto-hemo-vision-alert
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Cada integrante crea su propia base de datos local y su propio superusuario, porque el archivo `db.sqlite3` no se sube a GitHub.

- Si `python manage.py createsuperuser` se queda sin preguntar la contraseña, usar `winpty python manage.py createsuperuser`.
- El comando para activar el entorno virtual (`source .venv/Scripts/activate`) es el de Windows con Git Bash. En otros sistemas es distinto.


## 5. Flujo de una tarea

1. Actualizar: `git checkout develop` y `git pull origin develop`.
2. Si llegaron cambios de código: `python manage.py migrate`.
3. Crear la rama: `git checkout -b feature/nombre-de-la-tarea`.
4. Trabajar y revisar los cambios con `git status`.
5. Guardar: `git add <archivos>` y `git commit -m "feat: descripción"`.
6. Subir: `git push origin feature/nombre-de-la-tarea`.
7. Abrir el Pull Request en GitHub con **base `develop`** y a Josué como revisor.
8. Esperar la revisión. Si se piden cambios, corregir en la misma rama.

## 6. Convención de commits

| Prefijo | Uso |
|---|---|
| `feat:` | Función nueva |
| `fix:` | Corrección de un error |
| `docs:` | Documentación |
| `test:` | Pruebas |

## 7. Reglas del equipo

- Nadie trabaja directo en `master` ni en `develop`.
- Cada tarea tiene su propia rama, creada desde `develop`.
- Todo llega a `develop` por Pull Request, y la base debe decir `develop`.
- El líder técnico revisa y une los Pull Requests.
- Una tarea se considera terminada cuando está unida a `develop`, fue probada y su documentación está actualizada. (propuesta, por confirmar)

## 8. Problemas frecuentes

| Problema | Causa | Solución |
|---|---|---|
| El Pull Request se abre hacia `master` | GitHub propone `master` por defecto | Cambiar la base a `develop` antes de crearlo |
| `no such table: ...` al abrir una página | La base `db.sqlite3` es local y no se sube | `python manage.py migrate` |
| `Your local changes would be overwritten` al hacer `git pull` | Hay cambios sin guardar en un archivo que también cambió en GitHub | Revisar con `git diff` y decidir si descartar o guardar |
| El admin de Django no deja entrar | La base nueva no tiene usuarios | `python manage.py createsuperuser` |
| Pantalla que termina en `(END)` | Es el visor de Git | Pulsar `q` |
| Un Pull Request se unió a la rama equivocada | Se dejó `master` como base | Avisar al líder técnico antes de hacer nada. Revertir deshace todo el Pull Request, no solo una parte; para volver a subir el trabajo se usa `git cherry-pick` desde una rama nueva |
| Una app desaparece de `INSTALLED_APPS` | Se editó la lista de `settings.py` y se borró una línea sin querer | Revisar el cambio con `git diff` antes del commit (ver sección 9) |


## 9. Lista de verificación antes de abrir un Pull Request

1. `python manage.py check` no muestra errores.
2. `python manage.py test` pasa todas las pruebas.
3. Después de `git fetch origin`, `git --no-pager diff --stat origin/develop` muestra solo los archivos de la tarea.
4. Si se editó `config/settings.py`, revisar con `git --no-pager diff origin/develop -- config/settings.py` que no desapareció ninguna app de `INSTALLED_APPS`.
5. La base del Pull Request dice `develop`.