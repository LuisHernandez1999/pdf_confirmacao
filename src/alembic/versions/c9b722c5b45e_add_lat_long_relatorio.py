"""add lat long e colunas de imagens no relatorio"""

revision = 'c9b722c5b45e'
down_revision = '726ea92a516f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Adiciona colunas de imagens
    op.add_column('relatorio_confirmacao', sa.Column('imagem_antes', sa.Text(), nullable=True))
    op.add_column('relatorio_confirmacao', sa.Column('imagem_depois', sa.Text(), nullable=True))

    # Adiciona colunas de latitude/longitude
    op.add_column('relatorio_confirmacao', sa.Column('latitude_antes', sa.Float(), nullable=True))
    op.add_column('relatorio_confirmacao', sa.Column('longitude_antes', sa.Float(), nullable=True))
    op.add_column('relatorio_confirmacao', sa.Column('latitude_depois', sa.Float(), nullable=True))
    op.add_column('relatorio_confirmacao', sa.Column('longitude_depois', sa.Float(), nullable=True))


def downgrade():
    # Remove colunas caso seja necessário rollback
    op.drop_column('relatorio_confirmacao', 'longitude_depois')
    op.drop_column('relatorio_confirmacao', 'latitude_depois')
    op.drop_column('relatorio_confirmacao', 'longitude_antes')
    op.drop_column('relatorio_confirmacao', 'latitude_antes')
    op.drop_column('relatorio_confirmacao', 'imagem_depois')
    op.drop_column('relatorio_confirmacao', 'imagem_antes')
