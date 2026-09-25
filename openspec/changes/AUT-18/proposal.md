# Propuesta Backend para AUT-18

Para resolver la validación de disponibilidad del asesor y la duración de los servicios, se propone la siguiente estrategia en el backend:

1. **Cálculo de Duración Total**:
   - Al recibir una solicitud de cita, el backend consultará la tabla `appointment_reasons` para obtener la duración (`duration_minutes`) del `reason_id` enviado.
   - Se validará que `duration_minutes` sea mayor a 0. Si es nulo o 0, se retornará un error `400 Bad Request`.

2. **Endpoint de Disponibilidad (`GET /schedules/availability/{employee_id}`)**:
   - Este nuevo endpoint permitirá al frontend conocer la agenda de un asesor para un día específico.
   - **Lógica**:
     1. Obtener el día de la semana de la fecha consultada (0=Lunes, 6=Domingo).
     2. Consultar los bloques de trabajo base del empleado en `employee_schedule_blocks` para ese día de la semana.
     3. Consultar todas las citas activas (`appointments`) asignadas a ese `employee_id` en la fecha seleccionada.
     4. Retornar tanto el horario laboral del empleado como los rangos de tiempo ya ocupados por otras citas.

3. **Validación de Solapamiento en Creación de Citas**:
   - En el endpoint `POST /appointments/new-appointment/`, si se proporciona un `assigned_to` (ID del asesor):
     - Calcular la hora de fin estimada: `appointment_date + duration_minutes`.
     - Verificar en la base de datos que no existan citas para el mismo `assigned_to` cuyo intervalo de tiempo se solape con el rango propuesto.
     - Si hay solapamiento, retornar un error `409 Conflict`.
