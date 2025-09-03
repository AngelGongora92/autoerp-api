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

class UserUpdate(BaseModel):
    username: Optional[str] = None
    is_admin: Optional[bool] = None
    permissions: Optional[List[PermissionBase]] = None
    model_config = ConfigDict(extra='ignore')

class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_company: bool
    cname: Optional[str] = None  # Company name
    fname: Optional[str] = None  # First name
    lname: Optional[str] = None  # Last name
    address1: Optional[str] = None
    address2: Optional[str] = None
    email: str

class CustomerUpdate(BaseModel):
    is_company: Optional[bool] = None
    cname: Optional[str] = None  # Company name
    fname: Optional[str] = None  # First name
    lname: Optional[str] = None  # Last name
    address1: Optional[str] = None
    address2: Optional[str] = None
    email: str