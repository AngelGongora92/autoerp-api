# Tareas Backend para AUT-242

- [ ] **Modelos Pydantic:** Crear `CustomerSearchQuery` y `AppointmentFormalizeSchema`.
- [ ] **Endpoint de Búsqueda:** Implementar `GET /customers/search` con consultas ILIKE/Trigram en PostgreSQL para `phone` y `name`.
- [ ] **Endpoint de Formalización:** Crear `PATCH /appointments/{appointment_id}/formalize` para vincular cliente y vehículo a la cita.
- [ ] **Actualización de Servicio de Órdenes:** Modificar la lógica de `POST /orders/` para marcar la cita como atendida al asociarla con la nueva orden.
- [ ] **Pruebas Unitarias e Integración:** Escribir tests en Pytest verificando el flujo completo de formalización y creación de orden desde cita temporal.
