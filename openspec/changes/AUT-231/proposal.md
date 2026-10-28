# Propuesta Backend: Manejo de Motivos de Cita como Items con Notas Individuales (AUT-231)

## 1. Resumen
Se propone transformar la relación Many-to-Many entre citas y motivos (`appointment_reasons_link`) en una entidad dedicada de items de cita (`appointment_items`). Esta estructura permitirá adjuntar notas u observaciones específicas por motivo registrado, preparando los datos para ser convertidos posteriormente en partidas de Órdenes de Servicio (`order_items`).

## 2. Estrategia de BD y Migración Alembic
- Se creará la tabla `appointment_items` con campos `appointment_item_id`, `appointment_id`, `reason_id`, `notes` y `created_at`.
- Se creará un índice en `appointment_id` para acelerar las lecturas.
- La migración de Alembic copiará los datos de `appointment_reasons_link` a `appointment_items` asignando `notes = NULL` para garantizar que no haya pérdida de información histórica.

## 3. Compatibilidad e Integración en API
- **Retrocompatibilidad**: En `AppointmentCreate`, se soportará tanto el nuevo arreglo `items` como el campo legado `reason_ids`. Si el cliente envía `reason_ids`, el controlador los convertirá automáticamente a ítems con `notes=None`.
- **Notificaciones y Lecturas**: Se mantendrá la propiedad calculada `reasons` en las respuestas para evitar romper integraciones o plantillas de correo/WhatsApp vigentes.
