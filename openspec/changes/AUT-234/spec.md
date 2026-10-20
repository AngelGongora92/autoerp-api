# Especificación OpenAPI / Backend para AUT-234

## Endpoint
`PATCH /appointments/{appointment_id}/confirm`

### Request Body (Pydantic Schema: `AppointmentConfirmRequest`)
```json
{
  "send_whatsapp": true,
  "send_email": false
}
```

### Response (200 OK - Pydantic Schema: `AppointmentResponse`)
```json
{
  "message": "Cita confirmada exitosamente",
  "appointment_id": 123,
  "status": {
    "status_id": 2,
    "status": "Confirmada"
  },
  "notifications_sent": {
    "whatsapp": true,
    "email": false
  }
}
```

### Respuestas de Error:
- `404 Not Found`: Si la cita no existe.
- `400 Bad Request`: Si la cita ya está confirmada o cancelada.
- `401 / 403`: Falta de autenticación o permisos insuficientes.
