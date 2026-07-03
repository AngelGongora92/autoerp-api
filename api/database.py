import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Table, ForeignKey, Date, TIMESTAMP, Enum, Float, UniqueConstraint, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from api.schemas.user import BodyworkChecklistView # Importar el Enum
from .hashing import verify_password
from datetime import datetime


# Define la URL de la base de datos.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://root:123456@localhost/test")

# El engine se encarga de la comunicación con la base de datos
engine = create_engine(DATABASE_URL)

# `sessionmaker` crea una "fábrica" de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# `declarative_base` es una clase base de la que heredarán los modelos de la base de datos
Base = declarative_base()

# Define una dependencia para obtener una sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Modelos de la base de datos ---

# Tabla de asociación para la relación muchos a muchos entre User y Permission
user_permissions = Table('user_permissions', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.permission_id'), primary_key=True)
)

# Modelo de Compañía/Taller (tabla 'companies')
class Company(Base):
    __tablename__ = 'companies'
    company_id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True)


# Modelo de Usuario (tabla 'users')
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password = Column(String(200)) # Aquí se almacena la contraseña hasheada
    is_admin = Column(Boolean, default=False)
    is_employee = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='SET NULL'), nullable=True)
    supabase_uid = Column(String(64), unique=True, nullable=True, index=True)
    employee_id = Column(Integer, ForeignKey('employees.employee_id', ondelete='SET NULL'), nullable=True)

    # Relaciones
    company = relationship('Company')
    employee = relationship('Employee', backref=backref('user', uselist=False))
    # Relación de muchos a muchos con el modelo Permission
    permissions = relationship('Permission', secondary=user_permissions, lazy='subquery',
                                  backref='users')

    def check_password(self, password):
        """Verifica la contraseña hasheada."""
        return verify_password(password, self.password)

# Modelo de Permiso (tabla 'permissions')
class Permission(Base):
    __tablename__ = 'permissions'
    permission_id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(String(200))


# Modelo de Clientes (tabla 'customers')
class Customer(Base):
    __tablename__ = 'customers'
    customer_id = Column(Integer, primary_key=True)
    is_company = Column(Boolean, default=False)
    cname = Column(String(64), nullable=True)  # Company name
    fname = Column(String(64), nullable=True)  # First name
    lname = Column(String(64), nullable=True)  # Last name
    address1 = Column(String(128), nullable=True)
    address2 = Column(String(128), nullable=True)
    email = Column(String(128), nullable=False)
    phone = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='SET NULL'), nullable=True)

    company = relationship('Company')
    orders = relationship("Order", back_populates="customer")
    contacts = relationship("Contact", back_populates="customer", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", back_populates="customer", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = 'contacts'
    contact_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id', ondelete='CASCADE'), nullable=False)
    fname = Column(String(64), nullable=True)  # First name
    lname = Column(String(64), nullable=True)  # Last name
    email = Column(String(128), nullable=False)
    phone = Column(String(32), nullable=True)
    customer = relationship('Customer', back_populates='contacts')
    orders = relationship("Order", back_populates="contact")

class Position(Base):
    __tablename__ = 'positions'
    position_id = Column(Integer, primary_key=True)
    title = Column(String(64), unique=True, nullable=False)
    description = Column(String(200), nullable=True)
    employees = relationship("Employee", back_populates="position")

class Employee(Base):
    __tablename__ = 'employees'
    employee_id = Column(Integer, primary_key=True)
    fname = Column(String(64), nullable=False)
    lname1 = Column(String(64), nullable=False)
    lname2 = Column(String(64), nullable=True)
    email = Column(String(128), nullable=False)
    phone = Column(String(32), nullable=True)
    position_id = Column(Integer, ForeignKey('positions.position_id'))
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='SET NULL'), nullable=True)

    company = relationship('Company')
    position = relationship("Position", back_populates="employees")
    advised_orders = relationship("Order", foreign_keys='Order.advisor_id', back_populates="advisor")
    mechanic_orders = relationship("Order", foreign_keys='Order.mechanic_id', back_populates="mechanic")
    
    # Relaciones para el sistema de horarios
    schedule_blocks = relationship("EmployeeScheduleBlock", back_populates="employee", cascade="all, delete-orphan")
    schedule_overrides = relationship("ScheduleOverride", back_populates="employee", cascade="all, delete-orphan")

