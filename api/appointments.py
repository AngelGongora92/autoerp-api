from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import select, func
from api.database import get_db, Appointment, AppointmentReason, AppointmentStatus, Vehicle, Model, Customer
from .schemas.user import AppointmentCreate, AppointmentResponse, AppointmentStatusResponse, AppointmentReasonResponse
from sqlalchemy.orm import joinedload, Session
from api.notifications import send_whatsapp_confirmation, send_email_confirmation_brevo
from datetime import datetime
import datetime as dt_module
from zoneinfo import ZoneInfo
from pydantic import BaseModel

class RescheduleRequest(BaseModel):
    appointment_date: datetime
    send_whatsapp: bool = False
    send_email: bool = False

class ResendConfirmationRequest(BaseModel):
    send_whatsapp: bool = False
    send_email: bool = False

async def notify_appointment_confirmation(appointment: Appointment, send_whatsapp: bool, send_email: bool, db: Session):
    # Obtener cliente y vehículo de manera explícita (evita problemas de lazy loading)
    customer = None
    if appointment.customer_id:
        customer = db.get(Customer, appointment.customer_id)

    vehicle = None
    if appointment.vehicle_id:
        vehicle = db.get(Vehicle, appointment.vehicle_id)

    # 1. Nombre Cliente
    customer_name = appointment.temp_fname or "Cliente"
    if customer:
        if customer.is_company:
             customer_name = customer.cname or "Cliente"
        else:
             customer_name = f"{customer.fname or ''} {customer.lname or ''}".strip()

    # 2. Teléfono
    phone = appointment.temp_phone
    if not phone and customer:
        phone = customer.phone
    
    # 3. Fecha
    appt_dt = appointment.appointment_date
    if appt_dt.tzinfo is None:
        appt_dt = appt_dt.replace(tzinfo=dt_module.timezone.utc)
        
    local_tz = ZoneInfo("America/Mexico_City")
    local_appt_date = appt_dt.astimezone(local_tz)
    date_str = local_appt_date.strftime("%d/%m/%Y a las %H:%M")

    # 4. Vehículo
    vehicle_info = "Vehículo no especificado"
    if vehicle:
        try:
            make = vehicle.model.make.make if (vehicle.model and vehicle.model.make) else ""
            model = vehicle.model.model if vehicle.model else ""
            vehicle_info = f"{vehicle.year} {make} {model}".strip()
        except Exception:
            vehicle_info = "Vehículo Registrado"
    elif appointment.temp_vehicle_data and isinstance(appointment.temp_vehicle_data, dict):
        temp_v = appointment.temp_vehicle_data
        vehicle_info = f"{temp_v.get('year', '')} {temp_v.get('make', '')} {temp_v.get('model', '')}".strip()

    # Enviar notificación de WhatsApp si se solicita y hay teléfono
    if send_whatsapp and phone:
        await send_whatsapp_confirmation(phone, customer_name, date_str, vehicle_info, appointment.appointment_id)

    # Enviar notificación de correo por Brevo si se solicita y hay correo
    customer_email = appointment.temp_email
    if not customer_email and customer:
        customer_email = customer.email

    if send_email and customer_email:
        await send_email_confirmation_brevo(customer_email, customer_name, date_str, vehicle_info, appointment.appointment_id)


router = APIRouter()

@router.get("/", response_model=List[AppointmentResponse])
async def get_appointments(
    assigned_to: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Obtiene citas. Si se envía 'assigned_to', filtra por empleado.
    """
    stmt = (
        select(Appointment)
        .options(
            joinedload(Appointment.status),
            joinedload(Appointment.reasons),
            joinedload(Appointment.customer),  # Cargar la relación con el cliente
            joinedload(Appointment.vehicle)
                .joinedload(Vehicle.color), # Cargar el color del vehículo
            joinedload(Appointment.vehicle)
                .joinedload(Vehicle.model)
                .joinedload(Model.make) # Cargar el modelo y la marca del vehículo
        ) 
    )

    if assigned_to:
        stmt = stmt.where(Appointment.assigned_to == assigned_to)

    appointments = db.execute(stmt).scalars().unique().all()
    return appointments

@router.post("/new-appointment/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Crea una nueva cita en la base de datos.
    """
    # Validación de fecha y hora futura
    now = datetime.now(dt_module.timezone.utc)
    appt_date = appointment_data.appointment_date
    if appt_date.tzinfo is None:
        appt_date = appt_date.replace(tzinfo=dt_module.timezone.utc)
    else:
        appt_date = appt_date.astimezone(dt_module.timezone.utc)
        
    if appt_date < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden agendar citas en el pasado."
        )

    # 1. Extraer los datos y separar la lista de IDs de razones y flags de notificación
    data = appointment_data.model_dump()
    reason_ids = data.pop("reason_ids", [])
    send_whatsapp = data.pop("send_whatsapp", False)
    send_email = data.pop("send_email", False)

    # 2. Crear la instancia de la cita (sin las razones todavía)
    new_appointment = Appointment(**data)

    # 3. Buscar las razones en la DB y asignarlas (SQLAlchemy maneja la tabla intermedia)
    if reason_ids:
        reasons = db.scalars(select(AppointmentReason).where(AppointmentReason.reason_id.in_(reason_ids))).all()
        new_appointment.reasons = reasons

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    # Enviar notificaciones si se solicita
    await notify_appointment_confirmation(new_appointment, send_whatsapp, send_email, db)

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

