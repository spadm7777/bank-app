"""Add telegram_group to users

Revision ID: abcd1234
Revises: 9c4f4fab47f2
Create Date: 2025-07-23 19:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = 'abcd1234'
down_revision = '9c4f4fab47f2'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('telegram_group', sa.String(length=100), nullable=True))

def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('telegram_group')
