from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import select, func
from api.database import get_db, Appointment, AppointmentReason, AppointmentStatus
from .schemas.user import AppointmentCreate, AppointmentResponse, AppointmentStatusResponse, AppointmentReasonResponse
from sqlalchemy.orm import joinedload, Session


router = APIRouter()

@router.get("/", response_model=List[AppointmentResponse])
async def get_appointments(
    db: Session = Depends(get_db),
):
    """
    Obtiene todas las citas en la base de datos.
    """
    appointments = db.execute(
        select(Appointment)
        .options(
            joinedload(Appointment.status),
            joinedload(Appointment.reason)
        )
    ).scalars().all()
    return appointments

@router.post("/new-appointment/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
):
    """
    Crea una nueva cita en la base de datos.
    """
    # Simplemente desempaca todos los datos del esquema en el modelo.
    # Pydantic y SQLAlchemy se encargarán de mapear los campos correctos.
    new_appointment = Appointment(**appointment_data.model_dump())
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    return new_appointment

@router.get("/reasons/", response_model=List[AppointmentReasonResponse])
async def get_appointment_reasons(
    db: Session = Depends(get_db),
):
    """
    Obtiene todas las razones de citas disponibles.
    """
    reasons = db.execute(select(AppointmentReason)).scalars().all()
    return reasons