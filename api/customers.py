from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import List

# Importar las clases de Pydantic desde su nuevo archivo
from .schemas.user import UserResponse, UserUpdate, PermissionBase, CustomerResponse, CustomerUpdate

# Reutilizamos la dependencia get_db y los modelos
from .database import User, Permission, Customer
from .auth import get_db

# --- Creación del Router ---
router = APIRouter()

@router.get("/", response_model=List[CustomerResponse])
async def get_all_customers(
    db: Session = Depends(get_db),
):
    """
    Obtiene una lista de todos los clientes.
    """
    stmt = select(Customer)
    customers = db.scalars(stmt).unique().all()
    return customers


@router.get("/search", response_model=List[CustomerResponse])
async def search_customers_by_name(
    full_name: str,
    db: Session = Depends(get_db),
):
    """
    Busca clientes por nombre completo (fname y lname).
    """
    search_term = f"%{full_name.lower()}%"
    
    # Construir la consulta para buscar en fname y lname
    stmt = select(Customer).where(
        (Customer.fname.ilike(search_term)) |
        (Customer.lname.ilike(search_term)) |
        (Customer.cname.ilike(search_term))
    )
    
    customers = db.scalars(stmt).unique().all()
    
    if not customers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No customers found matching the search criteria"
        )
    
    return customers



@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer_by_id(
    customer_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene un solo customer por su ID.
    """
    # Usamos db.get() para buscar el usuario por su ID de manera más directa
    customer = db.get(Customer, customer_id)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
):
    """
    Actualiza un customer existente.
    """
    customer = db.get(Customer, customer_id)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Convertir el modelo Pydantic a un diccionario, excluyendo campos no enviados
    update_data = customer_data.model_dump(exclude_unset=True)

 
    for key, value in update_data.items():
        setattr(customer, key, value)

    db.add(customer)

    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer_by_id(
    customer_id: int,
    db: Session = Depends(get_db),
):
    """
    Elimina un usuario de la base de datos por su ID.
    """
    customer = db.get(Customer, customer_id)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    db.delete(customer)
    db.commit()
    return