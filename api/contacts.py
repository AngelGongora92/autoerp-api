from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import select

# Asumo que tus modelos y esquemas están en estos directorios.
# Ajusta las importaciones si tu estructura de proyecto es diferente.
from .database import get_db, Contact, Customer # Importamos Customer para verificar su existencia
from .schemas.user import ContactResponse, ContactCreate

# El prefijo y las etiquetas ayudan a organizar la API en la documentación de Swagger/OpenAPI
router = APIRouter()

@router.get("/{customer_id}", response_model=List[ContactResponse])
async def get_contacts_by_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene todos los contactos para un cliente específico por su ID.
    """
    # Paso 1: Verificar si el cliente existe en la base de datos.
    customer = db.scalar(select(Customer).where(Customer.id == customer_id))
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )
    
    # Paso 2: Si el cliente existe, buscar y devolver todos los contactos asociados.
    # Usamos select y scalars para obtener una lista de objetos Contact
    contacts = db.scalars(select(Contact).where(Contact.customer_id == customer_id)).all()
    
    # Si no se encuentran contactos, se devolverá una lista vacía [], lo cual es el comportamiento esperado.
    return contacts

@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un nuevo contacto en la base de datos.
    """
    # Paso 1: Verificar si el cliente existe en la base de datos.
    customer = db.scalar(select(Customer).where(Customer.id == contact_data.customer_id))
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {contact_data.customer_id} not found"
        )
    
    # Paso 2: Preparar los datos del nuevo contacto
    new_contact = Contact(
        customer_id=contact_data.customer_id,
        fname=contact_data.fname,
        lname=contact_data.lname,
        email=contact_data.email,
        phone=contact_data.phone
    )

    # Paso 3: Guardar el nuevo contacto en la base de datos
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    
    return new_contact


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact_by_id(
    contact_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene un solo contacto por su ID.
    """
    # Usamos db.get() para buscar el contacto por su ID de manera más directa
    contact = db.get(Contact, contact_id)

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    return contact

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact_data: ContactCreate,
    db: Session = Depends(get_db),
):
    """
    Actualiza un contacto existente.
    """
    contact = db.get(Contact, contact_id)

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Verificar si el nuevo customer_id existe
    if contact_data.customer_id != contact.customer_id:
        customer = db.scalar(select(Customer).where(Customer.id == contact_data.customer_id))
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {contact_data.customer_id} not found"
            )

    # Actualizar los campos del contacto
    contact.customer_id = contact_data.customer_id
    contact.fname = contact_data.fname
    contact.lname = contact_data.lname
    contact.email = contact_data.email
    contact.phone = contact_data.phone

    db.commit()
    db.refresh(contact)
    
    return contact

@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
):
    """
    Elimina un contacto existente.
    """
    contact = db.get(Contact, contact_id)

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    db.delete(contact)
    db.commit()
    
    return None