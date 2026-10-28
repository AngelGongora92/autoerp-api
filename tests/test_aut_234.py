import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from api.database import SessionLocal, Appointment, Employee, User
from api.schemas.appointments import AppointmentConfirmRequest
from api.appointments import confirm_appointment

def run_tests():
    db = SessionLocal()
    try:
        # Buscar usuario y asesor para pruebas
        user = db.query(User).filter(User.company_id.isnot(None)).first()
        assert user is not None, "Debe existir al menos un usuario en la BD"
        company_id = user.company_id

        advisor = db.query(Employee).filter(Employee.company_id == company_id).first()
        advisor_id = advisor.employee_id if advisor else None

        test_date = datetime.now(timezone.utc) + timedelta(days=2)

        # 1. Crear una cita de prueba sin confirmar (status_id = 1)
        appt = Appointment(
            assigned_to=advisor_id,
            appointment_date=test_date,
            duration_minutes=30,
            status_id=1,
            company_id=company_id,
            notes="Cita de prueba AUT-234"
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)
        appt_id = appt.appointment_id
        print(f"Cita creada con ID {appt_id}, status_id = {appt.status_id}")

        # 2. Confirmar la cita manualmente sin notificaciones
        payload = AppointmentConfirmRequest(send_whatsapp=False, send_email=False)
        updated = asyncio.run(confirm_appointment(
            appointment_id=appt_id,
            payload=payload,
            background_tasks=None,
            db=db,
            current_user=user
        ))

        assert updated.status_id == 2, f"Esperado status_id = 2, obtenido {updated.status_id}"
        print("Confirmación exitosa: status_id actualizado a 2.")

        # 3. Intentar confirmar de nuevo (debe fallar con 400)
        try:
            asyncio.run(confirm_appointment(
                appointment_id=appt_id,
                payload=payload,
                background_tasks=None,
                db=db,
                current_user=user
            ))
            assert False, "Debería haber lanzado HTTPException 400 por estar ya confirmada"
        except HTTPException as e:
            assert e.status_code == 400
            print("Validación correcta: error 400 cuando ya está confirmada.")

        # 4. Modificar a cancelada (status_id = 3) e intentar confirmar (debe fallar con 400)
        appt.status_id = 3
        db.commit()

        try:
            asyncio.run(confirm_appointment(
                appointment_id=appt_id,
                payload=payload,
                background_tasks=None,
                db=db,
                current_user=user
            ))
            assert False, "Debería haber lanzado HTTPException 400 por estar cancelada"
        except HTTPException as e:
            assert e.status_code == 400
            print("Validación correcta: error 400 cuando la cita está cancelada.")

        # 5. Intentar confirmar cita inexistente (debe fallar con 404)
        try:
            asyncio.run(confirm_appointment(
                appointment_id=9999999,
                payload=payload,
                background_tasks=None,
                db=db,
                current_user=user
            ))
            assert False, "Debería haber lanzado HTTPException 404 por no existir"
        except HTTPException as e:
            assert e.status_code == 404
            print("Validación correcta: error 404 cuando la cita no existe.")

        # Limpiar registro de prueba
        db.delete(appt)
        db.commit()
        print("AUT-234 Backend tests passed successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
