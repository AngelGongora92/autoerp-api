# Proposal: AUT-33 - Configuración de Citas, Horarios y Duraciones

## 📌 Contexto
Actualmente, el sistema de agendamiento de citas permite seleccionar fechas y horas sin validar restricciones específicas de la empresa, tales como el rango de horarios de atención diarios, los días habilitados de la semana, la duración por defecto de una cita y los tipos/razones de cita disponibles.

## 🎯 Objetivo
Proporcionar en el backend las estructuras de datos, endpoints de configuración y validaciones necesarias para que cada empresa pueda parametrizar:
1. Rango de horario diario permitido para agendar citas (hora de inicio y hora de fin).
2. Duración por defecto de las citas en minutos.
3. Días de la semana habilitados para agendar citas (ej. Lunes a Sábado).
4. Tipos/Razones de cita gestionables (`appointment_reasons`).

## 🏗️ Impacto en la Arquitectura (Backend)
1. **Modelos y Base de Datos:**
   - Extender o asegurar la presencia de campos de configuración de citas en `CompanySettings` (o tabla de configuración de citas por empresa):
     - `appointment_start_time`: Time (ej. 08:00)
     - `appointment_end_time`: Time (ej. 18:00)
     - `default_appointment_duration_minutes`: Integer (ej. 30 o 60 min)
     - `allowed_appointment_days`: Array / JSON (ej. `[0, 1, 2, 3, 4, 5]`)
   - Endpoints en `api/settings.py` o `api/appointments.py` para consultar y actualizar dicha configuración por empresa.
2. **Validación al Crear/Reagendar Cita:**
   - Validar que la hora seleccionada esté dentro del rango de atención.
   - Validar que el día de la semana sea un día permitido.
   - Calcular la hora de fin según la duración correspondiente.
