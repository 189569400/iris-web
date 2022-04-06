"""Add dark mode

Revision ID: b664ca1203a4
Revises: 2df770a4989c
Create Date: 2022-03-06 18:00:46.251407

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import engine_from_config
from sqlalchemy.engine import reflection

revision = 'b664ca1203a4'
down_revision = '2df770a4989c'
branch_labels = None
depends_on = None


def upgrade():
    if not _table_has_column('user', 'in_dark_mode'):
        op.add_column('user',
                      sa.Column('in_dark_mode', sa.Boolean)
                      )

        t_ua = sa.Table(
            'user',
            sa.MetaData(),
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('in_dark_mode', sa.Boolean)
        )
        conn = op.get_bind()
        conn.execute(t_ua.update().values(
            in_dark_mode=False
        ))

    pass


def downgrade():
    pass


def _table_has_column(table, column):
    config = op.get_context().config
    engine = engine_from_config(
        config.get_section(config.config_ini_section), prefix='sqlalchemy.')
    insp = reflection.Inspector.from_engine(engine)
    has_column = False

    for col in insp.get_columns(table):
        if column != col['name']:
            continue
        has_column = True
    return has_column