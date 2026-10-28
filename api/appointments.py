from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from sqlalchemy import select, func
from api.database import get_db, Appointment, AppointmentItem, AppointmentReason, AppointmentStatus, Vehicle, Model, Customer, User, CompanySettings, Employee
from api.auth_deps import get_current_user
from .schemas.appointments import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatusResponse,
    AppointmentReasonResponse,
    AppointmentReasonCreate,
    AppointmentReasonUpdate,
    AppointmentItemCreate,
    AppointmentItemResponse,
    TimeSlotAvailability,
    AppointmentConfirmRequest,
)
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

class CancelRequest(BaseModel):
    cancellation_reason: Optional[str] = None

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


def check_advisor_availability(
    advisor_id: int,
    start_dt: datetime,
    duration_minutes: int,
    db: Session,
    exclude_appointment_id: Optional[int] = None
) -> bool:
    """
    Verifica si un asesor específico está libre en el rango [start_dt, start_dt + duration_minutes].
    Retorna True si está libre, False si tiene empalme con otra cita activa (no cancelada).
    """
    if start_dt.tzinfo is None:
        new_start = start_dt.replace(tzinfo=dt_module.timezone.utc)
    else:
        new_start = start_dt.astimezone(dt_module.timezone.utc)

    new_end = new_start + dt_module.timedelta(minutes=duration_minutes)

    window_start = new_start - dt_module.timedelta(days=1)
    window_end = new_end + dt_module.timedelta(days=1)

    stmt = select(Appointment).where(
        Appointment.assigned_to == advisor_id,
        Appointment.appointment_date >= window_start,
        Appointment.appointment_date <= window_end,
        Appointment.status_id != 3  # Excluir canceladas
    )
    if exclude_appointment_id:
        stmt = stmt.where(Appointment.appointment_id != exclude_appointment_id)

    existing_appts = db.scalars(stmt).all()

    for appt in existing_appts:
        appt_start = appt.appointment_date
        if appt_start.tzinfo is None:
            appt_start = appt_start.replace(tzinfo=dt_module.timezone.utc)
        else:
            appt_start = appt_start.astimezone(dt_module.timezone.utc)

        appt_duration = appt.duration_minutes if (appt.duration_minutes and appt.duration_minutes > 0) else 30
        appt_end = appt_start + dt_module.timedelta(minutes=appt_duration)

        # Condición estándar de solapamiento: (start_a < end_b) AND (end_a > start_b)
        if (appt_start < new_end) and (appt_end > new_start):
            return False

    return True


def get_least_busy_available_advisor(
    start_dt: datetime,
    duration_minutes: int,
    company_id: Optional[int],
    db: Session
) -> Optional[int]:
    """
    Busca entre todos los asesores activos aquellos sin conflicto de horario,
    y retorna el ID de aquel con menor cantidad de citas agendadas en ese mismo día (Least Busy).
    """
    query = select(Employee).where(Employee.is_active == True)
    if company_id:
        query = query.where(Employee.company_id == company_id)

    # Filtrar asesores de servicio (position_id == 1)
    advisors = db.scalars(query.where(Employee.position_id == 1)).all()
    if not advisors:
        advisors = db.scalars(query).all()

    if not advisors:
        return None

    # Filtrar solo asesores libres
    available_advisors = [
        adv for adv in advisors
        if check_advisor_availability(adv.employee_id, start_dt, duration_minutes, db)
    ]

    if not available_advisors:
        return None

    # Calcular rango del día en la zona horaria local de la empresa
    local_tz = ZoneInfo("America/Mexico_City")
    local_dt = start_dt.astimezone(local_tz) if start_dt.tzinfo else start_dt.replace(tzinfo=dt_module.timezone.utc).astimezone(local_tz)

    day_start = datetime(local_dt.year, local_dt.month, local_dt.day, 0, 0, 0, tzinfo=local_tz).astimezone(dt_module.timezone.utc)
    day_end = datetime(local_dt.year, local_dt.month, local_dt.day, 23, 59, 59, 999999, tzinfo=local_tz).astimezone(dt_module.timezone.utc)

    advisor_counts = []
    for adv in available_advisors:
        count = db.scalar(
            select(func.count(Appointment.appointment_id)).where(
                Appointment.assigned_to == adv.employee_id,
                Appointment.appointment_date >= day_start,
                Appointment.appointment_date <= day_end,
                Appointment.status_id != 3
            )
        ) or 0
        advisor_counts.append((count, adv.employee_id))

    # Ordenar por conteo de citas ascendente y luego por ID
    advisor_counts.sort(key=lambda x: (x[0], x[1]))
    return advisor_counts[0][1]


