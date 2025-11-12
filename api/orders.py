from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import select, func
from .database import get_db, Order, OrderExtraItems, OrderExtraInfo, BodyworkDetailTypes, BodyworkDetails, OrderInventoryData
from sqlalchemy.orm import joinedload, Session
from .schemas.user import CreateOrder, OrderResponse, OrderUpdate, OrderExtraItemsResponse, OrderExtraInfoCreate, OrderExtraInfoResponse, BodyworkDetailTypesResponse, BodyworkDetailTypesCreate, BodyworkDetailsResponse, BodyworkDetailsCreate, BodyworkDetailTypesUpdate, BodyworkDetailsUpdate, InventoryTypesResponse, InventoryTypesCreate, InventoryItemsCreate, InventoryItemsResponse, InventoryItemsByTypeResponse, InventoryItemReorder, OrderInventoryDataCreate, OrderInventoryDataResponse, InventoryTypesReorder, InventoryTypesUpdate, InventoryItemsUpdate
from .database import InventoryTypes, InventoryItems, OrderInventoryData

router = APIRouter()



@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: CreateOrder,
    db: Session = Depends(get_db),
):
    """
    Crea una nueva orden en la base de datos.
    """
    # Convierte el objeto de Pydantic a un diccionario. Esto incluirá todos
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

