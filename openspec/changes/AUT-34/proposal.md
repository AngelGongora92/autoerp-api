# Propuesta Backend - AUT-34: Reagendar y Cancelar Citas

Para permitir a los asesores reagendar y cancelar citas, implementaremos cambios en la capa de servicios y controladores de `/appointments`.

### 1. Flujo de Reagendación (`PATCH`)
* El asesor podrá modificar la fecha y hora (`appointment_date`) y opcionalmente el empleado asignado (`assigned_to`).
* Se validará que el nuevo horario esté dentro del bloque de trabajo del empleado (`employee_schedule_blocks`) y que no colisione con otra cita existente.
* El estado de la cita cambiará automáticamente a un estado que represente la modificación si es necesario, o se mantendrá como activa pero con la nueva fecha.

### 2. Flujo de Cancelación (`POST`)
* Se expondrá un endpoint específico para cancelar la cita de forma segura.
* Se cambiará el estado de la cita a 'Cancelada' (ID correspondiente en la tabla `appointment_status`).
* Se liberará el bloque de tiempo para que el asesor/mecánico esté disponible nuevamente.

### 3. Seguridad y Permisos
* Se verificará que el usuario autenticado tenga el rol/permiso de 'asesor' o 'admin' para realizar estas operaciones.
