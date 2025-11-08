"""seed test shortlinks

Revision ID: 90ecba9a74e8
Revises: eb281a02da0b
Create Date: 2025-11-08 02:29:14.225483

"""
import os
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta
import random


# revision identifiers, used by Alembic.
revision = '90ecba9a74e8'
down_revision = 'eb281a02da0b'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    num_fixed_urls = int(os.environ.get('NUM_FIXED_URLS', 50000))
    data = [
        {
            "original_url": f"https://example.com/{i}",
            "short_url": f"t{i}",
            "expired": False,
            "expiration_date": datetime.utcnow() + timedelta(days=random.randint(1, 365)),
            "max_clicks": 100,
            "current_clicks": random.randint(0, 50),
            "deleted": False,
            "created_by": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        for i in range(num_fixed_urls)
    ]
    conn.execute(sa.text("""
        INSERT INTO shortlinks (
            original_url, short_url, expired, expiration_date,
            max_clicks, current_clicks, deleted, created_by, created_at, updated_at
        ) VALUES (
            :original_url, :short_url, :expired, :expiration_date,
            :max_clicks, :current_clicks, :deleted, :created_by, :created_at, :updated_at
        )
    """), data)


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM shortlinks WHERE short_url LIKE 't%'"))
