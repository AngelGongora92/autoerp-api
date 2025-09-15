from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from typing import List

# Importar las clases de Pydantic desde su nuevo archivo
from .schemas.user import UserResponse, UserUpdate, PermissionBase, CustomerResponse, CustomerUpdate, CustomerCreate

# Reutilizamos la dependencia get_db y los modelos
from .database import User, Permission, Customer, get_db


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
    Busca clientes por nombre completo (concatenando fname y lname) o por nombre de compañía.
    """
    search_term = f"%{full_name.lower()}%"
    
    # Concatenamos fname y lname para buscar el nombre completo en una sola cadena.
    # Esto permite búsquedas como "Angel Gongora" aunque estén en campos separados.
    full_name_db = func.concat(Customer.fname, ' ', Customer.lname)
    
    # Construir la consulta para buscar en el nombre completo concatenado o en el nombre de la compañía
    stmt = select(Customer).where(
        (full_name_db.ilike(search_term)) |
        (Customer.cname.ilike(search_term))
    )
    
    customers = db.scalars(stmt).unique().all()
    
    # Nota: Si no se encuentran clientes, se devuelve una lista vacía [], que es la respuesta correcta para una búsqueda sin resultados.
    return customers


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un nuevo customer en la base de datos.
    """
    # 1. Verificar si el email ya está en uso
    existing_customer = db.scalars(
        select(Customer).where(Customer.email == customer_data.email)
    ).first()
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está en uso"
        )

    # 2. Preparar los datos del nuevo customer
    new_customer = Customer(
        is_company=customer_data.is_company,
        cname=customer_data.cname,
        fname=customer_data.fname,
        lname=customer_data.lname,
        address1=customer_data.address1,
        address2=customer_data.address2,
        email=customer_data.email,
        phone=customer_data.phone
    )

    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


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