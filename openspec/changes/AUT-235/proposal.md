# Propuesta Backend para AUT-235: Filtrado de Citas por Rango de Fechas

## Contexto
La interfaz requiere vistas por día y por semana de las citas registradas en la agenda. Actualmente, el endpoint `GET /appointments/` solo admite el parámetro opcional `assigned_to`, lo que traería todas las citas sin límite temporal.

## Solución Propuesta
1. **Extensión de `GET /appointments/`**:
   - Añadir parámetros de query opcionales `start_date` y `end_date` (formato ISO `YYYY-MM-DD` o `YYYY-MM-DDTHH:MM:SS`).
2. **Lógica de Filtrado en DB (SQLAlchemy)**:
   - Si se reciben `start_date` y/o `end_date`, aplicar los filtros `appointment_date >= start_date` y `appointment_date <= end_date` en la consulta ORM.
3. **Compatibilidad con Clientes Existentes**:
   - Los parámetros serán opcionales para mantener compatibilidad hacia atrás si algún cliente realiza peticiones sin rango.
