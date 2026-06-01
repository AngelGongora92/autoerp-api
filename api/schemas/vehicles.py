from pydantic import BaseModel, ConfigDict
from typing import Optional

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

# Esquema simplificado para mostrar la información del vehículo en la cita
class VehicleInfoForAppointment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    year: int
    model: "VehicleModelsResponse"
    color: "ColorResponse"