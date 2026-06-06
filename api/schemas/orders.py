from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

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