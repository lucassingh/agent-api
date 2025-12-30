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
    bind = op.get_bind()
    
    result = bind.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole')"
    ).fetchone()
    userrole_exists = result[0]
    
    if not userrole_exists:
        userrole = postgresql.ENUM('admin', 'supervisor', 'operator', name='userrole')
        userrole.create(bind)
        print("✅ Tipo userrole creado")
    else:
        print("✅ Tipo userrole ya existe, omitiendo creación")
    
    userrole_enum = postgresql.ENUM('admin', 'supervisor', 'operator', name='userrole')
    
    result = bind.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'incidentstatus')"
    ).fetchone()
    incidentstatus_exists = result[0]
    
    if not incidentstatus_exists:
        incidentstatus = postgresql.ENUM('initiated', 'resolved', 'unresolved', name='incidentstatus')
        incidentstatus.create(bind)
        print("✅ Tipo incidentstatus creado")
    else:
        print("✅ Tipo incidentstatus ya existe, omitiendo creación")
    
    incidentstatus_enum = postgresql.ENUM('initiated', 'resolved', 'unresolved', name='incidentstatus')
   
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
    
    bind = op.get_bind()
    
    result = bind.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'incidentstatus')"
    ).fetchone()
    if result[0]:
        incidentstatus = postgresql.ENUM(name='incidentstatus')
        incidentstatus.drop(bind)
    
    # Verificar si userrole existe antes de eliminarlo
    result = bind.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole')"
    ).fetchone()
    if result[0]:
        userrole = postgresql.ENUM(name='userrole')
        userrole.drop(bind)