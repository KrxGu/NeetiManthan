"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create vector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create drafts table
    op.create_table('drafts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('text_uri', sa.String(length=1000), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_drafts'))
    )
    
    # Create clauses table
    op.create_table('clauses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ref', sa.String(length=100), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], name=op.f('fk_clauses_draft_id_drafts')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_clauses'))
    )
    
    # Create comments_raw table
    op.create_table('comments_raw',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_meta', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('text_raw', sa.Text(), nullable=False),
        sa.Column('lang', sa.String(length=10), nullable=True),
        sa.Column('pii_masked', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], name=op.f('fk_comments_raw_draft_id_drafts')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_comments_raw'))
    )
    
    # Create comments_processed table
    op.create_table('comments_processed',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('comment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text_normalized', sa.Text(), nullable=False),
        sa.Column('clause_guesses', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.ForeignKeyConstraint(['comment_id'], ['comments_raw.id'], name=op.f('fk_comments_processed_comment_id_comments_raw')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_comments_processed'))
    )
    
    # Create predictions table
    op.create_table('predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('comment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sentiment_label', sa.String(length=20), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('sentiment_intensity', sa.Float(), nullable=True),
        sa.Column('stance', sa.String(length=20), nullable=True),
        sa.Column('aspects', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('ci_low', sa.Float(), nullable=True),
        sa.Column('ci_high', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['comment_id'], ['comments_processed.comment_id'], name=op.f('fk_predictions_comment_id_comments_processed')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_predictions'))
    )
    
    # Create summaries table
    op.create_table('summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('comment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['comments_processed.comment_id'], name=op.f('fk_summaries_comment_id_comments_processed')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_summaries'))
    )
    
    # Create clusters table
    op.create_table('clusters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cluster_id', sa.Integer(), nullable=False),
        sa.Column('member_ids', postgresql.ARRAY(postgresql.UUID()), nullable=True),
        sa.Column('representative_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], name=op.f('fk_clusters_draft_id_drafts')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_clusters'))
    )
    
    # Create keywords table
    op.create_table('keywords',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('facet', sa.String(length=50), nullable=False),
        sa.Column('term', sa.String(length=200), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('frequency', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], name=op.f('fk_keywords_draft_id_drafts')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_keywords'))
    )
    
    # Create audits table
    op.create_table('audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('entity', sa.String(length=50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('change_type', sa.String(length=20), nullable=False),
        sa.Column('change_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_audits'))
    )
    
    # Create model_registry table
    op.create_table('model_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('model_uri', sa.String(length=500), nullable=False),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_model_registry')),
        sa.UniqueConstraint('model_version', name=op.f('uq_model_registry_model_version'))
    )
    
    # Create indexes
    op.create_index(op.f('ix_comments_raw_draft_id'), 'comments_raw', ['draft_id'], unique=False)
    op.create_index(op.f('ix_comments_processed_comment_id'), 'comments_processed', ['comment_id'], unique=False)
    op.create_index(op.f('ix_predictions_comment_id'), 'predictions', ['comment_id'], unique=False)
    op.create_index(op.f('ix_summaries_comment_id'), 'summaries', ['comment_id'], unique=False)
    op.create_index(op.f('ix_clusters_draft_id'), 'clusters', ['draft_id'], unique=False)
    op.create_index(op.f('ix_keywords_draft_id'), 'keywords', ['draft_id'], unique=False)
    op.create_index(op.f('ix_audits_entity_id'), 'audits', ['entity_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_audits_entity_id'), table_name='audits')
    op.drop_index(op.f('ix_keywords_draft_id'), table_name='keywords')
    op.drop_index(op.f('ix_clusters_draft_id'), table_name='clusters')
    op.drop_index(op.f('ix_summaries_comment_id'), table_name='summaries')
    op.drop_index(op.f('ix_predictions_comment_id'), table_name='predictions')
    op.drop_index(op.f('ix_comments_processed_comment_id'), table_name='comments_processed')
    op.drop_index(op.f('ix_comments_raw_draft_id'), table_name='comments_raw')
    
    # Drop tables
    op.drop_table('model_registry')
    op.drop_table('audits')
    op.drop_table('keywords')
    op.drop_table('clusters')
    op.drop_table('summaries')
    op.drop_table('predictions')
    op.drop_table('comments_processed')
    op.drop_table('comments_raw')
    op.drop_table('clauses')
    op.drop_table('drafts')
