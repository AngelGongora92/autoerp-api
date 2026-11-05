# Propuesta Backend - AUT-242: Deduplicación y Formalización Asistida de Citas Web

## 1. Alcance Backend
El problema principal radica en que las citas originadas desde el portal web persisten datos de clientes y vehículos de forma temporal (`temp_fname`, `temp_lname`, `temp_phone`, `temp_email`, `temp_vehicle_data`) con `customer_id = NULL` y `vehicle_id = NULL`. Al momento de crear una orden de servicio a partir de la cita, el backend debe proveer las herramientas para buscar coincidencias, formalizar la cita y enlazar las entidades de dominio reales.

## 2. Decisiones de Arquitectura
- **Búsqueda de Coincidencias (Deduplicación):** Crear un endpoint optimizado `GET /customers/search` que permita consultar clientes por coincidencia exacta o parcial de teléfono (`temp_phone`) y/o nombre completo (`temp_fname` + `temp_lname`).
- **Formalización de Cita:** Endpoint `PATCH /appointments/{appointment_id}/formalize` que asigna `customer_id` y `vehicle_id` persistentes a la cita, desvinculando la dependencia de los campos temporales.
- **Integración Transaccional con Órdenes (`POST /orders/`):** Al procesar la creación de una orden de servicio que especifique `appointment_id`, el backend verificará y actualizará la cita a estado 'Atendida' o 'En Orden', validando que `customer_id` y `vehicle_id` estén presentes y asociados correctamente.
