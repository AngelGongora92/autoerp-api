import asyncio
from api.database import SessionLocal, Customer, Contact, User
from api.customers import search_customers

def run_tests():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.company_id.isnot(None)).first()
        assert user is not None, "Debe existir al menos un usuario para las pruebas"
        company_id = user.company_id

        # 1. Crear un cliente con teléfono y un contacto secundario
        test_customer = Customer(
            company_id=company_id,
            fname="Roberto",
            lname="Hernández",
            email="roberto.test.aut228@example.com",
            phone="+52 999 123 4567",
            is_company=False,
            is_active=True
        )
        db.add(test_customer)
        db.flush()

        test_contact = Contact(
            customer_id=test_customer.customer_id,
            fname="Mariana",
            lname="Hernández",
            email="mariana.test.aut228@example.com",
            phone="999 876 5432"
        )
        db.add(test_contact)
        db.commit()
        db.refresh(test_customer)
        cust_id = test_customer.customer_id

        # 2. Prueba de búsqueda por número de teléfono del cliente (con formato exacto)
        res_exact_phone = asyncio.run(search_customers(
            q="+52 999 123",
            db=db,
            current_user=user
        ))
        assert any(c.customer_id == cust_id for c in res_exact_phone), "Debe encontrar al cliente por formato de teléfono"
        print("✓ Búsqueda por formato exacto de teléfono superada")

        # 3. Prueba de búsqueda por dígitos sin formato ni código de país (solo números "1234567")
        res_digits_phone = asyncio.run(search_customers(
            q="1234567",
            db=db,
            current_user=user
        ))
        assert any(c.customer_id == cust_id for c in res_digits_phone), "Debe encontrar al cliente por dígitos limpios del teléfono"
        print("✓ Búsqueda por dígitos limpios superada")

        # 4. Prueba de búsqueda por teléfono de contacto asociado ("8765432")
        res_contact_phone = asyncio.run(search_customers(
            q="8765432",
            db=db,
            current_user=user
        ))
        assert any(c.customer_id == cust_id for c in res_contact_phone), "Debe encontrar al cliente por teléfono de contacto asociado"
        print("✓ Búsqueda por teléfono de contacto superada")

        # 5. Prueba de búsqueda por nombre ("Roberto")
        res_name = asyncio.run(search_customers(
            q="Roberto",
            db=db,
            current_user=user
        ))
        assert any(c.customer_id == cust_id for c in res_name), "Debe encontrar al cliente por nombre de pila"
        print("✓ Búsqueda por nombre superada")

        # 6. Prueba con parámetro backwards-compatible `full_name`
        res_compat = asyncio.run(search_customers(
            full_name="1234567",
            db=db,
            current_user=user
        ))
        assert any(c.customer_id == cust_id for c in res_compat), "Debe soportar parámetro backwards-compatible full_name"
        print("✓ Búsqueda compatible con full_name superada")

        # 7. Término inexistente o menor a 2 caracteres
        res_empty = asyncio.run(search_customers(
            q="x",
            db=db,
            current_user=user
        ))
        assert len(res_empty) == 0, "Debe retornar lista vacía si la longitud es menor a 2 caracteres"
        print("✓ Validación de longitud mínima superada")

        # Limpieza
        db.delete(test_customer)
        db.commit()
        print("AUT-228 Backend unit tests passed successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
