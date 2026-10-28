# Propuesta Backend para AUT-40: Generación de Orden de Servicio desde Cita

## 1. Contexto
Actualmente las citas registradas en AutoERP no se convierten de manera automatizada en Órdenes de Servicio (OS). Para optimizar la recepción en taller, se requiere un mecanismo atómico que tome la cita, cree la Orden de Servicio, transfiera sus motivos/notas a la nueva tabla `order_items`, actualice el estado de la cita a 'Atendida' (id=4) y establezca una relación bidireccional entre la cita y la orden.

## 2. Puntos Clave de Arquitectura
- **Migración Alembic:**
  - Creación de la tabla `order_items` con campos de descripción libre, prioridad, cantidad, precio unitario y aprobación.
  - Modificación de `orders`: agregar columna `appointment_id` (FK indexed, nullable).
  - Modificación de `appointments`: agregar columna `order_id` (FK indexed, nullable) y columna `channel` (`String(32)`, default 'manual').
  - Inserción/Aseguramiento del estado `id=4` ('atendida') en `appointment_status`.
- **Lógica de Negocio en FastAPI:**
  - Endpoint relacional dentro de la transacción SQL: todo el proceso ocurre en un solo bloque `db.commit()` atómico para evitar inconclusiones.
  - Validación estricta de empresa (`company_id`), estado de la cita (`status_id != 3` y `order_id IS NULL`), y presencia de `customer_id` y `vehicle_id`.
  - Cálculo correlativo para `c_order_id` dentro de la compañía.
  - Mapeo de `appointment_items` -> `order_items` conservando `reason_id` y `notes`.