class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(Integer, primary_key=True)
    c_order_id = Column(String(32), unique=True, nullable=False)
    order_date = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    advisor_id = Column(Integer, ForeignKey('employees.employee_id', ondelete='SET NULL'), nullable=True)
    mechanic_id = Column(Integer, ForeignKey('employees.employee_id', ondelete='SET NULL'), nullable=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id', ondelete='SET NULL'), nullable=True)
    contact_id = Column(Integer, ForeignKey('contacts.contact_id', ondelete='SET NULL'), nullable=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.vehicle_id'), nullable=True)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='SET NULL'), nullable=True)

    company = relationship('Company') # Order status ID
    op_status_id = Column(Integer, ForeignKey('op_status.op_status_id'), nullable=True)  # Approval status ID
    adm_status_id = Column(Integer, ForeignKey('adm_status.adm_status_id'), nullable=True)  # Priority ID
    priority_id = Column(Integer, ForeignKey('priority.priority_id'), nullable=True)
    p_mileage = Column(Integer, nullable=True)  # Presumed mileage
    c_mileage = Column(Integer, nullable=True)  # Current mileage
    service_bay = Column(String(16), nullable = True)
    fuel_level = Column(Integer, nullable=True) # Nivel de combustible (ej: 1-8)
    has_extra_info = Column(Boolean, default=False)  # Indica si extra info es presente

    # Relationships
    advisor = relationship("Employee", foreign_keys=[advisor_id], back_populates="advised_orders")
    mechanic = relationship("Employee", foreign_keys=[mechanic_id], back_populates="mechanic_orders")
    customer = relationship("Customer", back_populates="orders")
    contact = relationship("Contact", back_populates="orders")
    vehicle = relationship("Vehicle", back_populates="orders")
    op_status = relationship("OpStatus", back_populates="orders")
    adm_status = relationship("AdmStatus", back_populates="orders")
    priority = relationship("Priority", back_populates="orders")
    # La relación mantiene el nombre que prefieres.
    extra_info = relationship("OrderExtraInfo", back_populates="order", cascade="all, delete-orphan")
    bodywork_details = relationship("BodyworkDetails", back_populates="order", cascade="all, delete-orphan") # Relación uno a muchos
    inventory_data = relationship("OrderInventoryData", back_populates="order", cascade="all, delete-orphan")


class OrderExtraInfo(Base):
    __tablename__ = 'order_extra_info'
    order_id = Column(Integer, ForeignKey('orders.order_id'), primary_key=True)
    item_id = Column(Integer, ForeignKey('order_extra_items.item_id'), primary_key=True)
    info = Column(String(256), nullable=True)
    # Relationships
    order = relationship("Order", back_populates="extra_info")
    item = relationship("OrderExtraItems", back_populates="infos")

class OrderExtraItems(Base):
    __tablename__ = 'order_extra_items'
    item_id = Column(Integer, primary_key=True)
    title = Column(String(128), nullable=False)
    description = Column(String(256), nullable=True)
    # Relationships (renombrado a plural 'infos' para mayor claridad)
    infos = relationship("OrderExtraInfo", back_populates="item")

class OpStatus(Base):
    __tablename__ = 'op_status'
    op_status_id = Column(Integer, primary_key=True)
    status = Column(String(64), unique=True, nullable=False)
    orders = relationship("Order", back_populates="op_status")

class AdmStatus(Base):
    __tablename__ = 'adm_status'
    adm_status_id = Column(Integer, primary_key=True)
    status = Column(String(64), unique=True, nullable=False)
    orders = relationship("Order", back_populates="adm_status")

class Priority(Base):
    __tablename__ = 'priority'
    priority_id = Column(Integer, primary_key=True)
    level = Column(String(64), unique=True, nullable=False)
    orders = relationship("Order", back_populates="priority")


class Vehicle(Base):
    __tablename__ = 'vehicles'
    vehicle_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id', ondelete='SET NULL'), nullable=True)
    vin = Column(String(32), unique=True, nullable=False)  # Vehicle Identification Number
    plate = Column(String(32), unique=True, nullable=True)  # Plate number
    year = Column(Integer, nullable=False)
    model_id = Column(Integer, ForeignKey('models.model_id'), nullable=False)
    mileage = Column(Integer, nullable=False)
    
    color_id = Column(Integer, ForeignKey('colors.color_id'), nullable=False)
    motor_id = Column(Integer, ForeignKey('motors.motor_id'), nullable=False)  # Engine details
    transmission_id = Column(Integer, ForeignKey('transmissions.transmission_id'), nullable=False)  # Transmission type
    cylinders = Column(Integer, nullable=False)
    liters = Column(String(16), nullable=False)  # Engine displacement in liters
    v_type_id = Column(Integer, ForeignKey('vehicle_types.v_type_id'), nullable=False)  # Vehicle type (e.g., sedan, SUV)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='SET NULL'), nullable=True)

    company = relationship('Company')

    orders = relationship("Order", back_populates="vehicle")
    customer = relationship("Customer", foreign_keys=[customer_id], back_populates="vehicles")
    color = relationship("Color", foreign_keys=[color_id], back_populates="vehicles")
    motor = relationship("Motor", foreign_keys=[motor_id], back_populates="vehicles")
    vehicle_type = relationship("VehicleType", foreign_keys=[v_type_id], back_populates="vehicles")
    model = relationship("Model", foreign_keys=[model_id])
    transmission = relationship("Transmission", foreign_keys=[transmission_id], back_populates="vehicles")

class Color(Base):
    __tablename__ = 'colors'
    color_id = Column(Integer, primary_key=True)
    color = Column(String(64), unique=True, nullable=False)
    vehicles = relationship("Vehicle", back_populates="color")

class Motor(Base):
    __tablename__ = 'motors'
    motor_id = Column(Integer, primary_key=True)
    type = Column(String(64), nullable=False)
    vehicles = relationship("Vehicle", back_populates="motor")

class VehicleType(Base):
    __tablename__ = 'vehicle_types'
    v_type_id = Column(Integer, primary_key=True)
    type = Column(String(64), unique=True, nullable=False)
    vehicles = relationship("Vehicle", back_populates="vehicle_type")

class Make(Base):
    __tablename__ = 'makes'
    make_id = Column(Integer, primary_key=True)
    make = Column(String(64), unique=True, nullable=False)
    models = relationship("Model", back_populates="make")

class Model(Base):
    __tablename__ = 'models'
    model_id = Column(Integer, primary_key=True)
    make_id = Column(Integer, ForeignKey('makes.make_id'), nullable=False)
    model = Column(String(64), nullable=False)
    make = relationship("Make", back_populates="models")

class Transmission(Base):
    __tablename__ = 'transmissions'
    transmission_id = Column(Integer, primary_key=True)
    type = Column(String(64), unique=True, nullable=False)
    vehicles = relationship("Vehicle", back_populates="transmission")

class BodyworkDetails(Base):
    __tablename__ = 'bodywork_details'
    detail_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.order_id', ondelete='CASCADE'), nullable=False)
    view = Column(Enum(BodyworkChecklistView, name="bodywork_checklist_view_enum"), nullable=False)
    detail_type_id = Column(Integer, ForeignKey('bodywork_detail_types.detail_type_id'), nullable=True)
    coordinates = Column(JSONB, nullable=True) # Almacena {"x": float, "y": float}
    detail_notes = Column(String(256), nullable=True)
    picture_path = Column(String(256), nullable=True)  # Ruta a la imagen almacenada
    order = relationship("Order", back_populates="bodywork_details")
    detail_type = relationship("BodyworkDetailTypes")

class BodyworkDetailTypes(Base):
    __tablename__ = 'bodywork_detail_types'
    detail_type_id = Column(Integer, primary_key=True)
    type = Column(String(128), unique=True, nullable=False)
    color = Column(String(32), nullable=True)  # Columna para el color (ej. #FF5733)
    # No es estrictamente necesario tener un back_populates aquí si no necesitas
    # navegar desde un BodyworkDetailType a todos los checklists que lo usan.
    # bodywork_checklist = relationship("BodyworkChecklist", back_populates="detail_type")


class InventoryTypes(Base):
    __tablename__ = 'inventory_types'
    inv_type_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    component_key = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    position = Column(Integer, nullable=False, default=0)
    picture_path = Column(String(512), nullable=True)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='SET NULL'), nullable=True)

    company = relationship('Company')
    # Relación uno a muchos con InventoryItems
    items = relationship("InventoryItems", back_populates="inventory_type", cascade="all, delete-orphan")


