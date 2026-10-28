import asyncio
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from api.database import SessionLocal, Appointment, AppointmentItem, AppointmentReason, Employee, User
from api.schemas.appointments import AppointmentCreate, AppointmentItemCreate
from api.appointments import create_appointment, get_appointments

def run_tests():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.company_id.isnot(None)).first()
        assert user is not None, "Debe existir al menos un usuario en la BD"
        company_id = user.company_id

        advisor = db.query(Employee).filter(Employee.company_id == company_id).first()
        advisor_id = advisor.employee_id if advisor else None

        reasons = db.query(AppointmentReason).all()
        assert len(reasons) >= 2, "Deben existir al menos 2 razones de cita para pruebas"
        r1, r2 = reasons[0], reasons[1]

        tz = ZoneInfo("America/Mexico_City")
        test_date = (datetime.now(timezone.utc) + timedelta(days=3)).replace(hour=11, minute=0, second=0, microsecond=0)

        # -------------------------------------------------------------
        # Test 1: Crear cita usando el nuevo formato `items` con notas
        # -------------------------------------------------------------
        note1 = "Revisión urgente de balatas delanteras"
        note2 = "Cambio con aceite sintético de alta densidad"

        payload_items = AppointmentCreate(
            appointment_date=test_date,
            duration_minutes=45,
            assigned_to=advisor_id,
            status_id=1,
            notes="Nota general de la cita",
            items=[
                AppointmentItemCreate(reason_id=r1.reason_id, notes=note1),
                AppointmentItemCreate(reason_id=r2.reason_id, notes=note2),
            ],
            temp_fname="Juan",
            temp_lname="Pérez",
            temp_phone="9991234567"
        )

        appt_created = asyncio.run(create_appointment(
            appointment_data=payload_items,
            background_tasks=None,
            db=db,
            current_user=user
        ))

        assert appt_created.appointment_id is not None
        assert len(appt_created.items) == 2, f"Se esperaban 2 items, se obtuvieron {len(appt_created.items)}"
        
        # Validar persistencia de notas
        notes_saved = {it.reason_id: it.notes for it in appt_created.items}
        assert notes_saved[r1.reason_id] == note1, f"Nota de r1 incorrecta: {notes_saved.get(r1.reason_id)}"
        assert notes_saved[r2.reason_id] == note2, f"Nota de r2 incorrecta: {notes_saved.get(r2.reason_id)}"

        # Validar retrocompatibilidad con la propiedad reasons
        assert len(appt_created.reasons) == 2, "La propiedad reasons debe contener los 2 motivos"
        reason_ids_in_reasons = [r.reason_id for r in appt_created.reasons]
        assert r1.reason_id in reason_ids_in_reasons
        assert r2.reason_id in reason_ids_in_reasons

        print("✓ Test 1 superado: Creación con `items` y notas individuales exitosa.")

        # -------------------------------------------------------------
        # Test 2: Crear cita usando formato legacy `reason_ids`
        # -------------------------------------------------------------
        test_date_legacy = (datetime.now(timezone.utc) + timedelta(days=4)).replace(hour=12, minute=0, second=0, microsecond=0)
        payload_legacy = AppointmentCreate(
            appointment_date=test_date_legacy,
            duration_minutes=30,
            assigned_to=advisor_id,
            status_id=1,
            reason_ids=[r1.reason_id],
            temp_fname="María",
            temp_lname="González"
        )

        appt_legacy = asyncio.run(create_appointment(
            appointment_data=payload_legacy,
            background_tasks=None,
            db=db,
            current_user=user
        ))

        assert appt_legacy.appointment_id is not None
        assert len(appt_legacy.items) == 1, "Debe mapear reason_ids a 1 item automáticamente"
        assert appt_legacy.items[0].reason_id == r1.reason_id
        assert appt_legacy.items[0].notes is None, "En legacy notes debe ser None"
        assert len(appt_legacy.reasons) == 1

        print("✓ Test 2 superado: Retrocompatibilidad con `reason_ids` exitosa.")

        # -------------------------------------------------------------
        # Test 3: Lectura vía `get_appointments`
        # -------------------------------------------------------------
        all_appts = asyncio.run(get_appointments(
            assigned_to=None,
            db=db,
            current_user=user
        ))
        ids = [a.appointment_id for a in all_appts]
        assert appt_created.appointment_id in ids
        found = next(a for a in all_appts if a.appointment_id == appt_created.appointment_id)
        assert len(found.items) == 2
        assert found.items[0].reason is not None, "El motivo anidado reason debe estar cargado"

        print("✓ Test 3 superado: Lectura con joinedload de items y reason correcta.")

        # Limpieza
        db.delete(appt_created)
        db.delete(appt_legacy)
        db.commit()

        print("Todos los tests de AUT-231 (Backend) pasaron exitosamente!")

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
