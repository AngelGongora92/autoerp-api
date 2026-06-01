from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional, Dict, Any

from .customers import CustomerInfoForAppointment
from .vehicles import VehicleInfoForAppointment


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
    reason_ids: List[int]
    status_id: int
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    appointment_id: int
    customer_id: Optional[int] = None
    contact_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    scheduled_by: Optional[int] = None
    assigned_to: Optional[int] = None
    appointment_date: datetime
    notes: Optional[str] = None
    rescheduled_count: int
    temp_cname: Optional[str] = None
    temp_fname: Optional[str] = None
    temp_lname: Optional[str] = None
    temp_email: Optional[str] = None
    temp_phone: Optional[str] = None
    temp_vehicle_data: Optional[Dict[str, Any]] = None
    status: Optional["AppointmentStatusResponse"] = None
    reasons: List["AppointmentReasonResponse"] = []
    customer: Optional[CustomerInfoForAppointment] = None
    vehicle: Optional[VehicleInfoForAppointment] = None

class AppointmentStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status_id: int
    status: str

class AppointmentReasonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reason_id: int
    reason: str