"""alter latitude/longitude columns to JSON

Revision ID: dc1234567890
Revises: c9b722c5b45e
Create Date: 2025-11-28 02:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'dc1234567890'
down_revision = 'c9b722c5b45e'
branch_labels = None
depends_on = None

def upgrade():
    # Alterar colunas de FLOAT para JSON
    op.alter_column('relatorio_confirmacao', 'latitude_antes',
                    existing_type=sa.Float(),
                    type_=sa.JSON(),
                    existing_nullable=True)
    op.alter_column('relatorio_confirmacao', 'longitude_antes',
                    existing_type=sa.Float(),
                    type_=sa.JSON(),
                    existing_nullable=True)
    op.alter_column('relatorio_confirmacao', 'latitude_depois',
                    existing_type=sa.Float(),
                    type_=sa.JSON(),
                    existing_nullable=True)
    op.alter_column('relatorio_confirmacao', 'longitude_depois',
                    existing_type=sa.Float(),
                    type_=sa.JSON(),
                    existing_nullable=True)

def downgrade():
    # Reverte JSON para FLOAT (atenção: se houver listas, pode perder dados)
    op.alter_column('relatorio_confirmacao', 'latitude_antes',
                    existing_type=sa.JSON(),
                    type_=sa.Float(),
                    existing_nullable=True)
    op.alter_column('relatorio_confirmacao', 'longitude_antes',
                    existing_type=sa.JSON(),
                    type_=sa.Float(),
                    existing_nullable=True)
    op.alter_column('relatorio_confirmacao', 'latitude_depois',
                    existing_type=sa.JSON(),
                    type_=sa.Float(),
                    existing_nullable=True)
    op.alter_column('relatorio_confirmacao', 'longitude_depois',
                    existing_type=sa.JSON(),
                    type_=sa.Float(),
                    existing_nullable=True)
