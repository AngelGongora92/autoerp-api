from pydantic import BaseModel, ConfigDict
from datetime import date, datetime, time
from typing import List, Optional, Dict, Any
from enum import Enum

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
    model_config = ConfigDict(extra='ignore')
    username: Optional[str] = None
    is_admin: Optional[bool] = None
    permissions: Optional[List[PermissionBase]] = None

# --- Esquemas para Clientes y Contactos ---

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

class CustomerInfoForAppointment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    fname: Optional[str] = None
    lname: Optional[str] = None
    cname: Optional[str] = None

# --- Esquemas para Empleados ---

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

# --- Esquemas para Vehículos ---

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

class VehicleMakesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    make_id: int
    make: str

class VehicleModelsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    model_id: int
    model: str
    make: VehicleMakesResponse

class VehicleTransmissionsResponse(BaseModel):
    transmission_id: int
    type: str

class VehicleCreate(BaseModel):
    customer_id: Optional[int] = None
    vin: str
    plate: Optional[str] = None
    year: int
    model_id: int
    mileage: int
    color_id: int
    motor_id: int
    transmission_id: int
    cylinders: int
    liters: str
    v_type_id: int

class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')
    vehicle_id: int
    customer_id: Optional[int] = None
    vin: str
    plate: Optional[str] = None
    year: int
    model: "VehicleModelsResponse"
    mileage: int
    color: ColorResponse
    motor: MotorResponse
    transmission: "VehicleTransmissionsResponse"
    cylinders: int
    liters: str
    vehicle_type: VehicleTypeResponse

class VehicleInfoForAppointment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    year: int
    model: "VehicleModelsResponse"
    color: "ColorResponse"
    plate: Optional[str] = None

class ColorCreate(BaseModel):
    color: str

class MotorCreate(BaseModel):
    type: str

class VehicleTypeCreate(BaseModel):
    type: str

# --- Esquemas para Órdenes ---

class CreateOrder(BaseModel):
    c_order_id: str
    order_date: datetime
    advisor_id: Optional[int] = None
    mechanic_id: Optional[int] = None
    customer_id: Optional[int] = None
    contact_id: Optional[int] = None
    adm_status_id: Optional[int] = 1
    op_status_id: Optional[int] = 1
    priority_id: Optional[int] = 1
    fuel_level: Optional[int] = None

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
    c_mileage: Optional[int] = None
    op_status_id: Optional[int] = None
    adm_status_id: Optional[int] = None
    priority_id: Optional[int] = None
    has_extra_info: Optional[bool] = None
    fuel_level: Optional[int] = None
    service_bay: Optional[str] = None

class OrderUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    c_order_id: Optional[str] = None
    order_date: Optional[datetime] = None
    advisor_id: Optional[int] = None
    mechanic_id: Optional[int] = None
    customer_id: Optional[int] = None
    contact_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    p_mileage: Optional[int] = None
    c_mileage: Optional[int] = None
    op_status_id: Optional[int] = None
    adm_status_id: Optional[int] = None
    priority_id: Optional[int] = None
    has_extra_info: Optional[bool] = None
    fuel_level: Optional[int] = None
    service_bay: Optional[str] = None

class OrderExtraItemsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    item_id: int
    title: str
    description: Optional[str] = None

class OrderExtraInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    item_id: int
    info: Optional[str] = None
    item: OrderExtraItemsResponse

class OrderExtraInfoCreate(BaseModel):
    order_id: int
    item_id: int
    info: Optional[str] = None

class BodyworkDetailTypesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    detail_type_id: int
    type: str
    color: Optional[str] = None

class BodyworkDetailCoordinates(BaseModel):
    x: float
    y: float

class BodyworkChecklistView(str, Enum):
    front = "front"
    back = "back"
    left = "left"
    right = "right"
    up = "up"

class BodyworkDetailTypesCreate(BaseModel):
    type: str
    color: Optional[str] = None

class BodyworkDetailTypesUpdate(BaseModel):
    type: Optional[str] = None
    color: Optional[str] = None

