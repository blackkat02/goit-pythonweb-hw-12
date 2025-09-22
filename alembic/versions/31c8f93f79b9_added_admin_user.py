"""added ADMIN, USER

Revision ID: 31c8f93f79b9
Revises: 08084c2dfd49
Create Date: 2025-09-22 19:01:32.804885

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31c8f93f79b9'
down_revision: Union[str, Sequence[str], None] = '08084c2dfd49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Оновлення ENUM: додавання нових значень
    op.execute("ALTER TYPE role ADD VALUE 'ADMIN';")
    op.execute("ALTER TYPE role ADD VALUE 'USER';")


def downgrade() -> None:
    # Відкат змін (зазвичай, складніше, але для цього випадку достатньо)
    op.execute("ALTER TYPE role RENAME TO role_old;")
    op.execute("CREATE TYPE role AS ENUM ('MODERATOR');")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE role USING role::text::role;")
    op.execute("DROP TYPE role_old;")
