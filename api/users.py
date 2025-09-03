from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import List

# Importar las clases de Pydantic desde su nuevo archivo
from .schemas.user import UserResponse, UserUpdate, PermissionBase

# Reutilizamos la dependencia get_db y los modelos
from .database import User, Permission
from .auth import get_db

# --- Creación del Router ---
router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    db: Session = Depends(get_db),
):
    """
    Obtiene una lista de todos los usuarios y sus permisos.
    """
    stmt = select(User).options(joinedload(User.permissions))
    users = db.scalars(stmt).unique().all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene un solo usuario por su ID.
    """
    # Usamos db.get() para buscar el usuario por su ID de manera más directa
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Cargamos los permisos del usuario después de obtenerlo para una sola consulta
    user_with_permissions = db.scalars(
        select(User)
        .options(joinedload(User.permissions))
        .where(User.id == user_id)
    ).first()

    return user_with_permissions


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Convertir el modelo Pydantic a un diccionario, excluyendo campos no enviados
    update_data = user_data.model_dump(exclude_unset=True)

    # Extraer los permisos para manejarlos por separado
    permissions_to_update = update_data.pop("permissions", None)

    # 1. Actualizar los campos del usuario (username, is_admin)
    for key, value in update_data.items():
        setattr(user, key, value)

    # 2. Actualizar los permisos si se proporcionaron
    if permissions_to_update is not None:
        permission_names = [p['name'] for p in permissions_to_update]
        
        # Obtenemos todos los permisos necesarios, existentes o no
        permissions_objs = [
            db.scalars(select(Permission).where(Permission.name == name)).first() or Permission(name=name)
            for name in permission_names
        ]
        
        # Asignar la lista completa al usuario
        user.permissions = permissions_objs
        
        db.add(user)

    # 3. Guardar todos los cambios
    db.commit()
    db.refresh(user)

    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Elimina un usuario de la base de datos por su ID.
    """
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    db.delete(user)
    db.commit()
    return