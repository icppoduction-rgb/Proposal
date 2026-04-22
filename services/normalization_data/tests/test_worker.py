from __future__ import annotations

import asyncio

from cybersec_platform.contracts.api import JobStatus, ValidationStatus
from cybersec_platform.ml.normalization import UnsupportedDatasetFormatError
from services.normalization_data.app import worker


class _FakeDataset:
    """EN: Minimal dataset stub used to exercise worker error handling.
    RU: Минимальный stub датасета для проверки обработки ошибок воркером.
    """

    def __init__(self) -> None:
        self.id = "dataset-1"
        self.storage_path = "broken.unsupported"
        self.manifest = {
            "name": "demo-dataset",
            "source_type": "network",
            "file_name": "broken.unsupported",
            "required_columns": ["feature_a"],
            "label_column": "label",
            "timestamp_column": "event_ts",
            "entity_id_column": "entity_id",
            "feature_families": ["network_flow"],
            "mitre_mapping": {},
            "lineage": {"source": "test"},
        }
        self.validation_status = ValidationStatus.PENDING.value
        self.validation_errors = {}
        self.normalized_path = "should-be-cleared.csv"
        self.detected_format = None
        self.normalization_profile = None
        self.normalization_summary = {}
        self.normalization_report_path = None


class _FakeTaskRecord:
    """EN: Minimal task stub capturing status updates from the worker.
    RU: Минимальный stub task-записи, фиксирующий обновления статуса от воркера.
    """

    def __init__(self) -> None:
        self.status = JobStatus.PENDING.value
        self.detail = {}


class _FakeScalarResult:
    """EN: Scalar-result stub that mimics SQLAlchemy's result API.
    RU: Stub scalar-result, имитирующий API результата SQLAlchemy.
    """

    def __init__(self, task_record: _FakeTaskRecord) -> None:
        self._task_record = task_record

    def scalars(self) -> "_FakeScalarResult":
        return self

    def first(self) -> _FakeTaskRecord:
        return self._task_record


class _FakeSession:
    """EN: Async-session stub exposing only the methods used by the worker.
    RU: Stub асинхронной сессии, предоставляющий только методы, используемые воркером.
    """

    def __init__(self, dataset: _FakeDataset, task_record: _FakeTaskRecord) -> None:
        self._dataset = dataset
        self._task_record = task_record
        self.committed = False

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def get(self, model, object_id: str):
        return self._dataset if object_id == self._dataset.id else None

    async def execute(self, statement):
        return _FakeScalarResult(self._task_record)

    async def commit(self) -> None:
        self.committed = True


class _FailingEngine:
    """EN: Engine stub that always raises an unsupported-format error.
    RU: Stub движка, который всегда поднимает ошибку неподдерживаемого формата.
    """

    def validate_and_normalize(self, *args, **kwargs):
        raise UnsupportedDatasetFormatError("Unsupported dataset format: .unsupported")


class _FakeSettings:
    """EN: Settings stub carrying only paths required by the worker.
    RU: Stub настроек, содержащий только пути, необходимые воркеру.
    """

    normalized_data_path = "./tmp/normalized"
    reports_path = "./tmp/reports"


def test_validate_dataset_marks_failure_for_unsupported_format(monkeypatch):
    dataset = _FakeDataset()
    task_record = _FakeTaskRecord()
    fake_session = _FakeSession(dataset, task_record)

    monkeypatch.setattr(worker, "async_session_factory", lambda: fake_session)
    monkeypatch.setattr(worker, "get_settings", lambda: _FakeSettings())
    monkeypatch.setattr(worker, "NormalizationEngine", _FailingEngine)

    asyncio.run(worker._validate_dataset(dataset.id))

    assert fake_session.committed is True
    assert dataset.validation_status == ValidationStatus.FAILED.value
    assert dataset.normalized_path is None
    assert dataset.validation_errors["error"] == "Unsupported dataset format: .unsupported"
    assert task_record.status == JobStatus.FAILED.value
    assert task_record.detail["error"] == "Unsupported dataset format: .unsupported"
