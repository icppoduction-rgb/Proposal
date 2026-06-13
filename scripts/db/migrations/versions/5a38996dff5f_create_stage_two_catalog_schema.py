"""create stage two catalog schema."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

revision: str = '5a38996dff5f'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the migration."""
    op.create_table('data_quality_reports',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('report_uid', sa.UUID(), nullable=False),
    sa.Column('artifact_type', sa.Text(), nullable=False),
    sa.Column('artifact_id', sa.BigInteger(), nullable=True),
    sa.Column('check_group', sa.Text(), nullable=False),
    sa.Column('check_name', sa.Text(), nullable=False),
    sa.Column('status', sa.Text(), nullable=False),
    sa.Column('severity', sa.Text(), server_default='INFO', nullable=False),
    sa.Column('rows_total', sa.BigInteger(), nullable=True),
    sa.Column('rows_valid', sa.BigInteger(), nullable=True),
    sa.Column('rows_failed', sa.BigInteger(), nullable=True),
    sa.Column('missing_values_count', sa.BigInteger(), nullable=True),
    sa.Column('duplicate_rows_count', sa.BigInteger(), nullable=True),
    sa.Column('schema_mismatch_count', sa.BigInteger(), nullable=True),
    sa.Column('leakage_issue_count', sa.BigInteger(), nullable=True),
    sa.Column('label_distribution_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('timestamp_coverage_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('details_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('report_path', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("artifact_type IN ('raw_file', 'normalized', 'feature', 'model_ready', 'preprocessing', 'catalog')", name=op.f('ck_data_quality_reports_artifact_type_valid')),
    sa.CheckConstraint("severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')", name=op.f('ck_data_quality_reports_severity_valid')),
    sa.CheckConstraint("status IN ('SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'SKIPPED', 'BLOCKED')", name=op.f('ck_data_quality_reports_status_valid')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_data_quality_reports')),
    sa.UniqueConstraint('report_uid', name=op.f('uq_data_quality_reports_report_uid'))
    )
    op.create_table('datasets',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('slug', sa.Text(), nullable=False),
    sa.Column('branch', sa.Text(), nullable=False),
    sa.Column('role', sa.Text(), nullable=False),
    sa.Column('source_group', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('dataset_version', sa.Text(), nullable=True),
    sa.Column('source_url', sa.Text(), nullable=True),
    sa.Column('license_name', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("branch IN ('dns', 'host', 'network', 'hybrid')", name=op.f('ck_datasets_branch_valid')),
    sa.CheckConstraint("role IN ('TRAIN', 'VALIDATION', 'TEST', 'EXPERIMENTS')", name=op.f('ck_datasets_role_valid')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_datasets')),
    sa.UniqueConstraint('name', 'branch', 'role', name='uq_datasets_name_branch_role'),
    sa.UniqueConstraint('slug', 'branch', 'role', name='uq_datasets_slug_branch_role')
    )
    op.create_table('ingestion_runs',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('run_uid', sa.UUID(), nullable=False),
    sa.Column('root_path', sa.Text(), nullable=False),
    sa.Column('root_path_kind', sa.Text(), nullable=False),
    sa.Column('branch', sa.Text(), nullable=True),
    sa.Column('role', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Text(), server_default='RUNNING', nullable=False),
    sa.Column('files_seen', sa.Integer(), server_default='0', nullable=False),
    sa.Column('files_new', sa.Integer(), server_default='0', nullable=False),
    sa.Column('files_existing', sa.Integer(), server_default='0', nullable=False),
    sa.Column('files_changed', sa.Integer(), server_default='0', nullable=False),
    sa.Column('files_failed', sa.Integer(), server_default='0', nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('report_path', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("branch IS NULL OR branch IN ('dns', 'host', 'network', 'hybrid')", name=op.f('ck_ingestion_runs_branch_valid')),
    sa.CheckConstraint("role IS NULL OR role IN ('TRAIN', 'VALIDATION', 'TEST', 'EXPERIMENTS')", name=op.f('ck_ingestion_runs_role_valid')),
    sa.CheckConstraint("status IN ('RUNNING', 'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'SKIPPED')", name=op.f('ck_ingestion_runs_status_valid')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ingestion_runs')),
    sa.UniqueConstraint('run_uid', name=op.f('uq_ingestion_runs_run_uid'))
    )
    op.create_table('label_mapping_rules',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('rule_uid', sa.Text(), nullable=False),
    sa.Column('rule_name', sa.Text(), nullable=False),
    sa.Column('branch', sa.Text(), nullable=False),
    sa.Column('role', sa.Text(), nullable=True),
    sa.Column('source_format', sa.Text(), nullable=True),
    sa.Column('dataset_name_pattern', sa.Text(), nullable=True),
    sa.Column('file_name_pattern', sa.Text(), nullable=True),
    sa.Column('source_field', sa.Text(), nullable=True),
    sa.Column('source_value_pattern', sa.Text(), nullable=True),
    sa.Column('label_binary', sa.SmallInteger(), nullable=True),
    sa.Column('label_family', sa.Text(), nullable=True),
    sa.Column('label_subtype', sa.Text(), nullable=True),
    sa.Column('label_source', sa.Text(), nullable=False),
    sa.Column('label_status', sa.Text(), nullable=False),
    sa.Column('label_confidence', sa.Numeric(precision=4, scale=3), nullable=True),
    sa.Column('priority', sa.Integer(), server_default='100', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("branch IN ('dns', 'host', 'network', 'hybrid')", name=op.f('ck_label_mapping_rules_branch_valid')),
    sa.CheckConstraint("label_status IN ('explicit_label', 'inferred_label', 'weak_label', 'partial_label', 'unlabeled', 'conflicting_label')", name=op.f('ck_label_mapping_rules_label_status_valid')),
    sa.CheckConstraint("role IS NULL OR role IN ('TRAIN', 'VALIDATION', 'TEST', 'EXPERIMENTS')", name=op.f('ck_label_mapping_rules_role_valid')),
    sa.CheckConstraint('label_binary IS NULL OR label_binary IN (0, 1)', name=op.f('ck_label_mapping_rules_label_binary_valid')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_label_mapping_rules')),
    sa.UniqueConstraint('rule_uid', name=op.f('uq_label_mapping_rules_rule_uid'))
    )
    op.create_table('parser_registry',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parser_name', sa.Text(), nullable=False),
    sa.Column('parser_version', sa.Text(), nullable=False),
    sa.Column('branch', sa.Text(), nullable=False),
    sa.Column('source_format', sa.Text(), nullable=False),
    sa.Column('supported_role', sa.Text(), nullable=True),
    sa.Column('normalized_schema_name', sa.Text(), nullable=False),
    sa.Column('normalized_schema_version', sa.Text(), nullable=False),
    sa.Column('parser_module', sa.Text(), nullable=False),
    sa.Column('parser_class', sa.Text(), nullable=False),
    sa.Column('priority', sa.Integer(), server_default='100', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('supports_streaming', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('requires_external_tools', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('external_tools_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('config_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("branch IN ('dns', 'host', 'network', 'hybrid')", name=op.f('ck_parser_registry_branch_valid')),
    sa.CheckConstraint("supported_role IS NULL OR supported_role IN ('TRAIN', 'VALIDATION', 'TEST', 'EXPERIMENTS')", name=op.f('ck_parser_registry_supported_role_valid')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_parser_registry')),
    sa.UniqueConstraint('parser_name', 'parser_version', 'branch', 'source_format', 'supported_role', name='uq_parser_registry_parser_name_parser_version')
    )
    op.create_table('schema_versions',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('schema_name', sa.Text(), nullable=False),
    sa.Column('schema_version', sa.Text(), nullable=False),
    sa.Column('layer', sa.Text(), nullable=False),
    sa.Column('branch', sa.Text(), nullable=True),
    sa.Column('schema_path', sa.Text(), nullable=True),
    sa.Column('schema_hash_sha256', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('columns_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("branch IS NULL OR branch IN ('dns', 'host', 'network', 'hybrid')", name=op.f('ck_schema_versions_branch_valid')),
    sa.CheckConstraint("layer IN ('normalized', 'features', 'model_ready')", name=op.f('ck_schema_versions_layer_valid')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_schema_versions')),
    sa.UniqueConstraint('schema_name', 'schema_version', 'layer', 'branch', name='uq_schema_versions_schema_name_schema_version')
    )
    op.create_table('dataset_files',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('dataset_id', sa.BigInteger(), nullable=False),
    sa.Column('ingestion_run_id', sa.BigInteger(), nullable=True),
    sa.Column('file_path', sa.Text(), nullable=False),
    sa.Column('relative_path', sa.Text(), nullable=True),
    sa.Column('file_name', sa.Text(), nullable=False),
    sa.Column('file_extension', sa.Text(), nullable=True),
    sa.Column('source_format', sa.Text(), nullable=False),
    sa.Column('mime_type', sa.Text(), nullable=True),
    sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
    sa.Column('file_hash_sha256', sa.Text(), nullable=True),
    sa.Column('file_modified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('role', sa.Text(), nullable=False),
    sa.Column('branch', sa.Text(), nullable=False),
    sa.Column('status', sa.Text(), server_default='REGISTERED', nullable=False),
    sa.Column('parser_hint', sa.Text(), nullable=True),
    sa.Column('has_embedded_label', sa.Boolean(), nullable=True),
    sa.Column('label_source_hint', sa.Text(), nullable=True),
    sa.Column('timestamp_source_hint', sa.Text(), nullable=True),
    sa.Column('encoding_hint', sa.Text(), nullable=True),
    sa.Column('compression_hint', sa.Text(), nullable=True),
    sa.Column('row_count_hint', sa.BigInteger(), nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('first_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("branch IN ('dns', 'host', 'network', 'hybrid')", name=op.f('ck_dataset_files_branch_valid')),
    sa.CheckConstraint("role IN ('TRAIN', 'VALIDATION', 'TEST', 'EXPERIMENTS')", name=op.f('ck_dataset_files_role_valid')),
    sa.CheckConstraint("status IN ('DISCOVERED', 'REGISTERED', 'CHANGED', 'EMPTY_FILE', 'UNSUPPORTED_FORMAT', 'READY_FOR_PARSING', 'PARSED', 'PARTIALLY_PARSED', 'FAILED', 'SKIPPED')", name=op.f('ck_dataset_files_status_valid')),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], name=op.f('fk_dataset_files_dataset_id_datasets')),
    sa.ForeignKeyConstraint(['ingestion_run_id'], ['ingestion_runs.id'], name=op.f('fk_dataset_files_ingestion_run_id_ingestion_runs')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_dataset_files')),
    sa.UniqueConstraint('dataset_id', 'file_path', name='uq_dataset_files_dataset_id_file_path')
    )
    op.create_index('idx_dataset_files_dataset_id', 'dataset_files', ['dataset_id'], unique=False)
    op.create_index('idx_dataset_files_hash', 'dataset_files', ['file_hash_sha256'], unique=False)
    op.create_index('idx_dataset_files_role_branch', 'dataset_files', ['role', 'branch'], unique=False)
    op.create_index('idx_dataset_files_source_format', 'dataset_files', ['source_format'], unique=False)
    op.create_index('idx_dataset_files_status', 'dataset_files', ['status'], unique=False)
    op.create_table('parser_runs',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('run_uid', sa.UUID(), nullable=False),
    sa.Column('file_id', sa.BigInteger(), nullable=False),
    sa.Column('parser_registry_id', sa.BigInteger(), nullable=True),
    sa.Column('parser_name', sa.Text(), nullable=False),
    sa.Column('parser_version', sa.Text(), nullable=False),
    sa.Column('schema_version_id', sa.BigInteger(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Text(), server_default='RUNNING', nullable=False),
    sa.Column('rows_read', sa.BigInteger(), nullable=True),
    sa.Column('rows_parsed', sa.BigInteger(), nullable=True),
    sa.Column('rows_failed', sa.BigInteger(), nullable=True),
    sa.Column('events_emitted', sa.BigInteger(), nullable=True),
    sa.Column('output_parquet_path', sa.Text(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('warning_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('report_path', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("status IN ('RUNNING', 'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'SKIPPED')", name=op.f('ck_parser_runs_status_valid')),
    sa.ForeignKeyConstraint(['file_id'], ['dataset_files.id'], name=op.f('fk_parser_runs_file_id_dataset_files')),
    sa.ForeignKeyConstraint(['parser_registry_id'], ['parser_registry.id'], name=op.f('fk_parser_runs_parser_registry_id_parser_registry')),
    sa.ForeignKeyConstraint(['schema_version_id'], ['schema_versions.id'], name=op.f('fk_parser_runs_schema_version_id_schema_versions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_parser_runs')),
    sa.UniqueConstraint('run_uid', name=op.f('uq_parser_runs_run_uid'))
    )
    op.create_index('idx_parser_runs_file_id', 'parser_runs', ['file_id'], unique=False)
    op.create_index('idx_parser_runs_parser', 'parser_runs', ['parser_name', 'parser_version'], unique=False)
    op.create_index('idx_parser_runs_status', 'parser_runs', ['status'], unique=False)
    op.create_table('normalized_artifacts',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('artifact_uid', sa.UUID(), nullable=False),
    sa.Column('dataset_id', sa.BigInteger(), nullable=False),
    sa.Column('file_id', sa.BigInteger(), nullable=False),
    sa.Column('parser_run_id', sa.BigInteger(), nullable=False),
    sa.Column('schema_version_id', sa.BigInteger(), nullable=True),
    sa.Column('role', sa.Text(), nullable=False),
    sa.Column('branch', sa.Text(), nullable=False),
    sa.Column('modality', sa.Text(), nullable=False),
    sa.Column('source_format', sa.Text(), nullable=False),
    sa.Column('normalized_path', sa.Text(), nullable=False),
    sa.Column('schema_name', sa.Text(), nullable=False),
    sa.Column('schema_version', sa.Text(), nullable=False),
    sa.Column('row_count', sa.BigInteger(), nullable=True),
    sa.Column('event_count', sa.BigInteger(), nullable=True),
    sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
    sa.Column('content_hash_sha256', sa.Text(), nullable=True),
    sa.Column('status', sa.Text(), server_default='SUCCESS', nullable=False),
    sa.Column('null_counts_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('label_distribution_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('min_timestamp', sa.DateTime(timezone=True), nullable=True),
    sa.Column('max_timestamp', sa.DateTime(timezone=True), nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("branch IN ('dns', 'host', 'network', 'hybrid')", name=op.f('ck_normalized_artifacts_branch_valid')),
    sa.CheckConstraint("role IN ('TRAIN', 'VALIDATION', 'TEST', 'EXPERIMENTS')", name=op.f('ck_normalized_artifacts_role_valid')),
    sa.CheckConstraint("status IN ('PENDING', 'RUNNING', 'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'SKIPPED', 'BLOCKED')", name=op.f('ck_normalized_artifacts_status_valid')),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], name=op.f('fk_normalized_artifacts_dataset_id_datasets')),
    sa.ForeignKeyConstraint(['file_id'], ['dataset_files.id'], name=op.f('fk_normalized_artifacts_file_id_dataset_files')),
    sa.ForeignKeyConstraint(['parser_run_id'], ['parser_runs.id'], name=op.f('fk_normalized_artifacts_parser_run_id_parser_runs')),
    sa.ForeignKeyConstraint(['schema_version_id'], ['schema_versions.id'], name=op.f('fk_normalized_artifacts_schema_version_id_schema_versions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_normalized_artifacts')),
    sa.UniqueConstraint('artifact_uid', name=op.f('uq_normalized_artifacts_artifact_uid')),
    sa.UniqueConstraint('parser_run_id', 'normalized_path', name='uq_normalized_artifacts_parser_run_id_normalized_path')
    )
    op.create_table('feature_artifacts',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('artifact_uid', sa.UUID(), nullable=False),
    sa.Column('dataset_id', sa.BigInteger(), nullable=False),
    sa.Column('normalized_artifact_id', sa.BigInteger(), nullable=True),
    sa.Column('role', sa.Text(), nullable=False),
    sa.Column('branch', sa.Text(), nullable=False),
    sa.Column('feature_group', sa.Text(), nullable=False),
    sa.Column('feature_path', sa.Text(), nullable=False),
    sa.Column('feature_schema_name', sa.Text(), nullable=False),
    sa.Column('feature_schema_version', sa.Text(), nullable=False),
    sa.Column('row_count', sa.BigInteger(), nullable=True),
    sa.Column('sample_count', sa.BigInteger(), nullable=True),
    sa.Column('feature_count', sa.Integer(), nullable=True),
    sa.Column('entity_count', sa.BigInteger(), nullable=True),
    sa.Column('window_size_seconds', sa.Integer(), nullable=True),
    sa.Column('window_step_seconds', sa.Integer(), nullable=True),
    sa.Column('label_distribution_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('excluded_columns_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('status', sa.Text(), server_default='SUCCESS', nullable=False),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("branch IN ('dns', 'host', 'network', 'hybrid')", name=op.f('ck_feature_artifacts_branch_valid')),
    sa.CheckConstraint("role IN ('TRAIN', 'VALIDATION', 'TEST', 'EXPERIMENTS')", name=op.f('ck_feature_artifacts_role_valid')),
    sa.CheckConstraint("status IN ('PENDING', 'RUNNING', 'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'SKIPPED', 'BLOCKED')", name=op.f('ck_feature_artifacts_status_valid')),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], name=op.f('fk_feature_artifacts_dataset_id_datasets')),
    sa.ForeignKeyConstraint(['normalized_artifact_id'], ['normalized_artifacts.id'], name=op.f('fk_feature_artifacts_normalized_artifact_id_normalized_artifacts')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_feature_artifacts')),
    sa.UniqueConstraint('artifact_uid', name=op.f('uq_feature_artifacts_artifact_uid'))
    )
    op.create_table('preprocessing_artifacts',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('artifact_uid', sa.UUID(), nullable=False),
    sa.Column('branch', sa.Text(), nullable=False),
    sa.Column('feature_group', sa.Text(), nullable=True),
    sa.Column('preprocessing_type', sa.Text(), nullable=False),
    sa.Column('artifact_path', sa.Text(), nullable=False),
    sa.Column('fitted_on_role', sa.Text(), server_default='TRAIN', nullable=False),
    sa.Column('fitted_on_feature_artifact_id', sa.BigInteger(), nullable=True),
    sa.Column('schema_version', sa.Text(), nullable=False),
    sa.Column('object_version', sa.Text(), nullable=False),
    sa.Column('columns_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('params_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('status', sa.Text(), server_default='SUCCESS', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("branch IN ('dns', 'host', 'network', 'hybrid')", name=op.f('ck_preprocessing_artifacts_branch_valid')),
    sa.CheckConstraint("fitted_on_role = 'TRAIN'", name=op.f('ck_preprocessing_artifacts_fitted_on_role_train')),
    sa.CheckConstraint("status IN ('PENDING', 'RUNNING', 'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'SKIPPED', 'BLOCKED')", name=op.f('ck_preprocessing_artifacts_status_valid')),
    sa.ForeignKeyConstraint(['fitted_on_feature_artifact_id'], ['feature_artifacts.id'], name=op.f('fk_preprocessing_artifacts_fitted_on_feature_artifact_id_feature_artifacts')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_preprocessing_artifacts')),
    sa.UniqueConstraint('artifact_uid', name=op.f('uq_preprocessing_artifacts_artifact_uid'))
    )
    op.create_table('model_ready_artifacts',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('artifact_uid', sa.UUID(), nullable=False),
    sa.Column('feature_artifact_id', sa.BigInteger(), nullable=True),
    sa.Column('preprocessing_artifact_id', sa.BigInteger(), nullable=True),
    sa.Column('role', sa.Text(), nullable=False),
    sa.Column('branch', sa.Text(), nullable=False),
    sa.Column('data_type', sa.Text(), nullable=False),
    sa.Column('artifact_path', sa.Text(), nullable=False),
    sa.Column('schema_name', sa.Text(), nullable=False),
    sa.Column('schema_version', sa.Text(), nullable=False),
    sa.Column('sample_count', sa.BigInteger(), nullable=True),
    sa.Column('feature_count', sa.Integer(), nullable=True),
    sa.Column('label_distribution_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('excluded_columns_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('sequence_length', sa.Integer(), nullable=True),
    sa.Column('status', sa.Text(), server_default='SUCCESS', nullable=False),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("branch IN ('dns', 'host', 'network', 'hybrid')", name=op.f('ck_model_ready_artifacts_branch_valid')),
    sa.CheckConstraint("data_type IN ('X', 'y', 'sequence', 'split_index', 'preprocessing_metadata')", name=op.f('ck_model_ready_artifacts_data_type_valid')),
    sa.CheckConstraint("role IN ('TRAIN', 'VALIDATION', 'TEST', 'EXPERIMENTS')", name=op.f('ck_model_ready_artifacts_role_valid')),
    sa.CheckConstraint("status IN ('PENDING', 'RUNNING', 'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'SKIPPED', 'BLOCKED')", name=op.f('ck_model_ready_artifacts_status_valid')),
    sa.ForeignKeyConstraint(['feature_artifact_id'], ['feature_artifacts.id'], name=op.f('fk_model_ready_artifacts_feature_artifact_id_feature_artifacts')),
    sa.ForeignKeyConstraint(['preprocessing_artifact_id'], ['preprocessing_artifacts.id'], name=op.f('fk_model_ready_artifacts_preprocessing_artifact_id_preprocessing_artifacts')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_model_ready_artifacts')),
    sa.UniqueConstraint('artifact_uid', name=op.f('uq_model_ready_artifacts_artifact_uid'))
    )


def downgrade() -> None:
    """Revert the migration."""
    op.drop_table('model_ready_artifacts')
    op.drop_table('preprocessing_artifacts')
    op.drop_table('feature_artifacts')
    op.drop_table('normalized_artifacts')
    op.drop_index('idx_parser_runs_status', table_name='parser_runs')
    op.drop_index('idx_parser_runs_parser', table_name='parser_runs')
    op.drop_index('idx_parser_runs_file_id', table_name='parser_runs')
    op.drop_table('parser_runs')
    op.drop_index('idx_dataset_files_status', table_name='dataset_files')
    op.drop_index('idx_dataset_files_source_format', table_name='dataset_files')
    op.drop_index('idx_dataset_files_role_branch', table_name='dataset_files')
    op.drop_index('idx_dataset_files_hash', table_name='dataset_files')
    op.drop_index('idx_dataset_files_dataset_id', table_name='dataset_files')
    op.drop_table('dataset_files')
    op.drop_table('schema_versions')
    op.drop_table('parser_registry')
    op.drop_table('label_mapping_rules')
    op.drop_table('ingestion_runs')
    op.drop_table('datasets')
    op.drop_table('data_quality_reports')
