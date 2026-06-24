from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import List
from .database import get_db, Vehicle, Color, Motor, VehicleType, Make, Model, Transmission, User
from .schemas.user import VehicleResponse, VehicleCreate, ColorResponse, ColorCreate, MotorResponse, MotorCreate, VehicleTypeResponse, VehicleTypeCreate, VehicleMakesResponse, VehicleModelsResponse, VehicleTransmissionsResponse
from fastapi import status
from fastapi.exceptions import HTTPException
from api.auth_deps import get_current_user


router = APIRouter()

@router.get("/", response_model=List[VehicleResponse])
async def get_all_vehicles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene una lista de todos los vehículos asociados al taller (tenant).
    """
    stmt = (
        select(Vehicle)
        .filter(Vehicle.company_id == current_user.company_id)
        .options(joinedload(Vehicle.color), joinedload(Vehicle.motor), joinedload(Vehicle.vehicle_type))
    )
    vehicles = db.scalars(stmt).unique().all()
    return vehicles

@router.get("/{customer_id}", response_model=List[VehicleResponse])
async def get_vehicles_by_id(
    customer_id: int,  # FastAPI espera un entero del parámetro de ruta
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene una lista de todos los vehículos de un cliente específico.
    """
    stmt = (
        select(Vehicle)
        .filter(Vehicle.customer_id == customer_id, Vehicle.company_id == current_user.company_id)
        .options(joinedload(Vehicle.color), joinedload(Vehicle.motor), joinedload(Vehicle.vehicle_type))
    )
    vehicles = db.scalars(stmt).unique().all()
    return vehicles


@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle_data: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crea un nuevo vehículo en la base de datos.
    """
    # 1. Verificar duplicidad de VIN en esta misma empresa
    if vehicle_data.vin:
        existing_vin = db.scalars(
            select(Vehicle).where(Vehicle.vin == vehicle_data.vin, Vehicle.company_id == current_user.company_id)
        ).first()
        if existing_vin:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El vehículo con este número VIN ya existe en tu taller."
            )

    # 2. Verificar duplicidad de Placas en esta misma empresa
    if vehicle_data.plate:
        existing_plate = db.scalars(
            select(Vehicle).where(Vehicle.plate == vehicle_data.plate, Vehicle.company_id == current_user.company_id)
        ).first()
        if existing_plate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El vehículo con estas placas ya existe en tu taller."
            )

    new_vehicle = Vehicle(**vehicle_data.model_dump())
    new_vehicle.company_id = current_user.company_id
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle

@router.get("/v/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle_by_id(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene un solo vehículo por su ID.
    """
    vehicle = db.scalar(
        select(Vehicle).where(Vehicle.vehicle_id == vehicle_id, Vehicle.company_id == current_user.company_id)
    )

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado o acceso denegado"
        )
    
    return vehicle

@router.get("/colors/{color_id}", response_model=ColorResponse)
async def get_color_by_id(
    color_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene un solo color por su ID.
    """
    color = db.get(Color, color_id)

    if not color:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Color not found"
        )
    
    return color

@router.post("/colors/", response_model=ColorCreate, status_code=status.HTTP_201_CREATED)
async def create_color(
    color_data: ColorCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un nuevo color en la base de datos.
    """
    new_color = Color(**color_data.model_dump())
    db.add(new_color)
    db.commit()
    db.refresh(new_color)
    return new_color


@router.get("/colors/", response_model=List[ColorResponse])
async def get_all_colors(
    db: Session = Depends(get_db),
):
    """
    Obtiene una lista de todas las órdenes.
    """
    stmt = select(Color)
    colors = db.scalars(stmt).unique().all()
    return colors

@router.get("/motors/{motor_id}", response_model=MotorResponse)
async def get_motor_by_id(
    motor_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene un solo motor por su ID.
    """
    motor = db.get(Motor, motor_id)

    if not motor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motor not found"
        )
    
    return motor

@router.get("/motors/", response_model=List[MotorResponse])
async def get_all_motors(
    db: Session = Depends(get_db),
):
    """
    Obtiene una lista de todos los motores.
    """
    stmt = select(Motor)
    motors = db.scalars(stmt).unique().all()
    return motors

@router.get("/types/{v_type_id}", response_model=VehicleTypeResponse)
async def get_vehicle_type_by_id(
    v_type_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene un solo tipo de vehículo por su ID.
    """
    vehicle_type = db.get(VehicleType, v_type_id)

    if not vehicle_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle type not found"
        )
    
    return vehicle_type

@router.get("/types/", response_model=List[VehicleTypeResponse])
async def get_all_vehicle_types(
    db: Session = Depends(get_db),
):
    """
    Obtiene una lista de todos los tipos de vehículos.
    """
    stmt = select(VehicleType)
    vehicle_types = db.scalars(stmt).unique().all()
    return vehicle_types

@router.get("/makes/", response_model=List[VehicleMakesResponse])
async def get_all_makes(
    db: Session = Depends(get_db),
):
    """
    Obtiene una lista de todas las marcas de vehículos.
    """
    stmt = select(Make)
    makes = db.scalars(stmt).unique().all()
    return makes

@router.get("/models/{make_id}", response_model=List[VehicleModelsResponse])
async def get_models_by_make_id(
    make_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene una lista de todos los modelos de una marca específica.
    """
    stmt = select(Model).filter(Model.make_id == make_id)
    models = db.scalars(stmt).unique().all()
    return models

@router.get("/transmissions/", response_model=List[VehicleTransmissionsResponse])
async def get_all_transmissions(
    db: Session = Depends(get_db),
):
    """
    Obtiene una lista de todos los tipos de transmisión.
    """
    stmt = select(Transmission)
    transmissions = db.scalars(stmt).unique().all()
    return transmissions