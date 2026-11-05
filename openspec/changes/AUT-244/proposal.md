# Propuesta Backend para AUT-244

## 1. Resumen de Cambios
Aunque el ticket se enfoca fuertemente en interacciones de UI (Drag & Drop y bloqueo visual de celdas pasadas), el frontend requiere invocar un endpoint backend al confirmar el reagendamiento para actualizar la cita en base de datos y gestionar el envío de notificaciones.

## 2. Definición del Endpoint
- **Ruta:** `PATCH /appointments/{appointment_id}/reschedule`
- **Descripción:** Actualiza la fecha/hora de la cita e inicia el envío opcional de notificaciones por WhatsApp y/o correo electrónico.
- **Validaciones Backend:**
  - La cita debe existir y no estar en estado cancelado (`CANCELLED`) ni completado (`COMPLETED`).
  - La nueva fecha/hora (`new_appointment_date`) debe ser posterior a la fecha/hora actual de la zona horaria de la sede.

## 3. Integración con Notificaciones
Se integrarán `BackgroundTasks` de FastAPI para desencadenar el envío de notificaciones por correo y WhatsApp sin bloquear la respuesta de la API.
