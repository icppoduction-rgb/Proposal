FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY shared/python /app/shared/python
COPY services/training_service/requirements.txt /app/services/training_service/requirements.txt
RUN pip install --no-cache-dir -r /app/services/training_service/requirements.txt

COPY services/training_service /app/services/training_service
COPY app-data /app/app-data

CMD ["celery", "-A", "services.training_service.app.worker:celery_app", "worker", "-Q", "training", "--loglevel=INFO"]
