"""initial

Revision ID: 20250702_044411
Revises: 
Create Date: 2025-07-02T04:44:11

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250702_044411"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'heartbeat_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )


def downgrade() -> None:
    op.drop_table('heartbeat_logs')