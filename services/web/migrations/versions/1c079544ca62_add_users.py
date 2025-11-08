from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '1c079544ca62'
down_revision = '8a87d5239b60'
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

    # Insert default user
    op.execute(f"""
        INSERT INTO users (id, username, password, created_at, updated_at)
        VALUES (1, 'admin', 'password', '{datetime.utcnow()}', '{datetime.utcnow()}')
    """)


def downgrade():
    op.drop_table('users')
