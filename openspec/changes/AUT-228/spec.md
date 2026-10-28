# Especificación Backend para AUT-228

### Endpoint: `GET /customers/search` 

#### Query Parameters:
- `q` (string, requerido): Término de búsqueda (Nombre, Apellido o Teléfono).
- `limit` (int, opcional, default=10): Cantidad máxima de resultados.

#### Respuesta (200 OK):
```json
[
  {
    "customer_id": 102,
    "first_name": "Juan",
    "last_name": "Pérez",
    "phone_number": "+525512345678",
    "email": "juan.perez@example.com"
  }
]
```

#### Modelos Pydantic:
- `CustomerSearchResponse`: `customer_id`, `first_name`, `last_name`, `phone_number`, `email`.
