import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Table, ForeignKey, Date, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
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

# Modelo de Usuario (tabla 'users')
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password = Column(String(200)) # Aquí se almacena la contraseña hasheada
    is_admin = Column(Boolean, default=False)
    is_employee = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

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
    position = relationship("Position", back_populates="employees")
    advised_orders = relationship("Order", foreign_keys='Order.advisor_id', back_populates="advisor")
    mechanic_orders = relationship("Order", foreign_keys='Order.mechanic_id', back_populates="mechanic")

class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(Integer, primary_key=True)
    c_order_id = Column(String(32), unique=True, nullable=False)
    order_date = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    advisor_id = Column(Integer, ForeignKey('employees.employee_id', ondelete='SET NULL'), nullable=True)
    mechanic_id = Column(Integer, ForeignKey('employees.employee_id', ondelete='SET NULL'), nullable=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id', ondelete='SET NULL'), nullable=True)
    contact_id = Column(Integer, ForeignKey('contacts.contact_id', ondelete='SET NULL'), nullable=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.vehicle_id'), nullable=True) # Order status ID
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
    extra_info = relationship("OrderExtraInfo", back_populates="order")
    


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
