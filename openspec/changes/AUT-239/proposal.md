# Propuesta Backend para AUT-239: Conversión de Cita a Orden mediante /orders/new

## Objetivo
Soportar el flujo de recepción física de vehículos permitiendo que la aplicación web consulte los detalles completos de una cita para precargar cliente, vehículo, kilometraje y motivos en la vista `/orders/new`. Al finalizar la creación de la orden (o al omitir la inspección), el backend debe vincular bidireccionalmente la orden con la cita y actualizar el estado de esta última a 'Atendida' de forma atómica.

## Alcance Backend
1. **Detalle de Cita (`GET /appointments/{appointment_id}`)**:
   - Proveer un endpoint que retorne la información completa de la cita, incluyendo cliente, vehículo, items/motivos precargados y datos temporales si aplican.
2. **Creación de Orden Vinculada (`POST /orders/`)**:
   - Aceptar un parámetro opcional `appointment_id` en la carga útil del request.
   - Ejecutar la creación de la orden, guardando los inventarios, kilometraje, combustible y daños.
   - En caso de recibir `appointment_id`, actualizar la cita asignando `order_id` y cambiando su estado a 'Atendida' (`ATTENDED`).
   - Garantizar la transacción en un único bloque de base de datos.
