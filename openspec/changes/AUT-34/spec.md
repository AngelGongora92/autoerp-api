# Especificación Técnica - AUT-34

### 1. Modelos de Base de Datos (Existentes / Modificaciones)
No se requieren cambios en la estructura de la tabla `appointments`, pero se asume la existencia de los siguientes campos:
* `status_id` (FK a `appointment_status`)
* `appointment_date` (DateTime)
* `assigned_to` (FK a `users`/`employees`)

### 2. Esquemas Pydantic

```python
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class AppointmentUpdateSchema(BaseModel):
    appointment_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    reason_id: Optional[int] = None

class AppointmentCancelSchema(BaseModel):
    cancellation_reason: Optional[str] = None
```

### 3. Nuevos Endpoints

#### `PATCH /appointments/{appointment_id}/`
* **Descripción:** Reagenda o actualiza los datos de una cita.
* **Seguridad:** Requiere token JWT (Permiso: `reagenda_cita` o rol `asesor`).
* **Input (Body):** `AppointmentUpdateSchema`
* **Output (200 OK):** Detalle de la cita actualizada.
* **Errores:** 
  * `404 Not Found`: Si la cita no existe.
  * `400 Bad Request`: Si el empleado no tiene disponibilidad en el nuevo horario o si la fecha es en el pasado.

#### `POST /appointments/{appointment_id}/cancel/`
* **Descripción:** Cancela una cita cambiando su estado a 'Cancelada'.
* **Seguridad:** Requiere token JWT (Permiso: `cancela_cita` o rol `asesor`).
* **Input (Body):** `AppointmentCancelSchema` (Opcional)
* **Output (200 OK):** `{ "message": "Cita cancelada exitosamente", "appointment_id": int }`
* **Errores:**
  * `404 Not Found`: Si la cita no existe.
  * `400 Bad Request`: Si la cita ya está cancelada o finalizada.
