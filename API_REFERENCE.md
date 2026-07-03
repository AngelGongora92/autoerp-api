# 📚 Referencia de API AutoERP

Este documento detalla los endpoints disponibles para el equipo de Frontend, especificando los datos de entrada, salida y la tabla de origen en la base de datos.

---

## 🔐 Autenticación (`/auth`)

### `POST /auth/login`
*   **Descripción:** Iniciar sesión y obtener permisos.
*   **Tabla Fuente:** `users`, `permissions`
*   **Entrada (Body JSON):**
    *   `username` (String): Nombre de usuario.
    *   `password` (String): Contraseña en texto plano.
*   **Salida (JSON):**
    *   `message` (String): Mensaje de éxito.
    *   `permissions` (List[String]): Lista de strings con los permisos (ej: `["admin", "ver_reportes"]`).

---

## 📅 Citas (`/appointments`)

### `GET /appointments/`
*   **Descripción:** Obtiene la lista de citas. Soporta filtrado.
*   **Tabla Fuente:** `appointments`
*   **Entrada (Query Params):**
    *   `assigned_to` (Int, Opcional): ID del empleado para filtrar sus citas.
*   **Salida (List[JSON]):**
    *   `appointment_id` (Int)
    *   `appointment_date` (Datetime): Fecha y hora de inicio.
    *   `reason` (Object): `{ reason: String, duration_minutes: Int }` (Viene de `appointment_reasons`).
    *   `status` (Object): `{ status: String }` (Viene de `appointment_status`).
    *   `customer` (Object): Datos básicos del cliente.
    *   `vehicle` (Object): Datos básicos del vehículo.
    *   `temp_*` (String): Campos temporales si el cliente/vehículo no está registrado (`temp_fname`, `temp_cname`, etc.).

### `POST /appointments/new-appointment/`
*   **Descripción:** Crea una nueva cita.
*   **Tabla Fuente:** `appointments`
*   **Entrada (Body JSON):**
    *   `appointment_date` (Datetime): Fecha y hora.
    *   `reason_id` (Int): ID del motivo.
    *   `assigned_to` (Int, Opcional): ID del mecánico/asesor.
    *   `customer_id` / `vehicle_id` (Int, Opcional): IDs si ya existen.
    *   `temp_fname`, `temp_phone`, etc. (String, Opcional): Datos si es cliente nuevo/rápido.

### `GET /appointments/reasons/`
*   **Descripción:** Lista los motivos de visita disponibles (ej. Mantenimiento, Reparación).
*   **Tabla Fuente:** `appointment_reasons`
*   **Salida (List[JSON]):**
    *   `reason_id` (Int)
    *   `reason` (String)
    *   `duration_minutes` (Int): Duración estimada en minutos.

---

## 🗓️ Horarios de Empleados (`/schedules`)

### `GET /schedules/blocks/{employee_id}`
*   **Descripción:** Obtiene el horario semanal base de un empleado.
*   **Tabla Fuente:** `employee_schedule_blocks`
*   **Salida (List[JSON]):**
    *   `block_id` (Int)
    *   `day_of_week` (Int): 0=Lunes, 6=Domingo.
    *   `start_time` (Time)
    *   `end_time` (Time)

### `POST /schedules/blocks/`
*   **Descripción:** Define un bloque de horario recurrente.
*   **Tabla Fuente:** `employee_schedule_blocks`
*   **Entrada (Body JSON):**
    *   `employee_id` (Int)
    *   `day_of_week` (Int): 0=Lunes, 6=Domingo.
    *   `start_time` (Time): Hora de entrada (ej: "09:00:00").
    *   `end_time` (Time): Hora de salida (ej: "18:00:00").

### `DELETE /schedules/blocks/{block_id}`
*   **Descripción:** Elimina un bloque de horario.
*   **Tabla Fuente:** `employee_schedule_blocks`

### `GET /schedules/overrides/{employee_id}`
*   **Descripción:** Obtiene las excepciones de horario de un empleado.
*   **Tabla Fuente:** `schedule_overrides`
*   **Salida (List[JSON]):**
    *   `override_id` (Int)
    *   `override_date` (Date)
    *   `is_available` (Bool)
    *   `start_time` (Time, Opcional)
    *   `end_time` (Time, Opcional)
    *   `reason` (String, Opcional)

### `POST /schedules/overrides/`
*   **Descripción:** Crea una excepción al horario (vacaciones, permiso, horas extra).
*   **Tabla Fuente:** `schedule_overrides`
*   **Entrada (Body JSON):**
    *   `employee_id` (Int)
    *   `override_date` (Date): Fecha específica (ej: "2023-12-25").
    *   `is_available` (Bool): `false` para día libre, `true` para horario especial.
    *   `start_time` (Time, Opcional)
    *   `end_time` (Time, Opcional)
    *   `reason` (String, Opcional)

---

## 🛠 Órdenes de Servicio (`/orders`)

