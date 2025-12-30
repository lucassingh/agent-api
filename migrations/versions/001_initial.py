"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-12-29 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Crear ENUMs usando SQL puro con IF NOT EXISTS
    op.execute("CREATE TYPE IF NOT EXISTS userrole AS ENUM ('admin', 'supervisor', 'operator')")
    op.execute("CREATE TYPE IF NOT EXISTS incidentstatus AS ENUM ('initiated', 'resolved', 'unresolved')")
    
    # 2. Crear tabla users - usando postgresql.ENUM con create_type=False
    userrole_enum = postgresql.ENUM('admin', 'supervisor', 'operator', name='userrole', create_type=False)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('lastname', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', userrole_enum, server_default='operator', nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('verification_code', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    
    # 3. Crear tabla incidents
    incidentstatus_enum = postgresql.ENUM('initiated', 'resolved', 'unresolved', name='incidentstatus', create_type=False)
    op.create_table('incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('problem_audio_path', sa.String(), nullable=False),
        sa.Column('solution_audio_path', sa.String(), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('status', incidentstatus_enum, server_default='initiated', nullable=False),
        sa.Column('is_resolved', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_incidents_id'), 'incidents', ['id'], unique=False)
    op.create_index(op.f('ix_incidents_title'), 'incidents', ['title'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_incidents_title'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_id'), table_name='incidents')
    op.drop_table('incidents')
    
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Eliminar ENUMs
    op.execute("DROP TYPE IF EXISTS incidentstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS userrole CASCADE")