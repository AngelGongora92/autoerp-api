# Tareas Backend para AUT-239

- [ ] **Endpoint GET Detalle Cita**:
  - Implementar la ruta `GET /appointments/{appointment_id}` en FastAPI.
  - Incluir relaciones con cliente, vehículo e items de la cita.

- [ ] **Schemas Pydantic**:
  - Crear o actualizar `AppointmentDetailResponse` con la estructura necesaria para precargar `/orders/new`.
  - Extender `OrderCreate` schema para incluir `appointment_id: Optional[int] = None`.

- [ ] **Lógica de Dominio y Persistencia**:
  - Modificar el servicio `OrderService.create_order` para procesar la vinculación con la cita.
  - Actualizar el estado de la cita a 'Atendida' dentro de la misma transacción.

- [ ] **Pruebas Unitarias / Integración**:
  - Crear test de integración para verificar la creación exitosa de orden desde cita y actualización del estado de la cita.
  - Probar rollback en caso de error durante la conversión.