### `GET /orders/`
*   **Descripción:** Listado paginado de órdenes del taller con relaciones anidadas.
*   **Parámetros de Consulta (Query Params):**
    *   `page` (Int, Opcional, por defecto 1)
    *   `limit` (Int, Opcional, por defecto 20)
*   **Salida (JSON):**
    *   `orders` (List[JSON]): Lista de órdenes de servicio con detalles anidados de:
        *   `customer` (JSON, Opcional): Información resumida del cliente.
        *   `vehicle` (JSON, Opcional): Información del vehículo (incluyendo marca y modelo).
        *   `mechanic` (JSON, Opcional): Información del mecánico asignado.
        *   `advisor` (JSON, Opcional): Información del asesor.
    *   `total` (Int): Total de órdenes del taller.
    *   `page` (Int): Página actual consultada.
    *   `limit` (Int): Cantidad máxima de registros por página.
    *   `pages` (Int): Total de páginas disponibles.

### `POST /orders/`
*   **Descripción:** Crear nueva orden.
*   **Tabla Fuente:** `orders`
*   **Entrada (Body JSON):**
    *   `c_order_id` (String): ID manual/custom.
    *   `vehicle_id` (Int)
    *   `customer_id` (Int)
    *   `advisor_id` (Int): ID del empleado asesor.
    *   `fuel_level` (Int): 1-8 (Octavos de tanque).

### `GET /orders/extra-info/{order_id}`
*   **Descripción:** Obtiene checklist de objetos extra (gato, llanta refacción, etc.).
*   **Tabla Fuente:** `order_extra_info` (relacionado con `order_extra_items`)
*   **Salida:** Lista de items con su estado/descripción para esa orden.

### `GET /orders/bodywork-details/{order_id}`
*   **Descripción:** Obtiene los detalles de carrocería (golpes, rayones) marcados.
*   **Tabla Fuente:** `bodywork_details`
*   **Salida (List[JSON]):**
    *   `detail_id` (Int)
    *   `view` (String): "front", "back", "left", "right", "up".
    *   `coordinates` (JSON): `{ "x": 10.5, "y": 20.0 }` (Posición en la imagen).
    *   `detail_type` (Object): Tipo de daño (ej. "Rayón").

### `GET /orders/inventory-data/{order_id}/{inv_type_id}`
*   **Descripción:** Obtiene los datos llenados de un checklist de inventario específico.
*   **Tabla Fuente:** `order_inventory_data`
*   **Salida:** Lista de valores ingresados para los items de ese inventario.

### `POST /orders/inventory-data/`
*   **Descripción:** Registra o actualiza (Upsert) múltiples entradas de datos de inventario para una orden.
*   **Tabla Fuente:** `order_inventory_data`
*   **Entrada (Body JSON):** Lista de objetos `{ order_id: Int, item_id: Int, data: JSON }`.

### `GET /orders/inventory-types/`
*   **Descripción:** Obtiene todos los tipos de inventario configurados para la empresa actual, ordenados por su posición.
*   **Tabla Fuente:** `inventory_types`
*   **Salida (List[JSON]):**
    *   `inv_type_id` (Int)
    *   `name` (String)
    *   `component_key` (String): "bodywork" o "generic_checklist".
    *   `is_active` (Bool)
    *   `position` (Int)
    *   `company_id` (Int)

### `POST /orders/inventory-types/`
*   **Descripción:** Crea un nuevo tipo de inventario personalizado para la empresa actual.
*   **Tabla Fuente:** `inventory_types`
*   **Entrada (Body JSON):** `{ name: String, component_key: Optional[String], is_active: Optional[Bool] }`

### `PATCH /orders/inventory-types/{inv_type_id}`
*   **Descripción:** Actualiza parcialmente un tipo de inventario de la empresa actual.
*   **Tabla Fuente:** `inventory_types`

### `DELETE /orders/inventory-types/{inv_type_id}`
*   **Descripción:** Elimina físicamente un tipo de inventario y sus ítems si pertenece a la empresa actual.
*   **Tabla Fuente:** `inventory_types` (cascades to `inventory_items`)

### `PUT /orders/inventory-types/reorder`
*   **Descripción:** Actualiza atómicamente el orden (posiciones) de los tipos de inventario.
*   **Entrada (Body JSON):** Lista de objetos `{ inv_type_id: Int, position: Int }`.

### `GET /orders/inventory-items/{inv_type_id}`
*   **Descripción:** Obtiene un tipo de inventario y todos sus ítems asociados de la empresa actual.
*   **Tabla Fuente:** `inventory_items`
*   **Salida (JSON):** `{ inventory_type: InventoryTypesResponse, items: List[InventoryItemStrippedResponse] }`

### `POST /orders/inventory-items/`
*   **Descripción:** Crea un nuevo ítem de inventario asociado a un tipo para la empresa actual.
*   **Tabla Fuente:** `inventory_items`
*   **Entrada (Body JSON):** `{ inv_type_id: Int, label: String, input_type: String, description: Optional[String], is_mandatory: Optional[Bool], picture_upload: Optional[Bool] }`