def parse_date_param(val: Optional[Union[str, datetime, dt_module.date]], is_end: bool = False) -> Optional[datetime]:
    if not val:
        return None
    local_tz = ZoneInfo("America/Mexico_City")
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=local_tz)
        return val
    if isinstance(val, dt_module.date):
        t = dt_module.time.max if is_end else dt_module.time.min
        return datetime.combine(val, t, tzinfo=local_tz)
    if isinstance(val, str):
        val_str = val.strip()
        if not val_str:
            return None
        # Formato ISO simple YYYY-MM-DD
        if len(val_str) == 10 and val_str.count("-") == 2:
            try:
                d = dt_module.date.fromisoformat(val_str)
                t = dt_module.time.max if is_end else dt_module.time.min
                return datetime.combine(d, t, tzinfo=local_tz)
            except Exception:
                pass
        try:
            iso_clean = val_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso_clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=local_tz)
            return dt
        except Exception:
            return None
    return None


router = APIRouter()


@router.get("/", response_model=List[AppointmentResponse])
async def get_appointments(
    assigned_to: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene citas del tenant. Si se envía 'assigned_to', filtra por empleado.
    Si se envían 'start_date' y/o 'end_date', filtra por el rango de fechas (AUT-235).
    """
    stmt = (
        select(Appointment)
        .options(
            joinedload(Appointment.status),
            joinedload(Appointment.items).joinedload(AppointmentItem.reason),
            joinedload(Appointment.assignee),
            joinedload(Appointment.customer),  # Cargar la relación con el cliente
            joinedload(Appointment.vehicle)
                .joinedload(Vehicle.color), # Cargar el color del vehículo
            joinedload(Appointment.vehicle)
                .joinedload(Vehicle.model)
                .joinedload(Model.make) # Cargar el modelo y la marca del vehículo
        ) 
        .where(Appointment.company_id == current_user.company_id)
    )

    if assigned_to:
        stmt = stmt.where(Appointment.assigned_to == assigned_to)

    start_dt = parse_date_param(start_date, is_end=False)
    if start_dt:
        stmt = stmt.where(Appointment.appointment_date >= start_dt)

    end_dt = parse_date_param(end_date, is_end=True)
    if end_dt:
        stmt = stmt.where(Appointment.appointment_date <= end_dt)

    stmt = stmt.order_by(Appointment.appointment_date.asc())

    appointments = db.execute(stmt).scalars().unique().all()
    return appointments


@router.get("/availability", response_model=List[TimeSlotAvailability])
async def get_appointment_availability(
    date: dt_module.date,
    assigned_to: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Consulta la disponibilidad de horarios para una fecha dada y opcionalmente un asesor.
    """
    settings = db.query(CompanySettings).filter(CompanySettings.id == 1).first()

    start_time = getattr(settings, 'appointment_start_time', None) or dt_module.time(8, 0)
    end_time = getattr(settings, 'appointment_end_time', None) or dt_module.time(18, 0)
    slot_duration = getattr(settings, 'slot_duration_minutes', 30) or 30
    allowed_days = getattr(settings, 'allowed_days', [0, 1, 2, 3, 4, 5])
    if allowed_days is None:
        allowed_days = [0, 1, 2, 3, 4, 5]

    local_tz = ZoneInfo("America/Mexico_City")
    is_day_allowed = date.weekday() in allowed_days

    # Lista de asesores de la empresa
    all_advisors = []
    if not assigned_to:
        adv_query = select(Employee).where(
            Employee.is_active == True,
            Employee.company_id == current_user.company_id,
            Employee.position_id == 1
        )
        all_advisors = db.scalars(adv_query).all()
        if not all_advisors:
            all_advisors = db.scalars(
                select(Employee).where(
                    Employee.is_active == True,
                    Employee.company_id == current_user.company_id
                )
            ).all()

    slots: List[TimeSlotAvailability] = []
    current_min = start_time.hour * 60 + start_time.minute
    end_min = end_time.hour * 60 + end_time.minute
    now_utc = datetime.now(dt_module.timezone.utc)

    while current_min < end_min:
        h = current_min // 60
        m = current_min % 60
        slot_time = dt_module.time(h, m)
        slot_str = slot_time.strftime("%H:%M")

        slot_dt_local = datetime.combine(date, slot_time, tzinfo=local_tz)
        slot_dt_utc = slot_dt_local.astimezone(dt_module.timezone.utc)

        if not is_day_allowed or slot_dt_utc < now_utc:
            slots.append(TimeSlotAvailability(
                time_slot=slot_str,
                is_available=False,
                available_advisors_count=0
            ))
            current_min += slot_duration
            continue

        if assigned_to:
            avail = check_advisor_availability(assigned_to, slot_dt_utc, slot_duration, db)
            slots.append(TimeSlotAvailability(
                time_slot=slot_str,
                is_available=avail,
                available_advisors_count=1 if avail else 0
            ))
        else:
            avail_count = sum(
                1 for adv in all_advisors
                if check_advisor_availability(adv.employee_id, slot_dt_utc, slot_duration, db)
            )
            slots.append(TimeSlotAvailability(
                time_slot=slot_str,
                is_available=(avail_count > 0),
                available_advisors_count=avail_count
            ))

        current_min += slot_duration

    return slots


@router.post("/new-appointment/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crea una nueva cita en la base de datos con persistencia de duración y validación de disponibilidad.
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

    # 1. Configuración de citas y duración
    settings = db.query(CompanySettings).filter(CompanySettings.id == 1).first()
    default_duration = getattr(settings, 'slot_duration_minutes', 30) or 30
    duration_minutes = appointment_data.duration_minutes or default_duration

    if settings:
        local_tz = ZoneInfo("America/Mexico_City")
        local_appt = appt_date.astimezone(local_tz)

        # Validar día de la semana (0=Lunes, ..., 6=Domingo)
        if settings.allowed_days is not None and isinstance(settings.allowed_days, list):
            if local_appt.weekday() not in settings.allowed_days:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El día seleccionado no está habilitado para agendar citas."
                )

        # Validar rango de horario
        appt_time = local_appt.time()
        if settings.appointment_start_time and appt_time < settings.appointment_start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La hora de la cita debe ser a partir de las {settings.appointment_start_time.strftime('%H:%M')}."
            )
        if settings.appointment_end_time and appt_time > settings.appointment_end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La hora de la cita debe ser anterior a las {settings.appointment_end_time.strftime('%H:%M')}."
            )

    # 2. Validación de solapamiento y auto-asignación si aplica
    final_assigned_to = appointment_data.assigned_to
    if final_assigned_to:
        if not check_advisor_availability(final_assigned_to, appt_date, duration_minutes, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El asesor seleccionado ya cuenta con una cita en ese horario."
            )
    else:
        final_assigned_to = get_least_busy_available_advisor(
            appt_date, duration_minutes, current_user.company_id, db
        )
        if not final_assigned_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay asesores disponibles en el horario seleccionado."
            )

    # 3. Extraer los datos y separar la lista de items/razones y flags de notificación
    data = appointment_data.model_dump()
    reason_ids = data.pop("reason_ids", None)
    items_input = data.pop("items", None)
    send_whatsapp = data.pop("send_whatsapp", False)
    send_email = data.pop("send_email", False)

    new_appointment = Appointment(**data)
    new_appointment.company_id = current_user.company_id
    new_appointment.duration_minutes = duration_minutes
    new_appointment.assigned_to = final_assigned_to

    # 4. Crear los items de la cita (AUT-231)
    appointment_items_to_add = []
    if items_input:
        for itm in items_input:
            r_id = itm.get("reason_id") if isinstance(itm, dict) else getattr(itm, "reason_id", None)
            nts = itm.get("notes") if isinstance(itm, dict) else getattr(itm, "notes", None)
            if isinstance(nts, str):
                nts = nts.strip() or None
            appointment_items_to_add.append(AppointmentItem(reason_id=r_id, notes=nts))
    elif reason_ids:
        for r_id in reason_ids:
            appointment_items_to_add.append(AppointmentItem(reason_id=r_id, notes=None))

    new_appointment.items = appointment_items_to_add

    db.add(new_appointment)
    db.commit()

    # Recargar con relaciones
    stmt_reload = (
        select(Appointment)
        .options(
            joinedload(Appointment.status),
            joinedload(Appointment.items).joinedload(AppointmentItem.reason),
            joinedload(Appointment.assignee),
            joinedload(Appointment.customer),
            joinedload(Appointment.vehicle).joinedload(Vehicle.color),
            joinedload(Appointment.vehicle).joinedload(Vehicle.model).joinedload(Model.make)
        )
        .where(Appointment.appointment_id == new_appointment.appointment_id)
    )
    reloaded_appointment = db.execute(stmt_reload).scalars().first()

    # Enviar notificaciones si se solicita
    await notify_appointment_confirmation(reloaded_appointment, send_whatsapp, send_email, db)

    return reloaded_appointment

