from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import List, Optional

class PermissionResponse(BaseModel):
    name: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    username: str
    is_admin: bool
    permissions: List[PermissionResponse] = []
    is_employee: bool
    is_active: bool


class PermissionBase(BaseModel):
    name: str

class UserCreate(BaseModel):
    username: str
    password: str # Campo obligatorio para un nuevo usuario
    is_admin: bool = False
    permissions: List[PermissionBase] = []
    is_employee: bool = False
    is_active: bool = True



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
    customer_id: int
    is_company: bool
    cname: Optional[str] = None  # Company name
    fname: Optional[str] = None  # First name
    lname: Optional[str] = None  # Last name
    address1: Optional[str] = None
    address2: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool

class CustomerUpdate(BaseModel):
    is_company: Optional[bool] = None
    cname: Optional[str] = None  # Company name
    fname: Optional[str] = None  # First name
    lname: Optional[str] = None  # Last name
    address1: Optional[str] = None
    address2: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    model_config = ConfigDict(extra='ignore')

class ContactCreate(BaseModel):
    customer_id: int  # ID del cliente al que pertenece el contacto
    fname: str  # First name
    lname: str  # Last name
    email: str  # Email del contacto
    phone: Optional[str] = None  # Teléfono del contacto

class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    contact_id: int
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

class EmployeeCreate(BaseModel):
    fname: str  # First name
    lname1: str  # Last name
    lname2: Optional[str] = None  # Second last name
    email: str  # Email del empleado
    phone: Optional[str] = None  # Teléfono del empleado
    position: str = None  # Job position

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

class CreateOrder(BaseModel):
    c_order_id: str  # Purchase order ID
    order_date: datetime  # Order date
    advisor_id: Optional[int] = None  # Advisor employee ID
    mechanic_id: Optional[int] = None  # Mechanic employee ID
    customer_id: Optional[int] = None  # Customer ID
    contact_id: Optional[int] = None  # Contact ID
    adm_status_id: Optional[int] = 1
    op_status_id: Optional[int] = 1
    priority_id: Optional[int] = 1


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    order_id: int
    c_order_id: str
    order_date: datetime
    advisor_id: Optional[int] = None
    mechanic_id: Optional[int] = None
    customer_id: Optional[int] = None
    contact_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    op_status_id: Optional[int] = None
    adm_status_id: Optional[int] = None
    priority_id: Optional[int] = None

class OrderUpdate(BaseModel):
    c_order_id: Optional[str] = None  # Purchase order ID
    order_date: Optional[datetime] = None  # Order date
    advisor_id: Optional[int] = None  # Advisor employee ID
    mechanic_id: Optional[int] = None  # Mechanic employee ID
    customer_id: Optional[int] = None  # Customer ID
    contact_id: Optional[int] = None  # Contact ID
    vehicle_id: Optional[int] = None
    op_status_id: Optional[int] = None
    adm_status_id: Optional[int] = None
    priority_id: Optional[int] = None

class ColorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    color_id: int
    color: str

class MotorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    motor_id: int
    type: str

class VehicleTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    v_type_id: int
    type: str

class VehicleCreate(BaseModel):
    customer_id: Optional[int] = None
    vin: str
    plate: Optional[str] = None
    year: int
    make: str
    model: str
    mileage: int
    fleet_number: Optional[int] = None
    color_id: int
    motor_id: int
    transmission: str
    cylinders: int
    liters: str
    v_type_id: int


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    vehicle_id: int
    customer_id: Optional[int] = None
    vin: str  # Vehicle Identification Number
    plate: Optional[str] = None  # Plate number
    year: int
    make: str
    model: str
    mileage: int
    fleet_number: Optional[int] = None  # Fleet number
    color: ColorResponse
    motor: MotorResponse
    transmission: str  # Transmission details
    cylinders: int
    liters: str  # Engine displacement in liters
    vehicle_type: VehicleTypeResponse

class VehicleUpdate:
    customer_id: Optional[int] = None
    vin: Optional[str] = None
    plate: Optional[str] = None
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    mileage: Optional[int] = None
    fleet_number: Optional[int] = None
    color_id: Optional[int] = None
    motor_id: Optional[int] = None
    transmission: Optional[str] = None
    cylinders: Optional[int] = None
    liters: Optional[str] = None
    v_type_id: Optional[int] = None
    
class ColorCreate(BaseModel):
    color: str

class MotorCreate(BaseModel):
    type: str

class VehicleTypeCreate(BaseModel):
    type: str