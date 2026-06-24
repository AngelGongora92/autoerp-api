# AutoERP — Architecture: Database & API Design

## Diseño de la Base de Datos (PostgreSQL)

Todas las tablas gestionadas por **Alembic** (migraciones versionadas). El ORM es SQLAlchemy 2.x en modo `declarative_base`.

---

### Diagrama de Relaciones (ERD simplificado)

```
companies
  ├── users (company_id → SET NULL)
  ├── customers (company_id → SET NULL)
  ├── employees (company_id → SET NULL)
  ├── vehicles (company_id → SET NULL)
  ├── orders (company_id → SET NULL)
  ├── appointments (company_id → SET NULL)
  └── whatsapp_configs (company_id → CASCADE, UNIQUE)
        └── whatsapp_conversations (company_id → CASCADE)
              └── whatsapp_messages (conversation_id → CASCADE)

users ──── user_permissions (M:M) ──── permissions
users ──── employees (employee_id, opcional)

customers
  ├── contacts (customer_id → CASCADE)
  └── vehicles (customer_id → SET NULL)

employees ──── positions (position_id)
employees ──── employee_schedule_blocks (CASCADE)
employees ──── schedule_overrides (CASCADE)

orders
  ├── customers (customer_id → SET NULL)
  ├── contacts (contact_id → SET NULL)
  ├── vehicles (vehicle_id)
  ├── employees [advisor] (advisor_id → SET NULL)
  ├── employees [mechanic] (mechanic_id → SET NULL)
  ├── op_status (op_status_id)
  ├── adm_status (adm_status_id)
  ├── priority (priority_id)
  ├── order_extra_info (CASCADE) ──── order_extra_items
  ├── bodywork_details (CASCADE) ──── bodywork_detail_types
  └── order_inventory_data (CASCADE) ──── inventory_items ──── inventory_types

vehicles
  ├── models ──── makes
  ├── colors
  ├── motors
  ├── transmissions
  └── vehicle_types

appointments
  ├── customers (customer_id → SET NULL)
  ├── contacts (contact_id → SET NULL)
  ├── vehicles (vehicle_id → SET NULL)
  ├── employees [scheduled_by] (→ SET NULL)
  ├── employees [assigned_to] (→ SET NULL)
  ├── appointment_status (status_id)
  └── appointment_reasons_link (M:M) ──── appointment_reasons
```

---

## Catálogo de Tablas

### `companies`
| Columna      | Tipo                       | Restricciones        |
|--------------|----------------------------|----------------------|
| company_id   | INTEGER                    | PK                   |
| name         | VARCHAR(128)               | NOT NULL             |
| created_at   | TIMESTAMP WITH TIME ZONE   | NOT NULL, default now|
| is_active    | BOOLEAN                    | default TRUE         |

---

### `users`
| Columna      | Tipo         | Restricciones                              |
|--------------|--------------|--------------------------------------------|
| user_id      | INTEGER      | PK                                         |
| username     | VARCHAR(64)  | UNIQUE, NOT NULL                           |
| password     | VARCHAR(200) | nullable (hash bcrypt)                     |
| is_admin     | BOOLEAN      | default FALSE                              |
| is_employee  | BOOLEAN      | default FALSE                              |
| is_active    | BOOLEAN      | default TRUE                               |
| company_id   | INTEGER      | FK → companies, SET NULL                   |
| supabase_uid | VARCHAR(64)  | UNIQUE, nullable, INDEX                    |
| employee_id  | INTEGER      | FK → employees, SET NULL, nullable         |

**Relaciones**: M:M con `permissions` (tabla puente `user_permissions`); 1:1 con `Employee` (backref).

---

### `permissions`
| Columna       | Tipo         | Restricciones    |
|---------------|--------------|------------------|
| permission_id | INTEGER      | PK               |
| name          | VARCHAR(80)  | UNIQUE, NOT NULL |
| description   | VARCHAR(200) | nullable         |

---

