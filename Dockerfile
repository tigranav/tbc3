FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir flask psycopg2-binary celery redis

ENV FLASK_APP=app:create_app
EXPOSE 5000

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]
