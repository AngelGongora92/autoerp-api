# Tareas de Desarrollo Backend - AUT-40

1. **Migración de Base de Datos (Alembic)**
   - [x] Generar script de migración Alembic `create_order_items_and_traceability`.
   - [x] Crear tabla `order_items` con PK, FKs y defaults especificados.
   - [x] Alterar tabla `orders`: añadir columna `appointment_id` con su FK e índice.
   - [x] Alterar tabla `appointments`: añadir columnas `order_id` (FK e índice) y `channel` (default 'manual').
   - [x] Insertar estado `id=4` ('atendida') en `appointment_status` si no existe.

2. **Modelos SQLAlchemy**
   - [x] Crear el modelo `OrderItem` en `api/database.py`.
   - [x] Actualizar modelo `Appointment` y `Order` agregando las relaciones correspondientes (`order_id`, `appointment_id`, `items`).

3. **Esquemas Pydantic**
   - [x] Definir `OrderItemResponse` y `CreatedOrderFromAppointmentResponse` en los esquemas del módulo de órdenes/citas.

4. **Servicio y Endpoint Backend**
   - [x] Implementar la función de negocio `create_order_from_appointment` en `api/appointments.py`.
   - [x] Validar pertenencia a la empresa (`company_id`), no cancelación (`status_id != 3`), no conversión previa (`order_id is None`) y presencia de `customer_id` y `vehicle_id`.
   - [x] Implementar cálculo del correlativo `c_order_id` e inserción atómica de `Order` y `OrderItems` replicando los `appointment_items`.
   - [x] Actualizar estado de la cita a `4` y setear su `order_id`.
   - [x] Registrar endpoint `POST /appointments/{appointment_id}/create-order` en el router de citas de FastAPI.

5. **Pruebas Unitarias e Integración**
   - [x] Crear tests unitarios en `tests/test_aut_40.py` verificando escenarios exitosos y fallidos (falta de cliente/auto, cita cancelada, cita doblemente convertida).

