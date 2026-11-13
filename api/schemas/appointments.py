from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional, Dict, Any

from .customers import CustomerInfoForAppointment
from .vehicles import VehicleInfoForAppointment
from .user import EmployeeResponseShort


class AppointmentItemCreate(BaseModel):
    reason_id: int
    notes: Optional[str] = None

class AppointmentItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    appointment_item_id: int
    reason_id: Optional[int] = None
    notes: Optional[str] = None
    reason: Optional["AppointmentReasonResponse"] = None


class AppointmentCreate(BaseModel):
    # IDs para cuando la cita la crea un empleado para un cliente existente
    customer_id: Optional[int] = None
    contact_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    scheduled_by: Optional[int] = None
    assigned_to: Optional[int] = None

    # Datos para cuando la cita la crea un cliente directamente (cita rápida)
    temp_cname: Optional[str] = None
    temp_fname: Optional[str] = None
    temp_lname: Optional[str] = None
    temp_email: Optional[str] = None
    temp_phone: Optional[str] = None
    temp_vehicle_data: Optional[Dict[str, Any]] = None

    appointment_date: datetime
    duration_minutes: Optional[int] = None
    reason_ids: Optional[List[int]] = None  # Deprecated (Legacy Support)
    items: Optional[List[AppointmentItemCreate]] = None  # AUT-231: items con notas individuales
    status_id: int
    notes: Optional[str] = None
    send_whatsapp: Optional[bool] = False
    send_email: Optional[bool] = False

class AppointmentConfirmRequest(BaseModel):
    send_whatsapp: bool = False
    send_email: bool = False

class AppointmentFormalize(BaseModel):
    customer_id: int
    vehicle_id: int

class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    appointment_id: int
    customer_id: Optional[int] = None
    contact_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    scheduled_by: Optional[int] = None
    assigned_to: Optional[int] = None
    appointment_date: datetime
    duration_minutes: int = 30
    notes: Optional[str] = None
    rescheduled_count: int
    cancellation_reason: Optional[str] = None
    cancellation_date: Optional[datetime] = None
    temp_cname: Optional[str] = None
    temp_fname: Optional[str] = None
    temp_lname: Optional[str] = None
    temp_email: Optional[str] = None
    temp_phone: Optional[str] = None
    temp_vehicle_data: Optional[Dict[str, Any]] = None
    order_id: Optional[int] = None
    channel: Optional[str] = 'manual'
    status: Optional["AppointmentStatusResponse"] = None
    items: List[AppointmentItemResponse] = []  # AUT-231: items con notas
    reasons: List["AppointmentReasonResponse"] = []  # Retrocompatibilidad
    customer: Optional[CustomerInfoForAppointment] = None
    vehicle: Optional[VehicleInfoForAppointment] = None
    assignee: Optional[EmployeeResponseShort] = None

class TimeSlotAvailability(BaseModel):
    time_slot: str
    is_available: bool
    available_advisors_count: int

class AppointmentStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status_id: int
    status: str

class AppointmentReasonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reason_id: int
    reason: str
    duration_minutes: Optional[int] = 60

class AppointmentReasonCreate(BaseModel):
    reason: str
    duration_minutes: Optional[int] = 60

class AppointmentReasonUpdate(BaseModel):
    reason: Optional[str] = None
    duration_minutes: Optional[int] = None


# --- Esquemas para Portal Público de Citas (AUT-245) ---

class PublicVehicleTempData(BaseModel):
    make: str
    model: str
    year: Optional[int] = None
    plate: Optional[str] = None
    color: Optional[str] = None
    notes: Optional[str] = None


class PublicAppointmentCreate(BaseModel):
    company_id: int
    appointment_date: datetime
    reason_ids: List[int]
    temp_fname: str
    temp_lname: str
    temp_cname: Optional[str] = None
    temp_phone: str
    temp_email: str
    temp_vehicle_data: PublicVehicleTempData
    notes: Optional[str] = None


class PublicAppointmentConfigResponse(BaseModel):
    company_id: int
    company_name: str
    public_portal_enabled: bool
    allowed_days: List[int]
    slot_duration_minutes: int
    reasons: List[AppointmentReasonResponse]


class PublicAppointmentAvailabilityResponse(BaseModel):
    date: str
    available_slots: List[str]
    slots_detail: Optional[List[TimeSlotAvailability]] = None


class PublicAppointmentCreateResponse(BaseModel):
    appointment_id: int
    message: str
    status: str
    appointment_date: datetime
