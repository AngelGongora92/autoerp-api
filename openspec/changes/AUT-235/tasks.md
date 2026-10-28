# Tareas Backend - AUT-235

- [x] **Esquemas Pydantic / Query Params**: Actualizar el handler de `GET /appointments/` para recibir `start_date: Optional[datetime]` y `end_date: Optional[datetime]`.
- [x] **Capa de Servicios / Repositorio**: Ajustar la consulta SQLAlchemy para aplicar `.where(Appointment.appointment_date >= start_date)` y `.where(Appointment.appointment_date <= end_date)` si son proporcionados.
- [x] **Manejo de Zona Horaria**: Asegurar que las fechas ingresadas en el query param consideren el timezone correcto antes de consultar PostgreSQL.
- [x] **Pruebas Unitarias/Integración**: Agregar tests para validar que el filtrado por rango diario y semanal retorne los registros correctos.

