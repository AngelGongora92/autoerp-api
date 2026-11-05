# Especificación Backend para AUT-244

## 1. Esquemas Pydantic

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

class AppointmentRescheduleRequest(BaseModel):
    new_appointment_date: datetime = Field(..., description="Nueva fecha y hora para la cita")
    notify_whatsapp: bool = Field(default=True, description="Indica si se envía notificación por WhatsApp")
    notify_email: bool = Field(default=True, description="Indica si se envía notificación por Correo")

    @field_validator('new_appointment_date')
    def validate_future_date(cls, v: datetime) -> datetime:
        # Asumimos validación timezone aware o UTC
        if v < datetime.now(v.tzinfo):
            raise ValueError("La nueva fecha y hora debe ser futura.")
        return v

class AppointmentRescheduleResponse(BaseModel):
    appointment_id: int
    appointment_date: datetime
    status: str
    message: str
```

## 2. Endpoint FastAPI

```python
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.patch("/{appointment_id}/reschedule", response_model=AppointmentRescheduleResponse)
def reschedule_appointment(
    appointment_id: int,
    payload: AppointmentRescheduleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada")
    
    if appointment.status in ["CANCELLED", "COMPLETED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede reagendar una cita con estado {appointment.status}"
        )
    
    # Actualizar fecha de la cita
    appointment.appointment_date = payload.new_appointment_date
    db.commit()
    db.refresh(appointment)
    
    # Tareas en segundo plano para notificaciones
    if payload.notify_whatsapp:
        background_tasks.add_task(send_whatsapp_reschedule_notification, appointment_id)
    if payload.notify_email:
        background_tasks.add_task(send_email_reschedule_notification, appointment_id)
        
    return AppointmentRescheduleResponse(
        appointment_id=appointment.id,
        appointment_date=appointment.appointment_date,
        status=appointment.status,
        message="Cita reagendada exitosamente"
    )
```
