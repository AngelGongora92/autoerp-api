from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from api.database import SessionLocal, Appointment, Employee, AppointmentStatus
from api.appointments import check_advisor_availability, get_least_busy_available_advisor

def run_tests():
    db = SessionLocal()
    try:
        # 1. Test check_advisor_availability
        local_tz = ZoneInfo("America/Mexico_City")
        test_date = datetime.now(timezone.utc) + timedelta(days=5)
        # Round to hour
        test_date = test_date.replace(minute=0, second=0, microsecond=0)

        # Buscar o crear un asesor de prueba
        advisor = db.query(Employee).filter(Employee.position_id == 1, Employee.is_active == True).first()
        if not advisor:
            advisor = db.query(Employee).first()
        assert advisor is not None, "Debe existir al menos un empleado"

        advisor_id = advisor.employee_id

        # Verificar que inicialmente esté libre
        is_free = check_advisor_availability(advisor_id, test_date, 30, db)
        print(f"Estado inicial del asesor {advisor_id}: libre={is_free}")

        # Crear una cita temporal
        appt = Appointment(
            assigned_to=advisor_id,
            appointment_date=test_date,
            duration_minutes=30,
            status_id=1,
            company_id=advisor.company_id,
            notes="Cita de prueba AUT-233"
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)

        # Ahora el horario test_date debe estar ocupado
        is_free_during = check_advisor_availability(advisor_id, test_date, 30, db)
        assert not is_free_during, "El horario debería estar ocupado"

        # Un horario 15 min después (solapado) debe estar ocupado
        overlap_date = test_date + timedelta(minutes=15)
        is_free_overlap = check_advisor_availability(advisor_id, overlap_date, 30, db)
        assert not is_free_overlap, "El horario empalmado a +15min debería estar ocupado"

        # Un horario 30 min después (inmediatamente contiguo) debe estar libre
        adjacent_date = test_date + timedelta(minutes=30)
        is_free_adjacent = check_advisor_availability(advisor_id, adjacent_date, 30, db)
        assert is_free_adjacent, "El horario contiguo (+30min) debería estar libre"

        # Excluyendo la cita actual (simulando reagendación), debe estar libre
        is_free_exclude = check_advisor_availability(advisor_id, test_date, 30, db, exclude_appointment_id=appt.appointment_id)
        assert is_free_exclude, "Excluyendo la propia cita, el horario debería considerarse libre"

        # Si la cita se cancela (status_id = 3), debe liberarse
        appt.status_id = 3
        db.commit()
        is_free_after_cancel = check_advisor_availability(advisor_id, test_date, 30, db)
        assert is_free_after_cancel, "Tras cancelar la cita, el horario debería quedar libre"

        # 2. Test get_least_busy_available_advisor
        least_busy = get_least_busy_available_advisor(test_date, 30, advisor.company_id, db)
        assert least_busy is not None, "Debería encontrar un asesor disponible"
        print(f"Least busy advisor seleccionado: {least_busy}")

        # Limpiar registro de prueba
        db.delete(appt)
        db.commit()

        print("AUT-233 Backend unit tests passed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
