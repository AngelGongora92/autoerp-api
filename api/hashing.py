from passlib.context import CryptContext

# 1. Creamos un contexto de criptografía
#    Le decimos que bcrypt es el esquema de hashing por defecto.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. Función para hashear una contraseña
def hash_password(plain_password: str) -> str:
    """
    Toma una contraseña en texto plano y devuelve su hash.
    """
    return pwd_context.hash(plain_password)

# 3. Función para verificar una contraseña
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara una contraseña en texto plano con un hash almacenado.
    Devuelve True si coinciden, False si no.
    """
    return pwd_context.verify(plain_password, hashed_password)