# Tareas Backend - AUT-237

- [ ] **Schemas Pydantic:** Crear `FormalizeAppointmentSchema`, `CustomerCreateSchema` y `VehicleCreateSchema` para validación de entrada.
- [ ] **Servicio de Formalización:** Implementar lógica de negocio en `AppointmentService.formalize_appointment` gestionando la transacción DB atómica (crear cliente, crear vehículo, actualizar cita).
- [ ] **Endpoint Formalizar:** Crear ruta `POST /appointments/{appointment_id}/formalize` en el router de citas.
- [ ] **Validación en Work Order:** Modificar el endpoint de creación de orden de servicio desde cita `POST /work-orders/from-appointment/{appointment_id}` para verificar que `customer_id` y `vehicle_id` no sean nulos.
- [ ] **Pruebas Unitarias e Integración:** Escribir tests con pytest verificando la conversión correcta de datos temporales a entidades permanentes y la prevención de creación de orden con datos temporales.
