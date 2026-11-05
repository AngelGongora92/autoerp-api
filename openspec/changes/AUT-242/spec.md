# Especificación de Endpoints y Schemas Pydantic

### 1. Búsqueda de Clientes (Deduplicación)
`GET /customers/search`
- **Query Params:**
  - `phone` (Optional[str]): Número telefónico sin formato o parcial.
  - `name` (Optional[str]): Término de búsqueda por nombre/apellido.
- **Respuesta (200 OK):** `List[CustomerResponseSchema]`

### 2. Formalización de Cita
`PATCH /appointments/{appointment_id}/formalize`
- **Request Body:**
```json
{
  "customer_id": 105,
  "vehicle_id": 42
}
```
- **Respuesta (200 OK):** `AppointmentResponseSchema` con `customer_id`, `vehicle_id` asignados.

### 3. Modificación a Creación de Orden
`POST /orders/`
- **Request Body:** Incluye opcionalmente `appointment_id` (int).
- **Lógica Interna:** Si se provee `appointment_id`, ejecuta dentro de una transacción BD:
  1. Verifica que la cita exista.
  2. Valida que `customer_id` y `vehicle_id` coincidan o se asignen.
  3. Cambia el estado de la cita a `ATENDIDA` (`appointment_status`).
  4. Crea la orden de servicio.
