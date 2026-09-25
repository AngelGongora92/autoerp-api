# Tareas de Desarrollo Backend

1. **Modelos y Schemas (Pydantic)**:
   - Crear el schema `EmployeeAvailabilityResponse` para estructurar la respuesta de horas laborables y bloques ocupados.
   - Asegurar que el schema de entrada de `POST /appointments/new-appointment/` valide correctamente los tipos de datos.

2. **Endpoints (FastAPI Routers)**:
   - Implementar la ruta `GET /schedules/availability/{employee_id}` en `routers/schedules.py`.
   - Integrar la lógica de consulta a `employee_schedule_blocks` y `appointments` filtrando por la fecha provista.

3. **Lógica de Negocio y Validaciones (Services/CRUD)**:
   - Implementar función auxiliar `check_advisor_overlap(db, employee_id, start_time, duration_minutes)` para encapsular la consulta de solapamientos.
   - Integrar esta validación en el flujo de creación de citas en `routers/appointments.py`.

4. **Pruebas Unitarias**:
   - Crear pruebas para verificar el cálculo correcto de disponibilidad cuando el empleado tiene/no tiene citas previas.
   - Crear pruebas de integración que fuercen un conflicto de horario (`409 Conflict`) al intentar agendar citas solapadas.
