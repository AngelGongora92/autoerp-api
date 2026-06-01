from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from api.database import get_db, EmployeeScheduleBlock, ScheduleOverride, Employee
from api.schemas.user import (
    EmployeeScheduleBlockCreate, 
    EmployeeScheduleBlockResponse, 
    ScheduleOverrideCreate, 
    ScheduleOverrideResponse
)

router = APIRouter()

# --- Bloques de Horario Semanal (Weekly Schedule) ---

@router.post("/blocks/", response_model=EmployeeScheduleBlockResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule_block(
    block_data: EmployeeScheduleBlockCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un bloque de horario recurrente para un empleado (ej: Lunes 9:00 - 18:00).
    """
    # Verificar que el empleado existe
    if not db.get(Employee, block_data.employee_id):
        raise HTTPException(status_code=404, detail="Employee not found")

    new_block = EmployeeScheduleBlock(**block_data.model_dump())
    db.add(new_block)
    db.commit()
    db.refresh(new_block)
    return new_block

@router.get("/blocks/{employee_id}", response_model=List[EmployeeScheduleBlockResponse])
async def get_schedule_blocks(
    employee_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene el horario semanal base de un empleado.
    """
    stmt = select(EmployeeScheduleBlock).where(EmployeeScheduleBlock.employee_id == employee_id)
    blocks = db.scalars(stmt).all()
    return blocks

@router.delete("/blocks/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule_block(
    block_id: int,
    db: Session = Depends(get_db),
):
    block = db.get(EmployeeScheduleBlock, block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Schedule block not found")
    
    db.delete(block)
    db.commit()
    return

# --- Excepciones de Horario (Overrides) ---

@router.post("/overrides/", response_model=ScheduleOverrideResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule_override(
    override_data: ScheduleOverrideCreate,
    db: Session = Depends(get_db),
):
    """
    Crea una excepción de horario (ej: Vacaciones, día libre, o horas extra en una fecha específica).
    """
    if not db.get(Employee, override_data.employee_id):
        raise HTTPException(status_code=404, detail="Employee not found")

    new_override = ScheduleOverride(**override_data.model_dump())
    db.add(new_override)
    db.commit()
    db.refresh(new_override)
    return new_override

@router.get("/overrides/{employee_id}", response_model=List[ScheduleOverrideResponse])
async def get_schedule_overrides(
    employee_id: int,
    db: Session = Depends(get_db),
):
    stmt = select(ScheduleOverride).where(ScheduleOverride.employee_id == employee_id)
    overrides = db.scalars(stmt).all()
    return overrides