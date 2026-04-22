FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY shared/python /app/shared/python
COPY services/normalization_data/requirements.txt /app/services/normalization_data/requirements.txt
RUN pip install --no-cache-dir -r /app/services/normalization_data/requirements.txt


COPY services/normalization_data /app/services/normalization_data
COPY app-data /app/app-data

CMD ["celery", "-A", "services.normalization_data.app.worker:celery_app", "worker", "-Q", "normalization", "--loglevel=INFO"]
