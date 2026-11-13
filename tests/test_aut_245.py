import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException

from api.database import SessionLocal, Appointment, AppointmentReason, Company, CompanySettings, Employee, User
from api.appointments import (
    get_public_appointment_config,
    get_public_appointment_availability,
    create_public_appointment,
)
from api.settings import get_appointment_config, update_appointment_config
from api.schemas.settings import AppointmentConfigSchema
from api.schemas.appointments import PublicAppointmentCreate, PublicVehicleTempData


def test_aut_245_public_portal():
    db = SessionLocal()
    created_appt_id = None
    created_advisor_id = None
    settings = db.query(CompanySettings).filter(CompanySettings.id == 1).first()
    original_portal_enabled = bool(getattr(settings, "public_portal_enabled", False)) if settings else False

    try:
        user = db.query(User).filter(User.company_id.isnot(None)).first()
        assert user is not None, "Debe existir al menos un usuario en la BD"
        company_id = user.company_id

        company = db.query(Company).filter(Company.company_id == company_id).first()
        assert company is not None, "Debe existir la empresa del usuario"

        advisor = db.query(Employee).filter(
            Employee.company_id == company_id,
            Employee.is_active == True,
            Employee.position_id == 1,
        ).first()
        if not advisor:
            advisor = Employee(
                fname="Asesor",
                lname1="Test245",
                email="asesor_test245@example.com",
                position_id=1,
                company_id=company_id,
                is_active=True,
            )
            db.add(advisor)
            db.commit()
            db.refresh(advisor)
            created_advisor_id = advisor.employee_id

        reason = db.query(AppointmentReason).first()
        assert reason is not None, "Debe existir al menos un motivo de cita"

        # 1. Asegurar portal deshabilitado -> debe retornar 403 en todos los endpoints públicos
        update_appointment_config(
            AppointmentConfigSchema(public_portal_enabled=False),
            db=db,
            current_user=user,
        )
        cfg_resp = get_appointment_config(db=db, current_user=user)
        assert cfg_resp.public_portal_enabled is False
        assert cfg_resp.company_id == company_id

        # Buscar un día futuro permitido (ej. próximo lunes-viernes)
        local_tz = ZoneInfo("America/Mexico_City")
        future_dt = datetime.now(local_tz) + timedelta(days=2)
        while future_dt.weekday() not in (cfg_resp.allowed_days or [0, 1, 2, 3, 4, 5]):
            future_dt += timedelta(days=1)
        future_dt = future_dt.replace(hour=10, minute=0, second=0, microsecond=0)

        for fn_call in [
            lambda: asyncio.run(get_public_appointment_config(company_id=company_id, db=db)),
            lambda: asyncio.run(get_public_appointment_availability(company_id=company_id, date=future_dt.date(), db=db)),
            lambda: asyncio.run(create_public_appointment(
                payload=PublicAppointmentCreate(
                    company_id=company_id,
                    appointment_date=future_dt,
                    reason_ids=[reason.reason_id],
                    temp_fname="Test",
                    temp_lname="Public",
                    temp_phone="5512345678",
                    temp_email="test_public@example.com",
                    temp_vehicle_data=PublicVehicleTempData(make="Nissan", model="Versa", year=2022),
                ),
                db=db,
            )),
        ]:
            try:
                fn_call()
                assert False, "Debió lanzar HTTPException 403 cuando el portal está deshabilitado"
            except HTTPException as exc:
                assert exc.status_code == 403

        # 2. Habilitar portal público desde settings
        updated_cfg = update_appointment_config(
            AppointmentConfigSchema(public_portal_enabled=True),
            db=db,
            current_user=user,
        )
        assert updated_cfg.public_portal_enabled is True

        # 3. Verificar GET /appointments/public/config
        pub_cfg = asyncio.run(get_public_appointment_config(company_id=company_id, db=db))
        assert pub_cfg.public_portal_enabled is True
        assert pub_cfg.company_id == company_id
        assert len(pub_cfg.reasons) >= 1

        # 4. Verificar GET /appointments/public/availability
        pub_avail = asyncio.run(get_public_appointment_availability(
            company_id=company_id,
            date=future_dt.date(),
            db=db,
        ))
        assert pub_avail.date == future_dt.date().isoformat()
        assert len(pub_avail.available_slots) >= 1

        # 5. Verificar rechazo de fecha pasada
        past_dt = datetime.now(local_tz) - timedelta(days=2)
        try:
            asyncio.run(create_public_appointment(
                payload=PublicAppointmentCreate(
                    company_id=company_id,
                    appointment_date=past_dt,
                    reason_ids=[reason.reason_id],
                    temp_fname="Test",
                    temp_lname="Past",
                    temp_phone="5512345678",
                    temp_email="test_past@example.com",
                    temp_vehicle_data=PublicVehicleTempData(make="Toyota", model="Corolla", year=2020),
                ),
                db=db,
            ))
            assert False, "Debió rechazar cita en fecha pasada"
        except HTTPException as exc:
            assert exc.status_code == 400

        # 6. Crear cita pública con datos temporales en primer slot disponible
        slot_h, slot_m = map(int, pub_avail.available_slots[0].split(":"))
        valid_dt = future_dt.replace(hour=slot_h, minute=slot_m, second=0, microsecond=0, tzinfo=None)

        created_resp = asyncio.run(create_public_appointment(
            payload=PublicAppointmentCreate(
                company_id=company_id,
                appointment_date=valid_dt,
                reason_ids=[reason.reason_id],
                temp_fname="Carlos",
                temp_lname="Mendoza",
                temp_cname="Transportes Mendoza",
                temp_phone="5598765432",
                temp_email="carlos.mendoza@example.com",
                temp_vehicle_data=PublicVehicleTempData(
                    make="Nissan",
                    model="Versa",
                    year=2021,
                    plate="XYZ-9876",
                    color="Gris",
                    notes="Revisión de frenos",
                ),
                notes="Cita de prueba AUT-245",
            ),
            db=db,
        ))
        created_appt_id = created_resp.appointment_id
        assert created_appt_id is not None
        assert created_resp.status == "Sin confirmar"

        saved = db.get(Appointment, created_appt_id)
        assert saved is not None
        assert saved.customer_id is None
        assert saved.vehicle_id is None
        assert saved.contact_id is None
        assert saved.temp_fname == "Carlos"
        assert saved.temp_lname == "Mendoza"
        assert saved.temp_cname == "Transportes Mendoza"
        assert saved.temp_vehicle_data["make"] == "Nissan"
        assert saved.status_id == 1

        print("AUT-245 BE tests PASSED successfully!")
    finally:
        if created_appt_id:
            appt = db.get(Appointment, created_appt_id)
            if appt:
                db.delete(appt)
                db.commit()
        if created_advisor_id:
            adv = db.get(Employee, created_advisor_id)
            if adv:
                db.delete(adv)
                db.commit()
        if settings:
            settings.public_portal_enabled = original_portal_enabled
            db.commit()
        db.close()


if __name__ == "__main__":
    test_aut_245_public_portal()
