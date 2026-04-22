from __future__ import annotations

from backend.app.services.auth import _db_utc_now
from cybersec_platform.db.models import utcnow


def test_auth_db_timestamp_helper_is_naive_utc():
    value = _db_utc_now()
    assert value.tzinfo is None


def test_shared_model_timestamp_helper_is_naive_utc():
    value = utcnow()
    assert value.tzinfo is None
