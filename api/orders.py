from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import select
from .database import get_db, Order, OrderExtraItems, OrderExtraInfo
from .schemas.user import CreateOrder, OrderResponse, OrderUpdate, OrderExtraItemsResponse, OrderExtraInfoCreate

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

@router.get("/extra-items/", response_model=List[OrderExtraItemsResponse])
async def get_all_order_extra_items(
    db: Session = Depends(get_db),
):
    """
    Obtiene todos los ítems extra de órdenes.
    """
    stmt = select(OrderExtraItems)
    items = db.scalars(stmt).all()
    return items

@router.post("/extra-info/", response_model=List[OrderExtraInfoCreate], status_code=status.HTTP_201_CREATED,
             summary="Crea una o más entradas de información extra para una orden")
async def create_order_extra_info(
    order_extra_info: List[OrderExtraInfoCreate],
    db: Session = Depends(get_db),
):
    """
    Crea una o más entradas de información extra asociadas a una orden.
    Acepta una lista de objetos para inserción masiva.
    Verifica que la `order_id` y la `item_id` existan antes de la creación.
    """
    created_info = []
    for info_data in order_extra_info:
        # Verificar que la order_id exista
        order_exists = db.get(Order, info_data.order_id)
        if not order_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID {info_data.order_id} not found."
            )
        
        # Verificar que la item_id exista en OrderExtraItems
        item_exists = db.get(OrderExtraItems, info_data.item_id)
        if not item_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OrderExtraItem with ID {info_data.item_id} not found."
            )

        new_info = OrderExtraInfo(**info_data.model_dump())
        db.add(new_info)
        created_info.append(new_info)

    db.commit()
    # El refresh no es estrictamente necesario aquí ya que no hay campos generados por DB,
    # pero es buena práctica si el modelo cambiara en el futuro.
    return created_info