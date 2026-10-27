FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN DJANGO_DEBUG=1 python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py ensure_superuser && if [ \"$SEED_DEMO\" = \"1\" ]; then python manage.py seed_demo; fi && if [ \"$SEED_CAFECIN\" = \"1\" ]; then python manage.py seed_cafecin; fi && python manage.py ensure_staff && python manage.py ensure_owner && daphne -b 0.0.0.0 -p 8000 config.asgi:application"]
