# Centro Cultural Inteligente

Aplicación web para el **registro de visitantes de eventos especiales** del Centro Cultural Inteligente. Proyecto académico del curso **Computación en la Nube y Orquestación de Entornos Virtuales** (Taller Grupal: DevOps CRUD Sprint).

Permite registrar, listar en tiempo real, editar y eliminar visitantes. Los datos se guardan en PostgreSQL de forma **persistente**, toda la aplicación se expone únicamente a través de **Nginx en el puerto 80**, y el despliegue a **AWS EC2** es automático mediante **GitHub Actions**.

---

## Descripción del proyecto

Un visitante se registra con **nombre**, **correo** y **categoría de entrada** (General, Estudiante, Adulto mayor, VIP). El frontend (HTML/CSS/JS puro) consume una API REST en Flask a través de rutas relativas `/api/...`. Nginx actúa como *API Gateway*: sirve los archivos estáticos y enruta `/api/` hacia el backend. PostgreSQL queda aislada en una red privada de Docker, sin exponer el puerto 5432.

## Arquitectura

```text
Cliente de Internet
      |
      v
AWS EC2  ─  Puerto público 80
      |
      v
   Nginx (API Gateway)
   |                 |
   |  /api/*         |  /  y estáticos
   v                 v
Flask + Gunicorn   HTML / CSS / JS
   |
   v
PostgreSQL (red privada, sin puerto público)
   |
   v
Bind mount en el host  ->  disco AWS EBS (persistencia)
```

- **public_network**: `nginx` y `backend`.
- **private_network** (`internal: true`): `backend` y `database`.
- Solo `nginx` publica un puerto (`80:80`).

## Características principales

- CRUD completo de visitantes (crear, listar, obtener, actualizar, eliminar).
- Health check `/api/health` con estado de la base de datos.
- Paginación y búsqueda en el listado.
- Validación de datos y manejo de errores con códigos HTTP correctos.
- Renderizado seguro en el frontend (prevención de XSS con `textContent`).
- Persistencia de datos ante `docker compose down` y recreación de contenedores.
- Aislamiento de red y hardening de contenedores.
- CI/CD automático a EC2 vía SSH tras cada merge a `main`.

## Stack tecnológico

| Capa | Tecnología |
| ---- | ---------- |
| Frontend | HTML5, CSS3, JavaScript (Fetch API) |
| Backend | Python 3.12, Flask, Gunicorn, psycopg2 |
| Base de datos | PostgreSQL 16 Alpine |
| Reverse proxy / API Gateway | Nginx Alpine |
| Orquestación | Docker Compose |
| CI/CD | GitHub Actions |
| Nube | AWS EC2 + EBS |
| Despliegue | SSH desde GitHub Actions |

## Estructura de carpetas

```text
centro-cultural-inteligente/
├── .github/workflows/deploy.yml   # CI/CD
├── backend/                       # API Flask (app.py, db.py, validation.py, Dockerfile)
├── database/schema.sql            # Esquema PostgreSQL
├── frontend/                      # index.html, styles.css, app.js
├── nginx/nginx.conf               # Configuración del API Gateway
├── scripts/                       # Pruebas (API, persistencia, concurrencia, hardening)
├── docs/                          # Documentación y defensas por rol
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .gitattributes
├── README.md
└── LICENSE
```

## Requisitos locales

- Docker Engine 24+ y Docker Compose v2.
- (Opcional) Python 3.12 y bash para ejecutar los scripts de prueba.

## Configuración de entorno

Copia la plantilla y edita los valores:

```bash
cp .env.example .env
```

Para desarrollo local, ajusta `POSTGRES_DATA_PATH=./postgres-data` y define una contraseña. **Nunca subas el archivo `.env` real** (está en `.gitignore`).

| Variable | Descripción |
| -------- | ----------- |
| `DB_NAME` | Nombre de la base de datos |
| `DB_USER` | Usuario de la base de datos |
| `DB_PASSWORD` | Contraseña (secreta) |
| `DB_HOST` | Host de la BD (por defecto `database`) |
| `DB_PORT` | Puerto interno de la BD (`5432`) |
| `POSTGRES_DATA_PATH` | Ruta del bind mount de datos |
| `APP_ENV` | Entorno de la aplicación |

## Ejecución local

```bash
docker compose up -d --build
docker compose ps
```

Abre `http://localhost` en el navegador.

## Endpoints de la API

