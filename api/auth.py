import logging
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func

# Importa las clases y la sesión desde el nuevo archivo database.py
from .database import SessionLocal, User, Permission

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)

# Crea una instancia de APIRouter
router = APIRouter()


# --- Modelos de Pydantic ---

# Modelo para la petición de inicio de sesión (lo que envía el cliente)
class UserLogin(BaseModel):
    username: str
    password: str


# MEJORA: Modelo específico para la respuesta de login exitoso.
# Esto mejora la documentación automática y la predictibilidad de la API.
class LoginResponse(BaseModel):
    message: str
    permissions: List[str]
    # En un sistema real, aquí devolverías un token de acceso:
    # access_token: str
    # token_type: str = "bearer"


# --- Dependencia de Base de Datos ---

# Define una dependencia para obtener una sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Rutas de Autenticación ---

@router.post("/login", response_model=LoginResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Valida las credenciales de un usuario y devuelve los permisos asignados.
    """
    logging.info(f"Intento de login para el usuario: {user_data.username}")

    # Consulta el usuario por su nombre de usuario (sin importar mayúsculas/minúsculas)
    stmt = select(User).where(func.lower(User.username) == func.lower(user_data.username))
    user = db.scalar(stmt)

    # Si el usuario existe y la contraseña es correcta...
    # La función check_password debería manejar la comparación de hashes de forma segura.
    if user and user.check_password(user_data.password):
        # ...construye una lista de permisos
        user_permissions = []
        if user.is_admin:
            user_permissions.append("admin")

        # Añade los permisos desde la tabla 'permissions'
        for perm in user.permissions:
            user_permissions.append(perm.name)

        logging.info(f"Login exitoso para el usuario: {user_data.username}")
        return {
            "message": "¡Inicio de sesión exitoso!",
            "permissions": user_permissions,
            # "access_token": "aqui_iria_un_jwt_token_real",
        }

    # Si el usuario no existe o la contraseña es incorrecta, lanza una excepción
    logging.warning(f"Login fallido para el usuario: {user_data.username}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nombre de usuario o contraseña inválidos."
    )