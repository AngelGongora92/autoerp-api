from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import List

# Importar las clases de Pydantic y los modelos de la base de datos
from .schemas.user import EmployeeResponse, EmployeeCreate, EmployeeUpdate, PositionResponse
from .database import get_db, Employee, User, Position
from api.auth_deps import get_current_user

# --- Creación del Router ---
router = APIRouter()

@router.get("/", response_model=List[EmployeeResponse])
async def get_all_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene una lista de todos los empleados de la empresa.
    """
    stmt = select(Employee).options(joinedload(Employee.position)).where(Employee.company_id == current_user.company_id)
    employees = db.scalars(stmt).all()
    return employees

@router.get("/positions/", response_model=List[PositionResponse])
async def get_all_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene una lista de todos los cargos/posiciones disponibles.
    """
    stmt = select(Position)
    positions = db.scalars(stmt).all()
    return positions

@router.get("/{position_id}", response_model=List[EmployeeResponse])
async def get_employees_by_position(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene una lista de empleados por ID de posición.
    """
    stmt = select(Employee).options(joinedload(Employee.position)).where(
        Employee.position_id == position_id,
        Employee.company_id == current_user.company_id
    )
    employees = db.scalars(stmt).all()
    return employees

@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crea un nuevo empleado asociado a la empresa del usuario.
    """
    if employee_data.position_id:
        pos = db.get(Position, employee_data.position_id)
        if not pos:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El cargo/posición especificado no existe."
            )

    new_employee = Employee(
        fname=employee_data.fname,
        lname1=employee_data.lname1,
        lname2=employee_data.lname2,
        email=employee_data.email,
        phone=employee_data.phone,
        position_id=employee_data.position_id,
        company_id=current_user.company_id,
        is_active=True
    )
    db.add(new_employee)
    db.commit()
    
    stmt = select(Employee).options(joinedload(Employee.position)).where(Employee.employee_id == new_employee.employee_id)
    return db.scalar(stmt)

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Actualiza los datos de un empleado de la empresa.
    """
    stmt = select(Employee).where(
        Employee.employee_id == employee_id,
        Employee.company_id == current_user.company_id
    )
    employee = db.scalar(stmt)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado o acceso denegado."
        )

    if employee_data.position_id:
        pos = db.get(Position, employee_data.position_id)
        if not pos:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El cargo/posición especificado no existe."
            )

    update_dict = employee_data.model_dump(exclude_unset=True)
    for key, val in update_dict.items():
        setattr(employee, key, val)

    db.commit()
    
    stmt = select(Employee).options(joinedload(Employee.position)).where(Employee.employee_id == employee_id)
    return db.scalar(stmt)

@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Desactiva lógicamente un empleado de la empresa (Soft Delete).
    """
    stmt = select(Employee).where(
        Employee.employee_id == employee_id,
        Employee.company_id == current_user.company_id
    )
    employee = db.scalar(stmt)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado o acceso denegado."
        )

    employee.is_active = False
    db.commit()
    return