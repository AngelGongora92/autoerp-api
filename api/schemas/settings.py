from pydantic import BaseModel, ConfigDict
from datetime import time
from typing import Optional

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

class CompanySettingsUpdate(CompanySettingsBase):
    pass

class CompanySettingsResponse(CompanySettingsBase):
    model_config = ConfigDict(from_attributes=True)
    id: int