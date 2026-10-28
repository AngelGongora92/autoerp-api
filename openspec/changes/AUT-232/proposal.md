# Propuesta Backend para AUT-232

## Análisis de Impacto
Tras revisar el detalle del ticket **AUT-232**, se identifica que la solicitud consiste en ajustar la posición de un mensaje de advertencia (warning/pop-up) en la interfaz de usuario cuando se selecciona un día no habilitado para agendar citas.

El flujo de validación de disponibilidad de horarios ya hace uso de los datos entregados por la API existente (`GET /schedules/blocks/{employee_id}`). La falta de visibilidad del mensaje por problemas de scroll es una responsabilidad puramente del Frontend.

## Conclusión
No se requieren modificaciones en modelos de datos, esquemas Pydantic, migraciones de Alembic ni nuevos endpoints de la API.
