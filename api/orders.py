from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import select
from .database import get_db, Order, OrderExtraItems, OrderExtraInfo, BodyworkDetailTypes, BodyworkDetails
from .schemas.user import CreateOrder, OrderResponse, OrderUpdate, OrderExtraItemsResponse, OrderExtraInfoCreate, OrderExtraInfoResponse, BodyworkDetailTypesResponse, BodyworkDetailTypesCreate, BodyworkDetailsResponse, BodyworkDetailsCreate, BodyworkDetailTypesUpdate, BodyworkDetailsUpdate


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


@router.get("/bodywork-detail-types/", response_model=List[BodyworkDetailTypesResponse])
async def get_all_bodywork_detail_types(
    db: Session = Depends(get_db),
):
    """
    Obtiene todos los tipos de detalle de carrocería.
    """
    stmt = select(BodyworkDetailTypes)
    detail_types = db.scalars(stmt).all()
    return detail_types

@router.post("/bodywork-detail-types/", response_model=BodyworkDetailTypesResponse, status_code=status.HTTP_201_CREATED)
async def create_bodywork_detail_type(
    detail_type_data: BodyworkDetailTypesCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un nuevo tipo de detalle de carrocería.
    """
    new_detail_type = BodyworkDetailTypes(**detail_type_data.model_dump())
    db.add(new_detail_type)
    db.commit()
    db.refresh(new_detail_type)
    return new_detail_type

@router.patch("/bodywork-detail-types/{detail_type_id}", response_model=BodyworkDetailTypesResponse)
async def update_bodywork_detail_type(
    detail_type_id: int,
    detail_type_data: BodyworkDetailTypesUpdate,
    db: Session = Depends(get_db),
):
    """
    Actualiza parcialmente un tipo de detalle de carrocería existente.
    """
    detail_type = db.get(BodyworkDetailTypes, detail_type_id)
    if not detail_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bodywork Detail Type with ID {detail_type_id} not found."
        )

    # Actualiza los campos
    update_data = detail_type_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(detail_type, key, value)

    db.commit()
    db.refresh(detail_type)
    return detail_type

@router.get("/bodywork-details/{order_id}", response_model=List[BodyworkDetailsResponse])
async def get_bodywork_details(
    order_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene todos los detalles de la lista de verificación de carrocería para una orden.
    """
    stmt = select(BodyworkDetails).where(BodyworkDetails.order_id == order_id)
    details = db.scalars(stmt).all()
    return details

@router.patch("/bodywork-details/{detail_id}", response_model=BodyworkDetailsResponse)
async def update_bodywork_detail(
    detail_id: int,
    detail_data: BodyworkDetailsUpdate,
    db: Session = Depends(get_db),
):
    """
    Actualiza parcialmente un detalle de la lista de verificación de carrocería.
    """
    detail = db.get(BodyworkDetails, detail_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bodywork Detail with ID {detail_id} not found."
        )

    # Actualiza los campos
    update_data = detail_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(detail, key, value)

    db.commit()
    db.refresh(detail)
    return detail

@router.delete("/bodywork-details/{detail_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bodywork_detail(
    detail_id: int,
    db: Session = Depends(get_db),
):
    """
    Elimina un detalle específico de la lista de verificación de carrocería.
    """
    detail = db.get(BodyworkDetails, detail_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bodywork Detail with ID {detail_id} not found."
        )

    db.delete(detail)
    db.commit()
    return None


@router.post("/bodywork-details/", response_model=List[BodyworkDetailsResponse], status_code=status.HTTP_201_CREATED)
async def create_bodywork_details(
    detail_items: List[BodyworkDetailsCreate],
    db: Session = Depends(get_db),
):
    """
    Crea una o más entradas en la lista de verificación de carrocería para una orden.
    Acepta una lista de objetos de checklist.
    """
    created_items = []
    for item_data in detail_items:
        # (Opcional pero recomendado) Verificar que las FKs existan para cada item
        if not db.get(Order, item_data.order_id):
            raise HTTPException(status_code=404, detail=f"Order with ID {item_data.order_id} not found.")
        if not db.get(BodyworkDetailTypes, item_data.detail_type_id):
            raise HTTPException(status_code=404, detail=f"Bodywork Detail Type with ID {item_data.detail_type_id} not found.")

        new_item = BodyworkDetails(**item_data.model_dump())
        db.add(new_item)
        created_items.append(new_item)

    db.commit()

    # Refrescar cada objeto para obtener los IDs generados por la base de datos
    for item in created_items:
        db.refresh(item)

    return created_items

@router.get("/order-exists/{c_order_id}", response_model=bool)
async def check_order_exists(
    c_order_id: str,
    db: Session = Depends(get_db),
):
    """
    Verifica si una orden existe.
    """
    order = db.get(Order, c_order_id)
    return order is not None

@router.get("/last-order-id/", response_model=Optional[int])
async def get_last_order_id(
    db: Session = Depends(get_db),
):
    """
    Obtiene el ID de la última orden.
    """
    stmt = select(Order).order_by(Order.order_id.desc())
    last_order = db.scalars(stmt).first()
    if last_order:
        return last_order.c_order_id
    return None
