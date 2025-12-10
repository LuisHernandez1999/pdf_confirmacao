"""create relatorio_confirmacao table"""

revision = '8a81323c8c54'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'relatorio_confirmacao',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('confirmacao_tag', sa.String(14), sa.ForeignKey('confirmacao_servico.tag_doc', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('obs_antes', sa.Text, nullable=True),
        sa.Column('obs_depois', sa.Text, nullable=True),
        sa.Column('observacao', sa.Text, nullable=True),
        sa.Column('data_geracao', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('relatorio_confirmacao')
