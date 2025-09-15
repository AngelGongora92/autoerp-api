from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class PermissionResponse(BaseModel):
    name: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    is_admin: bool
    permissions: List[PermissionResponse] = []

class PermissionBase(BaseModel):
    name: str

class UserCreate(BaseModel):
    username: str
    password: str # Campo obligatorio para un nuevo usuario
    is_admin: bool = False
    permissions: List[PermissionBase] = []

class UserUpdate(BaseModel):
    username: Optional[str] = None
    is_admin: Optional[bool] = None
    permissions: Optional[List[PermissionBase]] = None
    model_config = ConfigDict(extra='ignore')

class CustomerCreate(BaseModel):
    is_company: bool = False
    cname: Optional[str] = None  # Company name
    fname: Optional[str] = None  # First name
    lname: Optional[str] = None  # Last name
    address1: Optional[str] = None
    address2: Optional[str] = None
    email: str  # Campo obligatorio para un nuevo cliente
    phone: Optional[str] = None

class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_company: bool
    cname: Optional[str] = None  # Company name
    fname: Optional[str] = None  # First name
    lname: Optional[str] = None  # Last name
    address1: Optional[str] = None
    address2: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class CustomerUpdate(BaseModel):
    is_company: Optional[bool] = None
    cname: Optional[str] = None  # Company name
    fname: Optional[str] = None  # First name
    lname: Optional[str] = None  # Last name
    address1: Optional[str] = None
    address2: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class CustomerCreate(BaseModel):
    is_company: bool = False
    cname: Optional[str] = None  # Company name
    fname: Optional[str] = None  # First name
    lname: Optional[str] = None  # Last name
    address1: Optional[str] = None
    address2: Optional[str] = None
    email: str  # Campo obligatorio para un nuevo cliente
    phone: Optional[str] = None

class ContactCreate(BaseModel):
    customer_id: int  # ID del cliente al que pertenece el contacto
    fname: str  # First name
    lname: str  # Last name
    email: str  # Email del contacto
    phone: Optional[str] = None  # Teléfono del contacto

class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    fname: str
    lname: str
    email: str
    phone: Optional[str] = None



class ContactUpdate(BaseModel):
    fname: Optional[str] = None  # First name
    lname: Optional[str] = None  # Last name
    email: Optional[str] = None  # Email del contacto
    phone: Optional[str] = None  # Teléfono del contacto