# Lista de Tareas Backend para AUT-245

- [x] **Base de Datos & Alembic:**
  - [x] Agregar la columna `public_portal_enabled` al modelo SQLAlchemy `AppointmentSettings`.
  - [x] Generar y ejecutar la migración Alembic (`alembic revision --autogenerate`).

- [x] **Pydantic Schemas:**
  - [x] Actualizar esquemas en `settings.py` para incluir `public_portal_enabled`.
  - [x] Crear esquemas públicos: `PublicVehicleTempData`, `PublicAppointmentCreate`, `PublicAppointmentConfigResponse`.

- [x] **Servicios y Helpers:**
  - [x] Crear helper `check_public_portal_enabled(company_id, db)` para la validación del estado del portal.
  - [x] Reutilizar la lógica de cálculo de horarios libres filtrando por asesores de la empresa (`position_id = 1`).

- [x] **Endpoints Públicos (`/appointments/public`):**
  - [x] Implementar `GET /appointments/public/config`.
  - [x] Implementar `GET /appointments/public/availability`.
  - [x] Implementar `POST /appointments/public` con creación de cita en `status_id = 1` y poblado de datos `temp_*`.

- [x] **Notificaciones y Pruebas Pytest:**
  - [x] Disparar la confirmación por correo/WhatsApp a los datos temporales del cliente.
  - [x] Agregar tests unitarios para verificar rechazo `403 Forbidden` cuando `public_portal_enabled = False`.
  - [x] Agregar tests de integración para la creación exitosa de citas públicas.
