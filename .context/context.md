# AutoERP — Backend Context

## Descripción del Proyecto

**AutoERP** es un sistema ERP (Enterprise Resource Planning) especializado para **talleres automotrices**. Permite gestionar de forma centralizada clientes, vehículos, órdenes de servicio, citas, empleados y horarios, con soporte para notificaciones vía WhatsApp (Meta API) y correo electrónico (Brevo). El sistema es **multi-tenant**: cada entidad de negocio está aislada por `company_id`.

El backend expone una **REST API** construida con **FastAPI**, consumida por un frontend React/Vite desplegado en Vercel. La autenticación está delegada a **Supabase Auth** (JWT), con una capa local que mapea el `supabase_uid` a un usuario interno.

---

## Stack Tecnológico

| Componente          | Tecnología / Versión                       |
|---------------------|--------------------------------------------|
| Lenguaje            | Python (3.10+, detectado por `zoneinfo`)   |
| Framework Web       | **FastAPI** `0.116.1`                      |
| Servidor ASGI       | **Uvicorn** `0.35.0` + **uvloop** `0.21.0`|
| ORM                 | **SQLAlchemy** `2.0.43`                    |
| Migraciones DB      | **Alembic** `1.16.5`                       |
| Base de Datos       | **PostgreSQL** (driver: `psycopg2-binary 2.9.10`) |
| Validación          | **Pydantic** `2.11.7` + `pydantic_core 2.33.2` |
| Autenticación       | **Supabase Auth** (JWT via **PyJWT** `2.8.0`, algoritmos HS256 / ES256) |
| Hash de contraseñas | **bcrypt** `4.3.0` + **passlib** `1.7.4`  |
| HTTP client         | **httpx** `0.28.1` (llamadas async a Meta API / Brevo) |
| WebSockets          | **websockets** `15.0.1` (integrado en FastAPI) |
| Variables de entorno| **python-dotenv** `1.1.1`                  |
| Despliegue          | **Vercel** (`@vercel/python`)              |
| Frontend (CORS)     | `http://localhost:5173`, `https://autoerp-fe.vercel.app` |

---

## Estructura de Directorios

```
BE/
├── api/                        # Paquete principal de la aplicación
│   ├── main.py                 # Punto de entrada FastAPI, registro de routers
│   ├── database.py             # Modelos SQLAlchemy + configuración de sesión
│   ├── auth.py                 # Router /auth — login con contraseña local
│   ├── auth_deps.py            # Dependencia get_current_user (validación JWT Supabase)
│   ├── hashing.py              # Utilidades bcrypt: hash y verify_password
│   ├── users.py                # Router /users — CRUD de usuarios internos
│   ├── customers.py            # Router /customers — CRUD de clientes
│   ├── contacts.py             # Router /contacts — contactos de clientes empresa
│   ├── employees.py            # Router /employees — CRUD de empleados y posiciones
│   ├── vehicles.py             # Router /vehicles — CRUD de vehículos y catálogos
│   ├── orders.py               # Router /orders — órdenes de servicio, carrocería, inventario
│   ├── appointments.py         # Router /appointments — citas y notificaciones
│   ├── schedules.py            # Router /schedules — horarios semanales y excepciones
│   ├── settings.py             # Router /settings — configuración de la empresa (stub)
│   ├── notifications.py        # Helpers async: envío WhatsApp (Meta) y email (Brevo)
│   ├── whatsapp.py             # Router /whatsapp — Embedded Signup, webhook Meta, chat
│   ├── websocket.py            # Router WebSocket /ws/chat/{company_id} — push en tiempo real
│   └── schemas/
│       └── user.py             # Todos los esquemas Pydantic (Request / Response)
├── migrations/                 # Alembic: env.py, versions/
├── .env                        # Variables de entorno (no commitear)
├── alembic.ini                 # Configuración de Alembic
├── requirements.txt            # Dependencias Python fijadas
├── vercel.json                 # Configuración de despliegue en Vercel
└── start.sh                    # Script de arranque local
```

---

## Módulos y Responsabilidades

### `main.py` — Núcleo de la aplicación
- Instancia `FastAPI` con título "AutoERP API" versión `1.0.0`.
- Configura `CORSMiddleware` para los orígenes permitidos.
- Registra todos los routers con su prefijo y tag correspondiente.

