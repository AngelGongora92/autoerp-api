# Tareas Backend (AUT-233)

- [x] **Migración Alembic**: Crear y ejecutar migración para agregar `duration_minutes` a la tabla `appointments`.
- [x] **Modelos SQLAlchemy**: Actualizar el modelo `Appointment` agregando la columna `duration_minutes`.
- [x] **Schemas Pydantic**: Actualizar `AppointmentCreate` y `AppointmentResponse` con `duration_minutes`.
- [x] **Servicio de Validación de Empalmes**: Implementar `check_advisor_availability` utilizando comparaciones de intervalos de fechas.
- [x] **Servicio de Auto-Asignación**: Implementar `get_least_busy_available_advisor` con consulta agrupada por número de citas en el día.
- [x] **Nuevo Endpoint Availability**: Crear `GET /appointments/availability` para retornar horarios deshabilitados/disponibles.
- [x] **Actualización del Endpoint POST**: Integrar la persistencia de duración, validaciones HTTP 400 y auto-asignación en `POST /appointments/new-appointment/`.
- [x] **Pruebas Unitarias/Integración**: Cobertura para casos de solapamiento, cancelación liberadora de horario y balanceo por menor carga.
