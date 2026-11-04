# Tareas Backend para AUT-239

- [x] **Endpoint GET Detalle Cita**:
  - [x] Implementar la ruta `GET /appointments/{appointment_id}` en FastAPI.
  - [x] Incluir relaciones con cliente, vehículo e items de la cita.

- [x] **Schemas Pydantic**:
  - [x] Crear o actualizar `AppointmentDetailResponse` con la estructura necesaria para precargar `/orders/new`.
  - [x] Extender `OrderCreate` schema para incluir `appointment_id: Optional[int] = None`.

- [x] **Lógica de Dominio y Persistencia**:
  - [x] Modificar el servicio `OrderService.create_order` para procesar la vinculación con la cita.
  - [x] Actualizar el estado de la cita a 'Atendida' dentro de la misma transacción.

- [x] **Pruebas Unitarias / Integración**:
  - [x] Crear test de integración para verificar la creación exitosa de orden desde cita y actualización del estado de la cita.
  - [x] Probar rollback en caso de error durante la conversión.
