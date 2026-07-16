# 11 · Reporte Final de Auditoría

## Centro Cultural Inteligente — DevOps CRUD Sprint

---

## 1. Archivos creados
```text
.github/workflows/deploy.yml
backend/app.py, db.py, validation.py, requirements.txt, Dockerfile
database/schema.sql
frontend/index.html, styles.css, app.js
nginx/nginx.conf
scripts/test_api.sh, test_persistence.sh, test_concurrency.py, verify_hardening.sh
docs/00..11 (12 documentos en español)
docker-compose.yml, .env.example, .gitignore, .gitattributes, README.md, LICENSE
```

## 2. Funcionalidades completadas
- CRUD completo de visitantes (crear, listar, obtener, actualizar, eliminar).
- Health check con estado de la base de datos.
- Paginación y búsqueda.
- Validación, normalización y manejo de errores con códigos HTTP correctos.
- Frontend responsivo con renderizado seguro (anti-XSS).
- Persistencia con bind mount / EBS.
- Aislamiento de red y hardening de contenedores.
- CI/CD con validación y despliegue por SSH.

## 3. Endpoints de la API
| Método | Ruta | Estado |
| ------ | ---- | ------ |
| GET | `/api/health` | ✅ |
| POST | `/api/visitantes` | ✅ |
| GET | `/api/visitantes` | ✅ |
| GET | `/api/visitantes/<id>` | ✅ |
| PUT | `/api/visitantes/<id>` | ✅ |
| DELETE | `/api/visitantes/<id>` | ✅ |

## 4. Controles de seguridad implementados
- Consultas SQL parametrizadas (sin interpolación).
- Credenciales solo por variables de entorno.
- PostgreSQL y backend sin puertos públicos.
- Red privada interna para la base de datos.
- `no-new-privileges`, montajes de solo lectura en Nginx, usuario no root en backend.
- Cabeceras de seguridad y `server_tokens off` en Nginx.
- Límite de tamaño de payload (backend y Nginx).
- Secretos del despliegue en GitHub Secrets.

## 5. Diseño de persistencia
Los datos de PostgreSQL residen en un **bind mount** (`POSTGRES_DATA_PATH`) del host, respaldado por **EBS** en EC2. `docker compose down` elimina contenedores pero conserva los datos. Verificado con `test_persistence.sh` (PASS).

## 6. Diseño de CI/CD
Workflow con dos jobs: `validate` (config de Compose, sintaxis Python, build del backend con `.env` ficticio) y `deploy` (SSH a EC2, `git reset --hard origin/main`, `docker compose up -d --build --remove-orphans`, verificación de `/api/health`). No destructivo con los datos.

## 7. Pruebas ejecutadas (localmente, con Docker)
| Prueba | Comando | Resultado |
| ------ | ------- | --------- |
| Config de Compose | `docker compose config --quiet` | ✅ válido |
| Sintaxis Python | `py_compile` | ✅ OK |
| Build + arranque | `docker compose up -d --build` | ✅ 3 servicios healthy |
| Health | `curl /api/health` | ✅ 200, database connected |
| CRUD + errores | `bash scripts/test_api.sh` | ✅ 9 PASS / 0 FAIL |
| Concurrencia | `test_concurrency.py` (50/10) | ✅ 50 exitosas / 0 fallidas |
| Persistencia | `bash scripts/test_persistence.sh` | ✅ PASS |
| Puertos publicados | `docker compose ps` | ✅ solo `0.0.0.0:80->80` |

## 8. Pruebas NO ejecutadas
- **Verificación remota del puerto 5432** contra la IP pública de EC2 (requiere la instancia y otra máquina). En local, `verify_hardening.sh` marcó 5432 como accesible por un **falso positivo**: la máquina de desarrollo tiene su propio PostgreSQL escuchando en 5432. `docker compose ps` confirma que **nuestro contenedor no publica el 5432**.
- **Despliegue real por GitHub Actions** (requiere repositorio en GitHub, EC2 y secretos).

## 9. Limitaciones conocidas
- El health check del backend queda "degraded/503" si la BD está caída (comportamiento esperado y documentado).
- La búsqueda usa `ILIKE %texto%`, adecuada para el volumen del proyecto (no full-text search).
- No hay autenticación de usuarios (fuera del alcance del taller).