### `user_permissions` *(tabla de asociación M:M)*
| Columna       | Tipo    | Restricciones              |
|---------------|---------|----------------------------|
| user_id       | INTEGER | PK, FK → users (CASCADE)   |
| permission_id | INTEGER | PK, FK → permissions       |

---

### `customers`
| Columna     | Tipo         | Restricciones           |
|-------------|--------------|-------------------------|
| customer_id | INTEGER      | PK                      |
| is_company  | BOOLEAN      | default FALSE           |
| cname       | VARCHAR(64)  | nullable (razón social) |
| fname       | VARCHAR(64)  | nullable                |
| lname       | VARCHAR(64)  | nullable                |
| address1    | VARCHAR(128) | nullable                |
| address2    | VARCHAR(128) | nullable                |
| email       | VARCHAR(128) | NOT NULL                |
| phone       | VARCHAR(32)  | nullable                |
| is_active   | BOOLEAN      | default TRUE            |
| company_id  | INTEGER      | FK → companies, SET NULL|

**Relaciones**: 1:N con `orders`, `contacts`, `vehicles`.

---

### `contacts`
| Columna    | Tipo         | Restricciones                    |
|------------|--------------|----------------------------------|
| contact_id | INTEGER      | PK                               |
| customer_id| INTEGER      | FK → customers (CASCADE), NOT NULL|
| fname      | VARCHAR(64)  | nullable                         |
| lname      | VARCHAR(64)  | nullable                         |
| email      | VARCHAR(128) | NOT NULL                         |
| phone      | VARCHAR(32)  | nullable                         |

---

### `positions`
| Columna     | Tipo         | Restricciones    |
|-------------|--------------|------------------|
| position_id | INTEGER      | PK               |
| title       | VARCHAR(64)  | UNIQUE, NOT NULL |
| description | VARCHAR(200) | nullable         |

---

### `employees`
| Columna     | Tipo         | Restricciones            |
|-------------|--------------|--------------------------|
| employee_id | INTEGER      | PK                       |
| fname       | VARCHAR(64)  | NOT NULL                 |
| lname1      | VARCHAR(64)  | NOT NULL                 |
| lname2      | VARCHAR(64)  | nullable                 |
| email       | VARCHAR(128) | NOT NULL                 |
| phone       | VARCHAR(32)  | nullable                 |
| position_id | INTEGER      | FK → positions           |
| is_active   | BOOLEAN      | default TRUE             |
| company_id  | INTEGER      | FK → companies, SET NULL |

---

### Catálogos de Vehículos

#### `makes`
| Columna | Tipo        | Restricciones    |
|---------|-------------|------------------|
| make_id | INTEGER     | PK               |
| make    | VARCHAR(64) | UNIQUE, NOT NULL |

#### `models`
| Columna  | Tipo        | Restricciones          |
|----------|-------------|------------------------|
| model_id | INTEGER     | PK                     |
| make_id  | INTEGER     | FK → makes, NOT NULL   |
| model    | VARCHAR(64) | NOT NULL               |

#### `colors`
| Columna  | Tipo        | Restricciones    |
|----------|-------------|------------------|
| color_id | INTEGER     | PK               |
| color    | VARCHAR(64) | UNIQUE, NOT NULL |

#### `motors`
| Columna  | Tipo        | Restricciones |
|----------|-------------|---------------|
| motor_id | INTEGER     | PK            |
| type     | VARCHAR(64) | NOT NULL      |

#### `vehicle_types`
| Columna   | Tipo        | Restricciones    |
|-----------|-------------|------------------|
| v_type_id | INTEGER     | PK               |
| type      | VARCHAR(64) | UNIQUE, NOT NULL |

#### `transmissions`
| Columna          | Tipo        | Restricciones    |
|------------------|-------------|------------------|
| transmission_id  | INTEGER     | PK               |
| type             | VARCHAR(64) | UNIQUE, NOT NULL |

---

