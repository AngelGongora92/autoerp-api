# Tareas Backend (AUT-231)

- [ ] **Modelo BD**: Definir la clase `AppointmentItem` en SQLAlchemy y mapear la relación `items` en `Appointment`.
- [ ] **Migración Alembic**: Generar script de migración para crear `appointment_items`, agregar índices/FKs e incluir script de transferencia de datos desde `appointment_reasons_link`.
- [ ] **Schemas Pydantic**: Definir `AppointmentItemCreate`, `AppointmentItemResponse` y actualizar `AppointmentCreate`/`AppointmentResponse`.
- [ ] **Lógica de Creación**: Modificar el endpoint `POST /appointments/new-appointment/` para manejar tanto `items` como `reason_ids` de forma transparente.
- [ ] **Optimización de Consultas**: Actualizar las búsquedas de `GET /appointments/` con `joinedload` para incluir `items` y sus motivos.
- [ ] **Tests Unitarios**: Crear pruebas automatizadas en `tests/test_appointment_items.py` validando la creación de items con notas y retrocompatibilidad con payload legacy.
