FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
  && apt-get install -y gcc libpq-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV SECRET_KEY="django-insecure-ymgz-3#l#u_9f!%iw@b@=x#35p-mf-fa^evnvo@wi@7jjow&9n"

ENV CELERY_BROKER_URL="redis://redis:6379/0"

ENV CELERY_RESULT_BACKEND="redis://redis:6379/0"


RUN mkdir -p /app/staticfiles && chmod -R 755 /app/staticfiles


EXPOSE 8000

CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]