@router.post("/inventory-types/", response_model=InventoryTypesResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_type(
    inventory_type: InventoryTypesCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un nuevo tipo de inventario. La posición se asigna automáticamente.
    """
    # Calcular la siguiente posición
    max_position_stmt = select(func.max(InventoryTypes.position))
    max_position = db.scalar(max_position_stmt)
    
    next_position = (max_position + 1) if max_position is not None else 0

    # Crear el nuevo tipo de inventario con la posición calculada
    new_inventory_type = InventoryTypes(
        **inventory_type.model_dump(), position=next_position
    )
    db.add(new_inventory_type)
    db.commit()
    db.refresh(new_inventory_type)
    return new_inventory_type

@router.get("/inventory-types/", response_model=List[InventoryTypesResponse])
async def get_all_inventory_types(
    db: Session = Depends(get_db),
):
    """
    Obtiene todos los tipos de inventario.
    """
    stmt = select(InventoryTypes).order_by(InventoryTypes.position)
    inventory_types = db.scalars(stmt).all()
    return inventory_types

@router.patch("/inventory-types/{inv_type_id}", response_model=InventoryTypesResponse)
async def update_inventory_type(
    inv_type_id: int,
    inventory_type_data: InventoryTypesUpdate,
    db: Session = Depends(get_db),
):
    """
    Actualiza parcialmente un tipo de inventario existente.
    """
    inventory_type = db.get(InventoryTypes, inv_type_id)
    if not inventory_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory type not found")

    update_data = inventory_type_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(inventory_type, key, value)

    db.commit()
    db.refresh(inventory_type)
    return inventory_type

@router.put("/inventory-types/reorder", status_code=status.HTTP_200_OK)
async def reorder_inventory_types(
    reorder_data: List[InventoryTypesReorder],
    db: Session = Depends(get_db),
):
    """
    Reordena una lista de tipos de inventario.
    Recibe una lista completa de tipos con su nueva posición.
    Esta operación es atómica: o todos los tipos se reordenan, o ninguno lo hace.
    """
    if not reorder_data:
        return {"message": "No inventory types to reorder."}

    # Crear un mapa de inv_type_id a su nueva posición para una búsqueda rápida.
    position_map = {item.inv_type_id: item.position for item in reorder_data}
    inv_type_ids = list(position_map.keys())

    try:
        # Obtener todos los tipos de inventario de la base de datos en una sola consulta.
        types_to_update = db.scalars(select(InventoryTypes).where(InventoryTypes.inv_type_id.in_(inv_type_ids))).all()

        # Actualizar la posición de cada tipo en la sesión.
        for inv_type in types_to_update:
            inv_type.position = position_map[inv_type.inv_type_id]
        
        db.commit() # Guardar todos los cambios en una sola transacción.
    except Exception as e:
        db.rollback() # Si algo falla, revertir todos los cambios.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to reorder inventory types: {e}")

    return {"message": "Inventory types reordered successfully."}

@router.post("/inventory-items/", response_model=InventoryItemsResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    inventory_item: InventoryItemsCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un nuevo ítem de inventario. La posición se asigna automáticamente al final de la lista.
    """
    # 1. Calcular la siguiente posición para el tipo de inventario dado.
    # Se busca la posición máxima actual y se le suma 1.
    max_position_stmt = select(func.max(InventoryItems.position)).where(
        InventoryItems.inv_type_id == inventory_item.inv_type_id
    )
    max_position = db.scalar(max_position_stmt)
    
    # Si no hay ítems, la nueva posición es 0. De lo contrario, es max + 1.
    next_position = (max_position + 1) if max_position is not None else 0

    # 2. Crear el nuevo ítem con la posición calculada.
    new_inventory_item = InventoryItems(
        **inventory_item.model_dump(exclude_defaults=True), 
        position=next_position
    )
    db.add(new_inventory_item)
    db.commit()
    db.refresh(new_inventory_item)
    return new_inventory_item

@router.get("/inventory-items/{inv_type_id}", response_model=InventoryItemsByTypeResponse)
async def get_inventory_items_by_type(
    inv_type_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene un tipo de inventario y todos sus ítems asociados.
    """
    # 1. Obtener el tipo de inventario.
    inventory_type = db.get(InventoryTypes, inv_type_id)
    if not inventory_type:
        raise HTTPException(status_code=404, detail="Inventory type not found")

    # 2. Obtener todos los ítems asociados a ese tipo.
    # No necesitamos cargar la relación aquí porque ya tenemos el objeto inventory_type.
    stmt = select(InventoryItems).where(InventoryItems.inv_type_id == inv_type_id)
    items = db.scalars(stmt).all()

    # 3. Construir y devolver la respuesta estructurada.
    return {"inventory_type": inventory_type, "items": items}

@router.put("/inventory-items/reorder", status_code=status.HTTP_200_OK)
async def reorder_inventory_items(
    reorder_data: List[InventoryItemReorder],
    db: Session = Depends(get_db),
):
    """
    Reordena una lista de ítems de inventario.
    Recibe una lista completa de ítems con su nueva posición.
    Esta operación es atómica: o todos los ítems se reordenan, o ninguno lo hace.
    """
    if not reorder_data:
        return {"message": "No items to reorder."}

    # Crear un mapa de item_id a su nueva posición para una búsqueda rápida.
    position_map = {item.item_id: item.position for item in reorder_data}
    item_ids = list(position_map.keys())

    try:
        # Obtener todos los ítems de la base de datos en una sola consulta.
        items_to_update = db.scalars(select(InventoryItems).where(InventoryItems.item_id.in_(item_ids))).all()

        # Actualizar la posición de cada ítem en la sesión.
        for item in items_to_update:
            item.position = position_map[item.item_id]
        
        db.commit() # Guardar todos los cambios en una sola transacción.
    except Exception as e:
        db.rollback() # Si algo falla, revertir todos los cambios.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to reorder items: {e}")

    return {"message": "Items reordered successfully."}

@router.patch("/inventory-items/", response_model=List[InventoryItemsResponse])
async def update_inventory_items(
    items_to_update_data: List[InventoryItemsUpdate],
    db: Session = Depends(get_db),
):
    """
    Actualiza parcialmente múltiples ítems de inventario en una sola operación.
    Si algún `item_id` proporcionado no se encuentra, la operación fallará.
    """
    if not items_to_update_data:
        return []

    # 1. Extraer todos los IDs y crear un mapa con los datos de entrada.
    item_ids = [item.item_id for item in items_to_update_data]
    update_data_map = {item.item_id: item.model_dump(exclude_unset=True) for item in items_to_update_data}

    try:
        # 2. Obtener todos los ítems de la BD en una sola consulta.
        items_in_db = db.scalars(select(InventoryItems).where(InventoryItems.item_id.in_(item_ids))).all()

        # 3. Verificar que se encontraron todos los ítems solicitados.
        if len(items_in_db) != len(item_ids):
            found_ids = {item.item_id for item in items_in_db}
            missing_ids = set(item_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontraron los siguientes ítems: {list(missing_ids)}"
            )

        # 4. Actualizar los campos de cada ítem en la sesión de SQLAlchemy.
        for item in items_in_db:
            item_data = update_data_map[item.item_id]
            for key, value in item_data.items():
                if key != "item_id":  # No se debe actualizar la clave primaria
                    setattr(item, key, value)
        
        # 5. Guardar todos los cambios en una transacción atómica.
        db.commit()
        
        # 6. Refrescar los objetos para obtener el estado final de la BD.
        for item in items_in_db:
            db.refresh(item)
    except Exception as e:
        db.rollback() # Si algo falla, revertir todos los cambios.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al actualizar los ítems: {e}")

    return items_in_db


@router.post("/inventory-data/", response_model=List[OrderInventoryDataResponse], status_code=status.HTTP_200_OK)
async def upsert_order_inventory_data(
    data_entries: List[OrderInventoryDataCreate],
    db: Session = Depends(get_db),
):
    """
    Crea o actualiza (Upsert) múltiples entradas de datos de inventario para una orden.
    Acepta una lista de objetos. Para cada objeto:
    - Si ya existe una entrada para un `order_id` y `item_id`, la actualiza.
    - Si no existe, la crea.
    """
    if not data_entries:
        return []

    processed_entries = []
    # Extraemos los IDs para una consulta más eficiente
    order_id = data_entries[0].order_id
    item_ids = [entry.item_id for entry in data_entries]

    # 1. Obtenemos todas las entradas existentes para esta orden en una sola consulta.
    existing_entries_stmt = select(OrderInventoryData).where(
        OrderInventoryData.order_id == order_id,
        OrderInventoryData.item_id.in_(item_ids)
    )
    # Creamos un mapa para acceso rápido: {item_id: objeto_db}
    existing_entries_map = {entry.item_id: entry for entry in db.scalars(existing_entries_stmt).all()}

    for entry_data in data_entries:
        existing_entry = existing_entries_map.get(entry_data.item_id)
        if existing_entry:
            # 2. Si existe, actualiza el campo 'data'
            existing_entry.data = entry_data.data
            processed_entries.append(existing_entry)
        else:
            # 3. Si no existe, crea una nueva entrada
            new_entry = OrderInventoryData(**entry_data.model_dump())
            db.add(new_entry)
            processed_entries.append(new_entry)

    db.commit()
    
    # Refrescamos los objetos para asegurar que tienen los datos de la DB
    for entry in processed_entries:
        db.refresh(entry)

    return processed_entries

@router.get("/inventory-data/{order_id}/{inv_type_id}", response_model=List[OrderInventoryDataResponse])
async def get_order_inventory_data(
    order_id: int,
    inv_type_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene todas las entradas de datos de inventario para una orden y tipo de inventario específicos.
    """
    # 1. Obtener los item_ids que pertenecen al inv_type_id
    item_ids_stmt = select(InventoryItems.item_id).where(InventoryItems.inv_type_id == inv_type_id)
    item_ids = db.scalars(item_ids_stmt).all()
    if not item_ids:
        return [] # Si no hay items para ese tipo, no hay datos que devolver.

    # 2. Obtener los datos de la orden que coincidan con esos item_ids
    stmt = select(OrderInventoryData).where(
        OrderInventoryData.order_id == order_id,
        OrderInventoryData.item_id.in_(item_ids)
    )
    data_entries = db.scalars(stmt).all()
    return data_entries