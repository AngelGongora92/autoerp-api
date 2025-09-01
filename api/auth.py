from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any

# Crea una instancia de APIRouter
router = APIRouter()

# Define el modelo de datos para la petición de inicio de sesión
class UserLogin(BaseModel):
    username: str
    password: str

@router.post("/login", response_model=Dict[str, Any])
async def login(user_data: UserLogin):
    """
    Valida las credenciales de un usuario y devuelve los permisos asignados.
    """
    print(f"Petición de inicio de sesión recibida para el usuario: {user_data.username}")

    # Lógica de ejemplo (puedes probar con 'admin' y 'admin123')
    if user_data.username == "admin" and user_data.password == "admin123":
        return {
            "message": "¡Inicio de sesión exitoso!",
            "permissions": ["admin", "read", "write"]
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nombre de usuario o contraseña inválidos."
    )