### `vehicles`
| Columna         | Tipo        | Restricciones                         |
|-----------------|-------------|---------------------------------------|
| vehicle_id      | INTEGER     | PK                                    |
| customer_id     | INTEGER     | FK → customers, SET NULL              |
| vin             | VARCHAR(32) | UNIQUE, NOT NULL                      |
| plate           | VARCHAR(32) | UNIQUE, nullable                      |
| year            | INTEGER     | NOT NULL                              |
| model_id        | INTEGER     | FK → models, NOT NULL                 |
| mileage         | INTEGER     | NOT NULL                              |
| color_id        | INTEGER     | FK → colors, NOT NULL                 |
| motor_id        | INTEGER     | FK → motors, NOT NULL                 |
| transmission_id | INTEGER     | FK → transmissions, NOT NULL          |
| cylinders       | INTEGER     | NOT NULL                              |
| liters          | VARCHAR(16) | NOT NULL (ej: "2.0")                  |
| v_type_id       | INTEGER     | FK → vehicle_types, NOT NULL          |
| company_id      | INTEGER     | FK → companies, SET NULL              |

---

### `orders`
| Columna        | Tipo                     | Restricciones             |
|----------------|--------------------------|---------------------------|
| order_id       | INTEGER                  | PK                        |
| c_order_id     | VARCHAR(32)              | UNIQUE, NOT NULL          |
| order_date     | TIMESTAMP WITH TIME ZONE | NOT NULL, default now     |
| advisor_id     | INTEGER                  | FK → employees, SET NULL  |
| mechanic_id    | INTEGER                  | FK → employees, SET NULL  |
| customer_id    | INTEGER                  | FK → customers, SET NULL  |
| contact_id     | INTEGER                  | FK → contacts, SET NULL   |
| vehicle_id     | INTEGER                  | FK → vehicles             |
| company_id     | INTEGER                  | FK → companies, SET NULL  |
| op_status_id   | INTEGER                  | FK → op_status            |
| adm_status_id  | INTEGER                  | FK → adm_status           |
| priority_id    | INTEGER                  | FK → priority             |
| p_mileage      | INTEGER                  | nullable                  |
| c_mileage      | INTEGER                  | nullable                  |
| service_bay    | VARCHAR(16)              | nullable                  |
| fuel_level     | INTEGER                  | nullable (ej. 1–8)        |
| has_extra_info | BOOLEAN                  | default FALSE             |

#### Tablas de Catálogo de Orden

**`op_status`**: Estado operativo (ej: En progreso, Finalizado).  
**`adm_status`**: Estado administrativo (ej: Aprobado, Pendiente).  
**`priority`**: Nivel de prioridad (ej: Baja, Media, Alta).

---

### `order_extra_items`
| Columna     | Tipo         | Restricciones |
|-------------|--------------|---------------|
| item_id     | INTEGER      | PK            |
| title       | VARCHAR(128) | NOT NULL      |
| description | VARCHAR(256) | nullable      |

### `order_extra_info` *(PK compuesta)*
| Columna  | Tipo         | Restricciones                     |
|----------|--------------|-----------------------------------|
| order_id | INTEGER      | PK, FK → orders                   |
| item_id  | INTEGER      | PK, FK → order_extra_items        |
| info     | VARCHAR(256) | nullable                          |

---

### `bodywork_detail_types`
| Columna       | Tipo         | Restricciones    |
|---------------|--------------|------------------|
| detail_type_id| INTEGER      | PK               |
| type          | VARCHAR(128) | UNIQUE, NOT NULL |
| color         | VARCHAR(32)  | nullable (hex)   |

### `bodywork_details`
| Columna       | Tipo         | Restricciones                                         |
|---------------|--------------|-------------------------------------------------------|
| detail_id     | INTEGER      | PK                                                    |
| order_id      | INTEGER      | FK → orders (CASCADE), NOT NULL                       |
| view          | ENUM         | `front`, `back`, `left`, `right`, `up` (NOT NULL)    |
| detail_type_id| INTEGER      | FK → bodywork_detail_types                            |
| coordinates   | JSONB        | nullable — `{"x": float, "y": float}`                 |
| detail_notes  | VARCHAR(256) | nullable                                              |
| picture_path  | VARCHAR(256) | nullable                                              |

