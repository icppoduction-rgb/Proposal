from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from cybersec_platform.contracts.api import ArchiveFileOut, RawFileOut


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str


class UserOut(ORMModel):
    id: str
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    role_name: str
    session_status: str
    created_at: datetime


class DatasetOut(ORMModel):
    id: str
    name: str
    source_type: str
    description: str | None = None
    manifest: dict[str, Any]
    storage_path: str
    normalized_path: str | None = None
    detected_format: str | None = None
    normalization_profile: str | None = None
    normalization_summary: dict[str, Any] = Field(default_factory=dict)
    normalization_report_path: str | None = None
    validation_status: str
    validation_errors: dict[str, Any] = Field(default_factory=dict)
    lineage: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ManagedDatasetCreateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    raw_file_id: str
    feature_set: list[str] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("name is required")
        return normalized

    @field_validator("feature_set")
    @classmethod
    def normalize_feature_set(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if item.strip()]
        if not normalized:
            raise ValueError("feature_set must contain at least one value")
        if len(normalized) != len(set(normalized)):
            raise ValueError("feature_set must be unique")
        return normalized


class ManagedDatasetOut(ORMModel):
    id: str
    raw_file_id: str
    name: str
    file_path: str
    feature_set: list[str] = Field(default_factory=list)
    created_at: datetime


class RawDatasetInspectIn(BaseModel):
    relative_path: str | None = None
    raw_file_id: str | None = None

    @model_validator(mode="after")
    def validate_reference(self) -> "RawDatasetInspectIn":
        if not self.relative_path and not self.raw_file_id:
            raise ValueError("relative_path or raw_file_id is required")
        return self


class RawDatasetInspectOut(BaseModel):
    relative_path: str
    format: str
    normalization_profile: str
    columns: list[str]
    suggested_name: str
    target_columns: list[str]
    quality_warnings: list[str] = Field(default_factory=list)
    supporting_only: bool = False
    compatible_feature_schemas: list[str] = Field(default_factory=list)


class UploadSessionFileIn(BaseModel):
    relative_path: str
    size_bytes: int = Field(ge=1)
    content_type: str | None = None


class UploadSessionCreateIn(BaseModel):
    files: list[UploadSessionFileIn] = Field(min_length=1)


class UploadSessionFileOut(BaseModel):
    file_id: str
    relative_path: str
    size_bytes: int
    uploaded_bytes: int
    content_type: str | None = None
    status: str


class UploadSessionOut(BaseModel):
    session_id: str
    status: str
    created_at: datetime
    total_size_bytes: int
    files: list[UploadSessionFileOut]


class UploadChunkOut(BaseModel):
    session_id: str
    file_id: str
    status: str
    uploaded_bytes: int
    size_bytes: int


class UploadCompleteOut(BaseModel):
    session_id: str
    status: str
    uploaded_files: list[RawFileOut]
    raw_files: list[RawFileOut]


class ArchiveUploadCompleteOut(BaseModel):
    session_id: str
    status: str
    uploaded_archives: list[ArchiveFileOut]
    archives: list[ArchiveFileOut]


class FeatureSchemaOut(ORMModel):
    id: str
    name: str
    version: str
    source_type: str
    definition: dict[str, Any]
    created_at: datetime


class TrainingRunOut(ORMModel):
    id: str
    dataset_id: str
    feature_schema_id: str
    request_payload: dict[str, Any]
    status: str
    metrics: dict[str, Any]
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class ModelArtifactOut(ORMModel):
    id: str
    training_run_id: str
    model_name: str
    model_type: str
    status: str
    metrics: dict[str, Any]
    artifact_path: str
    artifact_metadata: dict[str, Any]
    created_at: datetime


class InferenceJobOut(ORMModel):
    id: str
    model_artifact_id: str
    request_payload: dict[str, Any]
    status: str
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class DetectionResultOut(ORMModel):
    id: str
    inference_job_id: str
    entity_id: str
    score: float
    predicted_label: int
    raw_output: dict[str, Any]
    created_at: datetime


class ExplanationJobOut(ORMModel):
    id: str
    model_artifact_id: str
    detection_result_id: str
    request_payload: dict[str, Any]
    status: str
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ExplanationResultOut(ORMModel):
    id: str
    explanation_job_id: str
    payload: dict[str, Any]
    report_path: str | None = None
    created_at: datetime


class TaskRecordOut(ORMModel):
    id: str
    task_name: str
    object_type: str
    object_id: str
    celery_task_id: str | None = None
    status: str
    detail: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AutoTrainingJobCreateIn(BaseModel):
    archive_ids: list[str] | None = None


class AutoTrainingJobOut(ORMModel):
    id: str
    requested_by_user_id: str | None = None
    source_type: str | None = None
    archive_ids: list[str] = Field(default_factory=list)
    status: str
    progress_percent: float
    current_step: str
    detail: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    dataset_id: str | None = None
    feature_schema_id: str | None = None
    training_run_ids: list[str] = Field(default_factory=list)
    model_artifact_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
