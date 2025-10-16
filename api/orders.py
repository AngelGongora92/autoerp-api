from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import select
from .database import get_db, Order, OrderExtraItems, OrderExtraInfo
from .schemas.user import CreateOrder, OrderResponse, OrderUpdate, OrderExtraItemsResponse, OrderExtraInfoCreate, OrderExtraInfoResponse


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

@router.get("/extra-info/{order_id}", response_model=List[OrderExtraInfoResponse])
async def get_order_extra_info(
    order_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene toda la información extra asociada a una orden específica.
    """
    stmt = select(OrderExtraInfo).where(OrderExtraInfo.order_id == order_id)
    extra_info = db.scalars(stmt).all()
    return extra_info

@router.post("/extra-info/", response_model=List[OrderExtraInfoResponse], status_code=status.HTTP_200_OK,
             summary="Crea o actualiza entradas de información extra para una orden (Upsert)")
async def upsert_order_extra_info(
    order_extra_info: List[OrderExtraInfoCreate],
    db: Session = Depends(get_db),
):
    """
    Crea o actualiza (Upsert) una o más entradas de información extra asociadas a una orden.
    Acepta una lista de objetos. Para cada objeto:
    - Si la combinación `(order_id, item_id)` ya existe, actualiza el campo `info`.
    - Si no existe, crea una nueva entrada.
    """
    processed_info = []
    for info_data in order_extra_info:
        # 1. Buscar si la entrada ya existe usando la clave primaria compuesta
        existing_info = db.get(OrderExtraInfo, (info_data.order_id, info_data.item_id))
 
        if existing_info:
            # 2. Si existe, actualiza el campo 'info'
            existing_info.info = info_data.info
            db.add(existing_info) # Marcar el objeto como 'dirty' para que se guarde
            processed_info.append(existing_info)
        else:
            # 3. Si no existe, crea una nueva entrada
            # (Opcional pero recomendado) Verificar que las FKs existan
            if not db.get(Order, info_data.order_id):
                raise HTTPException(status_code=404, detail=f"Order with ID {info_data.order_id} not found.")
            if not db.get(OrderExtraItems, info_data.item_id):
                raise HTTPException(status_code=404, detail=f"Item with ID {info_data.item_id} not found.")
 
            new_info = OrderExtraInfo(**info_data.model_dump())
            db.add(new_info)
            processed_info.append(new_info)
 
    db.commit()
 
    # Refrescar cada objeto para obtener el estado final de la DB (útil si hay triggers o defaults)
    for info in processed_info:
        db.refresh(info)
 
    return processed_info