---

### `inventory_types`
| Columna       | Tipo         | Restricciones        |
|---------------|--------------|----------------------|
| inv_type_id   | INTEGER      | PK                   |
| name          | VARCHAR(255) | NOT NULL             |
| component_key | VARCHAR(100) | NOT NULL             |
| is_active     | BOOLEAN      | NOT NULL, default TRUE|
| position      | INTEGER      | NOT NULL, default 0  |
| picture_path  | VARCHAR(512) | nullable             |

### `inventory_items`
| Columna        | Tipo         | Restricciones                    |
|----------------|--------------|----------------------------------|
| item_id        | INTEGER      | PK                               |
| inv_type_id    | INTEGER      | FK → inventory_types, NOT NULL   |
| label          | VARCHAR(255) | NOT NULL                         |
| input_type     | VARCHAR(50)  | NOT NULL (ej: "text", "checkbox")|
| position       | INTEGER      | NOT NULL, default 0              |
| description    | TEXT         | nullable                         |
| picture_upload | BOOLEAN      | NOT NULL, default FALSE          |
| is_mandatory   | BOOLEAN      | NOT NULL, default FALSE          |

### `order_inventory_data`
| Columna  | Tipo    | Restricciones                                      |
|----------|---------|----------------------------------------------------|
| data_id  | INTEGER | PK                                                 |
| order_id | INTEGER | FK → orders (CASCADE), NOT NULL, INDEX             |
| item_id  | INTEGER | FK → inventory_items (CASCADE), NOT NULL, INDEX    |
| data     | JSONB   | nullable — valor flexible del ítem                 |

**Restricción única**: `(order_id, item_id)` — `_order_item_uc`

---

### `appointments`
| Columna            | Tipo                     | Restricciones                 |
|--------------------|--------------------------|-------------------------------|
| appointment_id     | INTEGER                  | PK                            |
| customer_id        | INTEGER                  | FK → customers, SET NULL      |
| contact_id         | INTEGER                  | FK → contacts, SET NULL       |
| vehicle_id         | INTEGER                  | FK → vehicles, SET NULL       |
| scheduled_by       | INTEGER                  | FK → employees, SET NULL      |
| assigned_to        | INTEGER                  | FK → employees, SET NULL      |
| appointment_date   | TIMESTAMP WITH TIME ZONE | NOT NULL, INDEX               |
| status_id          | INTEGER                  | FK → appointment_status       |
| notes              | VARCHAR(256)             | nullable                      |
| rescheduled_count  | INTEGER                  | default 0                     |
| company_id         | INTEGER                  | FK → companies, SET NULL      |
| temp_cname         | VARCHAR(64)              | nullable (cliente temporal)   |
| temp_fname         | VARCHAR(64)              | nullable                      |
| temp_lname         | VARCHAR(64)              | nullable                      |
| temp_email         | VARCHAR(128)             | nullable                      |
| temp_phone         | VARCHAR(32)              | nullable                      |
| temp_vehicle_data  | JSONB                    | nullable                      |

### `appointment_status`
| Columna   | Tipo        | Restricciones    |
|-----------|-------------|------------------|
| status_id | INTEGER     | PK               |
| status    | VARCHAR(64) | UNIQUE, NOT NULL |

*Convención de IDs: 1=Pendiente, 2=Confirmado, 3=Cancelado*

### `appointment_reasons`
| Columna          | Tipo         | Restricciones    |
|------------------|--------------|------------------|
| reason_id        | INTEGER      | PK               |
| reason           | VARCHAR(128) | UNIQUE, NOT NULL |
| duration_minutes | INTEGER      | NOT NULL, default 60 |

