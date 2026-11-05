# Tareas Backend para AUT-244

- [x] **Esquemas Pydantic:** Crear `AppointmentRescheduleRequest` y `AppointmentRescheduleResponse` con validación de fechas pasadas.
- [x] **Endpoint Reschedule:** Implementar `PATCH /appointments/{appointment_id}/reschedule` en el router de appointments.
- [x] **Lógica de Notificaciones:** Integrar dispatches mediante `BackgroundTasks` para WhatsApp y Email condicionados por los flags del payload.
- [x] **Pruebas Unitarias:** Crear tests con `pytest` para verificar validaciones de negocio (intento de mover citas canceladas o a fechas pasadas) y actualización correcta en DB.
