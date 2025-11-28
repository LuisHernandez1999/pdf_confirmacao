

revision = '726ea92a516f'
down_revision = "8a81323c8c54"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('relatorio_confirmacao') as batch_op:
        batch_op.add_column(sa.Column('imagem_antes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('imagem_depois', sa.Text(), nullable=True))


def downgrade():
    # downgrade vazio → NÃO REMOVE NADA
    pass
