# Propuesta Backend para AUT-233

## 1. Problema
Actualmente, el backend de AutoERP permite agendar múltiples citas simultáneas en el mismo rango de tiempo para el mismo asesor, debido a la falta de validación de solapamiento (*overlap*). Además, las citas no congelan/persisten la duración configurada en el taller (`slot_duration_minutes`), generando inconsistencias históricas si esta cambia. Tampoco existe una lógica de auto-asignación inteligente cuando el usuario no selecciona un asesor específico.

## 2. Solución Planteada
- **Persistencia e Inmutabilidad de Duración:** Añadir la columna `duration_minutes` a la tabla `appointments`. Si no se especifica en la petición o en la razón de la cita, se tomará el valor global de la empresa (`CompanySettings.slot_duration_minutes`).
- **Validación de Solapamiento:** Prevenir doble agenda evaluando la condición de intersección entre intervalos: `(start_a < end_b) AND (end_a > start_b)`. Citas en estado cancelado se ignoran.
- **Auto-asignación (Least Busy):** Si `assigned_to` es nulo, el backend busca todos los asesores activos sin conflicto en el rango especificado y selecciona aquel con menor cantidad de citas agendadas en la misma fecha.
