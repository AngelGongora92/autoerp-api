"""migrar appointments a multiples razones

Revision ID: 0829815eb5d3
Revises: cd823d295d97
Create Date: 2026-03-06 13:09:15.420075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0829815eb5d3'
down_revision: Union[str, Sequence[str], None] = 'cd823d295d97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Crear la tabla intermedia
    op.create_table('appointment_reasons_link',
        sa.Column('appointment_id', sa.Integer(), nullable=False),
        sa.Column('reason_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.appointment_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reason_id'], ['appointment_reasons.reason_id'], ),
        sa.PrimaryKeyConstraint('appointment_id', 'reason_id')
    )

    # 2. Migrar datos existentes: Copiar el reason_id actual a la nueva tabla
    op.execute("""
        INSERT INTO appointment_reasons_link (appointment_id, reason_id)
        SELECT appointment_id, reason_id
        FROM appointments
        WHERE reason_id IS NOT NULL
    """)

    # 3. Eliminar la columna antigua y su constraint
    # Nota: 'appointments_reason_id_fkey' es el nombre estándar en Postgres, 
    # si falla, verifica el nombre exacto en tu DB.
    op.drop_constraint('appointments_reason_id_fkey', 'appointments', type_='foreignkey')
    op.drop_column('appointments', 'reason_id')


def downgrade() -> None:
    # 1. Recrear la columna antigua
    op.add_column('appointments', sa.Column('reason_id', sa.Integer(), nullable=True))
    op.create_foreign_key('appointments_reason_id_fkey', 'appointments', 'appointment_reasons', ['reason_id'], ['reason_id'])

    # 2. Intentar recuperar datos (tomando uno al azar si hay múltiples)
    op.execute("""
        UPDATE appointments
        SET reason_id = (
            SELECT reason_id 
            FROM appointment_reasons_link 
            WHERE appointment_reasons_link.appointment_id = appointments.appointment_id 
            LIMIT 1
        )
    """)

    # 3. Borrar tabla intermedia
    op.drop_table('appointment_reasons_link')
