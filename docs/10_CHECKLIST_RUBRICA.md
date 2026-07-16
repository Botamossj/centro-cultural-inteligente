# 10 · Checklist de Rúbrica (Matriz de Trazabilidad)

Matriz que conecta cada criterio de la rúbrica con su implementación técnica, archivo, evidencia, comando y estado.

Estados: ✅ Completo (verificado localmente) · ⚙️ Requiere configuración manual en AWS/GitHub.

---

## Criterio 1 — Git Flow

| Criterio de rúbrica | Implementación técnica | Archivo | Evidencia | Comando | Estado |
| ------------------- | ---------------------- | ------- | --------- | ------- | ------ |
| Cuatro ramas de feature | Ramas por rol | — | Vista de Branches | `git branch -a` | ⚙️ (crear en GitHub) |
| Sin commits directos a main | Branch protection | Config GitHub | Settings → Branches | — | ⚙️ |
| Integración por PR | Pull Requests | — | Pestaña PRs | `gh pr list --state merged` | ⚙️ |
| Autoría real | Identidad Git por integrante | `06_GUIA_GITHUB_GIT_FLOW.md` | Insights → Contributors | `git log --graph` | ⚙️ |
| Colaboradores | 4 miembros | — | Settings → Collaborators | — | ⚙️ |

## Criterio 2 — Persistencia y Hardening

| Criterio de rúbrica | Implementación técnica | Archivo | Evidencia | Comando | Estado |
| ------------------- | ---------------------- | ------- | --------- | ------- | ------ |
| Datos persistentes | Bind mount host/EBS | `docker-compose.yml` | Datos tras down/up | `bash scripts/test_persistence.sh` | ✅ |
| Sobrevive a `down` | Directorio en el host | `docker-compose.yml` | Script PASS | `docker compose down && up -d` | ✅ |
| PostgreSQL aislada | Red privada interna | `docker-compose.yml` | ps sin 5432 | `docker compose ps` | ✅ |
| 5432 no expuesto | Sin `ports` en database | `docker-compose.yml` | Test remoto | `bash scripts/verify_hardening.sh <IP>` | ✅ (local) / ⚙️ (remoto) |
| 5000 no expuesto | Sin `ports` en backend | `docker-compose.yml` | ps | `docker compose ps` | ✅ |
| Hardening contenedores | `no-new-privileges`, RO, no root | `docker-compose.yml`, `backend/Dockerfile` | Config | `docker compose config` | ✅ |
| Constraints e índices | PK, UNIQUE, CHECK, índices | `database/schema.sql` | `\d visitantes` | `psql -c "\d visitantes"` | ✅ |

## Criterio 3 — Nginx API Gateway

| Criterio de rúbrica | Implementación técnica | Archivo | Evidencia | Comando | Estado |
| ------------------- | ---------------------- | ------- | --------- | ------- | ------ |
| Único puerto público | `80:80` solo en Nginx | `docker-compose.yml` | ps | `docker compose ps` | ✅ |
| Sirve estáticos | `root /usr/share/nginx/html` | `nginx/nginx.conf` | Web carga | `curl -I http://localhost/` | ✅ |
| Proxy `/api/` | `proxy_pass backend:5000` | `nginx/nginx.conf` | Health por proxy | `curl http://localhost/api/health` | ✅ |
| Cabeceras reenviadas | Host, X-Real-IP, X-Forwarded-* | `nginx/nginx.conf` | Config | — | ✅ |
| Cabeceras de seguridad | X-Content-Type-Options, etc. | `nginx/nginx.conf` | `curl -I` | `curl -I http://localhost/` | ✅ |
| Sin CORS (mismo origen) | Frontend + API por Nginx | `nginx/nginx.conf`, `frontend/app.js` | Network DevTools | — | ✅ |
| `server_tokens off` | Oculta versión | `nginx/nginx.conf` | `curl -I` | `curl -I http://localhost/` | ✅ |

## Criterio 4 — Automatización CI/CD

| Criterio de rúbrica | Implementación técnica | Archivo | Evidencia | Comando | Estado |
| ------------------- | ---------------------- | ------- | --------- | ------- | ------ |
| Trigger en `main` | `on: push: branches: [main]` | `.github/workflows/deploy.yml` | Actions | — | ✅ (definido) |
| Job de validación | `docker compose config`, py_compile, build | `.github/workflows/deploy.yml` | Log del job | — | ✅ (definido) |
| Job de deploy vía SSH | SSH a EC2 + compose up | `.github/workflows/deploy.yml` | Log del job | — | ⚙️ (requiere EC2) |
| Secrets | `SERVER_IP`, `SERVER_USER`, `SSH_PRIVATE_KEY` | `.github/workflows/deploy.yml` | Settings → Secrets | `gh secret list` | ⚙️ |
| Verificación de health | `curl --fail /api/health` | `.github/workflows/deploy.yml` | Log del job | — | ✅ (definido) |
| Deploy no destructivo | Sin `rm -rf`/`prune` | `.github/workflows/deploy.yml` | Revisión de código | — | ✅ |

---

## Resumen
- **Completo y verificado localmente:** arquitectura, CRUD, persistencia, hardening de contenedores, Nginx, validación de CI.
- **Requiere acción manual:** crear repo y ramas en GitHub, PRs, protección de `main`, provisión de EC2, GitHub Secrets y ejecución real del deploy.
