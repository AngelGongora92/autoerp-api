# Especificación Técnica Backend - AUT-233

## 1. Base de Datos (SQLAlchemy & Alembic)
- **Tabla:** `appointments`
  - Agregar campo: `duration_minutes` (`Integer`, `nullable=False`, `server_default="30"`).

## 2. Esquemas Pydantic (`schemas/appointment.py`)
- **`AppointmentCreate`**:
  - `duration_minutes`: `Optional[int]` = None
  - `assigned_to`: `Optional[int]` = None
- **`AppointmentResponse`**:
  - Incluir `duration_minutes: int`.

## 3. Lógica de Negocio (`services/appointments.py`)
- **`check_advisor_availability(advisor_id: int, start_dt: datetime, duration: int, db: Session) -> bool`**:
  - Verifica si existe alguna cita activa donde `status != 'CANCELLED'` y exista empalme temporal.
- **`get_least_busy_available_advisor(start_dt: datetime, duration: int, db: Session) -> Optional[int]`**:
  - Obtiene los IDs de asesores activos libres en el rango.
  - Si no hay ninguno disponible, retorna `None`.
  - Cuenta las citas del día para cada uno de los asesores libres y retorna el ID con menor conteo (en empate, ID menor).

## 4. Endpoints

### `GET /appointments/availability`
- **Query Params:** `date` (Date, requerido), `assigned_to` (Int, opcional).
- **Respuesta:** Lista de bloques del día con su disponibilidad (`time_slot`, `is_available`, `available_advisors_count`).

### `POST /appointments/new-appointment/`
- Validar disponibilidad. Si no hay asesor disponible $\to$ HTTP 400 Bad Request (`"No hay asesores disponibles en el horario seleccionado"` o `"El asesor seleccionado ya cuenta con una cita en ese horario"`).
