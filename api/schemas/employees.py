from pydantic import BaseModel, ConfigDict
from typing import Optional

class EmployeeCreate(BaseModel):
    fname: str
    lname1: str
    lname2: Optional[str] = None
    email: str
    phone: Optional[str] = None
    position_id: Optional[int] = None

class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    employee_id: int
    fname: str
    lname1: str
    lname2: Optional[str] = None
    email: str
    phone: Optional[str] = None
    position_id: Optional[int] = None
    is_active: bool

class EmployeeUpdate(BaseModel):
    fname: Optional[str] = None
    lname1: Optional[str] = None
    lname2: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position_id: Optional[int] = None
    is_active: Optional[bool] = None