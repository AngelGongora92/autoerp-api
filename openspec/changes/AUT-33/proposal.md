# Propuesta Backend para AUT-33

Para cumplir con el requerimiento de parametrización y validación de bloques de tiempo en las citas, se propone la siguiente arquitectura:

1. **Configuración Global de Citas (`appointment_configs`):** Crear una nueva tabla para almacenar los parámetros generales del taller:
   - Rango de horas permitido para agendar (`start_time` y `end_time`).
   - Días de la semana permitidos (ej. Lunes a Viernes, representado como un array de enteros `[1,2,3,4,5]`).
   - Duración por defecto en minutos (en caso de que un tipo de cita no la tenga definida).

2. **Gestión de Tipos de Cita (`appointment_reasons`):** Asegurar que cada tipo de cita tenga su `duration_minutes` obligatorio y exponer endpoints para crearlos y editarlos.

3. **Motor de Validación de Citas:** Al intentar agendar una cita mediante `POST /appointments/new-appointment/`, el backend realizará las siguientes validaciones:
   - **Validación de Día:** Que el día de la semana de `appointment_date` esté dentro de los días permitidos.
   - **Validación de Horario:** Que la hora de inicio y la hora de fin calculada (`appointment_date` + `duration_minutes` del motivo) estén dentro del rango de horas configurado.
   - **Validación de Solapamiento (Bloqueo de Tiempo):** Verificar que el bloque de tiempo calculado no se solape con otra cita existente para el mismo empleado asignado (`assigned_to`).
