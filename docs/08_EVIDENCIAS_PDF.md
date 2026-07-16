# 08 · Estructura de Evidencias para el PDF Final

Estructura recomendada, página por página, para el PDF consolidado que se entrega. Cada sección indica el título, la explicación, la captura exacta, el comando a ejecutar, el resultado visible y el criterio de rúbrica que respalda.

> Criterios de rúbrica: **(1) Git Flow**, **(2) Persistencia y Hardening**, **(3) Nginx API Gateway**, **(4) CI/CD**.

---

## Página 1 — Portada
- **Título:** Centro Cultural Inteligente — DevOps CRUD Sprint.
- **Explicación:** nombre del curso, integrantes, roles, fecha, enlace al repositorio y URL de producción.
- **Captura:** ninguna (portada).
- **Comando:** —
- **Resultado visible:** datos del equipo.
- **Rúbrica:** general.

## Página 2 — Arquitectura
- **Título:** Arquitectura del sistema.
- **Explicación:** diagrama de capas (Cliente → Nginx → Backend/Frontend → PostgreSQL → EBS).
- **Captura:** el diagrama del README.
- **Comando:** —
- **Resultado visible:** flujo completo.
- **Rúbrica:** (3).

## Página 3 — Repositorio y colaboradores
- **Título:** Repositorio en GitHub.
- **Explicación:** repositorio con los cuatro colaboradores.
- **Captura:** pestaña **Settings → Collaborators**.
- **Comando:** —
- **Resultado visible:** cuatro miembros.
- **Rúbrica:** (1).

## Página 4 — Ramas
- **Título:** Ramas del proyecto.
- **Explicación:** las cuatro ramas `feature/*`.
- **Captura:** vista de **Branches** en GitHub.
- **Comando:** `git branch -a`
- **Resultado visible:** `feature/frontend`, `feature/backend`, `feature/database`, `feature/devops`.
- **Rúbrica:** (1).

## Página 5 — Commits por integrante
- **Título:** Autoría real de los commits.
- **Explicación:** cada integrante con sus commits.
- **Captura:** **Insights → Contributors**.
- **Comando:** `git log --oneline --graph --all`
- **Resultado visible:** commits atribuidos a cada persona.
- **Rúbrica:** (1).

## Página 6 — Pull Requests
- **Título:** Pull Requests y merges.
- **Explicación:** los cuatro PRs mergeados a `main`.
- **Captura:** pestaña **Pull requests (Closed)**.
- **Comando:** `gh pr list --state merged`
- **Resultado visible:** cuatro PRs mergeados.
- **Rúbrica:** (1).

## Página 7 — Protección de `main`
- **Título:** Rama protegida.
- **Explicación:** regla que impide pushes directos.
- **Captura:** **Settings → Branches**.
- **Comando:** —
- **Resultado visible:** regla activa con "Require a pull request".
- **Rúbrica:** (1).

## Página 8 — Servicios en ejecución
- **Título:** Contenedores activos.
- **Explicación:** tres servicios sanos, solo Nginx con puerto público.
- **Captura:** terminal.
- **Comando:** `docker compose ps`
- **Resultado visible:** `healthy` y solo `0.0.0.0:80->80`.
- **Rúbrica:** (2), (3).

## Página 9 — Health check
- **Título:** Estado del servicio.
- **Explicación:** API y BD conectadas.
- **Captura:** terminal o navegador.
- **Comando:** `curl http://localhost/api/health`
- **Resultado visible:** `{"status":"ok",...,"database":"connected"}`.
- **Rúbrica:** (3), (4).

## Página 10 — CRUD en la interfaz
- **Título:** Registro de visitantes.
- **Explicación:** crear/editar/eliminar desde la web.
- **Captura:** navegador con la tabla poblada.
- **Comando:** —
- **Resultado visible:** visitantes listados.
- **Rúbrica:** general.

## Página 11 — Pruebas de API
- **Título:** Suite de pruebas CRUD.
- **Explicación:** todas las pruebas pasan.
- **Captura:** salida del script.
- **Comando:** `bash scripts/test_api.sh http://localhost`
- **Resultado visible:** `9 PASS / 0 FAIL`.
- **Rúbrica:** general.

## Página 12 — Concurrencia
- **Título:** Prueba de concurrencia.
- **Explicación:** 50 peticiones concurrentes.
- **Captura:** salida del script.
- **Comando:** `python scripts/test_concurrency.py --url http://localhost --requests 50 --concurrency 10`
- **Resultado visible:** `50 exitosas / 0 fallidas`.
- **Rúbrica:** (4).

## Página 13 — Persistencia (Chaos)
- **Título:** Persistencia tras `down`/`up`.
- **Explicación:** los datos sobreviven al reinicio.
- **Captura:** salida del script.
- **Comando:** `bash scripts/test_persistence.sh http://localhost`
- **Resultado visible:** `PASS: los datos PERSISTIERON`.
- **Rúbrica:** (2).

## Página 14 — Hardening del 5432
- **Título:** PostgreSQL no expuesta.
- **Explicación:** el puerto 5432 no es accesible.
- **Captura:** salida del script (desde otra máquina) y `docker compose ps`.
- **Comando:** `bash scripts/verify_hardening.sh <IP_PUBLICA_EC2>`
- **Resultado visible:** "el puerto 5432 no es accesible".
- **Rúbrica:** (2).

## Página 15 — Nginx como Gateway
- **Título:** Mismo origen, sin CORS.
- **Explicación:** frontend y API por el mismo host.
- **Captura:** DevTools → Network mostrando URLs relativas `/api/...`.
- **Comando:** —
- **Resultado visible:** peticiones al mismo origen.
- **Rúbrica:** (3).

## Página 16 — Workflow de CI/CD
- **Título:** GitHub Actions.
- **Explicación:** jobs `validate` y `deploy` en verde.
- **Captura:** pestaña **Actions** con el run exitoso.
- **Comando:** —
- **Resultado visible:** ambos jobs verdes.
- **Rúbrica:** (4).

## Página 17 — Despliegue en AWS
- **Título:** App en producción.
- **Explicación:** la app funcionando en la IP pública.
- **Captura:** navegador en `http://<IP_PUBLICA>`.
- **Comando:** `curl http://<IP_PUBLICA>/api/health`
- **Resultado visible:** app y health OK.
- **Rúbrica:** (2), (4).

## Página 18 — Security Group
- **Título:** Reglas de firewall en AWS.
- **Explicación:** 80 abierto, 22 restringido, 5432/5000 cerrados.
- **Captura:** consola EC2 → Security Group.
- **Comando:** —
- **Resultado visible:** reglas correctas.
- **Rúbrica:** (2).

## Página 19 — Logs sin credenciales
- **Título:** Logs del sistema.
- **Explicación:** logs útiles sin exponer secretos.
- **Captura:** salida de logs.
- **Comando:** `docker compose logs --tail=100`
- **Resultado visible:** logs limpios.
- **Rúbrica:** (2).

## Página 20 — Cierre
- **Título:** Checklist de rúbrica.
- **Explicación:** tabla de cumplimiento (ver `10_CHECKLIST_RUBRICA.md`).
- **Captura:** la tabla.
- **Comando:** —
- **Resultado visible:** todos los criterios cubiertos.
- **Rúbrica:** (1)(2)(3)(4).
