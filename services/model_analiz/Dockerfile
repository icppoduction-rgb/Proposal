FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY shared/python /app/shared/python
COPY services/model_analiz/requirements.txt /app/services/model_analiz/requirements.txt
RUN pip install --no-cache-dir -r /app/services/model_analiz/requirements.txt

COPY services/model_analiz /app/services/model_analiz
COPY app-data /app/app-data

CMD ["uvicorn", "services.model_analiz.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
