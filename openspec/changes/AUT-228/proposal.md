# Propuesta Backend para AUT-228

## Resumen
Permitir la búsqueda unificada de clientes tanto por nombre completo como por número telefónico utilizando una consulta parcial (ILIKE/trigram search) sobre la tabla de clientes.

## Enfoque Técnico
- Endpoint: `GET /customers/search`
- Query Parameter: `q` (string, min_length=2)
- Lógica de búsqueda: Filtro OR con `ILIKE` en `first_name`, `last_name` y `phone_number` (normalizando espacios y caracteres no numéricos si aplica).
- Límite de resultados: Paginado o top 10 resultados para autocompletado rápido.
