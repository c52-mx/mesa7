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
- Auth: `POST /api/auth/register/`, `/api/auth/login/`, `/api/auth/token/refresh/`
- Si el usuario pertenece a varios negocios, enviar el header `X-Tenant: <slug>`
- Pedidos: `/api/orders/`, KDS: `/api/kds/orders/?branch=<id>`, push: `POST /api/devices/`
- WebSocket (`/ws/orders/<id>/` cliente, `/ws/kds/<branch_id>/` personal): al conectar, el primer
  mensaje es `{"type": "auth", "token": "<access JWT>", "tenant": "<slug>"}`; el servidor responde
  `{"type": "ready"}` y luego envía `{"type": "order.update", "order": {...}}`.
  Cierres: 4401 (token inválido o sin auth en 10 s), 4403 (sin permiso).
- Demo: `docker compose exec backend python manage.py seed_demo`

```bash
cd mobile
npm install
npx expo start
```

Para probar en el teléfono: instala **Expo Go**, conecta teléfono y computadora a la misma wifi y escanea el QR.
La app usa la API de staging por defecto; para usar tu backend local copia `mobile/.env.example` a
`mobile/.env.local` y pon `EXPO_PUBLIC_API_URL=http://<IP de tu computadora>:8000`
(y agrega esa IP a `DJANGO_ALLOWED_HOSTS`). `EXPO_PUBLIC_TENANT` elige el negocio (por defecto `demo`).

Marca blanca: el color principal, el secundario y el logo viven en el tenant (admin de Django) y la app
los lee de `GET /api/tenants/<slug>/`; el resto del tema se deriva de esos dos colores.

## Despliegue (Dokploy)

El backend se despliega desde `backend/Dockerfile` (Daphne/ASGI, puerto 8000). Variables requeridas:
`DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`,
`DATABASE_URL`, `REDIS_URL`. Postgres y Redis se crean como servicios en Dokploy.
