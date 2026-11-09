FROM python:3.11-slim

ARG GITHUB_SHA=development

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus-multiproc \
    GITHUB_SHA=${GITHUB_SHA}

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir gunicorn
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "main:app"]
