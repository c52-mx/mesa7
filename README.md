# Mesa7

Monorepo: `backend/` (Django + DRF + Channels), `mobile/` (Expo), `web/` (KDS y POS, pendiente).

## Desarrollo local

```bash
cp .env.example .env
docker compose up --build        # Postgres, Redis y API en http://localhost:8000
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py test
```

- Health check: `GET /api/health/`
- Admin: `/admin/`
- JWT: `POST /api/auth/token/` y `/api/auth/token/refresh/`

```bash
cd mobile
npm install
npx expo start
```

## Despliegue (Dokploy)

El backend se despliega desde `backend/Dockerfile` (Daphne/ASGI, puerto 8000). Variables requeridas:
`DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`,
`DATABASE_URL`, `REDIS_URL`. Postgres y Redis se crean como servicios en Dokploy.