## 10. Pasos manuales pendientes
1. Crear el repositorio en GitHub y añadir a los 4 colaboradores.
2. Cada integrante: configurar su identidad Git, clonar, crear su rama y hacer sus propios commits.
3. Abrir y aprobar los 4 Pull Requests hacia `main`.
4. Activar la protección de la rama `main`.
5. Provisionar la instancia EC2 (Ubuntu + Docker + Git + EBS).
6. Crear el `.env` de producción en el servidor.
7. Configurar los GitHub Secrets (`SERVER_IP`, `SERVER_USER`, `SSH_PRIVATE_KEY`).
8. Ejecutar el primer despliegue y capturar evidencias.

## 11. Comandos para subir a GitHub
```bash
git init
git branch -M main
git add .
git commit -m "chore: initialize project structure"
git remote add origin https://github.com/USUARIO/centro-cultural-inteligente.git
git push -u origin main
```
O con GitHub CLI:
```bash
gh auth login
gh repo create centro-cultural-inteligente --private --source=. --remote=origin --push
```

## 12. Comandos de despliegue en AWS
```bash
ssh -i mi-clave.pem ubuntu@<IP_PUBLICA>
sudo mkdir -p /opt/centro-cultural/app && sudo chown -R $USER:$USER /opt/centro-cultural
cd /opt/centro-cultural/app
git clone https://github.com/USUARIO/centro-cultural-inteligente.git .
cp .env.example .env && nano .env       # POSTGRES_DATA_PATH=/opt/centro-cultural/postgres-data
docker compose up -d --build
docker compose ps
curl --fail http://localhost/api/health
```

## 13. Checklist de GitHub Secrets
- [ ] `SERVER_IP` = IP pública de EC2.
- [ ] `SERVER_USER` = usuario SSH (ej. `ubuntu`).
- [ ] `SSH_PRIVATE_KEY` = clave privada de despliegue completa.

## 14. Checklist de captura de evidencias
Ver `08_EVIDENCIAS_PDF.md` (20 páginas). Prioridad: colaboradores, ramas, PRs, protección de main, `docker compose ps`, health, pruebas, persistencia, hardening remoto, Actions en verde, app en la IP pública, Security Group.

## 15. Porcentaje de cumplimiento de la rúbrica
- **Implementación técnica local:** 100 % (código, arquitectura, pruebas verificadas).
- **Acciones de nube/GitHub pendientes de ejecución manual:** las 4 áreas están **totalmente preparadas y documentadas**; su ejecución depende de credenciales reales del equipo.
- **Estimación global de preparación:** ~90 % completado; el ~10 % restante son acciones manuales inevitables (crear repo real, EC2 real, secretos reales).

## 16. Tabla final de requisitos

| Requisito del prompt | Estado |
| -------------------- | ------ |
| Frontend HTML/CSS/JS con Fetch y rutas relativas | ✅ Completo |
| Backend Flask + Gunicorn + psycopg2, CRUD + health | ✅ Completo |
| Validación, transacciones, parametrización | ✅ Completo |
| PostgreSQL 16 con schema, constraints, índices, trigger | ✅ Completo |
| Persistencia por bind mount / EBS | ✅ Completo |
| Dos redes Docker; privada interna | ✅ Completo |
| 5432 y 5000 no expuestos; solo 80 público | ✅ Completo |
| Health checks y `restart: unless-stopped` | ✅ Completo |
| Hardening (`no-new-privileges`, RO, no root) | ✅ Completo |
| Nginx API Gateway (proxy, cabeceras, seguridad) | ✅ Completo |
| `.env.example`, `.gitignore`, `.gitattributes` | ✅ Completo |
| GitHub Actions (validate + deploy) | ✅ Completo (definido) |
| Scripts de prueba (API, persistencia, concurrencia, hardening) | ✅ Completo |
| Documentación en español (README + 12 docs) | ✅ Completo |
| Validación local (config, build, tests) | ✅ Completo |
| Crear repositorio y ramas en GitHub | ⚙️ Requiere acción manual en GitHub |
| Pull Requests y protección de `main` | ⚙️ Requiere acción manual en GitHub |
| GitHub Secrets | ⚙️ Requiere configuración manual en GitHub |
| Provisión de EC2 y `.env` de producción | ⚙️ Requiere configuración manual en AWS |
| Ejecución real del deploy y evidencias | ⚙️ Requiere configuración manual en AWS/GitHub |
| Verificación remota del puerto 5432 | ⚙️ Requiere otra máquina contra EC2 |
