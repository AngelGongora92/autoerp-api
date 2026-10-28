# Especificación Técnica Backend - AUT-231

## 1. Modelo de Base de Datos (SQLAlchemy)
```python
class AppointmentItem(Base):
    __tablename__ = 'appointment_items'

    appointment_item_id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey('appointments.appointment_id', ondelete='CASCADE'), nullable=False, index=True)
    reason_id = Column(Integer, ForeignKey('appointment_reasons.reason_id', ondelete='SET NULL'), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    appointment = relationship('Appointment', back_populates='items')
    reason = relationship('AppointmentReason')
```

## 2. Esquemas Pydantic (`api/schemas/appointments.py`)
```python
class AppointmentItemCreate(BaseModel):
    reason_id: int
    notes: Optional[str] = None

class AppointmentItemResponse(BaseModel):
    appointment_item_id: int
    reason_id: Optional[int]
    notes: Optional[str]
    reason: Optional[AppointmentReasonResponse] = None

    class Config:
        from_attributes = True

class AppointmentCreate(BaseModel):
    appointment_date: datetime
    assigned_to: Optional[int] = None
    customer_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    reason_ids: Optional[List[int]] = None  # Deprecated (Legacy Support)
    items: Optional[List[AppointmentItemCreate]] = None  # Nuevo campo
```

## 3. Comportamiento en Controlador (`api/appointments.py`)
- **POST /appointments/new-appointment/**:
  - Si `payload.items` está presente, crear instancias de `AppointmentItem` con sus notas.
  - Si solo se recibe `payload.reason_ids`, mapear cada ID a `AppointmentItem(reason_id=id, notes=None)`.
- **GET /appointments/**:
  - Modificar las consultas SQLAlchemy usando `options(joinedload(Appointment.items).joinedload(AppointmentItem.reason))` para evitar problemas de N+1 queries.
