import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy import select
from api.database import SessionLocal, Appointment, AppointmentItem, AppointmentReason, Employee, User, Customer, Vehicle, Order, OrderItem
from api.schemas.user import CreateOrder
from api.orders import create_order
from api.appointments import get_appointment_by_id

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

        advisor = db.query(Employee).filter(Employee.company_id == company_id).first()
        advisor_id = advisor.employee_id if advisor else None

        reasons = db.query(AppointmentReason).all()
        assert len(reasons) >= 1, "Debe existir al menos un motivo"
        r1 = reasons[0]

        # -------------------------------------------------------------
        # Test 1: Crear cita con items y consultar GET /appointments/{id}
        # -------------------------------------------------------------
        test_date = datetime.now(timezone.utc) + timedelta(days=2)
        appt = Appointment(
            company_id=company_id,
            customer_id=customer.customer_id,
            vehicle_id=vehicle.vehicle_id,
            assigned_to=advisor_id,
            appointment_date=test_date,
            status_id=1,  # Programada
            channel="web",
            notes="Cita de prueba para AUT-239"
        )
        db.add(appt)
        db.flush()

        item1 = AppointmentItem(
            appointment_id=appt.appointment_id,
            reason_id=r1.reason_id,
            notes="Nota específica para motivo en AUT-239"
        )
        db.add(item1)
        db.commit()

        # Consultar GET /appointments/{id}
        fetched_appt = await get_appointment_by_id(appt.appointment_id, db, user)
        assert fetched_appt is not None
        assert fetched_appt.appointment_id == appt.appointment_id
        assert len(fetched_appt.items) >= 1
        assert fetched_appt.items[0].notes == "Nota específica para motivo en AUT-239"
        print("✓ Test 1 superado: GET /appointments/{id} retorna cita e items con notas correctamente.")

        # -------------------------------------------------------------
        # Test 2: Crear Orden vía POST /orders/ vinculando la cita
        # -------------------------------------------------------------
        order_folio = f"TEST-239-{appt.appointment_id}"
        order_data = CreateOrder(
            c_order_id=order_folio,
            order_date=datetime.now(timezone.utc),
            customer_id=customer.customer_id,
            vehicle_id=vehicle.vehicle_id,
            advisor_id=advisor_id,
            appointment_id=appt.appointment_id,
            c_mileage=50000,
            fuel_level=4,
            service_bay="Bahía 1"
        )

        created_order = await create_order(order_data, db, user)
        assert created_order is not None
        assert created_order.appointment_id == appt.appointment_id

        # Verificar que la cita pasó a estado 'atendida' (4) y se vinculó con order_id
        db.refresh(appt)
        assert appt.order_id == created_order.order_id
        assert appt.status_id == 4

        # Verificar que los motivos se copiaron a order_items
        order_items = db.scalars(select(OrderItem).where(OrderItem.order_id == created_order.order_id)).all()
        assert len(order_items) >= 1
        assert order_items[0].reason_id == r1.reason_id
        assert order_items[0].notes == "Nota específica para motivo en AUT-239"
        print("✓ Test 2 superado: POST /orders/ vincula cita, traslada items a order_items y marca cita como 'atendida'.")

        # Limpieza de registros de prueba
        db.query(OrderItem).filter(OrderItem.order_id == created_order.order_id).delete()
        db.query(Order).filter(Order.order_id == created_order.order_id).delete()
        db.query(AppointmentItem).filter(AppointmentItem.appointment_id == appt.appointment_id).delete()
        db.query(Appointment).filter(Appointment.appointment_id == appt.appointment_id).delete()
        db.commit()
        print("✓ Limpieza de datos de prueba exitosa.")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_tests())
    print("\n🎉 TODOS LOS TESTS DE AUT-239 PASARON EXITOSAMENTE.")
