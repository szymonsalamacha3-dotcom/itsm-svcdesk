# ai-generated: 90% - Docker runtime for Python 3.13 FastAPI service; required by Lab 1 compose and core build checks
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src/ /app/src/
COPY tests/ /app/tests/
RUN mkdir -p /data
ENV SVCDESK_DB=/data/svcdesk.db
ENV SVCDESK_TEST_CLOCK="1"

EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
