from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SourceType(StrEnum):
    HOST = "host"
    NETWORK = "network"


class DatasetFormat(StrEnum):
    CSV = "csv"
    TSV = "tsv"
    PARQUET = "parquet"
    XLSX = "xlsx"
    JSON = "json"
    PCAP = "pcap"
    RES = "res"
    SC = "sc"


class NormalizationProfile(StrEnum):
    DNS2021_TABULAR_FEATURES = "dns2021_tabular_features"
    DNS2021_DOMAIN_LISTS = "dns2021_domain_lists"
    DNS_EXF_STATEFUL = "dns_exf_stateful"
    DNS_EXF_STATELESS = "dns_exf_stateless"
    DNS_PCAP_DNS_FLOW = "dns_pcap_dns_flow"
    GENERIC_TABULAR = "generic_tabular"
    GENERIC_JSON = "generic_json"


class ValidationStatus(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    FAILED = "failed"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ArtifactStatus(StrEnum):
    CANDIDATE = "candidate"
    PROMOTED = "promoted"
    DEPRECATED = "deprecated"


class RoleName(StrEnum):
    ADMIN = "admin"
    ANALYST = "analyst"


class FeatureFamily(StrEnum):
    NETWORK_FLOW = "network_flow"
    DNS = "dns"
    FILE_SYSTEM = "file_system"
    PROCESS = "process"
    PRIVILEGE = "privilege"
    USER_ACTIVITY = "user_activity"
    SEQUENCE = "sequence"


class DatasetManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=120)
    source_type: SourceType
    description: str | None = None
    file_name: str
    required_columns: list[str] = Field(min_length=1)
    label_column: str = "label"
    timestamp_column: str = "event_ts"
    entity_id_column: str = "entity_id"
    attack_stage_column: str | None = "attack_stage"
    feature_families: list[FeatureFamily] = Field(min_length=1)
    mitre_mapping: dict[str, str] = Field(default_factory=dict)
    lineage: dict[str, Any] = Field(default_factory=dict)
    default_label: int | None = Field(default=None, ge=0, le=1)
    default_attack_stage: str | None = None

    @field_validator("required_columns")
    @classmethod
    def ensure_columns_unique(cls, value: list[str]) -> list[str]:
        lowered = [item.lower() for item in value]
        if len(lowered) != len(set(lowered)):
            raise ValueError("required_columns must be unique")
        return value


class CanonicalEventRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    source_type: SourceType
    event_ts: datetime
    label: int = Field(ge=0, le=1)
    attack_stage: str | None = None
    mitre_tactic: str | None = None
    features: dict[str, float | int | str | None] = Field(default_factory=dict)


class NormalizationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_count: int = 0
    dropped_rows: int = 0
    duplicate_rows: int = 0
    missing_values: int = 0
    invalid_values: int = 0
    supporting_only: bool = False
    warnings: list[str] = Field(default_factory=list)
    profile_details: dict[str, Any] = Field(default_factory=dict)


class FeatureSchemaDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    source_type: SourceType
    required_columns: list[str]
    canonical_mappings: dict[str, str]
    feature_families: list[FeatureFamily]
    mitre_tactics: dict[str, str] = Field(default_factory=dict)
    notes: str | None = None


class TrainingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    feature_schema_id: str
    models: list[str] = Field(default_factory=lambda: ["random_forest", "xgboost", "cnn", "lstm", "fusion"])
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    sequence_length: int = Field(default=50, ge=50, le=100)
    sequence_stride: int = Field(default=10, ge=1, le=50)
    notes: str | None = None


class TrainingRunStatus(BaseModel):
    id: str
    status: JobStatus
    metrics: dict[str, float] = Field(default_factory=dict)
    artifact_ids: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


class ModelArtifactDescriptor(BaseModel):
    id: str
    training_run_id: str
    model_name: str
    model_type: str
    status: ArtifactStatus
    metrics: dict[str, float] = Field(default_factory=dict)
    artifact_path: str
    created_at: datetime


class InferenceRecord(BaseModel):
    entity_id: str
    event_ts: datetime
    features: dict[str, float | int | str | None]
    source_type: SourceType


class InferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_artifact_id: str
    records: list[InferenceRecord] = Field(min_length=1)


class DetectionDecision(BaseModel):
    entity_id: str
    score: float = Field(ge=0.0, le=1.0)
    predicted_label: int = Field(ge=0, le=1)
    top_features: list[str] = Field(default_factory=list)
    explanation_job_id: str | None = None


class ExplanationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_artifact_id: str
    detection_result_id: str
    top_k: int = Field(default=10, ge=1, le=50)


class ShapExplanationItem(BaseModel):
    feature: str
    contribution: float


class ShapExplanationPayload(BaseModel):
    model_artifact_id: str
    detection_result_id: str
    generated_at: datetime
    top_positive: list[ShapExplanationItem]
    top_negative: list[ShapExplanationItem]
    summary: str
    model_branch: str | None = None
    feature_family_hints: list[str] = Field(default_factory=list)
    mitre_tactic_hints: list[str] = Field(default_factory=list)
    report_path: str | None = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=16)
    role: RoleName = RoleName.ANALYST
    full_name: str | None = None
    is_active: bool = True


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=16)
    role: RoleName | None = None
    full_name: str | None = None
    is_active: bool | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RawFileOut(BaseModel):
    id: str
    name: str
    path: str
    relative_path: str
    size: int = Field(ge=0)
    format: str
    modified_at: datetime | None = None


class ArchiveFileOut(BaseModel):
    id: str
    name: str
    path: str
    relative_path: str
    size: int = Field(ge=0)
    format: str
    created_at: datetime | None = None


class EditorSessionCreateIn(BaseModel):
    page_size: int = Field(default=50, ge=1, le=200)
    sheet_name: str | None = None


class EditorRowOut(BaseModel):
    row_index: int = Field(ge=0)
    values: dict[str, Any] = Field(default_factory=dict)


class EditorSessionOut(BaseModel):
    session_id: str
    file_name: str
    file_path: str
    dataset_format: str
    read_only: bool = False
    page_size: int = Field(ge=1, le=200)
    total_rows: int = Field(ge=0)
    total_pages: int = Field(ge=0)
    columns: list[str] = Field(default_factory=list)
    available_sheets: list[str] = Field(default_factory=list)
    active_sheet: str | None = None
    deleted_row_count: int = Field(default=0, ge=0)
    deleted_columns: list[str] = Field(default_factory=list)
    pending_cell_count: int = Field(default=0, ge=0)


class EditorPageOut(EditorSessionOut):
    page: int = Field(ge=1)
    rows: list[EditorRowOut] = Field(default_factory=list)


class CellPatch(BaseModel):
    row_index: int = Field(ge=0)
    column: str = Field(min_length=1)
    value: Any = None


class CellPatchIn(BaseModel):
    patches: list[CellPatch] = Field(min_length=1)


class DeleteRowsIn(BaseModel):
    row_indices: list[int] = Field(min_length=1)

    @field_validator("row_indices")
    @classmethod
    def ensure_unique_indices(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("row_indices must be unique")
        return value


class DeleteColumnsIn(BaseModel):
    columns: list[str] = Field(min_length=1)

    @field_validator("columns")
    @classmethod
    def ensure_unique_columns(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value]
        if any(not item for item in normalized):
            raise ValueError("columns must be non-empty")
        if len(normalized) != len(set(normalized)):
            raise ValueError("columns must be unique")
        return normalized


class EditorSaveOut(BaseModel):
    session_id: str
    file_path: str
    size_bytes: int = Field(ge=0)
    modified_at: datetime
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
