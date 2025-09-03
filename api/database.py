import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from werkzeug.security import check_password_hash

# Define la URL de la base de datos.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://root:123456@localhost/test")

# El engine se encarga de la comunicación con la base de datos
engine = create_engine(DATABASE_URL)

# `sessionmaker` crea una "fábrica" de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# `declarative_base` es una clase base de la que heredarán los modelos de la base de datos
Base = declarative_base()

# --- Modelos de la base de datos ---

# Tabla de asociación para la relación muchos a muchos entre User y Permission
user_permissions = Table('user_permissions', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

# Modelo de Usuario (tabla 'users')
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password = Column(String(200)) # Aquí se almacena la contraseña hasheada
    is_admin = Column(Boolean, default=False)

    # Relación de muchos a muchos con el modelo Permission
    permissions = relationship('Permission', secondary=user_permissions, lazy='subquery',
                                  backref='users')

    def check_password(self, password):
        """Verifica la contraseña hasheada."""
        return check_password_hash(self.password, password)

# Modelo de Permiso (tabla 'permissions')
class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(String(200))


# Modelo de Clientes (tabla 'customers')
class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    is_company = Column(Boolean, default=False)
    cname = Column(String(64), nullable=True)  # Company name
    fname = Column(String(64), nullable=True)  # First name
    lname = Column(String(64), nullable=True)  # Last name
    address1 = Column(String(128), nullable=True)
    address2 = Column(String(128), nullable=True)
    email = Column(String(128), nullable=False)
    phone = Column(String(32), nullable=True)