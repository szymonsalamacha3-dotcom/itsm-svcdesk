# ai-generated: 90% - Docker runtime for Python 3.13 FastAPI service; required by Lab 1 compose and core build checks
FROM python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90

WORKDIR /app

RUN apt-get update \
    && apt-get install --only-upgrade -y zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && pip uninstall -y pip

COPY src/ /app/src/
COPY tests/ /app/tests/
COPY fixtures/ /app/fixtures/
RUN mkdir -p /data
ENV SVCDESK_DB=/data/svcdesk.db
ENV SVCDESK_TEST_CLOCK="1"

EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
