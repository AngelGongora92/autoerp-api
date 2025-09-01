from fastapi import FastAPI
from api import auth as auth_router # Importa el router de autenticación

# Crea la instancia principal de la aplicación FastAPI
app = FastAPI(
    title="Mi Proyecto de APIs",
    description="API de prueba para el proyecto de gestión.",
    version="1.0.0",
)

# Incluye el router de autenticación.
# El prefijo "/auth" hará que todas las rutas en auth_router
# se sirvan bajo la URL /auth/... (ej. /auth/login)
app.include_router(auth_router.router, prefix="/auth", tags=["Autenticación"])

@app.get("/")
async def read_root():
    """
    Ruta de bienvenida de la API.
    """
    return {"message": "¡API en funcionamiento! Revisa la documentación en http://127.0.0.1:8000/docs"}