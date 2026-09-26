from pydantic import BaseModel, ConfigDict
from datetime import time
from typing import Optional, List

class CompanySettingsBase(BaseModel):
    company_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    tax_id: Optional[str] = None
    business_hours_start: Optional[time] = None
    business_hours_end: Optional[time] = None
    info: Optional[str] = None
    appointment_start_time: Optional[time] = None
    appointment_end_time: Optional[time] = None
    slot_duration_minutes: Optional[int] = 30
    allowed_days: Optional[List[int]] = [0, 1, 2, 3, 4, 5]

class CompanySettingsUpdate(CompanySettingsBase):
    pass

class CompanySettingsResponse(CompanySettingsBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

class AppointmentConfigSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    appointment_start_time: Optional[time] = None
    appointment_end_time: Optional[time] = None
    slot_duration_minutes: Optional[int] = 30
    allowed_days: Optional[List[int]] = [0, 1, 2, 3, 4, 5]