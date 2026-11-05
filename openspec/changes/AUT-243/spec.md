# Especificación Backend para AUT-243

## Confirmación de Contrato de API Existente

No hay cambios de especificación u OpenAPI en este ticket. Los endpoints backend vigentes proveen toda la información necesaria:

* **`GET /appointments/`**:
  * Parámetros de consulta: `assigned_to`, `start_date`, `end_date`.
  * Retorna la lista de citas en el rango seleccionado (`appointment_date`, motivos, estado).
  * El Frontend utiliza estas citas para calcular qué rangos horarios están ocupados y dibujar los espacios libres.

* **`GET /appointments/reasons/`**:
  * Retorna el catálogo de motivos disponiendo del campo `duration_minutes` (Int).
  * El Frontend realiza la suma acumulada de este campo para reflejar el tiempo total estimado.
