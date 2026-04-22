from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_platform.contracts.api import JobStatus
from cybersec_platform.db import TaskRecord
from cybersec_platform.observability import log_event, observed
from cybersec_platform.tasks import celery_app

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
    """EN: Queue a background task and persist a tracking record in the database.
    RU: Ставит фоновую задачу в очередь и сохраняет tracking-record в базе данных.

    Args:
        session: EN: Active database session. RU: Активная сессия базы данных.
        task_name: EN: Celery task name. RU: Имя Celery-задачи.
        object_type: EN: Domain object type associated with the task. RU: Тип доменного объекта, связанного с задачей.
        object_id: EN: Domain object identifier. RU: Идентификатор доменного объекта.
        queue: EN: Queue name used for dispatch. RU: Имя очереди для отправки.
        kwargs: EN: Serialized Celery keyword arguments. RU: Сериализованные keyword-аргументы Celery.

        Returns:
            EN: Persisted task tracking record.
            RU: Сохранённая tracking-запись задачи.

        Side Effects:
            EN: Sends a Celery message and writes a DB row.
            RU: Отправляет сообщение Celery и записывает строку в БД.

        Raises:
            EN: Propagates broker or database errors unchanged.
            RU: Пробрасывает ошибки брокера или базы данных без изменений.
    """

    task = celery_app.send_task(task_name, kwargs=kwargs, queue=queue)
    record = TaskRecord(
        task_name=task_name,
        object_type=object_type,
        object_id=object_id,
        celery_task_id=task.id,
        status=JobStatus.PENDING.value,
        detail={"queue": queue},
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    log_event(
        logger,
        logging.INFO,
        "Background task dispatched",
        function="dispatch_task",
        object_type=object_type,
        object_id=object_id,
        queue=queue,
        celery_task_id=task.id,
        task_name=task_name,
    )
    return record
