# Tasks: AUT-33 - Configuración de Citas (Backend)

- [ ] Task 1: Revisar modelos de SQLAlchemy (`CompanySettings` o `Company`) y añadir campos de configuración de citas si no existen.
- [ ] Task 2: Generar y ejecutar migración de Alembic para campos de configuración de citas por empresa.
- [ ] Task 3: Crear schemas de Pydantic para lectura y actualización de configuración de citas (`AppointmentSettingsConfig`).
- [ ] Task 4: Implementar endpoints GET y PUT para la configuración de citas en `api/settings.py`.
- [ ] Task 5: Implementar/verificar endpoints CRUD para tipos de cita (`appointment_reasons`) en `api/appointments.py`.
- [ ] Task 6: Añadir validaciones de horario, días y duración en la creación de citas en `api/appointments.py`.
- [ ] Task 7: Probar endpoints localmente y validar respuestas.
