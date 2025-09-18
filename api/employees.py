from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

# Importar las clases de Pydantic y los modelos de la base de datos
from .schemas.user import EmployeeResponse
from .database import get_db, Employee

# --- Creación del Router ---
router = APIRouter()

@router.get("/", response_model=List[EmployeeResponse])
async def get_all_employees(
    db: Session = Depends(get_db),
):
    """
    Obtiene una lista de todos los empleados.
    """
    stmt = select(Employee)
    employees = db.scalars(stmt).all()
    return employees

@router.get("/{position_id}", response_model=List[EmployeeResponse])
async def get_employees_by_position(
    position_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene una lista de empleados por ID de posición.
    """
    stmt = select(Employee).where(Employee.position_id == position_id)
    employees = db.scalars(stmt).all()
    return employees