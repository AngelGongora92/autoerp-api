# Propuesta Backend para AUT-243

## Análisis de Impacto Backend

Tras el análisis detallado de los requerimientos y los criterios de aceptación del ticket **AUT-243**, se determinó que **no se requieren cambios en el Backend** (sin modificaciones en base de datos, modelos SQLAlchemy/Pydantic ni nuevos endpoints de FastAPI).

### Justificación por Criterio:
1. **Dropdown de Cliente Truncado:** Es una corrección de estilos CSS/Tailwind (`overflow-visible`, control de `z-index`) en los componentes de React `NewAppointmentPage.jsx` y `CustomerAutocomplete.jsx`.
2. **Card de Contacto Inconsistente:** Rediseño UI en el Frontend para igualar el componente visual utilizado en `NewOrderPage` (`AUT-240`).
3. **Cálculo Erróneo de Duración:** Ajuste en la lógica de estado del cliente (React) para inicializar el contador de duración en `0 min` en lugar del valor por defecto (`30 min`) cuando `selectedReasonIds` está vacío, sumando dinámicamente el campo `duration_minutes` proveniente del endpoint `GET /appointments/reasons/`.
4. **Horarios Libres en Agenda:** Generación visual en el cliente de la grilla horaria (intervalos de 30/60 min) en `AppointmentsView.jsx` y `AppointmentWeekView.jsx`. El Frontend utiliza las citas retornadas por `GET /appointments/` para determinar y dibujar los bloques vacíos/disponibles.
