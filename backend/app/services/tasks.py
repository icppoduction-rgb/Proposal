from __future__ import annotations

import logging
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.outbox import build_message_headers, publish_pending_outbox_messages
from cybersec_platform.contracts.api import JobStatus
from cybersec_platform.db import OutboxMessage, TaskRecord
from cybersec_platform.observability import get_request_context, log_event, observed

logger = logging.getLogger(__name__)


@observed("dispatch_task")
async def dispatch_task(
    session: AsyncSession,
    *,
    task_name: str,
    object_type: str,
    object_id: str,
    queue: str,
    kwargs: dict,
) -> TaskRecord:
    """Persist a task tracking row and an outbox message in the caller transaction."""

    correlation_id = str(get_request_context().get("correlation_id") or uuid4())
    record = TaskRecord(
        task_name=task_name,
        object_type=object_type,
        object_id=object_id,
        status=JobStatus.PENDING.value,
        detail={"queue": queue, "publish_state": "pending", "correlation_id": correlation_id},
    )
    session.add(record)
    await session.flush()

    outbox_message = OutboxMessage(
        topic=task_name,
        queue_name=queue,
        payload=dict(kwargs),
        headers=build_message_headers(
            object_type=object_type,
            object_id=object_id,
            task_record_id=record.id,
            correlation_id=correlation_id,
        ),
        object_type=object_type,
        object_id=object_id,
        task_record_id=record.id,
    )
    session.add(outbox_message)
    await session.flush()
    record.detail = {
        **(record.detail or {}),
        "outbox_message_id": outbox_message.id,
        "message_id": outbox_message.headers.get("message_id"),
    }
    log_event(
        logger,
        logging.INFO,
        "Background task staged",
        function="dispatch_task",
        object_type=object_type,
        object_id=object_id,
        queue=queue,
        outbox_message_id=outbox_message.id,
        correlation_id=correlation_id,
        celery_task_id=record.celery_task_id,
        task_name=task_name,
    )
    return record


@observed("trigger_task_publish")
async def trigger_task_publish(session: AsyncSession, record: TaskRecord) -> TaskRecord:
    """Best-effort publish for a committed task record."""

    outbox_message_id = (record.detail or {}).get("outbox_message_id")
    if not outbox_message_id:
        return record

    try:
        await publish_pending_outbox_messages(limit=1, message_ids=[outbox_message_id])
    except Exception as exc:
        logger.exception(
            "Outbox publish trigger failed",
            extra={"function": "trigger_task_publish", "error": {"type": type(exc).__name__, "message": str(exc)}},
        )

    await session.refresh(record)
    return record
