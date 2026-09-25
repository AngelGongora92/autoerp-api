# Tareas de Desarrollo Backend - AUT-34

1. **Base de Datos & Semillas:**
   - [x] Verificar/insertar los estados 'Cancelada' y 'Reagendada' en la tabla `appointment_status`.
   - [x] Incluir campos `cancellation_reason` y `cancellation_date` en el modelo `Appointment` para trazabilidad completa.

2. **Esquemas Pydantic:**
   - [x] Crear `RescheduleRequest`, `CancelRequest` y actualizar `AppointmentResponse` en `api/schemas/appointments.py`.

3. **Lógica de Negocio & Controladores (FastAPI):**
   - [x] Implementar y verificar `PATCH /appointments/{appointment_id}/reschedule` con contador de reprogramaciones.
   - [x] Implementar y verificar `PATCH /appointments/{appointment_id}/cancel` almacenando motivo y fecha de cancelación.

4. **Verificación & Pruebas:**
   - [x] Validar que las firmas e importaciones del backend compilen e importen sin errores.
