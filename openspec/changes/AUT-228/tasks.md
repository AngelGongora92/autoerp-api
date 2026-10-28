# Tareas Backend para AUT-228

1. [ ] Definir esquema Pydantic `CustomerSearchResponse`.
2. [ ] Crear/Actualizar endpoint `GET /customers/search` en el router de clientes (`src/api/v1/endpoints/customers.py`).
3. [ ] Implementar la consulta SQLAlchemy utilizando `or_` y `ilike` para filtrar por `first_name`, `last_name` y `phone_number`.
4. [ ] Agregar índices en PostgreSQL si fuera necesario (`phone_number`, gin_trgm_ops) para optimizar la búsqueda rápida.
5. [ ] Escribir pruebas unitarias e integración para validar búsquedas por nombre, teléfono y combinaciones parcialmente coincidentes.
