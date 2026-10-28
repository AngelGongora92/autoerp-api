import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from api.database import SessionLocal, Appointment, AppointmentItem, AppointmentReason, Employee, User, Customer, Vehicle, Order, OrderItem
from api.appointments import create_order_from_appointment

def test_aut_40_conversion_and_traceability():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.company_id.isnot(None)).first()
        assert user is not None, "Debe existir un usuario en la BD"
        company_id = user.company_id

        # Buscar o verificar cliente, vehículo y asesor de la misma empresa
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
        # Test 1: Conversión exitosa de cita con items y notas a Orden
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
            notes="Cita de prueba para AUT-40"
        )
        db.add(appt)
        db.flush()

        # Agregar item con notas
        item_note = "Revisar ruido en frenos delanteros y vibración"
        appt_item = AppointmentItem(
            appointment_id=appt.appointment_id,
            reason_id=r1.reason_id,
            notes=item_note
        )
        db.add(appt_item)
        db.commit()

        # Ejecutar conversión
        created_order = asyncio.run(create_order_from_appointment(
            appointment_id=appt.appointment_id,
            db=db,
            current_user=user
        ))

        assert created_order is not None
        assert created_order.order_id is not None
        assert created_order.c_order_id is not None
        assert created_order.appointment_id == appt.appointment_id
        assert created_order.customer_id == customer.customer_id
        assert created_order.vehicle_id == vehicle.vehicle_id

        # Validar trazabilidad bidireccional y cambio de estado a Atendida
        db.refresh(appt)
        assert appt.status_id == 4, f"El estado de la cita debe ser 4 (atendida), pero es {appt.status_id}"
        assert appt.order_id == created_order.order_id, "La cita debe tener el order_id de la orden generada"

        # Validar order_items creados
        order_items = db.query(OrderItem).filter(OrderItem.order_id == created_order.order_id).all()
        assert len(order_items) == 1, f"Se esperaba 1 order_item, se obtuvieron {len(order_items)}"
        assert order_items[0].reason_id == r1.reason_id
        assert order_items[0].notes == item_note
        assert float(order_items[0].quantity) == 1.0

        print("✓ Test 1 superado: Conversión exitosa con items, notas y trazabilidad.")

        # -------------------------------------------------------------
        # Test 2: Validación de no doble conversión
        # -------------------------------------------------------------
        try:
            asyncio.run(create_order_from_appointment(
                appointment_id=appt.appointment_id,
                db=db,
                current_user=user
            ))
            assert False, "Debió lanzar HTTPException por cita ya convertida"
        except HTTPException as e:
            assert e.status_code == 400
            assert "ya fue convertida" in e.detail
            print("✓ Test 2 superado: Rechazo de doble conversión verificado.")

        # -------------------------------------------------------------
        # Test 3: Validación de cita cancelada (status_id=3)
        # -------------------------------------------------------------
        appt_cancelled = Appointment(
            company_id=company_id,
            customer_id=customer.customer_id,
            vehicle_id=vehicle.vehicle_id,
            appointment_date=test_date,
            status_id=3,  # Cancelada
            notes="Cita cancelada de prueba"
        )
        db.add(appt_cancelled)
        db.commit()

        try:
            asyncio.run(create_order_from_appointment(
                appointment_id=appt_cancelled.appointment_id,
                db=db,
                current_user=user
            ))
            assert False, "Debió lanzar HTTPException por cita cancelada"
        except HTTPException as e:
            assert e.status_code == 400
            assert "cancelada" in e.detail
            print("✓ Test 3 superado: Rechazo de cita cancelada verificado.")

        # -------------------------------------------------------------
        # Test 4: Validación de cita sin cliente o sin vehículo
        # -------------------------------------------------------------
        appt_no_cust = Appointment(
            company_id=company_id,
            customer_id=None,
            vehicle_id=vehicle.vehicle_id,
            temp_fname="Temporal",
            appointment_date=test_date,
            status_id=1
        )
        db.add(appt_no_cust)
        db.commit()

        try:
            asyncio.run(create_order_from_appointment(
                appointment_id=appt_no_cust.appointment_id,
                db=db,
                current_user=user
            ))
            assert False, "Debió lanzar HTTPException por falta de cliente"
        except HTTPException as e:
            assert e.status_code == 400
            assert "cliente registrado" in e.detail
            print("✓ Test 4 superado: Rechazo de cita sin cliente formalizado verificado.")

        # -------------------------------------------------------------
        # Test 5: Validación de cita inexistente (404)
        # -------------------------------------------------------------
        try:
            asyncio.run(create_order_from_appointment(
                appointment_id=99999999,
                db=db,
                current_user=user
            ))
            assert False, "Debió lanzar HTTPException 404"
        except HTTPException as e:
            assert e.status_code == 404
            print("✓ Test 5 superado: 404 Not Found verificado.")

        print("\n🎉 TODOS LOS TESTS DE AUT-40 PASARON EXITOSAMENTE.")

    finally:
        db.close()

if __name__ == "__main__":
    test_aut_40_conversion_and_traceability()
