# Tareas Backend para AUT-234

- [x] **Esquemas Pydantic**: Crear `AppointmentConfirmRequest` con banderas booleanas `send_whatsapp` y `send_email`.
- [x] **Servicio de Citas**: Implementar función `confirm_appointment(db, appointment_id, notification_options)` para actualizar `status_id = 2` y manejar errores de estado previo.
- [x] **Integración de Notificaciones**: Conectar la lógica de envío de mensajes de WhatsApp y Email mediante `FastAPI BackgroundTasks`.
- [x] **Ruta FastAPI**: Agregar la ruta `PATCH /appointments/{appointment_id}/confirm` en el router de `/appointments` con dependencias de autenticación/permisos.
- [x] **Pruebas Unitarias e Integración**: Escribir tests para verificación de cambio de estado y envío condicional de notificaciones.
