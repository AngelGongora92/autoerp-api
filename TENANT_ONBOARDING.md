# 🏢 Requisitos y Datos Obligatorios para Nuevos Tenants (AutoERP)

Este documento describe la estructura y datos mínimos obligatorios que deben existir en la base de datos de AutoERP al registrar o aprovisionar una nueva empresa/taller (**Tenant**), para garantizar que ningún módulo (Citas, Empleados, Órdenes, Inventario, Login) arroje errores `HTTP 400`, `HTTP 500` o fallos de claves foráneas.

---

## 📌 Resumen de Dependencias Críticas

```
Company (Empresa)
  ├── User (Admin inicial) ──► user_permissions (Permisos del sistema)
  ├── Employee (⚠️ MÍNIMO 1 ASESOR con position_id = 1)
  ├── InventoryTypes & InventoryItems (Clonados de plantillas globales)
  └── CompanySettings (Configuración de horarios e intervalo de citas)
```

---

## 🗄️ 1. Entidades Obligatorias por Tenant

### 1.1. Empresa (`companies`)
Representa la entidad legal o taller.
* **Campos obligatorios:**
  * `name`: Nombre comercial o razón social.
  * `is_active`: `True` por defecto.
* **Genera:** `id` (`company_id`) requerido como clave foránea en todas las tablas multi-tenant.

### 1.2. Usuario Administrador Inicial (`users`)
Permite al propietario/administrador acceder a la plataforma.
* **Campos obligatorios:**
  * `supabase_uid`: Identificador UUID generado por Supabase Auth al crear la cuenta.
  * `username`: Correo electrónico o identificador único.
  * `company_id`: ID de la empresa creada.
  * `is_admin`: `True`.
  * `is_active`: `True`.
* **Permisos Obligatorios (`user_permissions`):**
  El usuario debe contar con los 7 permisos base del sistema vinculados a su `user_id`:
  * `view_dashboard`
  * `view_appointments`
  * `view_inventory`
  * `view_billing`
  * `view_conversations`
  * `view_employees`
  * `manage_users`

### 1.3. Empleado Asesor Inicial (`employees`) — ⚠️ CRÍTICO
* **Requisito:** Cada tenant **DEBE tener al menos un empleado activo con `position_id = 1` (Asesor)**.
* **¿Por qué es obligatorio?**
  * El módulo de citas (`/appointments/` y `/appointments/availability`) valida la disponibilidad y asigna asesores automáticamente (ej. algoritmo *least busy*).
  * Si un taller no tiene ningún empleado asesor registrado con `position_id = 1`, cualquier intento de agendar una cita fallará inmediatamente con:
    ```json
    HTTP 400 Bad Request: "No hay asesores disponibles en el horario seleccionado"
    ```
  * Además, en el Frontend el selector de asesor aparecerá vacío.
* **Campos mínimos:**
  * `first_name`: Nombre del asesor/administrador del taller.
  * `last_name`: Apellidos.
  * `company_id`: ID del tenant.
  * `position_id`: `1` (*Asesor* en catálogo `positions`).
  * `is_active`: `True`.

### 1.4. Inventario Inicial (`inventory_types` y `inventory_items`)
* Al registrar un nuevo tenant mediante `POST /users/register`, el backend clona automáticamente los tipos y categorías globales (`company_id IS NULL`) hacia el nuevo `company_id`.
* Si se aprovisiona manualmente por base de datos, deben clonarse estos registros asignándoles el nuevo `company_id`.

---

## 🌐 2. Catálogos Globales Prerrequisito (Tablas Compartidas)

Antes de aprovisionar un tenant, la base de datos de producción/desarrollo debe tener pobladas las siguientes tablas base:

| Catálogo | Registros Mínimos Requeridos | Propósito |
| :--- | :--- | :--- |
| **`positions`** | `id=1: Asesor`, `id=2: Tecnico` | Asignación de roles a empleados |
| **`permissions`** | 7 permisos (`view_dashboard`, `view_appointments`, etc.) | Control de accesos RBAC |
| **`appointment_status`**| `id=1: sin confirmar`, `id=2: confirmado`, `id=3: cancelado` | Ciclo de vida de citas |
| **`appointment_reasons`**| Al menos 1 registro activo (ej. `id=1: Mantenimiento`) | Motivos de agendamiento |
| **`op_status`** | Al menos 1 estado (ej. `id=1: Recibido` o `Pendiente`) | Estado operativo de órdenes |
| **`adm_status`** | Al menos 1 estado (ej. `id=1: En proceso`) | Estado administrativo de órdenes |
| **`priority`** | Al menos 1 prioridad (ej. `id=1: Media` o `Normal`) | Prioridad de órdenes |
| **`makes` / `models` / `colors`** | Catálogo básico de vehículos | Registro de autos de clientes |

