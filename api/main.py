from fastapi import FastAPI
from api import auth as auth_router  # Importa el router de autenticación
from api import users as users_router  # Importa el router de usuarios
from api import customers as customers_router  # Importa el router de clientes

# Crea la instancia principal de la aplicación FastAPI
app = FastAPI(
    title="AutoERP API",
    description="API de prueba para el proyecto de gestión.",
    version="1.0.0",
)

# Incluye el router de autenticación.
# El prefijo "/auth" hará que todas las rutas en auth_router
app.include_router(auth_router.router, prefix="/auth", tags=["Autenticación"])
app.include_router(users_router.router, prefix="/users", tags=["Usuarios"])
app.include_router(customers_router.router, prefix="/customers", tags=["Clientes"])


@app.get("/")
async def read_root():
    """
    Ruta de bienvenida de la API.
    """
    return {"message": "¡API en funcionamiento! Revisa la documentación en http://127.0.0.1:8000/docs"}