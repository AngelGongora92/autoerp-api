# Lista de Tareas Backend para AUT-245

- [ ] **Base de Datos & Alembic:**
  - [ ] Agregar la columna `public_portal_enabled` al modelo SQLAlchemy `AppointmentSettings`.
  - [ ] Generar y ejecutar la migración Alembic (`alembic revision --autogenerate`).

- [ ] **Pydantic Schemas:**
  - [ ] Actualizar esquemas en `settings.py` para incluir `public_portal_enabled`.
  - [ ] Crear esquemas públicos: `PublicVehicleTempData`, `PublicAppointmentCreate`, `PublicAppointmentConfigResponse`.

- [ ] **Servicios y Helpers:**
  - [ ] Crear helper `check_public_portal_enabled(company_id, db)` para la validación del estado del portal.
  - [ ] Reutilizar la lógica de cálculo de horarios libres filtrando por asesores de la empresa (`position_id = 1`).

- [ ] **Endpoints Públicos (`/appointments/public`):**
  - [ ] Implementar `GET /appointments/public/config`.
  - [ ] Implementar `GET /appointments/public/availability`.
  - [ ] Implementar `POST /appointments/public` con creación de cita en `status_id = 1` y poblado de datos `temp_*`.

- [ ] **Notificaciones y Pruebas Pytest:**
  - [ ] Disparar la confirmación por correo/WhatsApp a los datos temporales del cliente.
  - [ ] Agregar tests unitarios para verificar rechazo `403 Forbidden` cuando `public_portal_enabled = False`.
  - [ ] Agregar tests de integración para la creación exitosa de citas públicas.
