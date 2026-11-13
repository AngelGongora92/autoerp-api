# Propuesta Backend para AUT-245: Portal Público de Agendamiento de Citas

## 1. Modificaciones en Base de Datos & Alembic
- Modificar el modelo SQLAlchemy de configuración de citas (`AppointmentSettings`) añadiendo el campo `public_portal_enabled` de tipo `Boolean`, `nullable=False`, con `server_default=text('false')`.
- Generar migración con Alembic (`alembic revision --autogenerate`).

## 2. Esquemas Pydantic
- Actualizar `AppointmentSettingsRead` y `AppointmentSettingsUpdate` para incluir `public_portal_enabled: bool`.
- Crear esquemas específicos para el flujo público:
  - `PublicVehicleTempData`: Esquema para validar la estructura JSONB del vehículo (`make`, `model`, `year`, `plate`, `color`, `notes`).
  - `PublicAppointmentCreate`: Esquema de creación pública que recibe `company_id`, `appointment_date`, `reason_ids`, datos personales temporales (`temp_fname`, `temp_lname`, `temp_cname`, `temp_phone`, `temp_email`) y `temp_vehicle_data`.
  - `PublicAppointmentConfigResponse`: Datos públicos del taller (nombre comercial, días autorizados `allowed_days`, `slot_duration_minutes`, servicios/motivos disponibles `reasons` y estado `public_portal_enabled`).

## 3. Helper de Validación y Endpoints Públicos
- **Función Reutilizable:** Implementar `validate_public_portal_status(company_id: int, db: Session)` que consulte la configuración del taller y lance un `HTTPException(status_code=403, detail="El portal público de citas se encuentra deshabilitado para este taller.")` si `public_portal_enabled == False`.
- **`GET /appointments/public/config`**: Retorna los catálogos y configuración necesaria para renderizar la vista pública.
- **`GET /appointments/public/availability`**: Consulta las franjas horarias disponibles según los asesores con `position_id = 1` y los servicios seleccionados.
- **`POST /appointments/public`**: Valida disponibilidad y fechas futuras, inserta en `appointments` fijando `status_id = 1` (Sin confirmar) y asignando `customer_id=None`, `vehicle_id=None`, guardando toda la información en las columnas `temp_*`. Al finalizar, dispara el servicio de notificaciones a `temp_email` / `temp_phone`.