@router.get("/public/{appointment_id}", response_model=AppointmentResponse)
async def get_public_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene los detalles públicos de una cita (sin requerir inicio de sesión).
    """
    stmt = (
        select(Appointment)
        .options(
            joinedload(Appointment.status),
            joinedload(Appointment.reasons),
            joinedload(Appointment.customer),
            joinedload(Appointment.vehicle)
                .joinedload(Vehicle.color),
            joinedload(Appointment.vehicle)
                .joinedload(Vehicle.model)
                .joinedload(Model.make)
        )
        .where(Appointment.appointment_id == appointment_id)
    )
    appointment = db.execute(stmt).scalars().unique().first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return appointment

@router.post("/public/{appointment_id}/confirm")
async def confirm_public_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
):
    """
    Confirma una cita públicamente (cambia status_id a 2).
    """
    appointment = db.scalar(select(Appointment).where(Appointment.appointment_id == appointment_id))
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    appointment.status_id = 2  # Confirmado
    db.commit()
    return {"message": "Cita confirmada exitosamente"}

@router.post("/public/{appointment_id}/cancel")
async def cancel_public_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
):
    """
    Cancela una cita públicamente (cambia status_id a 3).
    """
    appointment = db.scalar(select(Appointment).where(Appointment.appointment_id == appointment_id))
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Verificar si existe el estado 3 en la base de datos, si no, lo insertamos
    status_canceled = db.scalar(select(AppointmentStatus).where(AppointmentStatus.status_id == 3))
    if not status_canceled:
      status_canceled = AppointmentStatus(status_id=3, status="cancelado")
      db.add(status_canceled)
      db.flush()  # Usar flush para asegurar que el registro exista antes de asociarlo
        
    appointment.status_id = 3  # Cancelado
    db.commit()
    return {"message": "Cita cancelada exitosamente"}


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    appointment_id: int,
    payload: RescheduleRequest,
    db: Session = Depends(get_db)
):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Validación de fecha y hora futura
    now = datetime.now(dt_module.timezone.utc)
    appt_date = payload.appointment_date
    if appt_date.tzinfo is None:
        appt_date = appt_date.replace(tzinfo=dt_module.timezone.utc)
    else:
        appt_date = appt_date.astimezone(dt_module.timezone.utc)
        
    if appt_date < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden reprogramar citas en el pasado."
        )

    appointment.appointment_date = payload.appointment_date
    appointment.rescheduled_count = (appointment.rescheduled_count or 0) + 1
    
    # Al reprogramar, vuelve a estar "sin confirmar"
    appointment.status_id = 1
    
    db.commit()
    db.refresh(appointment)
    
    # Enviar notificaciones si se solicita
    await notify_appointment_confirmation(appointment, payload.send_whatsapp, payload.send_email, db)
    
    return appointment


@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
        
    # Verificar si existe el estado 3 (cancelado) en la base de datos
    status_canceled = db.scalar(select(AppointmentStatus).where(AppointmentStatus.status_id == 3))
    if not status_canceled:
        status_canceled = AppointmentStatus(status_id=3, status="cancelado")
        db.add(status_canceled)
        db.flush()
        
    appointment.status_id = 3  # Cancelado
    db.commit()
    db.refresh(appointment)
    return appointment


@router.post("/{appointment_id}/resend-confirmation")
async def resend_appointment_confirmation(
    appointment_id: int,
    payload: ResendConfirmationRequest,
    db: Session = Depends(get_db)
):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
        
    await notify_appointment_confirmation(appointment, payload.send_whatsapp, payload.send_email, db)
    return {"status": "ok", "message": "Confirmación reenviada correctamente"}