---

## ⚙️ 3. Configuración y Horarios del Taller

### 3.1. Horarios de Trabajo (`CompanySettings` / Horario General)
* Por defecto, el sistema asume un horario laboral de **08:00 a 18:00** con slots basados en `appointment_interval_minutes` (por defecto 30 min) y `appointment_duration_minutes` (por defecto 30 min).
* `employee_schedule_blocks` y `schedule_overrides` son **opcionales**; sólo se usan para descansos (almuerzo) o ausencias programadas.

### 3.2. Integraciones Externas
* **`whatsapp_configs`**: Opcional. Sólo se requiere si el taller activa notificaciones automáticas por WhatsApp.

---

## 🚨 4. Diagnóstico de Errores Comunes de Onboarding

| Síntoma / Error HTTP | Causa Raíz | Solución |
| :--- | :--- | :--- |
| `HTTP 400: "No hay asesores disponibles..."` | El tenant no tiene ningún empleado con `position_id = 1` o todos están inactivos. | Crear un registro en `employees` con `company_id = <ID>`, `position_id = 1`, `is_active = True`. |
| Error `403 Forbidden` tras iniciar sesión | El usuario fue creado sin registros en `user_permissions`. | Ejecutar inserción en `user_permissions` asociando el `user_id` a los 7 permisos del sistema. |
| Fallo al crear una Orden de Trabajo | Faltan los estados predeterminados en `op_status`, `adm_status` o `priority`. | Verificar e insertar IDs requeridos en los catálogos globales de órdenes. |
| `UniqueViolation: Key (id)=(...) already exists` | Se insertaron registros manuales con ID fijo y la secuencia serial de Postgres quedó desfasada. | Ejecutar: `SELECT setval('<tabla>_id_seq', COALESCE((SELECT MAX(id) FROM <tabla>), 1));` |

---

## 📝 5. Script SQL de Onboarding Completo (Ejemplo de Referencia)

Si se necesita dar de alta un tenant manualmente en PostgreSQL:

```sql
BEGIN;

-- 1. Crear Empresa
INSERT INTO companies (name, is_active, created_at, updated_at)
VALUES ('Taller Ejemplo S.A.', true, NOW(), NOW())
RETURNING id; -- Supongamos que retorna company_id = 10

-- 2. Crear Usuario Administrador (supabase_uid viene de Supabase Auth)
INSERT INTO users (supabase_uid, username, company_id, is_admin, is_active, created_at, updated_at)
VALUES ('00000000-0000-0000-0000-000000000000', 'admin@tallerejemplo.com', 10, true, true, NOW(), NOW())
RETURNING id; -- Supongamos que retorna user_id = 25

-- 3. Asignar Permisos al Administrador
INSERT INTO user_permissions (user_id, permission_id)
SELECT 25, id FROM permissions;

-- 4. ⚠️ OBLIGATORIO: Crear al menos un Asesor (position_id = 1)
INSERT INTO employees (first_name, last_name, company_id, position_id, is_active, created_at, updated_at)
VALUES ('Asesor Principal', 'Taller', 10, 1, true, NOW(), NOW());

-- 5. Clonar Tipos de Inventario Base
INSERT INTO inventory_types (name, description, company_id, created_at, updated_at)
SELECT name, description, 10, NOW(), NOW()
FROM inventory_types
WHERE company_id IS NULL;

-- 6. Sincronizar secuencias
SELECT setval('companies_id_seq', COALESCE((SELECT MAX(id) FROM companies), 1));
SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1));
SELECT setval('employees_id_seq', COALESCE((SELECT MAX(id) FROM employees), 1));
SELECT setval('inventory_types_id_seq', COALESCE((SELECT MAX(id) FROM inventory_types), 1));

COMMIT;
```