### `appointment_reasons_link` *(M:M)*
| Columna        | Tipo    | Restricciones                              |
|----------------|---------|--------------------------------------------|
| appointment_id | INTEGER | PK, FK → appointments (CASCADE)            |
| reason_id      | INTEGER | PK, FK → appointment_reasons              |

---

### `employee_schedule_blocks`
| Columna     | Tipo    | Restricciones                     |
|-------------|---------|-----------------------------------|
| block_id    | INTEGER | PK                                |
| employee_id | INTEGER | FK → employees (CASCADE), NOT NULL|
| day_of_week | INTEGER | NOT NULL (0=Lun … 6=Dom)          |
| start_time  | TIME    | NOT NULL                          |
| end_time    | TIME    | NOT NULL                          |

### `schedule_overrides`
| Columna       | Tipo    | Restricciones                     |
|---------------|---------|-----------------------------------|
| override_id   | INTEGER | PK                                |
| employee_id   | INTEGER | FK → employees (CASCADE), NOT NULL|
| override_date | DATE    | NOT NULL                          |
| is_available  | BOOLEAN | NOT NULL                          |
| start_time    | TIME    | nullable                          |
| end_time      | TIME    | nullable                          |
| reason        | VARCHAR(256) | nullable                     |

---

### `company_settings`
| Columna               | Tipo         | Restricciones        |
|-----------------------|--------------|----------------------|
| id                    | INTEGER      | PK, default 1        |
| company_name          | VARCHAR(128) | default "Mi Taller"  |
| address               | VARCHAR(256) | nullable             |
| phone                 | VARCHAR(32)  | nullable             |
| email                 | VARCHAR(128) | nullable             |
| website               | VARCHAR(128) | nullable             |
| tax_id                | VARCHAR(64)  | nullable             |
| business_hours_start  | TIME         | nullable             |
| business_hours_end    | TIME         | nullable             |
| info                  | TEXT         | nullable             |

---

### `whatsapp_configs`
| Columna         | Tipo         | Restricciones                         |
|-----------------|--------------|---------------------------------------|
| config_id       | INTEGER      | PK                                    |
| company_id      | INTEGER      | FK → companies (CASCADE), UNIQUE      |
| phone_number_id | VARCHAR(64)  | UNIQUE, NOT NULL                      |
| waba_id         | VARCHAR(64)  | NOT NULL                              |
| access_token    | VARCHAR(512) | NOT NULL                              |
| phone_number    | VARCHAR(32)  | nullable                              |
| is_active       | BOOLEAN      | default TRUE                          |

### `whatsapp_conversations`
| Columna        | Tipo                     | Restricciones                  |
|----------------|--------------------------|--------------------------------|
| conversation_id| INTEGER                  | PK                             |
| company_id     | INTEGER                  | FK → companies (CASCADE)       |
| customer_phone | VARCHAR(32)              | NOT NULL                       |
| customer_name  | VARCHAR(128)             | nullable                       |
| last_message_at| TIMESTAMP WITH TIME ZONE | NOT NULL, default now          |
| created_at     | TIMESTAMP WITH TIME ZONE | NOT NULL, default now          |

**Restricción única**: `(company_id, customer_phone)` — `_company_customer_phone_uc`

### `whatsapp_messages`
| Columna              | Tipo                     | Restricciones                           |
|----------------------|--------------------------|-----------------------------------------|
| message_id           | INTEGER                  | PK                                      |
| conversation_id      | INTEGER                  | FK → whatsapp_conversations (CASCADE)   |
| whatsapp_message_id  | VARCHAR(128)             | UNIQUE, nullable                        |
| direction            | VARCHAR(16)              | NOT NULL — `inbound` / `outbound`       |
| type                 | VARCHAR(16)              | NOT NULL — `text`, `image`, `document`, `system` |
| body                 | VARCHAR(1024)            | nullable                                |
| media_url            | VARCHAR(512)             | nullable                                |
| status               | VARCHAR(16)              | NOT NULL — `sent`, `delivered`, `read`, `failed` |
| created_at           | TIMESTAMP WITH TIME ZONE | NOT NULL, default now                   |

