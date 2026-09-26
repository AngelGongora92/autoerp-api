# Tareas Backend para AUT-33

1. **Base de Datos y Migraciones:**
   - Crear el modelo SQLAlchemy `AppointmentConfig`.
   - Generar la migración de Alembic (`alembic revision --autogenerate`).
   - Crear un script de semilla (seed) para insertar una configuración por defecto en la base de datos.

2. **Esquemas Pydantic:**
   - Definir `AppointmentConfigSchema` para lectura y actualización.
   - Definir `AppointmentReasonCreate` y `AppointmentReasonUpdate`.

3. **Desarrollo de Endpoints de Configuración:**
   - Implementar `GET /appointments/config`.
   - Implementar `PUT /appointments/config` (con validación de que `start_time` < `end_time`).

4. **Desarrollo de Endpoints de Motivos (Reasons):**
   - Implementar `POST /appointments/reasons/`.
   - Implementar `PUT /appointments/reasons/{reason_id}`.

5. **Refactor de Creación de Citas (`POST /appointments/new-appointment/`):**
   - Implementar el servicio de validación de disponibilidad de bloques de tiempo.
   - Integrar las validaciones de días permitidos, rango de horas y solapamiento de agenda para el empleado asignado.

6. **Pruebas Unitarias e Integración:**
   - Crear tests para verificar que no se permitan citas fuera del horario configurado.
   - Crear tests para verificar que no se permitan citas en días no laborales.
   - Crear tests para verificar que se bloquee el agendamiento si hay solapamiento de tiempos con el mismo mecánico/asesor.
