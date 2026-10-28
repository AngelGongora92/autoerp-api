# Especificación Backend - AUT-235

## Endpoint Modificado

### `GET /appointments/`

**Parámetros de Entrada (Query Params):**
- `assigned_to` (Int, Opcional): ID del empleado asignado.
- `start_date` (Datetime/Date, Opcional): Fecha/hora inicio para filtrar (inclusive).
- `end_date` (Datetime/Date, Opcional): Fecha/hora fin para filtrar (inclusive).

**Ejemplo de Petición:**
`GET /appointments/?start_date=2023-10-23T00:00:00&end_date=2023-10-29T23:59:59&assigned_to=5`

**Respuesta (200 OK):**
Lista de objetos de cita que caen dentro del rango especificado.
```json
[
  {
    "appointment_id": 101,
    "appointment_date": "2023-10-24T09:00:00",
    "reason": {
      "reason": "Mantenimiento 10k",
      "duration_minutes": 60
    },
    "status": {
      "status": "Confirmado"
    },
    "customer": {
      "id": 12,
      "name": "Juan Pérez"
    },
    "vehicle": {
      "id": 45,
      "plate": "ABC-1234"
    }
  }
]
```