---

## Diseño de la API REST

### Convenciones Generales

| Aspecto            | Convención                                                          |
|--------------------|---------------------------------------------------------------------|
| Base URL local     | `http://127.0.0.1:8000`                                             |
| Base URL producción| `https://autoerp-be.vercel.app` (o dominio configurado en Vercel)  |
| Formato            | JSON (`Content-Type: application/json`)                             |
| Autenticación      | `Authorization: Bearer <JWT_Supabase>` en endpoints protegidos      |
| Multi-tenancy      | Filtrado automático por `company_id` del usuario autenticado        |
| Paginación         | No implementada (listas retornan todos los elementos del tenant)    |
| Documentación      | Swagger UI en `/docs`, ReDoc en `/redoc`                            |

---

### Routers y Endpoints

#### `/auth` — Autenticación
| Método | Ruta          | Auth | Descripción                              |
|--------|---------------|------|------------------------------------------|
| POST   | `/auth/login` | ❌   | Login con username/password. Retorna permisos. |

**Response `POST /auth/login`**:
```json
{
  "message": "¡Inicio de sesión exitoso!",
  "permissions": ["admin", "ventas"]
}
```

---

#### `/users` — Usuarios
| Método | Ruta            | Auth | Descripción              |
|--------|-----------------|------|--------------------------|
| GET    | `/users/`       | ✅   | Lista usuarios           |
| POST   | `/users/`       | ✅   | Crea usuario             |
| GET    | `/users/{id}`   | ✅   | Obtiene usuario por ID   |
| PATCH  | `/users/{id}`   | ✅   | Actualiza usuario        |
| DELETE | `/users/{id}`   | ✅   | Elimina usuario          |

---

#### `/customers` — Clientes
| Método | Ruta                | Auth | Descripción              |
|--------|---------------------|------|--------------------------|
| GET    | `/customers/`       | ✅   | Lista clientes del tenant|
| POST   | `/customers/`       | ✅   | Crea cliente             |
| GET    | `/customers/{id}`   | ✅   | Obtiene cliente por ID   |
| PATCH  | `/customers/{id}`   | ✅   | Actualiza cliente        |
| DELETE | `/customers/{id}`   | ✅   | Desactiva cliente        |

---

#### `/contacts` — Contactos
| Método | Ruta              | Auth | Descripción           |
|--------|-------------------|------|-----------------------|
| POST   | `/contacts/`      | ✅   | Crea contacto         |
| GET    | `/contacts/{id}`  | ✅   | Obtiene contacto      |
| PATCH  | `/contacts/{id}`  | ✅   | Actualiza contacto    |
| DELETE | `/contacts/{id}`  | ✅   | Elimina contacto      |

---

#### `/employees` — Empleados
| Método | Ruta                    | Auth | Descripción             |
|--------|-------------------------|------|-------------------------|
| GET    | `/employees/`           | ✅   | Lista empleados         |
| POST   | `/employees/`           | ✅   | Crea empleado           |
| GET    | `/employees/{id}`       | ✅   | Obtiene empleado        |
| PATCH  | `/employees/{id}`       | ✅   | Actualiza empleado      |
| GET    | `/employees/positions/` | ✅   | Lista posiciones/cargos |

---

#### `/vehicles` — Vehículos
| Método | Ruta                        | Auth | Descripción              |
|--------|-----------------------------|------|--------------------------|
| GET    | `/vehicles/`                | ✅   | Lista vehículos          |
| POST   | `/vehicles/`                | ✅   | Crea vehículo            |
| GET    | `/vehicles/{id}`            | ✅   | Obtiene vehículo         |
| PATCH  | `/vehicles/{id}`            | ✅   | Actualiza vehículo       |
| GET    | `/vehicles/makes/`          | ✅   | Lista marcas             |
| GET    | `/vehicles/models/{make_id}`| ✅   | Modelos por marca        |
| GET    | `/vehicles/colors/`         | ✅   | Lista colores            |
| GET    | `/vehicles/motors/`         | ✅   | Lista tipos de motor     |
| GET    | `/vehicles/transmissions/`  | ✅   | Lista transmisiones      |
| GET    | `/vehicles/types/`          | ✅   | Lista tipos de vehículo  |

