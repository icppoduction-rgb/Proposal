from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select

from cybersec_platform.db import OutboxMessage, TaskRecord
from cybersec_platform.db.models import utcnow
from cybersec_platform.db.session import async_session_factory, get_settings
from cybersec_platform.observability import get_request_context, log_event, request_context
from cybersec_platform.tasks import celery_app

logger = logging.getLogger(__name__)


def build_message_headers(
    *,
    object_type: str,
    object_id: str,
    task_record_id: str,
    correlation_id: str | None = None,
) -> dict[str, str]:
    runtime_context = get_request_context()
    effective_correlation_id = correlation_id or runtime_context.get("correlation_id") or str(uuid4())
    return {
        "message_id": str(uuid4()),
        "message_version": "1",
        "correlation_id": effective_correlation_id,
        "idempotency_key": task_record_id,
        "object_type": object_type,
        "object_id": object_id,
        "request_type": str(runtime_context.get("type", "system")),
    }


async def publish_pending_outbox_messages(*, limit: int | None = None, message_ids: list[str] | None = None) -> int:
    settings = get_settings()
    batch_limit = limit or settings.outbox_publish_batch_size
    published_count = 0

    for _ in range(batch_limit):
        async with async_session_factory() as session:
            statement = (
                select(OutboxMessage)
                .where(OutboxMessage.status == "pending", OutboxMessage.available_at <= utcnow())
                .order_by(OutboxMessage.created_at.asc(), OutboxMessage.id.asc())
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            if message_ids:
                statement = statement.where(OutboxMessage.id.in_(message_ids))

            result = await session.execute(statement)
            message = result.scalar_one_or_none()
            if message is None:
                break

            task_record = await session.get(TaskRecord, message.task_record_id) if message.task_record_id else None
            publish_context = {
                "type": "outbox",
                "service": "backend",
                "outbox_message_id": message.id,
                "task_record_id": message.task_record_id,
                "correlation_id": message.headers.get("correlation_id"),
            }
            with request_context(publish_context):
                try:
                    celery_result = celery_app.send_task(
                        message.topic,
                        kwargs=dict(message.payload),
                        queue=message.queue_name,
                        headers=dict(message.headers),
                    )
                    message.status = "published"
                    message.published_at = utcnow()
                    message.last_error = None
                    message.attempts += 1
                    if task_record is not None:
                        task_record.celery_task_id = celery_result.id
                        task_record.detail = {
                            **(task_record.detail or {}),
                            "queue": message.queue_name,
                            "publish_state": "published",
                            "outbox_message_id": message.id,
                            "correlation_id": message.headers.get("correlation_id"),
                            "message_id": message.headers.get("message_id"),
                        }
                    await session.commit()
                    published_count += 1
                    log_event(
                        logger,
                        logging.INFO,
                        "Outbox message published",
                        function="publish_pending_outbox_messages",
                        outbox_message_id=message.id,
                        task_record_id=message.task_record_id,
                        celery_task_id=celery_result.id,
                        topic=message.topic,
                        queue=message.queue_name,
                    )
                except Exception as exc:
                    message.attempts += 1
                    message.last_error = str(exc)
                    delay_seconds = min(60, 2 ** min(message.attempts, 6))
                    if message.attempts >= settings.outbox_max_attempts:
                        message.status = "failed"
                    message.available_at = utcnow() + timedelta(seconds=delay_seconds)
                    if task_record is not None:
                        task_record.detail = {
                            **(task_record.detail or {}),
                            "queue": message.queue_name,
                            "publish_state": message.status,
                            "outbox_message_id": message.id,
                            "correlation_id": message.headers.get("correlation_id"),
                            "last_publish_error": str(exc),
                        }
                    await session.commit()
                    logger.exception(
                        "Outbox publish attempt failed",
                        extra={
                            "function": "publish_pending_outbox_messages",
                            "error": {"type": type(exc).__name__, "message": str(exc)},
                            "outbox_message_id": message.id,
                            "task_record_id": message.task_record_id,
                            "attempts": message.attempts,
                        },
                    )

    return published_count


async def run_outbox_publisher(stop_event: asyncio.Event) -> None:
    settings = get_settings()
    poll_interval_seconds = max(settings.outbox_poll_interval_ms, 100) / 1000

    while not stop_event.is_set():
        try:
            await publish_pending_outbox_messages()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception(
                "Outbox publisher loop failed",
                extra={"function": "run_outbox_publisher", "error": {"type": type(exc).__name__, "message": str(exc)}},
            )

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=poll_interval_seconds)
        except TimeoutError:
            continue
