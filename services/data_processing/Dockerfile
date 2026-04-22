FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY shared/python /app/shared/python
COPY services/data_processing/requirements.txt /app/services/data_processing/requirements.txt
RUN pip install --no-cache-dir -r /app/services/data_processing/requirements.txt

COPY services/data_processing /app/services/data_processing
COPY app-data /app/app-data

CMD ["uvicorn", "services.data_processing.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