---

#### `/orders` — Órdenes de Servicio
| Método | Ruta                                          | Auth | Descripción                                |
|--------|-----------------------------------------------|------|--------------------------------------------|
| POST   | `/orders/`                                    | ✅   | Crea orden                                 |
| GET    | `/orders/`                                    | ✅   | Lista órdenes del tenant                   |
| GET    | `/orders/{id}`                                | ✅   | Obtiene orden por ID                       |
| PATCH  | `/orders/{id}`                                | ✅   | Actualiza orden (parcial)                  |
| GET    | `/orders/customId/{c_order_id}`               | ✅   | Obtiene orden por ID personalizado         |
| GET    | `/orders/order-exists/{c_order_id}`           | ✅   | Verifica si existe una orden               |
| GET    | `/orders/last-order-id/`                      | ✅   | Obtiene el último `c_order_id`             |
| GET    | `/orders/extra-items/`                        | ❌   | Lista ítems extra configurables            |
| GET    | `/orders/extra-info/{order_id}`               | ❌   | Extra-info de una orden                    |
| POST   | `/orders/extra-info/`                         | ❌   | Upsert de extra-info (lista)               |
| GET    | `/orders/bodywork-detail-types/`              | ❌   | Lista tipos de daño de carrocería          |
| POST   | `/orders/bodywork-detail-types/`              | ❌   | Crea tipo de daño                          |
| PATCH  | `/orders/bodywork-detail-types/{id}`          | ❌   | Actualiza tipo de daño                     |
| GET    | `/orders/bodywork-details/{order_id}`         | ❌   | Detalles de carrocería de una orden        |
| POST   | `/orders/bodywork-details/`                   | ❌   | Crea detalles de carrocería (lista)        |
| PATCH  | `/orders/bodywork-details/{id}`               | ❌   | Actualiza detalle de carrocería            |
| DELETE | `/orders/bodywork-details/{id}`               | ❌   | Elimina detalle de carrocería              |
| GET    | `/orders/inventory-types/`                    | ❌   | Lista tipos de inventario                  |
| POST   | `/orders/inventory-types/`                    | ❌   | Crea tipo de inventario                    |
| PATCH  | `/orders/inventory-types/{id}`                | ❌   | Actualiza tipo de inventario               |
| PUT    | `/orders/inventory-types/reorder`             | ❌   | Reordena tipos de inventario (atómico)     |
| GET    | `/orders/inventory-items/{inv_type_id}`       | ❌   | Ítems de un tipo de inventario             |
| POST   | `/orders/inventory-items/`                    | ❌   | Crea ítem de inventario                    |
| PATCH  | `/orders/inventory-items/`                    | ❌   | Actualiza múltiples ítems (lista)          |
| PUT    | `/orders/inventory-items/reorder`             | ❌   | Reordena ítems de inventario               |
| POST   | `/orders/inventory-data/`                     | ❌   | Upsert datos de inventario por orden       |
| GET    | `/orders/inventory-data/{order_id}/{type_id}` | ❌   | Datos de inventario por orden y tipo       |

---