class InventoryItems(Base):
    __tablename__ = 'inventory_items'
    item_id = Column(Integer, primary_key=True)
    inv_type_id = Column(Integer, ForeignKey('inventory_types.inv_type_id'), nullable=False)
    label = Column(String(255), nullable=False)
    input_type = Column(String(50), nullable=False)
    position = Column(Integer, nullable=False, default=0)
    description = Column(String, nullable=True)  # Se mapea a TEXT en PostgreSQL
    picture_upload = Column(Boolean, nullable=False, default=False)
    is_mandatory = Column(Boolean, nullable=False, default=False)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='SET NULL'), nullable=True)

    company = relationship('Company')
    inventory_type = relationship("InventoryTypes", back_populates="items")


class OrderInventoryData(Base):
    __tablename__ = 'order_inventory_data'
    data_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.order_id', ondelete='CASCADE'), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey('inventory_items.item_id', ondelete='CASCADE'), nullable=False, index=True)
    data = Column(JSONB, nullable=True) # Valor del input, puede ser un objeto JSON

    # Relationships
    order = relationship("Order", back_populates="inventory_data")
    item = relationship("InventoryItems")

    __table_args__ = (UniqueConstraint('order_id', 'item_id', name='_order_item_uc'),)


# --- Tabla de asociación para Citas y Razones (Muchos a Muchos) ---
appointment_reasons_link = Table('appointment_reasons_link', Base.metadata,
    Column('appointment_id', Integer, ForeignKey('appointments.appointment_id', ondelete='CASCADE'), primary_key=True),
    Column('reason_id', Integer, ForeignKey('appointment_reasons.reason_id'), primary_key=True)
)


