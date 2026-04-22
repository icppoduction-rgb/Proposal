FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY shared/python /app/shared/python
COPY services/log_service/requirements.txt /app/services/log_service/requirements.txt
RUN pip install --no-cache-dir -r /app/services/log_service/requirements.txt

COPY services/log_service /app/services/log_service
COPY app-data /app/app-data

CMD ["uvicorn", "services.log_service.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
