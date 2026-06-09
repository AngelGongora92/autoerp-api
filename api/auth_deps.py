import os
import logging
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import get_db, User

# Configurar logging
logger = logging.getLogger(__name__)

security = HTTPBearer()

# Clave secreta para decodificar JWTs de Supabase
# Se obtiene de variables de entorno con un fallback para pruebas locales
SUPABASE_JWT_SECRET = os.environ.get(
    "SUPABASE_JWT_SECRET", 
    "super-secret-supabase-jwt-key-for-local-testing-change-in-production"
)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependencia de FastAPI para obtener el usuario autenticado desde el JWT de Supabase.
    """
    token = credentials.credentials
    try:
        # Decodificar el token JWT de Supabase usando el secreto del proyecto
        # NOTA: Supabase firma los tokens usando HS256 con el JWT Secret del proyecto
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Supabase aud suele ser 'authenticated'
        )
        
        supabase_uid = payload.get("sub")
        if not supabase_uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: falta el campo sub (UUID de usuario)."
            )
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de sesión ha expirado."
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Error decodificando JWT: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sesión inválido."
        )

    # Buscar el usuario en la base de datos local por su supabase_uid
    stmt = select(User).where(User.supabase_uid == supabase_uid)
    user = db.scalar(stmt)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no registrado en la base de datos local de Auto ERP."
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La cuenta de usuario está desactivada."
        )
        
    return user