### `PATCH /orders/inventory-items/`
*   **Descripción:** Actualiza múltiples ítems de inventario de forma masiva (bulk).
*   **Tabla Fuente:** `inventory_items`
*   **Entrada (Body JSON):** Lista de objetos `{ item_id: Int, ...fields }`.

### `DELETE /orders/inventory-items/{item_id}`
*   **Descripción:** Elimina un ítem de inventario si pertenece a la empresa actual.
*   **Tabla Fuente:** `inventory_items`

### `PUT /orders/inventory-items/reorder`
*   **Descripción:** Actualiza la posición de múltiples ítems de un tipo de inventario de forma atómica.
*   **Entrada (Body JSON):** Lista de objetos `{ item_id: Int, position: Int }`.

---

## 🚗 Vehículos (`/vehicles`)

### `GET /vehicles/`
*   **Descripción:** Obtiene todos los vehículos asociados al taller (tenant).
*   **Tabla Fuente:** `vehicles`
*   **Salida (List[JSON]):**
    *   `vehicle_id` (Int)
    *   `vin` (String)
    *   `plate` (String)
    *   `model` (Object): `{ model: String, make: { make: String } }`
    *   `color` (Object): `{ color: String }`
    *   `year` (Int)

### `GET /vehicles/{customer_id}`
*   **Descripción:** Obtiene todos los vehículos de un cliente.
*   **Tabla Fuente:** `vehicles`
*   **Salida (List[JSON]):**
    *   `vehicle_id` (Int)
    *   `vin` (String)
    *   `plate` (String)
    *   `model` (Object): `{ model: String, make: { make: String } }` (Viene de `models` y `makes`).
    *   `color` (Object): `{ color: String }` (Viene de `colors`).
    *   `year` (Int)

### `POST /vehicles/`
*   **Descripción:** Registrar un vehículo.
*   **Tabla Fuente:** `vehicles`
*   **Entrada (Body JSON):**
    *   `vin` (String)
    *   `plate` (String)
    *   `model_id` (Int)
    *   `color_id` (Int)
    *   `motor_id` (Int)
    *   `customer_id` (Int)

### `PATCH /vehicles/{vehicle_id}`
*   **Descripción:** Actualiza parcialmente un vehículo.
*   **Tabla Fuente:** `vehicles`
*   **Entrada (Body JSON):**
    *   Cualquier campo del vehículo opcional (ej: `mileage`, `vin`, `plate`, etc.).
*   **Salida (JSON):**
    *   Objeto `VehicleResponse` del vehículo actualizado.

### `GET /vehicles/makes/`
*   **Descripción:** Catálogo de Marcas.
*   **Tabla Fuente:** `makes`

### `GET /vehicles/models/{make_id}`
*   **Descripción:** Catálogo de Modelos filtrado por Marca.
*   **Tabla Fuente:** `models`

---

## 👥 Clientes (`/customers`)

### `GET /customers/search`
*   **Descripción:** Buscar clientes por nombre o empresa.
*   **Tabla Fuente:** `customers`
*   **Entrada (Query Param):**
    *   `full_name` (String): Texto a buscar.
*   **Salida:** Lista de clientes coincidentes.

### `POST /customers/`
*   **Descripción:** Crear cliente.
*   **Tabla Fuente:** `customers`
*   **Entrada (Body JSON):**
    *   `is_company` (Bool)
    *   `fname` (String): Nombre.
    *   `lname` (String): Apellido.
    *   `cname` (String): Nombre empresa (si aplica).
    *   `email` (String)
    *   `phone` (String)

---

## 👷 Empleados (`/employees`)

### `GET /employees/`
*   **Descripción:** Listar todos los empleados.
*   **Tabla Fuente:** `employees`
*   **Salida (List[JSON]):**
    *   `employee_id` (Int)
    *   `fname` (String)
    *   `lname1` (String)
    *   `position_id` (Int): ID del cargo (Mecánico, Asesor, etc).

### `GET /employees/{position_id}`
*   **Descripción:** Listar empleados filtrados por cargo (ej. solo Asesores).
*   **Tabla Fuente:** `employees`

---

## 👤 Usuarios del Sistema (`/users`)

### `GET /users/`
*   **Descripción:** Listar usuarios con acceso al sistema.
*   **Tabla Fuente:** `users`
*   **Salida:**
    *   `username` (String)
    *   `is_admin` (Bool)
    *   `permissions` (List): Permisos asignados.

### `POST /users/`
*   **Descripción:** Crear usuario de sistema.
*   **Tabla Fuente:** `users`
*   **Entrada:**
    *   `username` (String)
    *   `password` (String)
    *   `permissions` (List[Object]): `[{ "name": "permiso_x" }]`

---

## ⚙️ Configuración (`/settings`)
*(Endpoints pendientes de implementación)*
*   **Tabla Fuente:** `company_settings`