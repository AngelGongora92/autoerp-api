# Especificación Backend - AUT-40

## 1. Modelos de Base de Datos (SQLAlchemy)

```python
# order_items Model
class OrderItem(Base):
    __tablename__ = 'order_items'

    order_item_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.order_id', ondelete='CASCADE'), nullable=False, index=True)
    reason_id = Column(Integer, ForeignKey('appointment_reasons.reason_id', ondelete='SET NULL'), nullable=True)
    custom_description = Column(String(256), nullable=True)
    notes = Column(Text, nullable=True)
    priority_id = Column(Integer, ForeignKey('priority.priority_id', ondelete='SET NULL'), nullable=True)
    quantity = Column(Numeric(10, 2), nullable=False, server_default='1.0')
    unit_price = Column(Numeric(10, 2), nullable=True)
    is_approved = Column(Boolean, nullable=True, server_default='false')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order = relationship('Order', back_populates='items')
    reason = relationship('AppointmentReason')
```

## 2. Definición del Endpoint

### `POST /appointments/{appointment_id}/create-order`
- **Summary:** Crea una Orden de Servicio a partir de una cita y marca la cita como Atendida.
- **Headers:** `Authorization: Bearer <token>`
- **Path Params:** `appointment_id` (Integer, required)
- **Respuestas:**
  - `201 Created`: Devuelve los detalles de la orden generada y sus items.
  - `400 Bad Request`: Si la cita carece de cliente/vehículo o si ya fue convertida/cancelada.
  - `404 Not Found`: Cita no existe o no pertenece a la empresa del usuario.

### Schemas Pydantic

```python
class OrderItemResponse(BaseModel):
    order_item_id: int
    order_id: int
    reason_id: Optional[int]
    custom_description: Optional[str]
    notes: Optional[str]
    priority_id: Optional[int]
    quantity: float
    unit_price: Optional[float]
    is_approved: bool

    class Config:
        orm_mode = True

class CreatedOrderFromAppointmentResponse(BaseModel):
    order_id: int
    c_order_id: str
    appointment_id: int
    customer_id: int
    vehicle_id: int
    advisor_id: Optional[int]
    op_status_id: int
    priority_id: int
    items: List[OrderItemResponse]
```
