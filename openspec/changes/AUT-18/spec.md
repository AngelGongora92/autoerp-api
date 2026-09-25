# Especificación de API para AUT-18

### 1. Obtener Disponibilidad de Empleado

* **Endpoint:** `GET /schedules/availability/{employee_id}`
* **Query Params:**
  * `date` (String, Requerido): Fecha en formato `YYYY-MM-DD`.
* **Respuesta (200 OK):**
```json
{
  "employee_id": 12,
  "date": "2023-10-27",
  "working_hours": [
    {
      "start_time": "09:00:00",
      "end_time": "14:00:00"
    },
    {
      "start_time": "15:00:00",
      "end_time": "18:00:00"
    }
  ],
  "busy_slots": [
    {
      "start_time": "10:00:00",
      "end_time": "11:00:00",
      "appointment_id": 45
    }
  ]
}
```

### 2. Modificación de Creación de Cita

* **Endpoint:** `POST /appointments/new-appointment/`
* **Validaciones Backend Adicionales:**
  * Buscar el `duration_minutes` del `reason_id` provisto.
  * Si no existe o es `<= 0`, retornar `400 Bad Request` con detalle: `"El motivo de cita seleccionado no tiene una duración válida."`
  * Si `assigned_to` está presente, verificar que el rango `[appointment_date, appointment_date + duration_minutes]` esté dentro de los `working_hours` del empleado y no se cruce con ningún bloque de `busy_slots`.
  * Si falla la validación de horario, retornar `409 Conflict` con detalle: `"El asesor no está disponible en el horario seleccionado."`