#### `/appointments` — Citas
| Método | Ruta                                      | Auth | Descripción                               |
|--------|-------------------------------------------|------|-------------------------------------------|
| GET    | `/appointments/`                          | ✅   | Lista citas del tenant (filtro por asignado)|
| POST   | `/appointments/new-appointment/`          | ✅   | Crea cita + notificaciones opcionales     |
| GET    | `/appointments/reasons/`                  | ❌   | Lista razones de cita                     |
| GET    | `/appointments/public/{id}`               | ❌   | Detalles públicos de la cita              |
| POST   | `/appointments/public/{id}/confirm`       | ❌   | Confirmación pública de la cita           |
| POST   | `/appointments/public/{id}/cancel`        | ❌   | Cancelación pública de la cita            |
| PATCH  | `/appointments/{id}/reschedule`           | ✅   | Reprogramar cita                          |
| PATCH  | `/appointments/{id}/cancel`               | ✅   | Cancelar cita (panel interno)             |
| POST   | `/appointments/{id}/resend-confirmation`  | ✅   | Reenviar notificación de confirmación     |

---

#### `/schedules` — Horarios de Empleados
| Método | Ruta                           | Auth | Descripción                          |
|--------|--------------------------------|------|--------------------------------------|
| POST   | `/schedules/blocks/`           | ❌   | Crea bloque semanal recurrente       |
| GET    | `/schedules/blocks/{emp_id}`   | ❌   | Horario semanal de un empleado       |
| DELETE | `/schedules/blocks/{id}`       | ❌   | Elimina bloque de horario            |
| POST   | `/schedules/overrides/`        | ❌   | Crea excepción de horario            |
| GET    | `/schedules/overrides/{emp_id}`| ❌   | Excepciones de horario de un empleado|

---

#### `/whatsapp` — Integración WhatsApp Business
| Método | Ruta                                         | Auth | Descripción                            |
|--------|----------------------------------------------|------|----------------------------------------|
| GET    | `/whatsapp/webhook`                          | ❌   | Verificación del webhook con Meta      |
| POST   | `/whatsapp/webhook`                          | ❌   | Recepción de mensajes/estados de Meta  |
| POST   | `/whatsapp/embedded-signup/callback`         | ❌   | Intercambio de código OAuth → token    |
| GET    | `/whatsapp/conversations`                    | ❌   | Lista conversaciones por company_id    |
| POST   | `/whatsapp/conversations/{id}/send`          | ❌   | Envía mensaje saliente                 |
| GET    | `/whatsapp/conversations/{id}/messages`      | ❌   | Historial de mensajes de conversación  |

---

#### `/ws` — WebSocket
| Protocolo | Ruta                     | Descripción                                     |
|-----------|--------------------------|-------------------------------------------------|
| WS        | `/ws/chat/{company_id}`  | Canal push en tiempo real por taller            |

**Eventos WebSocket emitidos por el servidor**:
```json
// Nuevo mensaje entrante/saliente
{ "event": "new_message", "data": { "message_id": 1, "conversation_id": 5, "direction": "inbound", "body": "Hola" ... } }

// Actualización de estado de mensaje
{ "event": "message_status", "data": { "whatsapp_message_id": "wamid.xxx", "status": "read", "conversation_id": 5 } }
```

---

## Patrón de Respuesta de la API

### Respuesta Exitosa (2xx)
```json
// Objeto individual
{
  "order_id": 42,
  "c_order_id": "ORD-2026-001",
  "order_date": "2026-06-19T18:00:00Z",
  ...
}

// Lista
[
  { "customer_id": 1, "fname": "Juan", ... },
  { "customer_id": 2, "fname": "María", ... }
]
```

### Respuesta de Error (4xx / 5xx)
```json
{
  "detail": "Descripción del error en texto legible"
}
```

### Códigos HTTP Utilizados
| Código | Significado                        |
|--------|------------------------------------|
| 200    | OK — GET, PATCH exitoso            |
| 201    | Created — POST exitoso             |
| 204    | No Content — DELETE exitoso        |
| 400    | Bad Request — datos inválidos      |
| 401    | Unauthorized — token inválido/expirado |
| 403    | Forbidden — webhook token incorrecto |
| 404    | Not Found — recurso no encontrado  |
| 422    | Unprocessable Entity — validación Pydantic |
| 500    | Internal Server Error              |
| 502    | Bad Gateway — fallo con Meta/Brevo API |
| 503    | Service Unavailable — sin conexión con Meta |
