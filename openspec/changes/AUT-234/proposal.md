# Propuesta Backend para AUT-234: Confirmación Manual de Cita por Asesor

## 1. Contexto y Objetivos
Actualmente las citas se crean con el estado 'sin confirmar' (`status_id = 1`). Este ticket busca permitir que un asesor/mecanico confirme manualmente la cita (`status_id = 2`) desde la interfaz web, activando opcionalmente el envío de notificaciones al cliente vía WhatsApp, Email o ambos.

## 2. Cambios Arquitecturales y Flujo de Datos
- **Endpoint PATCH**: Se expondrá un nuevo endpoint `PATCH /appointments/{appointment_id}/confirm` que aceptará parámetros de configuración de notificación.
- **Lógica de Negocio**:
  1. Validar existencia y estado actual de la cita.
  2. Actualizar el estado de la cita a `status_id = 2` ('Confirmada').
  3. Si la solicitud indica envío de notificaciones (`send_whatsapp` y/o `send_email`), encolar o ejecutar en segundo plano (`FastAPI BackgroundTasks` / servicio de notificaciones) el envío del mensaje de confirmación al cliente.
- **Validación de Seguridad**: El endpoint estará protegido exigiendo autenticación y permisos adecuados (`confirm_appointment` o rol de asesor/admin).
