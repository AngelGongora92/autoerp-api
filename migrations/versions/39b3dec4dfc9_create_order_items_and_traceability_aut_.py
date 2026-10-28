"""create_order_items_and_traceability_aut_40

Revision ID: 39b3dec4dfc9
Revises: 8f2a67637cb3
Create Date: 2026-10-28 15:30:14.264042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39b3dec4dfc9'
down_revision: Union[str, Sequence[str], None] = '8f2a67637cb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Crear tabla order_items
    op.create_table(
        'order_items',
        sa.Column('order_item_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.order_id', ondelete='CASCADE'), nullable=False),
        sa.Column('reason_id', sa.Integer(), sa.ForeignKey('appointment_reasons.reason_id', ondelete='SET NULL'), nullable=True),
        sa.Column('custom_description', sa.String(length=256), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('priority_id', sa.Integer(), sa.ForeignKey('priority.priority_id', ondelete='SET NULL'), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), server_default='1.0', nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_approved', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])

    # 2. Agregar columna appointment_id a orders
    op.add_column('orders', sa.Column('appointment_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_orders_appointment_id', 'orders', 'appointments', ['appointment_id'], ['appointment_id'], ondelete='SET NULL')
    op.create_index('ix_orders_appointment_id', 'orders', ['appointment_id'])

    # 3. Agregar columnas order_id y channel a appointments
    op.add_column('appointments', sa.Column('order_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_appointments_order_id', 'appointments', 'orders', ['order_id'], ['order_id'], ondelete='SET NULL')
    op.create_index('ix_appointments_order_id', 'appointments', ['order_id'])
    op.add_column('appointments', sa.Column('channel', sa.String(length=32), server_default='manual', nullable=True))

    # 4. Asegurar estado id=4 ('atendida') en appointment_status
    op.execute("""
    INSERT INTO appointment_status (status_id, status)
    VALUES (4, 'atendida')
    ON CONFLICT (status_id) DO NOTHING;
    """)


def downgrade() -> None:
    # 1. Revertir columnas de appointments
    op.drop_column('appointments', 'channel')
    op.drop_index('ix_appointments_order_id', table_name='appointments')
    op.drop_constraint('fk_appointments_order_id', 'appointments', type_='foreignkey')
    op.drop_column('appointments', 'order_id')

    # 2. Revertir columna de orders
    op.drop_index('ix_orders_appointment_id', table_name='orders')
    op.drop_constraint('fk_orders_appointment_id', 'orders', type_='foreignkey')
    op.drop_column('orders', 'appointment_id')

    # 3. Eliminar tabla order_items
    op.drop_index('ix_order_items_order_id', table_name='order_items')
    op.drop_table('order_items')
