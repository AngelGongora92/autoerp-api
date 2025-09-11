from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import List
from.schemas.user import UserCreate
from . import hashing  # Asegúrate de tener un módulo de hashing para las contr

# Importar las clases de Pydantic desde su nuevo archivo
from .schemas.user import UserResponse, UserUpdate, PermissionBase

# Reutilizamos la dependencia get_db y los modelos
from .database import User, Permission
from .auth import get_db

# --- Creación del Router ---
router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    # 1. Verificar si el usuario ya existe
    existing_user = db.scalars(
        select(User).where(User.username == user_data.username)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya está en uso"
        )

    # 2. Hashear la contraseña (¡MUY IMPORTANTE!)
    hashed_password = hashing.hash_password(user_data.password)

    # 3. Preparar los datos del nuevo usuario
    new_user = User(
        username=user_data.username,
        password=hashed_password, # Guarda la contraseña hasheada
        is_admin=user_data.is_admin
    )

    # --- LÓGICA DE PERMISOS ---
    if user_data.is_admin:
        # Si es admin, ignora los permisos enviados y asigna TODOS
        all_permissions = db.scalars(select(Permission)).all()
        new_user.permissions = list(all_permissions)
    elif user_data.permissions:
        # Si no es admin, procesa los permisos enviados (como antes)
        permission_names = [p.name for p in user_data.permissions]
        permissions_objs = [
            db.scalars(select(Permission).where(Permission.name == name)).first() or Permission(name=name)
            for name in permission_names
        ]
        new_user.permissions = permissions_objs

    
    # 4. Manejar y asignar los permisos
    if user_data.permissions:
        permission_names = [p.name for p in user_data.permissions]
        permissions_objs = [
            db.scalars(select(Permission).where(Permission.name == name)).first() or Permission(name=name)
            for name in permission_names
        ]
        new_user.permissions = permissions_objs

    # 5. Guardar el nuevo usuario en la base de datos
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


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

    update_data = user_data.model_dump(exclude_unset=True)
    permissions_to_update = update_data.pop("permissions", None)

    # 1. Actualizar campos básicos (username, is_admin)
    for key, value in update_data.items():
        setattr(user, key, value)

    # --- LÓGICA DE PERMISOS ---
    if user.is_admin:
        # Si el usuario AHORA es admin (después de la actualización), asigna todos los permisos
        all_permissions = db.scalars(select(Permission)).all()
        user.permissions = list(all_permissions)
    elif permissions_to_update is not None:
        # Si NO es admin y se enviaron permisos, procesa los permisos enviados
        permission_names = [p['name'] for p in permissions_to_update]
        permissions_objs = [
            db.scalars(select(Permission).where(Permission.name == name)).first() or Permission(name=name)
            for name in permission_names
        ]
        user.permissions = permissions_objs
        
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