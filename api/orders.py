from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import select
from .database import get_db, Order
from .schemas.user import CreateOrder, OrderResponse, OrderUpdate

router = APIRouter()



@router.post("/", response_model=OrderResponse)
async def create_order(
    order_data: CreateOrder,
    db: Session = Depends(get_db),
):
    """
    Crea una nueva orden en la base de datos.
    """
    # Convierte el objeto de Pydantic a un diccionario. Esto incluirá todos
    # los valores por defecto si no fueron enviados por el cliente.
    order_dict = order_data.model_dump()

    # Crea una nueva instancia de la clase de la base de datos
    # usando el diccionario. Esto garantiza que todos los campos
    # de Pydantic se asignen correctamente.
    new_order = Order(**order_dict)

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order

@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: Session = Depends(get_db),
):
    """
    Actualiza una orden existente de forma parcial.
    """
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Convierte el modelo Pydantic a un diccionario, excluyendo campos no enviados
    update_data = order_data.model_dump(exclude_unset=True)

    # Actualiza los campos del objeto de la base de datos
    for key, value in update_data.items():
        setattr(order, key, value)

    db.commit()
    db.refresh(order)

    return order


@router.get("/", response_model=List[OrderResponse])
async def get_all_orders(
    db: Session = Depends(get_db),
):
    """
    Obtiene una lista de todas las órdenes.
    """
    stmt = select(Order)
    orders = db.scalars(stmt).unique().all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene orden por ID
    """
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/customId/{c_order_id}", response_model=OrderResponse)
async def get_order_by_custom_id(
    c_order_id: str,
    db: Session = Depends(get_db),
):
    """
    Obtiene orden por el custom_ID
    """
    stmt = select(Order).where(Order.c_order_id == c_order_id)
    order = db.scalars(stmt).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order with custom ID '{c_order_id}' not found")
    return order