# Propuesta Backend para AUT-237: Gestión de Citas con Datos Temporales

## Contexto y Problemática
Las citas creadas vía web pública o WhatsApp contienen información de cliente y vehículo almacenada en campos temporales (`temp_fname`, `temp_phone`, `temp_vehicle_data`) con `customer_id = null` y `vehicle_id = null`. Las Órdenes de Servicio requieren relaciones estrictas (`FOREIGN KEY`) a las tablas `customers` y `vehicles`.

## Solución Seleccionada: Opción A / C (Validación con Endpoint de Formalización Atómica)
1. **Validación Estricta al Generar Orden:** El endpoint `POST /work-orders/from-appointment/{appointment_id}` validará que la cita tenga asignados `customer_id` y `vehicle_id`. En caso contrario, retornará un error `422 Unprocessable Entity` con un código de error de dominio (`APPOINTMENT_TEMPORARY_DATA`).
2. **Endpoint de Formalización:** Se implementa `POST /appointments/{appointment_id}/formalize`, permitiendo al asesor confirmar o completar los datos requeridos. En una sola transacción de base de datos:
   - Crea el registro en `customers` (o vincula uno existente por RFC/Teléfono).
   - Crea el registro en `vehicles` (vinculado al cliente).
   - Actualiza la cita estableciendo `customer_id`, `vehicle_id` y limpiando/conservando los datos temporales.
3. **Creación Subsecuente de Orden:** Una vez formalizada la cita, el frontend puede llamar exitosamente a la creación de la Orden de Servicio.