class Appointment(Base):
    __tablename__ = 'appointments'
    appointment_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id', ondelete='SET NULL'), nullable=True)
    contact_id = Column(Integer, ForeignKey('contacts.contact_id', ondelete='SET NULL'), nullable=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.vehicle_id', ondelete='SET NULL'), nullable=True)
    scheduled_by = Column(Integer, ForeignKey('employees.employee_id', ondelete='SET NULL'), nullable=True)
    assigned_to = Column(Integer, ForeignKey('employees.employee_id', ondelete='SET NULL'), nullable=True)
    appointment_date = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    status_id = Column(Integer, ForeignKey('appointment_status.status_id'), nullable=True)
    notes = Column(String(256), nullable=True)
    rescheduled_count = Column(Integer, default=0)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='SET NULL'), nullable=True)

    company = relationship('Company')

    #Temporal fields
    temp_cname = Column(String(64), nullable=True)  # Temporary company name
    temp_fname = Column(String(64), nullable=True)  # Temporary first name
    temp_lname = Column(String(64), nullable=True)  # Temporary last name
    temp_email = Column(String(128), nullable=True)  # Temporary email
    temp_phone = Column(String(32), nullable=True)  # Temporary phone number
    temp_vehicle_data = Column(JSONB, nullable=True) # Datos temporales del vehículo en formato JSON


    # Relationships
    customer = relationship("Customer")
    contact = relationship("Contact")
    vehicle = relationship("Vehicle")
    scheduler = relationship("Employee", foreign_keys=[scheduled_by])
    assignee = relationship("Employee", foreign_keys=[assigned_to])
    status = relationship("AppointmentStatus", foreign_keys=[status_id])
    reasons = relationship("AppointmentReason", secondary=appointment_reasons_link, back_populates="appointments")

    
