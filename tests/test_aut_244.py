import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from api.database import SessionLocal, Appointment, Employee, User
from api.appointments import reschedule_appointment, RescheduleRequest

def test_aut_244_reschedule_validations():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.company_id.isnot(None)).first()
        assert user is not None, "Debe existir al menos un usuario en la BD"
        company_id = user.company_id

        advisor = db.query(Employee).filter(Employee.company_id == company_id).first()
        advisor_id = advisor.employee_id if advisor else None

        now_utc = datetime.now(timezone.utc)
        future_date = now_utc + timedelta(days=2)
        past_date = now_utc - timedelta(days=2)

        # 1. Crear cita de prueba activa
        appt_active = Appointment(
            assigned_to=advisor_id,
            appointment_date=future_date,
            duration_minutes=30,
            status_id=1,
            company_id=company_id,
            notes="AUT-244 test active appt"
        )
        # 2. Crear cita de prueba cancelada
        appt_cancelled = Appointment(
            assigned_to=advisor_id,
            appointment_date=future_date,
            duration_minutes=30,
            status_id=3,
            company_id=company_id,
            notes="AUT-244 test cancelled appt"
        )
        # 3. Crear cita de prueba atendida
        appt_attended = Appointment(
            assigned_to=advisor_id,
            appointment_date=future_date,
            duration_minutes=30,
            status_id=4,
            company_id=company_id,
            notes="AUT-244 test attended appt"
        )

        db.add_all([appt_active, appt_cancelled, appt_attended])
        db.commit()
        db.refresh(appt_active)
        db.refresh(appt_cancelled)
        db.refresh(appt_attended)

        # Caso A: Intento de reprogramar a una fecha pasada -> Debe fallar con 400
        try:
            asyncio.run(reschedule_appointment(
                appointment_id=appt_active.appointment_id,
                payload=RescheduleRequest(
                    appointment_date=past_date,
                    send_whatsapp=False,
                    send_email=False
                ),
                db=db,
                current_user=user
            ))
            assert False, "Debió lanzar HTTPException por fecha pasada"
        except HTTPException as e:
            assert e.status_code == 400
            assert "pasado" in str(e.detail).lower()

        # Caso B: Intento de reprogramar una cita cancelada -> Debe fallar con 400
        try:
            asyncio.run(reschedule_appointment(
                appointment_id=appt_cancelled.appointment_id,
                payload=RescheduleRequest(
                    appointment_date=future_date + timedelta(hours=1),
                    send_whatsapp=False,
                    send_email=False
                ),
                db=db,
                current_user=user
            ))
            assert False, "Debió lanzar HTTPException por cita cancelada"
        except HTTPException as e:
            assert e.status_code == 400
            assert "cancelada" in str(e.detail).lower()

        # Caso C: Intento de reprogramar una cita atendida -> Debe fallar con 400
        try:
            asyncio.run(reschedule_appointment(
                appointment_id=appt_attended.appointment_id,
                payload=RescheduleRequest(
                    appointment_date=future_date + timedelta(hours=1),
                    send_whatsapp=False,
                    send_email=False
                ),
                db=db,
                current_user=user
            ))
            assert False, "Debió lanzar HTTPException por cita atendida"
        except HTTPException as e:
            assert e.status_code == 400
            assert "atendida" in str(e.detail).lower()

        # Caso D: Reprogramación exitosa a fecha futura válida
        new_valid_date = future_date + timedelta(hours=3)
        res = asyncio.run(reschedule_appointment(
            appointment_id=appt_active.appointment_id,
            payload=RescheduleRequest(
                appointment_date=new_valid_date,
                send_whatsapp=False,
                send_email=False
            ),
            db=db,
            current_user=user
        ))
        assert res.appointment_id == appt_active.appointment_id
        assert res.rescheduled_count >= 1
        assert res.status_id == 1

        print("AUT-244 BE tests PASSED successfully!")
    finally:
        # Cleanup
        if 'appt_active' in locals() and appt_active.appointment_id:
            db.delete(appt_active)
        if 'appt_cancelled' in locals() and appt_cancelled.appointment_id:
            db.delete(appt_cancelled)
        if 'appt_attended' in locals() and appt_attended.appointment_id:
            db.delete(appt_attended)
        db.commit()
        db.close()

if __name__ == "__main__":
    test_aut_244_reschedule_validations()
