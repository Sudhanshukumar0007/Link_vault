"""add workspace_id to links

Revision ID: a26307ec58b1
Revises: cbb05e55b08f
Create Date: 2026-07-04 09:34:39.811443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a26307ec58b1'
down_revision: Union[str, Sequence[str], None] = 'cbb05e55b08f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('links', sa.Column('workspace_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(None, 'links', 'workspaces', ['workspace_id'], ['id'])
    op.create_foreign_key(None, 'workspace_members', 'workspaces', ['workspace_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_constraint(None, 'workspace_members', type_='foreignkey')
    op.drop_constraint(None, 'links', type_='foreignkey')
    op.drop_column('links', 'workspace_id')
    # ### end Alembic commands ###