class AppointmentStatus(Base):
    __tablename__ = 'appointment_status'
    status_id = Column(Integer, primary_key=True)
    status = Column(String(64), unique=True, nullable=False)  # e.g., Scheduled, Completed, Canceled

class AppointmentReason(Base):
    __tablename__ = 'appointment_reasons'
    reason_id = Column(Integer, primary_key=True)
    reason = Column(String(128), unique=True, nullable=False)  # e.g., Maintenance, Repair, Inspection
    duration_minutes = Column(Integer, default=60, server_default='60', nullable=False) # Duración estimada en minutos

    # Relación inversa para poder ver todas las citas de una razón
    appointments = relationship("Appointment", secondary=appointment_reasons_link, back_populates="reasons")

# --- Modelos para Horarios de Empleados ---

class EmployeeScheduleBlock(Base):
    __tablename__ = 'employee_schedule_blocks'
    block_id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.employee_id', ondelete='CASCADE'), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Lunes, 1=Martes, ..., 6=Domingo
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    employee = relationship("Employee", back_populates="schedule_blocks")

class ScheduleOverride(Base):
    __tablename__ = 'schedule_overrides'
    override_id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.employee_id', ondelete='CASCADE'), nullable=False)
    override_date = Column(Date, nullable=False)
    is_available = Column(Boolean, nullable=False)
    start_time = Column(Time, nullable=True) # Nulo si is_available es false
    end_time = Column(Time, nullable=True)   # Nulo si is_available es false
    reason = Column(String(256), nullable=True) # Opcional: "Vacaciones", "Cita médica"
    employee = relationship("Employee", back_populates="schedule_overrides")

# --- Modelo para Configuración de la Empresa ---

class CompanySettings(Base):
    __tablename__ = 'company_settings'
    
    id = Column(Integer, primary_key=True, default=1)
    company_name = Column(String(128), default="Mi Taller")
    address = Column(String(256), nullable=True)
    phone = Column(String(32), nullable=True)
    email = Column(String(128), nullable=True)
    website = Column(String(128), nullable=True)
    tax_id = Column(String(64), nullable=True)
    business_hours_start = Column(Time, nullable=True)
    business_hours_end = Column(Time, nullable=True)
    info = Column(String, nullable=True) # Campo para información extra


# --- Modelos para la Integración de WhatsApp ---

class WhatsAppConfig(Base):
    __tablename__ = 'whatsapp_configs'
    config_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False, unique=True)
    phone_number_id = Column(String(64), unique=True, nullable=False)
    waba_id = Column(String(64), nullable=False)
    access_token = Column(String(512), nullable=False)
    phone_number = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True)

    company = relationship("Company")


class WhatsAppConversation(Base):
    __tablename__ = 'whatsapp_conversations'
    conversation_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    customer_phone = Column(String(32), nullable=False)
    customer_name = Column(String(128), nullable=True)
    last_message_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    company = relationship("Company")
    messages = relationship("WhatsAppMessage", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('company_id', 'customer_phone', name='_company_customer_phone_uc'),)


class WhatsAppMessage(Base):
    __tablename__ = 'whatsapp_messages'
    message_id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('whatsapp_conversations.conversation_id', ondelete='CASCADE'), nullable=False)
    whatsapp_message_id = Column(String(128), unique=True, nullable=True)
    direction = Column(String(16), nullable=False) # 'inbound' o 'outbound'
    type = Column(String(16), default='text', nullable=False) # 'text', 'image', 'document', 'system'
    body = Column(String(1024), nullable=True)
    media_url = Column(String(512), nullable=True)
    status = Column(String(16), default='sent', nullable=False) # 'sent', 'delivered', 'read', 'failed'
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    conversation = relationship("WhatsAppConversation", back_populates="messages")