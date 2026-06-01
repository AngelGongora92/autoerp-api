from pydantic import BaseModel, ConfigDict
from typing import Optional

class CustomerCreate(BaseModel):
    is_company: bool = False
    cname: Optional[str] = None
    fname: Optional[str] = None
    lname: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    email: str
    phone: Optional[str] = None

class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    customer_id: int
    is_company: bool
    cname: Optional[str] = None
    fname: Optional[str] = None
    lname: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool

class CustomerUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    is_company: Optional[bool] = None
    cname: Optional[str] = None
    fname: Optional[str] = None
    lname: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class ContactCreate(BaseModel):
    customer_id: int
    fname: str
    lname: str
    email: str
    phone: Optional[str] = None

class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    contact_id: int
    customer_id: int
    fname: str
    lname: str
    email: str
    phone: Optional[str] = None

# Esquema simplificado para mostrar la información del cliente en la cita
class CustomerInfoForAppointment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    fname: Optional[str] = None
    lname: Optional[str] = None
    cname: Optional[str] = None