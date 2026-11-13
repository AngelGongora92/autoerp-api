# Especificación Backend - AUT-237

## 1. POST /appointments/{appointment_id}/formalize
**Descripción:** Convierte los datos temporales de una cita en registros reales de `Customer` y `Vehicle`, actualizando la cita.

### Entrada (Body JSON):
```json
{
  "customer": {
    "first_name": "Juan",
    "last_name": "Pérez",
    "phone": "5551234567",
    "email": "juan.perez@example.com",
    "tax_id": "PERJ800101XXX"
  },
  "vehicle": {
    "vin": "1HGCR2F83HA000000",
    "license_plate": "ABC-123",
    "make": "Honda",
    "model": "Civic",
    "year": 2017
  }
}
```

### Salida (200 OK):
```json
{
  "appointment_id": 102,
  "customer_id": 45,
  "vehicle_id": 88,
  "message": "Cita formalizada exitosamente"
}
```

## 2. POST /work-orders/from-appointment/{appointment_id}
**Descripción:** Genera una nueva Orden de Servicio a partir de una cita formalizada.

### Respuestas de Error:
* **422 Unprocessable Entity** (Si la cita tiene datos temporales):
```json
{
  "detail": "La cita contiene datos temporales. Debe formalizar el cliente y vehículo antes de generar una orden de servicio.",
  "code": "APPOINTMENT_TEMPORARY_DATA"
}
```