class BodyworkDetailsCreate(BaseModel):
    order_id: int
    view: BodyworkChecklistView
    detail_type_id: int = None
    coordinates: Optional[BodyworkDetailCoordinates] = None
    detail_notes: Optional[str] = None
    picture_path: Optional[str] = None

class BodyworkDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    detail_id: int
    view: BodyworkChecklistView
    detail_type: BodyworkDetailTypesResponse
    coordinates: Optional[BodyworkDetailCoordinates] = None
    detail_notes: Optional[str] = None
    picture_path: Optional[str] = None

class BodyworkDetailsUpdate(BaseModel):
    view: Optional[BodyworkChecklistView] = None
    detail_type_id: Optional[int] = None
    coordinates: Optional[BodyworkDetailCoordinates] = None
    detail_notes: Optional[str] = None
    picture_path: Optional[str] = None

class InventoryTypesCreate(BaseModel):
    name: str
    component_key: Optional[str] = "generic_checklist"
    is_active: bool = True
    picture_path: Optional[str] = None

class InventoryTypesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    inv_type_id: int
    name: str
    component_key: str
    is_active: bool
    position: int
    picture_path: Optional[str] = None

class InventoryTypesUpdate(BaseModel):
    name: Optional[str] = None
    component_key: Optional[str] = None
    is_active: Optional[bool] = None
    position: Optional[int] = None
    picture_path: Optional[str] = None

class InventoryTypesReorder(BaseModel):
    inv_type_id: int
    position: int

class InventoryItemsCreate(BaseModel):
    inv_type_id: int
    label: str
    input_type: str
    description: Optional[str] = ""
    is_mandatory: bool = False
    picture_upload: bool = False

class InventoryItemsUpdate(BaseModel):
    item_id: int
    inv_type_id: Optional[int] = None
    label: Optional[str] = None
    input_type: Optional[str] = None
    position: Optional[int] = None
    description: Optional[str] = None
    is_mandatory: Optional[bool] = None
    picture_upload: Optional[bool] = None

class InventoryItemsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    item_id: int
    inv_type_id: int
    label: str
    input_type: str
    position: int
    description: Optional[str] = None
    is_mandatory: bool
    picture_upload: bool
    inventory_type: InventoryTypesResponse

class InventoryItemStrippedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    item_id: int
    label: str
    input_type: str
    position: int
    description: Optional[str] = None
    is_mandatory: bool
    picture_upload: bool

class InventoryItemsByTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    inventory_type: InventoryTypesResponse
    items: List[InventoryItemStrippedResponse]

class InventoryItemReorder(BaseModel):
    item_id: int
    position: int

class OrderInventoryDataCreate(BaseModel):
    order_id: int
    item_id: int
    data: Optional[Dict[str, Any]] = None

class OrderInventoryDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    data_id: int
    order_id: int
    item_id: int
    data: Optional[Dict[str, Any]] = None

# --- Esquemas para Citas ---

class AppointmentCreate(BaseModel):
    customer_id: Optional[int] = None
    contact_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    scheduled_by: Optional[int] = None
    assigned_to: Optional[int] = None
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
    send_whatsapp: Optional[bool] = False
    send_email: Optional[bool] = False

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
    duration_minutes: int

# --- Esquemas para Horarios de Empleados ---

class EmployeeScheduleBlockBase(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time

class EmployeeScheduleBlockCreate(EmployeeScheduleBlockBase):
    employee_id: int

class EmployeeScheduleBlockResponse(EmployeeScheduleBlockBase):
    model_config = ConfigDict(from_attributes=True)
    block_id: int
    employee_id: int

class ScheduleOverrideBase(BaseModel):
    override_date: date
    is_available: bool
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = None

class ScheduleOverrideCreate(ScheduleOverrideBase):
    employee_id: int

class ScheduleOverrideResponse(ScheduleOverrideBase):
    model_config = ConfigDict(from_attributes=True)
    override_id: int
    employee_id: int

# --- Esquemas para Configuración de la Empresa ---

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