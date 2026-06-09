# 🤖 Reglas y Directrices para Agentes de IA (agent_rules.md) - BACKEND API

Este archivo contiene las reglas obligatorias que todo agente de IA (como Antigravity, Cline, Roo Code, etc.) debe leer y cumplir estrictamente al trabajar en el proyecto Backend de la API.

---

## 📍 Identidad y Ruta del Proyecto (Backend)

*   **Nombre del Proyecto:** AutoERP API (Servicio Backend)
*   **Ruta Base Absoluta Local:** `/Users/rafipacheco/autoerp-api-run`
*   **Repositorio Remoto Git:** `AngelGongora92/autoerp-api`
*   **Validación de Ámbito:** Antes de realizar cualquier lectura, creación o modificación de archivos, el agente debe verificar que el archivo en cuestión se encuentre estrictamente dentro de la ruta base anterior. **PROHIBIDO** modificar código de otros proyectos (como portales de transparencia u otros frontends) que aparezcan abiertos en el contexto o workspaces activos del IDE.

---

## 📋 1. Flujo de Trabajo y Gestión de Tickets (Linear & Git)

Antes de modificar cualquier parte del código, el agente debe seguir obligatoriamente este ciclo de vida:

1. **Planificación y Creación del Ticket:**
   * Antes de realizar cualquier cambio, se debe asegurar la existencia de un ticket en Linear que represente la tarea, especificando claramente si corresponde al **FE (Frontend)** o **BE (Backend)**.
   * Se debe documentar el **Plan de Implementación** (ya sea en el ticket de Linear o en un archivo `implementation_plan.md` si es un feature complejo) antes de escribir código.

2. **Inicio del Desarrollo:**
   * Crear siempre una rama de Git descriptiva a partir del `main` actualizado (ej. `feature/AUT-XX-descripcion-corta` o `bugfix/AUT-XX-error`).
   * Cambiar el estado del ticket en Linear a **"In Progress"** (En Progreso).
   * **NUNCA** hacer commits directos ni pushes a `main`.

3. **Finalización del Trabajo y Revisión:**
   * Escribir commits claros y descriptivos siguiendo la convención de *Conventional Commits* (ej. `feat(employees): add delete endpoint...`).
   * Hacer push de la rama local al repositorio remoto en GitHub.
   * Cambiar el estado del ticket en Linear a **"In Review"** (En Revisión) para solicitar la revisión del usuario.
   * **NUNCA** realizar merges automáticos hacia `main` ni abrir Pull Requests autointegrables. El usuario revisará los cambios, hará el merge a `main` si todo está correcto y cerrará el ticket.

4. **Inicio de una Nueva Tarea y Limpieza:**
   * Cuando se solicite trabajar en una tarea nueva, el agente debe revisar las ramas locales y remotas creadas anteriormente.
   * Si la rama ya ha sido integrada en `main` (merge completado) y el ticket correspondiente está en estado **"Closed"** o **"Completed"**, el agente debe borrar esas ramas locales y remotas antiguas de forma segura para mantener limpio el repositorio.
   * Si el ticket previo aún no se ha cerrado o sigue en revisión, la rama debe dejarse intacta.

---

## 🗄️ 2. Base de Datos y Modelos (PostgreSQL + SQLAlchemy)

Para evitar pérdidas de integridad en datos históricos e inconsistencias de claves foráneas:

1. **Soft Deletes Obligatorios:**
   * **PROHIBIDO** realizar eliminaciones físicas (`DELETE` / `session.delete(obj)`) de registros con referencias o dependencias en el sistema (ej. Empleados, Clientes, Citas).
   * Se debe utilizar exclusivamente el borrado lógico (Soft Delete) cambiando el estado de visibilidad o activación, por ejemplo `is_active = False` o similar.

2. **Sincronización de Secuencias Seriales:**
   * Al insertar manualmente registros con IDs estáticos o predefinidos (como en scripts de siembra/seeds o pruebas de integración), es **obligatorio** reiniciar o actualizar la secuencia serial de Postgres asociada a esa tabla.
   * Utilizar la sentencia SQL:
     ```sql
     SELECT setval('nombre_tabla_id_seq', COALESCE((SELECT MAX(id) FROM nombre_tabla), 1));
     ```
     para prevenir errores de clave duplicada (`UniqueViolation`) en futuros inserts autoincrementales de producción o pruebas.

---

## ⚡ 3. Desarrollo de APIs y Enrutamiento (FastAPI)

1. **Orden de Rutas y Prevención de Colisiones:**
   * Al declarar endpoints en los routers de FastAPI, todas las rutas estáticas (ej. `/positions/`, `/me/`) deben definirse siempre **ANTES** de las rutas parametrizadas o dinámicas (ej. `/{employee_id}/`, `/{username}/`).
   * Esto previene que FastAPI intente interpretar una ruta estática como el valor de un parámetro dinámico e intente parsearlo incorrectamente (ej. interpretando `"positions"` como un ID entero).

2. **Tipado y Validación de Datos:**
   * Todo endpoint debe usar modelos de Pydantic para la validación estricta de las peticiones (`Schemas`) y respuestas.
   * Retornar respuestas explícitas con tipado estricto en la firma de la función utilizando `response_model` o tipado en FastAPI.

---

## 📑 4. Referencias y Parámetros del Proyecto

* **URL de la API de Linear:** `https://api.linear.app/graphql`
* **Tecnologías Core:** Python 3.10+, FastAPI, SQLAlchemy, Alembic, PostgreSQL.
