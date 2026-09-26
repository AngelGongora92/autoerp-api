# Requirement Spec: AUT-33 - Configuración de Citas (Backend)

## 📋 Requerimientos Funcionales

### 1. Configuración de Citas por Empresa
- **GET /settings/appointment-config**: Retorna los parámetros de citas de la empresa del usuario autenticado (`start_time`, `end_time`, `slot_duration_minutes`, `allowed_days`, etc.).
- **PUT /settings/appointment-config**: Actualiza los parámetros de citas para la empresa.

### 2. Gestión de Tipos / Razones de Cita (`appointment_reasons`)
- **GET /appointments/reasons/**: Retorna los tipos de cita configurados.
- **POST /appointments/reasons/**: Permite añadir un nuevo tipo de cita con su nombre y duración estimada (`duration_minutes`).
- **PUT/PATCH /appointments/reasons/{reason_id}**: Modifica un tipo de cita existente.
- **DELETE /appointments/reasons/{reason_id}**: Borra o desactiva un tipo de cita.

### 3. Criterios de Aceptación
- La API debe impedir agendar citas fuera del horario configurado para la empresa.
- La API debe rechazar solicitudes en días no habilitados en la configuración.
- Toda cita nueva o reagendada debe validar el bloque de tiempo disponible.
