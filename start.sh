#!/usr/bin/env bash
# Iniciar la base de datos (si aplica)
# python -m your_app.database.py

# Iniciar el servidor Uvicorn
uvicorn api.main:app --host 0.0.0.0 --port $PORT