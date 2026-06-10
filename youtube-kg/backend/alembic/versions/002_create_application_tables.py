"""Create application tables

Revision ID: 002
Revises: 001
Create Date: 2026-06-10

This migration is idempotent - it uses raw SQL with IF NOT EXISTS
to handle tables that may have been created by Base.metadata.create_all()
during previous deployments.
"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Use raw SQL with IF NOT EXISTS for idempotency
    # This handles the case where tables were created by Base.metadata.create_all()

    op.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id UUID NOT NULL PRIMARY KEY,
        user_id UUID NOT NULL REFERENCES users(id),
        name VARCHAR(255) NOT NULL,
        creator_url TEXT NOT NULL,
        status VARCHAR(50) DEFAULT 'created' NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
    )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects(user_id)")

    op.execute("""
    CREATE TABLE IF NOT EXISTS creators (
        id UUID NOT NULL PRIMARY KEY,
        project_id UUID NOT NULL REFERENCES projects(id),
        name VARCHAR(255) NOT NULL,
        channel_url TEXT,
        bio TEXT,
        verified BOOLEAN DEFAULT false NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS detected_domains (
        id UUID NOT NULL PRIMARY KEY,
        project_id UUID NOT NULL REFERENCES projects(id),
        domain VARCHAR(255) NOT NULL,
        frequency INTEGER DEFAULT 1 NOT NULL,
        confidence FLOAT,
        selected BOOLEAN DEFAULT false NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id UUID NOT NULL PRIMARY KEY,
        project_id UUID NOT NULL REFERENCES projects(id),
        youtube_id VARCHAR(255) NOT NULL,
        title VARCHAR(500),
        description TEXT,
        transcript TEXT,
        duration_seconds INTEGER,
        published_at TIMESTAMP WITH TIME ZONE,
        status VARCHAR(50) DEFAULT 'pending' NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
    )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS ix_videos_youtube_id ON videos(youtube_id)")

    op.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id UUID NOT NULL PRIMARY KEY,
        project_id UUID NOT NULL REFERENCES projects(id),
        type VARCHAR(50) NOT NULL,
        status VARCHAR(50) DEFAULT 'pending' NOT NULL,
        result JSONB,
        error_message TEXT,
        started_at TIMESTAMP WITH TIME ZONE,
        completed_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id UUID NOT NULL PRIMARY KEY,
        project_id UUID NOT NULL REFERENCES projects(id),
        format VARCHAR(50) NOT NULL,
        content BYTEA,
        status VARCHAR(50) DEFAULT 'pending' NOT NULL,
        file_url TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id UUID NOT NULL PRIMARY KEY,
        user_id UUID NOT NULL REFERENCES users(id),
        action VARCHAR(100) NOT NULL,
        resource_type VARCHAR(50) NOT NULL,
        resource_id UUID,
        details JSONB,
        ip_address VARCHAR(45),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
    )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at)")


def downgrade():
    # Drop tables in reverse order of dependencies
    op.execute("DROP TABLE IF EXISTS audit_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS reports CASCADE")
    op.execute("DROP TABLE IF EXISTS jobs CASCADE")
    op.execute("DROP TABLE IF EXISTS videos CASCADE")
    op.execute("DROP TABLE IF EXISTS detected_domains CASCADE")
    op.execute("DROP TABLE IF EXISTS creators CASCADE")
    op.execute("DROP TABLE IF EXISTS projects CASCADE")
