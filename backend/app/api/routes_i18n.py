from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from cybersec_platform.db.session import get_settings

router = APIRouter(prefix="/i18n", tags=["i18n"])


def _get_locale_path(language: str) -> Path:
    settings = get_settings()
    locale_paths = {
        "en": Path(settings.language_en_path),
        "ru": Path(settings.language_ru_path),
    }
    target = locale_paths.get(language)
    if target is None:
        raise HTTPException(status_code=404, detail="Locale not found")
    return target


@router.get("/{language}")
async def get_language_pack(language: str) -> JSONResponse:
    locale_path = _get_locale_path(language)
    if not locale_path.exists():
        raise HTTPException(status_code=404, detail="Locale file not found")

    try:
        with locale_path.open("r", encoding="utf-8-sig") as locale_file:
            payload: dict[str, Any] = json.load(locale_file)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Locale file is invalid") from exc

    return JSONResponse(content=payload)
