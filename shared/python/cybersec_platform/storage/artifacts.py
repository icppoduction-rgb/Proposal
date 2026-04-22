from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

from cybersec_platform.db.session import get_settings


class ArtifactStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.models_dir = Path(settings.models_path)
        self.reports_dir = Path(settings.reports_path)
        self.explanations_dir = Path(settings.explanations_path)
        self.normalized_dir = Path(settings.normalized_data_path)
        self.raw_dir = Path(settings.raw_data_path)
        self.archives_dir = Path(settings.archive_data_path)
        self.tmp_dir = Path(settings.tmp_path)
        for path in (
            self.models_dir,
            self.reports_dir,
            self.explanations_dir,
            self.normalized_dir,
            self.raw_dir,
            self.archives_dir,
            self.tmp_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def save_model(self, file_name: str, payload: Any) -> str:
        target = self.models_dir / file_name
        joblib.dump(payload, target)
        return str(target)

    def load_model(self, path: str) -> Any:
        return joblib.load(path)

    def save_json_report(self, subdir: str, file_name: str, payload: dict[str, Any]) -> str:
        target_dir = self.reports_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / file_name
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(target)

    def save_explanation(self, file_name: str, payload: dict[str, Any]) -> str:
        target = self.explanations_dir / file_name
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(target)
