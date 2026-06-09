from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
import jwt

from .schemas.user import UserCreate, UserResponse, UserUpdate, PermissionBase
from .database import User, Permission, Company, get_db
from . import hashing
from api.auth_deps import get_current_user, SUPABASE_JWT_SECRET

# --- Creación del Router ---
router = APIRouter()

# DTO para el registro de nueva compañía y administrador
class UserRegisterPayload(BaseModel):
    company_name: str
    token: str

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene el perfil del usuario autenticado actualmente y sus permisos.
    """
    stmt = select(User).options(joinedload(User.permissions), joinedload(User.employee)).where(User.user_id == current_user.user_id)
    user = db.scalar(stmt)
    return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_new_company_and_user(
    payload: UserRegisterPayload,
    db: Session = Depends(get_db)
):
    """
    Registra de manera pública un nuevo taller/empresa junto con su primer usuario Administrador.
    Verifica la sesión decodificando el token de Supabase Auth directamente.
    """
    try:
        # Decodificar el token de Supabase usando el decodificador híbrido compartido
        from api.auth_deps import decode_supabase_token
        decoded = decode_supabase_token(payload.token)
        supabase_uid = decoded.get("sub")
        email = decoded.get("email") or decoded.get("username")
        if not supabase_uid or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El token de Supabase no contiene información de usuario válida."
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de Supabase ha expirado."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token de Supabase inválido o expirado: {str(e)}"
        )
        
    # Verificar si el usuario ya está registrado localmente
    existing_user = db.scalar(select(User).where(User.supabase_uid == supabase_uid))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este usuario ya está registrado en Auto ERP."
        )
        
    # Crear la nueva compañía/taller
    new_company = Company(name=payload.company_name)
    db.add(new_company)
    db.flush() # Genera el company_id
    
    # Crear el usuario administrador de esta nueva compañía
    new_user = User(
        username=email,
        supabase_uid=supabase_uid,
        company_id=new_company.company_id,
        is_admin=True,
        is_active=True,
        is_employee=False
    )
    
    # Asignar automáticamente todos los permisos del sistema al primer administrador
    all_permissions = db.scalars(select(Permission)).all()
    new_user.permissions = list(all_permissions)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crea un nuevo usuario asociado a la misma empresa del administrador. (Solo para administradores)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden crear usuarios."
        )

    # 1. Verificar si el nombre de usuario ya existe en el sistema
    existing_user = db.scalars(
        select(User).where(User.username == user_data.username)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya está en uso."
        )

    # 2. Hashear la contraseña (si se envía)
    hashed_password = hashing.hash_password(user_data.password) if user_data.password else None

    # 3. Crear el nuevo usuario
    new_user = User(
        username=user_data.username,
        password=hashed_password,
        is_admin=user_data.is_admin,
        is_employee=user_data.is_employee,
        is_active=user_data.is_active,
        company_id=current_user.company_id,
        supabase_uid=user_data.supabase_uid,
        employee_id=user_data.employee_id
    )

    # 4. Asignar los permisos
    if user_data.is_admin:
        # Administradores heredan automáticamente todos los permisos
        all_permissions = db.scalars(select(Permission)).all()
        new_user.permissions = list(all_permissions)
    elif user_data.permissions:
        permission_names = [p.name for p in user_data.permissions]
        permissions_objs = [
            db.scalars(select(Permission).where(Permission.name == name)).first() or Permission(name=name)
            for name in permission_names
        ]
        new_user.permissions = permissions_objs

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene una lista de todos los usuarios de la misma empresa. (Solo para administradores)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado."
        )

    stmt = select(User).options(joinedload(User.permissions), joinedload(User.employee)).where(User.company_id == current_user.company_id)
    users = db.scalars(stmt).unique().all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene los detalles de un usuario específico de la empresa. (Solo para administradores)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado."
        )

    stmt = (
        select(User)
        .options(joinedload(User.permissions), joinedload(User.employee))
        .where(User.user_id == user_id, User.company_id == current_user.company_id)
    )
    user = db.scalar(stmt)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado o acceso denegado."
        )

    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Actualiza un usuario y sus permisos asignados. (Solo para administradores)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado."
        )

    user = db.scalar(
        select(User).where(User.user_id == user_id, User.company_id == current_user.company_id)
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado o acceso denegado."
        )

    update_data = user_data.model_dump(exclude_unset=True)
    permissions_to_update = update_data.pop("permissions", None)

    # 1. Actualizar campos básicos
    for key, value in update_data.items():
        setattr(user, key, value)

    # 2. Actualizar permisos
    if user.is_admin:
        # Admins heredan todos los permisos
        all_permissions = db.scalars(select(Permission)).all()
        user.permissions = list(all_permissions)
    elif permissions_to_update is not None:
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
    current_user: User = Depends(get_current_user),
):
    """
    Elimina un usuario de la empresa. (Solo para administradores)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado."
        )

    user = db.scalar(
        select(User).where(User.user_id == user_id, User.company_id == current_user.company_id)
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado o acceso denegado."
        )

    db.delete(user)
    db.commit()
    return