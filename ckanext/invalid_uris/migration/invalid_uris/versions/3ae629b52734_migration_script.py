"""Migration script

Revision ID: 3ae629b52734
Revises: 
Create Date: 2024-07-25 20:38:31.971049

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ae629b52734'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()
    if 'invalid_uri' not in tables:
        op.create_table(
            'invalid_uri',
            sa.Column('id', sa.UnicodeText, primary_key=True),
            sa.Column('entity_type', sa.UnicodeText, nullable=False),
            sa.Column('entity_id', sa.UnicodeText, nullable=False),
            sa.Column('parent_entity_id', sa.UnicodeText),
            sa.Column('field', sa.UnicodeText, nullable=False),
            sa.Column('uri', sa.UnicodeText, nullable=False),
            sa.Column('status_code', sa.UnicodeText, nullable=False),
            sa.Column('reason', sa.UnicodeText, nullable=False),
            sa.Column('date_created', sa.DateTime, default=sa.func.now()),
            sa.Column('date_last_checked', sa.DateTime, default=sa.func.now())
        )


def downgrade():
    op.drop_table('invalid_uri')
