# Tareas de Desarrollo Backend

1. **Base de Datos & Semillas:**
   * Verificar/insertar los estados 'Cancelada' y 'Reagendada' en la tabla `appointment_status` mediante una migración de Alembic o script de seed.

2. **Esquemas Pydantic:**
   * Crear `AppointmentUpdateSchema` y `AppointmentCancelSchema` en `app/schemas/appointments.py`.

3. **Lógica de Negocio (Services):**
   * Implementar función `reschedule_appointment` en `app/services/appointments.py` que valide la disponibilidad del empleado (cruce de horarios con `employee_schedule_blocks` y otras citas activas).
   * Implementar función `cancel_appointment` que actualice el `status_id` al estado de 'Cancelada'.

4. **Controladores / Rutas (FastAPI):**
   * Crear el endpoint `PATCH /appointments/{appointment_id}/` en `app/api/v1/endpoints/appointments.py`.
   * Crear el endpoint `POST /appointments/{appointment_id}/cancel/` en el mismo archivo.
   * Integrar dependencias de autenticación y verificación de permisos de asesor.

5. **Pruebas Unitarias:**
   * Escribir pruebas para verificar el flujo exitoso de reagendación.
   * Escribir pruebas para verificar que no se permite reagendar en un horario ocupado.
   * Escribir pruebas para la cancelación de citas y validación de estados de transición no permitidos.
