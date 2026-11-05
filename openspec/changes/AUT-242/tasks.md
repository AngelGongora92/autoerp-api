# Tareas Backend para AUT-242

- [x] **Modelos Pydantic:** Crear `CustomerSearchQuery` y `AppointmentFormalizeSchema`.
- [x] **Endpoint de Búsqueda:** Implementar `GET /customers/search` con consultas ILIKE/Trigram en PostgreSQL para `phone` y `name`.
- [x] **Endpoint de Formalización:** Crear `PATCH /appointments/{appointment_id}/formalize` para vincular cliente y vehículo a la cita.
- [x] **Actualización de Servicio de Órdenes:** Modificar la lógica de `POST /orders/` para marcar la cita como atendida al asociarla con la nueva orden.
- [x] **Pruebas Unitarias e Integración:** Escribir tests en Pytest verificando el flujo completo de formalización y creación de orden desde cita temporal.