@router.get("/reasons/", response_model=List[AppointmentReasonResponse])
async def get_appointment_reasons(
    db: Session = Depends(get_db),
):
    """
    Obtiene todas las razones de citas disponibles.
    """
    reasons = db.execute(select(AppointmentReason)).scalars().all()
    return reasons

@router.post("/reasons/", response_model=AppointmentReasonResponse)
async def create_appointment_reason(
    reason_data: AppointmentReasonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crea un nuevo tipo o razón de cita.
    """
    existing = db.execute(select(AppointmentReason).where(AppointmentReason.reason == reason_data.reason)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un tipo de cita con ese nombre."
        )
    
    new_reason = AppointmentReason(
        reason=reason_data.reason,
        duration_minutes=reason_data.duration_minutes or 60
    )
    db.add(new_reason)
    db.commit()
    db.refresh(new_reason)
    return new_reason

@router.put("/reasons/{reason_id}", response_model=AppointmentReasonResponse)
async def update_appointment_reason(
    reason_id: int,
    reason_data: AppointmentReasonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Actualiza un tipo de cita existente.
    """
    reason_obj = db.get(AppointmentReason, reason_id)
    if not reason_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de cita no encontrado."
        )
    
    if reason_data.reason is not None:
        reason_obj.reason = reason_data.reason
    if reason_data.duration_minutes is not None:
        reason_obj.duration_minutes = reason_data.duration_minutes
        
    db.commit()
    db.refresh(reason_obj)
    return reason_obj

