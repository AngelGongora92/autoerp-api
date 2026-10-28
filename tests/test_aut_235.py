import asyncio
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from api.database import SessionLocal, Appointment, Employee, User
from api.appointments import get_appointments, parse_date_param

def run_tests():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.company_id.isnot(None)).first()
        assert user is not None, "Debe existir al menos un usuario en la BD"
        company_id = user.company_id

        advisor = db.query(Employee).filter(Employee.company_id == company_id).first()
        advisor_id = advisor.employee_id if advisor else None

        tz = ZoneInfo("America/Mexico_City")
        now_local = datetime.now(tz)
        today_str = now_local.strftime("%Y-%m-%d")
        tomorrow_str = (now_local + timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_str = (now_local - timedelta(days=1)).strftime("%Y-%m-%d")

        # Test parse_date_param unit checks
        start_p = parse_date_param("2026-10-27", is_end=False)
        assert start_p is not None
        assert start_p.hour == 0 and start_p.minute == 0 and start_p.second == 0

        end_p = parse_date_param("2026-10-27", is_end=True)
        assert end_p is not None
        assert end_p.hour == 23 and end_p.minute == 59 and end_p.second == 59

        # Create two test appointments today: one at 10:00 AM, one at 2:00 PM
        today_10am = now_local.replace(hour=10, minute=0, second=0, microsecond=0)
        today_2pm = now_local.replace(hour=14, minute=0, second=0, microsecond=0)
        yesterday_10am = (now_local - timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)

        appt1 = Appointment(
            assigned_to=advisor_id,
            appointment_date=today_2pm,
            duration_minutes=30,
            status_id=1,
            company_id=company_id,
            notes="AUT-235 test appt today 2pm"
        )
        appt2 = Appointment(
            assigned_to=advisor_id,
            appointment_date=today_10am,
            duration_minutes=30,
            status_id=1,
            company_id=company_id,
            notes="AUT-235 test appt today 10am"
        )
        appt3 = Appointment(
            assigned_to=advisor_id,
            appointment_date=yesterday_10am,
            duration_minutes=30,
            status_id=1,
            company_id=company_id,
            notes="AUT-235 test appt yesterday 10am"
        )

        db.add_all([appt1, appt2, appt3])
        db.commit()
        db.refresh(appt1)
        db.refresh(appt2)
        db.refresh(appt3)

        # 1. Query with start_date and end_date matching today
        res_today = asyncio.run(get_appointments(
            assigned_to=None,
            start_date=today_str,
            end_date=today_str,
            db=db,
            current_user=user
        ))

        res_ids = [a.appointment_id for a in res_today]
        assert appt1.appointment_id in res_ids, "appt1 should be in res_today"
        assert appt2.appointment_id in res_ids, "appt2 should be in res_today"
        assert appt3.appointment_id not in res_ids, "appt3 (yesterday) should NOT be in res_today"

        # Verify chronological ordering
        today_dates = [a.appointment_date for a in res_today]
        for i in range(len(today_dates) - 1):
            assert today_dates[i] <= today_dates[i+1], "Appointments must be ordered chronologically ascending"

        # 2. Query with range covering yesterday to today
        res_range = asyncio.run(get_appointments(
            assigned_to=None,
            start_date=yesterday_str,
            end_date=today_str,
            db=db,
            current_user=user
        ))
        res_range_ids = [a.appointment_id for a in res_range]
        assert appt3.appointment_id in res_range_ids, "appt3 should be in res_range"
        assert appt1.appointment_id in res_range_ids, "appt1 should be in res_range"

        print("All AUT-235 tests passed successfully!")

        # Cleanup
        db.delete(appt1)
        db.delete(appt2)
        db.delete(appt3)
        db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
