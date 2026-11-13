# Especificación Técnica Backend - AUT-245

## 1. Migración de Base de Datos (Alembic)
```python
# alembic/versions/xxxx_add_public_portal_enabled.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('appointment_settings', sa.Column('public_portal_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')))

def downgrade():
    op.drop_column('appointment_settings', 'public_portal_enabled')
```

## 2. Endpoints de Configuración (Existentes - Actualizados)

### `GET /settings/appointments`
- **Auth:** Requiere JWT
- **Respuesta 200 OK:** Incluye `public_portal_enabled: bool`.

### `PUT /settings/appointments`
- **Auth:** Requiere JWT
- **Body:** Incluye opcionalmente `public_portal_enabled: bool`.

---

## 3. Endpoints Públicos (Nuevos - Sin Autenticación)

### `GET /appointments/public/config`
- **Query Params:** `company_id` (Int, Requerido)
- **Respuesta 200 OK:**
```json
{
  "company_name": "AutoERP Workshop",
  "public_portal_enabled": true,
  "allowed_days": [1, 2, 3, 4, 5],
  "slot_duration_minutes": 30,
  "reasons": [
    {
      "reason_id": 1,
      "reason": "Mantenimiento Preventivo",
      "duration_minutes": 60
    }
  ]
}
```
- **Respuesta 403 Forbidden:**
```json
{
  "detail": "El portal público de citas se encuentra deshabilitado para este taller."
}
```

### `GET /appointments/public/availability`
- **Query Params:**
  - `company_id` (Int, Requerido)
  - `date` (String YYYY-MM-DD, Requerido)
  - `reason_ids` (List[Int], Opcional)
- **Respuesta 200 OK:**
```json
{
  "date": "2024-06-15",
  "available_slots": ["09:00", "10:00", "11:00", "15:00"]
}
```
- **Respuesta 403 Forbidden:** Si el portal está desactivado.

### `POST /appointments/public`
- **Body JSON:**
```json
{
  "company_id": 1,
  "appointment_date": "2024-06-15T09:00:00",
  "reason_ids": [1],
  "temp_fname": "Carlos",
  "temp_lname": "Mendoza",
  "temp_cname": null,
  "temp_phone": "+525598765432",
  "temp_email": "carlos.mendoza@example.com",
  "temp_vehicle_data": {
    "make": "Nissan",
    "model": "Versa",
    "year": 2021,
    "plate": "XYZ-9876",
    "color": "Gris",
    "notes": "Revisión de frenos y cambio de aceite"
  }
}
```
- **Respuesta 201 Created:**
```json
{
  "appointment_id": 1050,
  "message": "Cita agendada exitosamente",
  "status": "Sin confirmar",
  "appointment_date": "2024-06-15T09:00:00"
}
```
- **Respuestas de Error:**
  - `403 Forbidden`: Portal deshabilitado.
  - `400 Bad Request`: Fecha pasada, día no permitido o sin asesores disponibles.
