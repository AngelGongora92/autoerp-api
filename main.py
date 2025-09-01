from fastapi import FastAPI

# Crea la instancia principal de la aplicación FastAPI
app = FastAPI(
    title="Mi Proyecto de APIs",
    description="API de prueba para el proyecto de gestión.",
    version="1.0.0",
)

@app.get("/")
async def read_root():
    """
    Ruta de bienvenida de la API.
    """
    return {"message": "¡API en funcionamiento! Revisa la documentación en http://127.0.0.1:8000/docs"}