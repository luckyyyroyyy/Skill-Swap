"""add_credits_endorsements_and_workspace

Revision ID: a730815c2d7e
Revises: ff3ebdd6ad70
Create Date: 2026-09-05 14:31:24.460368

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a730815c2d7e'
down_revision = 'ff3ebdd6ad70'
branch_labels = None
depends_on = None


from sqlalchemy import inspect


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    # 1. Create skill_endorsement table if it doesn't exist
    if 'skill_endorsement' not in tables:
        op.create_table('skill_endorsement',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('skill_id', sa.Integer(), nullable=False),
            sa.Column('endorser_id', sa.Integer(), nullable=False),
            sa.Column('swap_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['endorser_id'], ['user.id'], ),
            sa.ForeignKeyConstraint(['skill_id'], ['skill.id'], ),
            sa.ForeignKeyConstraint(['swap_id'], ['swap_request.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('skill_endorsement', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_skill_endorsement_endorser_id'), ['endorser_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_skill_endorsement_skill_id'), ['skill_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_skill_endorsement_swap_id'), ['swap_id'], unique=False)

    # 2. Add credits column to user table if not present
    user_columns = [col['name'] for col in inspector.get_columns('user')]
    with op.batch_alter_table('user', schema=None) as batch_op:
        if 'credits' not in user_columns:
            batch_op.add_column(sa.Column('credits', sa.Integer(), nullable=True, server_default='3'))

    # 3. Add endorsements_count to skill table if not present
    skill_columns = [col['name'] for col in inspector.get_columns('skill')]
    with op.batch_alter_table('skill', schema=None) as batch_op:
        if 'endorsements_count' not in skill_columns:
            batch_op.add_column(sa.Column('endorsements_count', sa.Integer(), nullable=True, server_default='0'))

    # 4. Add credits_settled and session_notes to swap_request table if not present
    swap_columns = [col['name'] for col in inspector.get_columns('swap_request')]
    with op.batch_alter_table('swap_request', schema=None) as batch_op:
        if 'credits_settled' not in swap_columns:
            batch_op.add_column(sa.Column('credits_settled', sa.Boolean(), nullable=True, server_default=sa.text('0')))
        if 'session_notes' not in swap_columns:
            batch_op.add_column(sa.Column('session_notes', sa.Text(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if 'swap_request' in tables:
        swap_columns = [col['name'] for col in inspector.get_columns('swap_request')]
        with op.batch_alter_table('swap_request', schema=None) as batch_op:
            if 'session_notes' in swap_columns:
                batch_op.drop_column('session_notes')
            if 'credits_settled' in swap_columns:
                batch_op.drop_column('credits_settled')

    if 'skill' in tables:
        skill_columns = [col['name'] for col in inspector.get_columns('skill')]
        with op.batch_alter_table('skill', schema=None) as batch_op:
            if 'endorsements_count' in skill_columns:
                batch_op.drop_column('endorsements_count')

    if 'user' in tables:
        user_columns = [col['name'] for col in inspector.get_columns('user')]
        with op.batch_alter_table('user', schema=None) as batch_op:
            if 'credits' in user_columns:
                batch_op.drop_column('credits')

    if 'skill_endorsement' in tables:
        with op.batch_alter_table('skill_endorsement', schema=None) as batch_op:
            try:
                batch_op.drop_index(batch_op.f('ix_skill_endorsement_swap_id'))
                batch_op.drop_index(batch_op.f('ix_skill_endorsement_skill_id'))
                batch_op.drop_index(batch_op.f('ix_skill_endorsement_endorser_id'))
            except Exception:
                pass
        op.drop_table('skill_endorsement')


