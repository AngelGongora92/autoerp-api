from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from dotenv import load_dotenv

# Cargar variables de entorno desde .env al iniciar la app
load_dotenv()

from .database import Base, engine  # Importamos la Base y el engine
from api import auth as auth_router  # Importa el router de autenticación
from api import users as users_router  # Importa el router de usuarios
from api import customers as customers_router  # Importa el router de clientes
from api.contacts import router as contacts_router  # Importa el router de contactos
from api import employees as employees_router # Importa el router de empleados
from api import orders as orders_router # Importa el router de órdenes
from api import vehicles as vehicles_router # Importa el router de vehículos
from api import appointments as appointments_router # Importa el router de citas
from api import schedules as schedules_router # Importa el router de horarios
from api import settings as settings_router # Importa el router de configuración

# --- Creación de Tablas en la Base de Datos ---
# Se hizo el cambio a Alembic, ahora Alembic maneja las migraciones.

# Crea la instancia principal de la aplicación FastAPI
app = FastAPI(
    title="AutoERP API",
    description="API de prueba para el proyecto de gestión.",
    version="1.0.0",
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://autoerp-fe.vercel.app",
    "https://autoerp-fe.vercel.app/",
]

# PASO 3: Añade el middleware a tu aplicación
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Permite los orígenes especificados
    allow_credentials=True, # Permite cookies (si las usas)
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], # Asegúrate de incluir PATCH y OPTIONS    # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],    # Permite todos los encabezados
)





# Incluye el router de autenticación.
# El prefijo "/auth" hará que todas las rutas en auth_router
app.include_router(auth_router.router, prefix="/auth", tags=["Autenticación"])
app.include_router(users_router.router, prefix="/users", tags=["Usuarios"])
app.include_router(customers_router.router, prefix="/customers", tags=["Clientes"])
app.include_router(contacts_router, prefix="/contacts", tags=["Contactos"])
app.include_router(employees_router.router, prefix="/employees", tags=["Empleados"])
app.include_router(orders_router.router, prefix="/orders", tags=["Órdenes"])
app.include_router(vehicles_router.router, prefix="/vehicles", tags=["Vehículos"])
app.include_router(appointments_router.router, prefix="/appointments", tags=["Citas"])
app.include_router(schedules_router.router, prefix="/schedules", tags=["Horarios"])
app.include_router(settings_router.router, prefix="/settings", tags=["Configuración"])


@app.get("/")
async def root():
    """
    Ruta de bienvenida de la API.
    """
    return {"message": "¡API en funcionamiento! Revisa la documentación en http://127.0.0.1:8000/docs"}

@app.get("/test-env")
async def test_env():
    import os
    return {
        "META_TOKEN_SET": bool(os.environ.get("META_TOKEN")),
        "META_PHONE_ID_SET": bool(os.environ.get("META_PHONE_ID")),
        "META_TEST_PHONE_NUMBER_SET": bool(os.environ.get("META_TEST_PHONE_NUMBER")),
        "BREVO_API_KEY_SET": bool(os.environ.get("BREVO_API_KEY")),
        "BREVO_SENDER_EMAIL_SET": bool(os.environ.get("BREVO_SENDER_EMAIL")),
        "BREVO_SENDER_NAME_SET": bool(os.environ.get("BREVO_SENDER_NAME")),
        "DATABASE_URL_SET": bool(os.environ.get("DATABASE_URL")),
    }