### `database.py` — Capa de datos
- Define el `engine` de SQLAlchemy usando `DATABASE_URL` desde variables de entorno.
- Declara todos los modelos ORM (tablas PostgreSQL).
- Provee la función `get_db()` como dependencia de inyección de sesión.

### `auth.py` + `auth_deps.py` — Autenticación
- **`auth.py`**: Login con `username/password` (hasheado con bcrypt). Devuelve lista de permisos. ⚠️ Sin JWT propio aún (retorna permisos como lista de strings).
- **`auth_deps.py`**: Dependencia `get_current_user` que valida tokens JWT de Supabase (HS256 en dev, ES256 vía JWKS en producción) y retorna el objeto `User` local mapeado por `supabase_uid`.

### `orders.py` — Órdenes de servicio (módulo más extenso)
Incluye endpoints para:
- CRUD de órdenes (`/orders/`)
- Extra-info configurable por orden (`/orders/extra-info/`)
- Checklist de carrocería con coordenadas JSONB (`/orders/bodywork-details/`)
- Catálogo de tipos de detalle de carrocería (`/orders/bodywork-detail-types/`)
- Tipos e ítems de inventario configurable (`/orders/inventory-types/`, `/orders/inventory-items/`)
- Datos de inventario por orden (`/orders/inventory-data/`)

### `appointments.py` — Citas
- CRUD de citas con validación de fecha futura.
- Soporte para clientes temporales (campos `temp_*`) para citas sin cliente registrado.
- Envío de confirmaciones por WhatsApp (template Meta) y correo (Brevo) de forma asíncrona.
- Endpoints públicos para que clientes confirmen/cancelen vía link.

### `whatsapp.py` — Integración WhatsApp Business
- **Embedded Signup**: recibe el código de OAuth de Meta y obtiene credenciales por compañía.
- **Webhook**: recibe mensajes entrantes/actualizaciones de estado de Meta y los persiste. Difunde eventos en tiempo real por WebSocket.
- **Chat**: lista conversaciones y mensajes; permite enviar mensajes salientes.
- Soporte para modo mock/desarrollo (tokens ficticios).

### `websocket.py` — Tiempo real
- `ConnectionManager` multi-tenant: mantiene un mapa `company_id → [WebSocket]`.
- Endpoint `ws://host/ws/chat/{company_id}` para que el frontend reciba eventos push (nuevos mensajes, cambios de estado).

### `notifications.py` — Notificaciones
- `send_whatsapp_confirmation`: envía template `nueva_cita_confirmacion` vía Meta Graph API v22.0.
- `send_email_confirmation_brevo`: envía correo HTML con detalles de la cita vía Brevo SMTP API.

### `schedules.py` — Horarios de empleados
- Bloques recurrentes semanales (`day_of_week`, `start_time`, `end_time`).
- Excepciones puntuales por fecha (`ScheduleOverride`).

---

## Variables de Entorno Relevantes

| Variable                | Descripción                                              |
|-------------------------|----------------------------------------------------------|
| `DATABASE_URL`          | URL de conexión PostgreSQL                               |
| `SUPABASE_JWT_SECRET`   | Secreto para validar JWTs HS256 en desarrollo local      |
| `SUPABASE_URL`          | URL del proyecto Supabase (para JWKS en producción)      |
| `WHATSAPP_VERIFY_TOKEN` | Token de verificación del webhook de Meta                |
| `META_APP_ID`           | App ID de Meta (para Embedded Signup)                    |
| `META_APP_SECRET`       | App Secret de Meta                                       |
| `META_TOKEN`            | Token de acceso fallback para notificaciones             |
| `META_PHONE_ID`         | Phone Number ID fallback                                 |
| `META_TEST_PHONE_NUMBER`| Teléfono de prueba (sandbox de Meta)                     |
| `BREVO_API_KEY`         | API Key de Brevo para envío de correos                   |
| `BREVO_SENDER_EMAIL`    | Email remitente de Brevo                                 |
| `BREVO_SENDER_NAME`     | Nombre del remitente de Brevo                            |
| `FRONTEND_URL`          | URL del frontend (para links en emails)                  |
