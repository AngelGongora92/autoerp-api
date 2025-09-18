from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from .database import Vehicle, get_db
from .schemas.user import VehicleResponse

router = APIRouter()

@router.get("/{customer_id}", response_model=List[VehicleResponse])
async def get_vehicles_by_id(
    customer_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene una lista de todos los vehículos de un cliente específico.
    """
    stmt = select(Vehicle).filter(Vehicle.customer_id == customer_id)
    vehicles = db.scalars(stmt).unique().all()
    return vehicles