@router.delete("/reasons/{reason_id}")
async def delete_appointment_reason(
    reason_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Elimina un tipo de cita.
    """
    reason_obj = db.get(AppointmentReason, reason_id)
    if not reason_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de cita no encontrado."
        )
    
    db.delete(reason_obj)
    db.commit()
    return {"message": "Tipo de cita eliminado exitosamente."}


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
            joinedload(Appointment.items).joinedload(AppointmentItem.reason),
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = db.scalar(select(Appointment).where(
        Appointment.appointment_id == appointment_id,
        Appointment.company_id == current_user.company_id
    ))
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada o acceso denegado")

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

    # Validar disponibilidad del asesor asignado excluyendo la cita actual
    if appointment.assigned_to:
        duration = appointment.duration_minutes or 30
        if not check_advisor_availability(
            appointment.assigned_to,
            appt_date,
            duration,
            db,
            exclude_appointment_id=appointment.appointment_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El asesor ya cuenta con otra cita en el nuevo horario seleccionado."
            )

    appointment.appointment_date = payload.appointment_date
    appointment.rescheduled_count = (appointment.rescheduled_count or 0) + 1
    
    # Al reprogramar, vuelve a estar "sin confirmar"
    appointment.status_id = 1
    
    db.commit()

    stmt_reload = (
        select(Appointment)
        .options(
            joinedload(Appointment.status),
            joinedload(Appointment.items).joinedload(AppointmentItem.reason),
            joinedload(Appointment.assignee),
            joinedload(Appointment.customer),
            joinedload(Appointment.vehicle).joinedload(Vehicle.color),
            joinedload(Appointment.vehicle).joinedload(Vehicle.model).joinedload(Model.make)
        )
        .where(Appointment.appointment_id == appointment.appointment_id)
    )
    reloaded_appointment = db.execute(stmt_reload).scalars().first()

    # Enviar notificaciones si se solicita
    await notify_appointment_confirmation(reloaded_appointment, payload.send_whatsapp, payload.send_email, db)
    
    return reloaded_appointment


@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: int,
    payload: Optional[CancelRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = db.scalar(select(Appointment).where(
        Appointment.appointment_id == appointment_id,
        Appointment.company_id == current_user.company_id
    ))
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada o acceso denegado")
        
    # Verificar si existe el estado 3 (cancelado) en la base de datos
    status_canceled = db.scalar(select(AppointmentStatus).where(AppointmentStatus.status_id == 3))
    if not status_canceled:
        status_canceled = AppointmentStatus(status_id=3, status="cancelado")
        db.add(status_canceled)
        db.flush()
        
    appointment.status_id = 3  # Cancelado
    if payload and payload.cancellation_reason:
        appointment.cancellation_reason = payload.cancellation_reason
    appointment.cancellation_date = datetime.now(dt_module.timezone.utc)

    db.commit()
    db.refresh(appointment)
    return appointment


@router.post("/{appointment_id}/resend-confirmation")
async def resend_appointment_confirmation(
    appointment_id: int,
    payload: ResendConfirmationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = db.scalar(select(Appointment).where(
        Appointment.appointment_id == appointment_id,
        Appointment.company_id == current_user.company_id
    ))
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada o acceso denegado")
        
    await notify_appointment_confirmation(appointment, payload.send_whatsapp, payload.send_email, db)
    return {"status": "ok", "message": "Confirmación reenviada correctamente"}


@router.patch("/{appointment_id}/confirm", response_model=AppointmentResponse)
async def confirm_appointment(
    appointment_id: int,
    payload: Optional[AppointmentConfirmRequest] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Confirma manualmente una cita existente por parte del asesor (AUT-234),
    cambiando su estado a 'confirmado' (status_id = 2) y enviando opcionalmente
    las notificaciones solicitadas por WhatsApp o correo.
    """
    appointment = db.scalar(select(Appointment).where(
        Appointment.appointment_id == appointment_id,
        Appointment.company_id == current_user.company_id
    ))
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada o acceso denegado")

    if appointment.status_id == 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede confirmar una cita que ha sido cancelada."
        )

    if appointment.status_id == 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cita ya se encuentra confirmada."
        )

    # Verificar si existe el estado 2 (confirmado) en la base de datos
    status_confirmed = db.scalar(select(AppointmentStatus).where(AppointmentStatus.status_id == 2))
    if not status_confirmed:
        status_confirmed = AppointmentStatus(status_id=2, status="confirmado")
        db.add(status_confirmed)
        db.flush()

    appointment.status_id = 2  # Confirmada
    db.commit()

    # Recargar cita con relaciones cargadas para la respuesta
    stmt_reload = (
        select(Appointment)
        .options(
            joinedload(Appointment.status),
            joinedload(Appointment.items).joinedload(AppointmentItem.reason),
            joinedload(Appointment.assignee),
            joinedload(Appointment.customer),
            joinedload(Appointment.vehicle).joinedload(Vehicle.color),
            joinedload(Appointment.vehicle).joinedload(Vehicle.model).joinedload(Model.make)
        )
        .where(Appointment.appointment_id == appointment.appointment_id)
    )
    reloaded_appointment = db.execute(stmt_reload).scalars().first()

    send_whatsapp = payload.send_whatsapp if payload else False
    send_email = payload.send_email if payload else False

    if send_whatsapp or send_email:
        if background_tasks:
            background_tasks.add_task(notify_appointment_confirmation, reloaded_appointment, send_whatsapp, send_email, db)
        else:
            await notify_appointment_confirmation(reloaded_appointment, send_whatsapp, send_email, db)

    return reloaded_appointment