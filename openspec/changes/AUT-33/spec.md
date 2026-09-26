# Especificación Backend para AUT-33

## 1. Modelos de Base de Datos (SQLAlchemy)

```python
class AppointmentConfig(Base):
    __tablename__ = 'appointment_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(Time, nullable=False, default="08:00:00")
    end_time = Column(Time, nullable=False, default="18:00:00")
    allowed_days = Column(ARRAY(Integer), nullable=False, default=[1,2,3,4,5]) # 0=Domingo, 1=Lunes, etc.
    default_duration_minutes = Column(Integer, nullable=False, default=30)
```

## 2. Modelos Pydantic

```python
class AppointmentConfigSchema(BaseModel):
    start_time: time
    end_time: time
    allowed_days: List[int]
    default_duration_minutes: int

    class Config:
        orm_mode = True

class AppointmentReasonCreate(BaseModel):
    reason: str
    duration_minutes: int
```

## 3. Nuevos Endpoints y Modificaciones

### `GET /appointments/config`
* **Descripción:** Obtiene la configuración actual de citas.
* **Salida:** `AppointmentConfigSchema`

### `PUT /appointments/config`
* **Descripción:** Actualiza la configuración global de citas.
* **Entrada:** `AppointmentConfigSchema`
* **Salida:** `AppointmentConfigSchema`

### `POST /appointments/reasons/`
* **Descripción:** Crea un nuevo tipo de cita con su duración estimada.
* **Entrada:** `AppointmentReasonCreate`
* **Salida:** `AppointmentReasonSchema`

### `POST /appointments/new-appointment/` (Modificado)
* **Lógica de Validación Backend:**
  1. Obtener la configuración activa desde `appointment_configs`.
  2. Obtener la duración estimada desde `appointment_reasons` usando el `reason_id`. Si no se encuentra, usar `default_duration_minutes`.
  3. Calcular `end_date = appointment_date + duration_minutes`.
  4. **Validar Día:** `appointment_date.weekday()` debe estar en `allowed_days`.
  5. **Validar Rango Horario:** `appointment_date.time() >= start_time` y `end_date.time() <= end_time`.
  6. **Validar Solapamiento:** Consultar si existe alguna cita en la tabla `appointments` para el mismo `assigned_to` donde se cumpla:
     `(appointment_date < existing_end_date) AND (end_date > existing_start_date)`.
  7. Si alguna validación falla, retornar `HTTP 400 Bad Request` con un mensaje descriptivo.
