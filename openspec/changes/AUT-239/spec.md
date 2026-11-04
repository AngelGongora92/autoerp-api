# Especificación Técnica Backend para AUT-239

## Base de Datos y Modelos
- **Tabla `appointments`**:
  - `order_id` (FK a `orders.order_id`, Nullable).
  - Actualizar el catálogo de estados `appointment_status` para soportar el estado `ATTENDED` ('Atendida').
- **Tabla `orders` / `work_orders`**:
  - `appointment_id` (FK a `appointments.appointment_id`, Nullable).

## Endpoints

### 1. `GET /appointments/{appointment_id}`
- **Descripción**: Retorna la información detallada de una cita por su ID.
- **Parámetros de Ruta**: `appointment_id` (Int).
- **Respuesta (200 OK)**:
  ```json
  {
    "appointment_id": 101,
    "appointment_date": "2023-10-25T10:00:00",
    "customer_id": 45,
    "vehicle_id": 12,
    "customer": { "customer_id": 45, "first_name": "Juan", "phone": "5551234567" },
    "vehicle": { "vehicle_id": 12, "plate": "ABC-123", "mileage": 45000 },
    "items": [
      { "appointment_item_id": 1, "reason_id": 3, "reason": "Mantenimiento", "notes": "Revisar frenos" }
    ],
    "status": { "status": "CONFIRMED" }
  }
  ```

### 2. `POST /orders/`
- **Descripción**: Registra una nueva orden de trabajo e integra opcionalmente el cierre de la cita.
- **Entrada (Body JSON)**:
  - `appointment_id` (Int, Opcional)
  - `customer_id` (Int)
  - `vehicle_id` (Int)
  - `mileage` (Int)
  - `fuel_level` (String/Float)
  - `items` (List[Object]): Motivos/Servicios solicitados.
  - `inventory` (List[Object], Opcional): Checkbox de accesorios/inventario.
  - `damages` (List[Object], Opcional): Registro de daños en carrocería.
- **Lógica Backend**:
  1. Iniciar transacción DB (`db.begin()`).
  2. Insertar el registro de la orden.
  3. Si `appointment_id` está presente:
     - Validar que la cita existe.
     - Asignar `appointment.order_id = new_order.id`.
     - Cambiar estado de la cita a 'Atendida'.
     - Asignar `new_order.appointment_id = appointment.id`.
  4. Confirmar cambios (`db.commit()`).
