from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import select, func
from api.database import get_db, Appointment, AppointmentReason, AppointmentStatus, Vehicle, Model
from .schemas.user import AppointmentCreate, AppointmentResponse, AppointmentStatusResponse, AppointmentReasonResponse
from sqlalchemy.orm import joinedload, Session
from api.notifications import send_whatsapp_confirmation


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
    # 1. Extraer los datos y separar la lista de IDs de razones
    data = appointment_data.model_dump()
    reason_ids = data.pop("reason_ids", [])

    # 2. Crear la instancia de la cita (sin las razones todavía)
    new_appointment = Appointment(**data)

    # 3. Buscar las razones en la DB y asignarlas (SQLAlchemy maneja la tabla intermedia)
    if reason_ids:
        reasons = db.scalars(select(AppointmentReason).where(AppointmentReason.reason_id.in_(reason_ids))).all()
        new_appointment.reasons = reasons

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    # --- Preparar datos para notificación ---
    # 1. Nombre Cliente
    customer_name = new_appointment.temp_fname or "Cliente"
    if new_appointment.customer:
        if new_appointment.customer.is_company:
             customer_name = new_appointment.customer.cname or "Cliente"
        else:
             customer_name = f"{new_appointment.customer.fname or ''} {new_appointment.customer.lname or ''}".strip()

    # 2. Teléfono
    phone = new_appointment.temp_phone
    if not phone and new_appointment.customer:
        phone = new_appointment.customer.phone
    
    # 3. Fecha
    date_str = new_appointment.appointment_date.strftime("%d/%m/%Y a las %H:%M")

    # 4. Vehículo
    vehicle_info = "Vehículo no especificado"
    if new_appointment.vehicle:
        try:
            v = new_appointment.vehicle
            make = v.model.make.make if (v.model and v.model.make) else ""
            model = v.model.model if v.model else ""
            vehicle_info = f"{v.year} {make} {model}".strip()
        except Exception:
            vehicle_info = "Vehículo Registrado"
    elif new_appointment.temp_vehicle_data and isinstance(new_appointment.temp_vehicle_data, dict):
        data = new_appointment.temp_vehicle_data
        vehicle_info = f"{data.get('year', '')} {data.get('make', '')} {data.get('model', '')}".strip()

    # Enviar notificación de WhatsApp en segundo plano si hay teléfono
    if phone:
        background_tasks.add_task(send_whatsapp_confirmation, phone, customer_name, date_str, vehicle_info)

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