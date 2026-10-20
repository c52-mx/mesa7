# Guion de demo — Cafecín (≈ 15 min)

Objetivo: que el cliente viva el ciclo completo de la **app de lealtad y pedidos**, de la compra al canje, y se lleve la idea de que **todo lo configura él** desde el admin.

## Antes de la reunión (30 min antes)

1. **Staging arriba:** abre `http://31.220.60.177:8010/api/health/` → debe responder `{"status":"ok"}`.
2. **Datos de Cafecín:** el negocio `cafecin` se carga solo al desplegar (variable `SEED_CAFECIN=1`).
3. **Empezar limpio:** en la terminal del contenedor `mesa7-backend` de Dokploy:
   ```bash
   python manage.py reset_demo --tenant cafecin --yes
   ```
   Borra pedidos y puntos de Cafecín; conserva usuarios, menú y configuración.
4. **Dos teléfonos** (o uno que alterne):
   - **Cliente:** Expo Go o el APK. Cuenta nueva con un correo de prueba (se registra en vivo) o una ya creada.
   - **Caja:** la misma app con la cuenta del personal (`caja.cafecin@example.com`; la contraseña la guardó quien configuró el servidor). Al entrar ve las pestañas **Pedidos** y **Caja** en lugar de las del cliente.
5. **Admin abierto** en una pestaña del navegador (`/admin/`) con sesión iniciada.
6. Teléfonos con **brillo alto, sin modo ahorro de batería** y con el sonido/vibración activos.

## Recorrido

### 1. Primera impresión (1 min)
- Abre la app: pantalla de arranque con el **logo y el nombre** de Cafecín; colores de la marca.
- Mensaje: *"Es su app, con su marca. Los colores, el logo y el nombre se cambian desde el admin, sin tocar código."*

### 2. Registro y pedido (4 min) — teléfono del cliente
1. **Regístrate** (nombre, correo, contraseña con el ojito para ver lo que escribes).
2. **Inicio:** saludo con el nombre, promociones, "Disponible en sucursal" y la tarjeta de puntos en 0.
3. **Ordena → Ordena ahora.** Muestra **Destacados**, la búsqueda y las categorías.
4. Abre **Gloria** (el café de la casa): elige **Grande** y **leche de avena** (grupos obligatorios), agrega una **nota** ("bien caliente") y súbele la cantidad.
5. Agrega también una **concha** (sabor y "¿lo calentamos?").
6. **Carrito** (siempre visible con su contador): revisa, elige **Pagar en el mostrador** y **Hacer pedido**.
   - Para que alcance el primer premio, que el pedido pase de **$250** (3 Gloria grandes con avena ≈ $303 → 30 puntos).

### 3. La cocina (3 min) — teléfono de caja
1. Pestaña **Pedidos:** el pedido aparece **en vivo** (vibra) con cliente, opciones, la nota resaltada y el **semáforo** por tiempo.
2. **Preparar** → en el teléfono del cliente salta el aviso *"Tu pedido está en preparación"* (aunque esté en otra pantalla).
3. **Listo** → *"¡Tu pedido está listo! Pasa a recogerlo"*.
4. **Cobrar $303** y **Entregado**.
- Mensaje: *"El cliente sigue su pedido en vivo y el equipo trabaja con un tablero simple."*

### 4. Lealtad (4 min)
1. Teléfono del cliente → **Mi tarjeta:** ya tiene **30 puntos**, la barra de avance y la recompensa de 25 desbloqueada. Muestra el **QR**.
2. Teléfono de caja → **Caja → escanear:** lee el QR, muestra nombre, puntos y recompensas.
3. **Canjear** "Café americano de cortesía" → descuenta 25; el cliente ve el movimiento en su tarjeta.
4. **Compra en mostrador:** escribe un monto (por ejemplo $87.50) → **suma 8 puntos** a quien paga sin usar la app.
- Mensaje: *"Funciona aunque el cliente no pida por la app: en caja sumas y canjeas con el QR."*

### 5. Es suyo: el admin (2 min)
Desde `/admin/`, en vivo:
- **Cambiar un precio o agregar un producto** y verlo en la app al recargar.
- **Opciones del producto:** "Grupos de opciones" (tamaños, leches, extras con precio) y asignarlos a productos.
- **Promociones del Inicio:** agregar un banner nuevo.
- **Lealtad:** pesos por punto y recompensas; y el interruptor **`loyalty_enabled`** del negocio (si lo apagan, desaparecen la tarjeta y los puntos). Demuéstralo y vuélvelo a encender.

## Qué decir que **todavía no está** (con honestidad)
- **Pago en línea con tarjeta:** hoy se paga en el mostrador. Se integra con Mercado Pago o Stripe en la fase de pagos.
- **Avisos con la app cerrada (push):** hoy los avisos llegan con la app abierta; el push real requiere la app instalada con un build propio.
- **Dominio y HTTPS:** el servidor de pruebas va por IP; para las tiendas de apps hará falta un dominio.
- **Fotos reales de los productos** y logo final: se cargan desde el admin cuando los tengan.
- **Apps en App Store / Google Play:** el APK es para probar y dar retroalimentación.
- **QR de la tarjeta:** es fijo en esta versión; después puede cambiar cada minuto contra capturas de pantalla.

## Preguntas para la retroalimentación
1. ¿El pedido y la personalización (tamaño, leche, notas) reflejan cómo piden sus clientes?
2. ¿Los puntos, hitos y premios son los que ofrecerían? ¿Cuánto equivale un punto?
3. ¿Quién cobra en caja: celular o tablet? ¿Les sirve el tablero de pedidos como está?
4. ¿Qué falta para que empiecen a usarlo en una sucursal?
5. ¿Cobrarían en la app con tarjeta desde el inicio o primero en mostrador?

## Si algo falla en vivo
- **El teléfono no carga:** revisa que `…:8010/api/health/` responda; si no, el servidor está reiniciándose (espera 1 min).
- **No aparece el pedido en Pedidos:** baja para refrescar o cambia de pestaña y regresa (se actualiza solo cada 15 s).
- **El QR no se lee:** escribe el código de 12 dígitos de la tarjeta en "Caja".
- **Quieres repetir la demo:** repite el paso 3 de "Antes de la reunión".
