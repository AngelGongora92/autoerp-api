import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy import select
from api.database import SessionLocal, Appointment, Customer, Vehicle, Order, User
from api.schemas.appointments import AppointmentFormalize
from api.schemas.user import CreateOrder
from api.customers import search_customers
from api.appointments import formalize_appointment, get_appointment_by_id
from api.orders import create_order

async def run_tests():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.company_id.isnot(None)).first()
        assert user is not None, "Debe existir un usuario en la BD"
        company_id = user.company_id

        customer = db.query(Customer).filter(Customer.company_id == company_id).first()
        assert customer is not None, "Debe existir al menos un cliente"

        vehicle = db.query(Vehicle).filter(Vehicle.customer_id == customer.customer_id).first()
        if not vehicle:
            vehicle = db.query(Vehicle).first()
        assert vehicle is not None, "Debe existir al menos un vehículo"

        # -------------------------------------------------------------
        # Test 1: Búsqueda de clientes por name y phone
        # -------------------------------------------------------------
        if customer.fname:
            results_name = await search_customers(name=customer.fname, db=db, current_user=user)
            assert any(c.customer_id == customer.customer_id for c in results_name)
            print(f"✓ Test 1A superado: Búsqueda por nombre ({customer.fname}) encontró al cliente.")

        if customer.phone:
            results_phone = await search_customers(phone=customer.phone, db=db, current_user=user)
            assert any(c.customer_id == customer.customer_id for c in results_phone)
            print(f"✓ Test 1B superado: Búsqueda por teléfono ({customer.phone}) encontró al cliente.")

        # -------------------------------------------------------------
        # Test 2: Formalizar cita con datos temporales
        # -------------------------------------------------------------
        test_date = datetime.now(timezone.utc) + timedelta(days=3)
        temp_appt = Appointment(
            company_id=company_id,
            customer_id=None,
            vehicle_id=None,
            temp_fname="Cliente",
            temp_lname="Temporal 242",
            temp_email="temp242@test.com",
            temp_phone="5599887766",
            temp_vehicle_data={"plate": "TMP-242", "make": "Nissan", "model": "Versa", "year": 2022},
            appointment_date=test_date,
            status_id=1,
            channel="web",
            notes="Cita de prueba AUT-242"
        )
        db.add(temp_appt)
        db.commit()
        db.refresh(temp_appt)

        # Formalizar
        formalize_payload = AppointmentFormalize(customer_id=customer.customer_id, vehicle_id=vehicle.vehicle_id)
        formalized_appt = await formalize_appointment(
            appointment_id=temp_appt.appointment_id,
            payload=formalize_payload,
            db=db,
            current_user=user
        )
        assert formalized_appt.customer_id == customer.customer_id
        assert formalized_appt.vehicle_id == vehicle.vehicle_id
        print("✓ Test 2 superado: PATCH /appointments/{id}/formalize vinculó customer_id y vehicle_id.")

        # -------------------------------------------------------------
        # Test 3: Crear orden desde cita temporal formalizada
        # -------------------------------------------------------------
        order_payload = CreateOrder(
            c_order_id=f"ORD-AUT242-{int(datetime.now().timestamp())}",
            order_date=datetime.now(timezone.utc),
            customer_id=customer.customer_id,
            vehicle_id=vehicle.vehicle_id,
            appointment_id=temp_appt.appointment_id,
            priority_id=1
        )
        created_order = await create_order(
            order_data=order_payload,
            db=db,
            current_user=user
        )
        assert created_order.order_id is not None
        assert created_order.customer_id == customer.customer_id
        print("✓ Test 3 superado: Creación de orden vinculada a cita.")

        # Limpieza
        db.query(Order).filter(Order.order_id == created_order.order_id).delete()
        db.query(Appointment).filter(Appointment.appointment_id == temp_appt.appointment_id).delete()
        db.commit()
        print("✓ Limpieza de datos de prueba exitosa.")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_tests())
    print("\n🎉 TODOS LOS TESTS DE AUT-242 (BACKEND) PASARON EXITOSAMENTE.")
