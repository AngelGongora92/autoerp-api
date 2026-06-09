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

# Clave secreta para decodificar JWTs locales simétricos (Mock Auth en desarrollo)
SUPABASE_JWT_SECRET = os.environ.get(
    "SUPABASE_JWT_SECRET", 
    "super-secret-supabase-jwt-key-for-local-testing-change-in-production"
)

# URL pública de Supabase para obtener las llaves asimétricas JWKS en producción
SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "https://phkzgddelreeslypfeqd.supabase.co"
)
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"

# Inicializar cliente JWKS de PyJWT
jwks_client = jwt.PyJWKClient(JWKS_URL)

# Diagnóstico de importación de cryptography
crypto_error = None
try:
    import cryptography
except Exception as e:
    crypto_error = f"Error al importar cryptography: {type(e).__name__} - {str(e)}"

def decode_supabase_token(token: str) -> dict:
    """
    Decodifica y valida un token JWT de Supabase.
    Soporta algoritmos simétricos (HS256 local) y asimétricos (ES256 en producción).
    """
    unverified_header = jwt.get_unverified_header(token)
    alg = unverified_header.get("alg", "HS256")
    
    if alg == "HS256":
        # Decodificación simétrica clásica (Desarrollo local con Mock Auth)
        return jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
    elif alg == "ES256":
        # Decodificación asimétrica dinámica usando JWKS (Producción con Supabase real)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            options={"verify_aud": False}
        )
    else:
        raise jwt.InvalidAlgorithmError(f"Algoritmo de token '{alg}' no soportado.")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependencia de FastAPI para obtener el usuario autenticado desde el JWT de Supabase.
    Soporta algoritmos simétricos (HS256 local) y asimétricos (ES256 en producción).
    """
    token = credentials.credentials
    try:
        payload = decode_supabase_token(token)
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
    except Exception as e:
        logger.error(f"Error decodificando JWT: {str(e)}")
        err_msg = f"Token de sesión inválido: {str(e)}"
        if crypto_error:
            err_msg += f" | DIAGNOSTICO: {crypto_error}"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err_msg
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