| Método | Ruta | Descripción | Códigos |
| ------ | ---- | ----------- | ------- |
| GET | `/api/health` | Estado del servicio y la BD | 200, 503 |
| POST | `/api/visitantes` | Crear visitante | 201, 400, 409 |
| GET | `/api/visitantes` | Listar (paginado + búsqueda) | 200 |
| GET | `/api/visitantes/<id>` | Obtener uno | 200, 404 |
| PUT | `/api/visitantes/<id>` | Actualizar | 200, 400, 404, 409 |
| DELETE | `/api/visitantes/<id>` | Eliminar | 204, 404 |

Parámetros del listado: `?page=1&limit=50&search=texto` (límite máximo 100).

## Comandos de Docker útiles

```bash
docker compose config --quiet        # Validar configuración
docker compose up -d --build         # Levantar
docker compose ps                    # Estado
docker compose logs --tail=100       # Logs
docker compose down                  # Detener (los datos persisten)
```

## Comandos de prueba

```bash
bash scripts/test_api.sh http://localhost
bash scripts/test_persistence.sh http://localhost
python scripts/test_concurrency.py --url http://localhost --requests 50 --concurrency 10
bash scripts/verify_hardening.sh <IP_PUBLICA_EC2>   # ejecutar desde otra máquina
```

## Despliegue en AWS (resumen)

1. Crear instancia EC2 (Ubuntu) con un volumen EBS.
2. Instalar Docker, Docker Compose y Git.
3. Clonar el repositorio en `/opt/centro-cultural/app`.
4. Crear `.env` con `POSTGRES_DATA_PATH=/opt/centro-cultural/postgres-data`.
5. `docker compose up -d --build`.
6. Configurar el Security Group: abrir 80, restringir 22, cerrar 5432 y 5000.

Guía completa: [`docs/05_GUIA_DESPLIEGUE_AWS.md`](docs/05_GUIA_DESPLIEGUE_AWS.md).

## GitHub Actions (resumen)

El workflow `.github/workflows/deploy.yml` se ejecuta al hacer push a `main`:

1. **validate**: crea un `.env` de prueba, valida `docker compose config`, la sintaxis de Python y construye la imagen del backend.
2. **deploy**: se conecta por SSH a EC2, actualiza el código, ejecuta `docker compose up -d --build --remove-orphans` y verifica `/api/health`.

Secrets necesarios: `SERVER_IP`, `SERVER_USER`, `SSH_PRIVATE_KEY`.

## Seguridad

- Credenciales solo por variables de entorno; nunca en el código.
- Consultas SQL 100 % parametrizadas.
- PostgreSQL sin puerto público; backend sin puerto público.
- Cabeceras de seguridad en Nginx y `server_tokens off`.
- `no-new-privileges` y montajes de solo lectura donde aplica.
- Contenedor de backend ejecutado como usuario no root.

## Persistencia

Los datos de PostgreSQL viven en un **bind mount** del host (`POSTGRES_DATA_PATH`), respaldado por **EBS** en EC2. Por eso sobreviven a `docker compose down`, a la recreación de contenedores y a un redeploy. Detalle en [`docs/03_DEFENSA_DATABASE_SRE.md`](docs/03_DEFENSA_DATABASE_SRE.md).

## Solución de problemas

| Problema | Causa probable | Solución |
| -------- | -------------- | -------- |
| `/api/health` devuelve 503 | La BD aún no arranca | Esperar; revisar `docker compose logs database` |
| `502 Bad Gateway` en `/api/` | Backend no listo | `docker compose logs backend` |
| Datos perdidos tras `down` | `POSTGRES_DATA_PATH` mal configurado | Verificar el bind mount en `.env` |
| Scripts `.sh` fallan con `\r` | Finales de línea CRLF | Ya resuelto con `.gitattributes` (LF) |

## Roles del equipo

| Integrante | Rol | Rama |
| ---------- | --- | ---- |
| A | Frontend | `feature/frontend` |
| B | Backend | `feature/backend` |
| C | Base de datos / SRE | `feature/database` |
| D | DevOps | `feature/devops` |

## Enlaces

- Repositorio: `https://github.com/USUARIO/centro-cultural-inteligente` *(reemplazar)*
- URL de producción: `http://<IP_PUBLICA_EC2>` *(reemplazar)*

## Licencia

MIT. Ver [`LICENSE`](LICENSE).
