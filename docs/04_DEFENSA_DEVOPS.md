# 04 · Defensa del Rol DevOps

## 1. Nombre del rol
**Integrante D — DevOps Architect.** Rama `feature/devops`.

## 2. Archivos bajo mi responsabilidad
- `nginx/nginx.conf` — reverse proxy / API Gateway.
- `.github/workflows/deploy.yml` — CI/CD.
- `docker-compose.yml` — orquestación (coordinado con el equipo).
- Configuración de GitHub Secrets y protección de rama.
- Guía de despliegue en AWS.

## 3. Objetivo de mi capa
Integrar todos los servicios en un único punto de entrada seguro (Nginx:80), orquestarlos con Docker Compose y automatizar el despliegue a AWS EC2 con validación previa mediante GitHub Actions.

## 4. Explicación detallada (fácil de memorizar)
- **Nginx** escucha en el 80, sirve el frontend y reenvía `/api/` al backend → mismo origen, **sin CORS**.
- **Docker Compose** define tres servicios, dos redes y health checks; solo Nginx publica puerto.
- **GitHub Actions**: al mergear a `main`, el job `validate` comprueba la configuración y el job `deploy` entra por **SSH** a EC2, actualiza el código y levanta los contenedores, verificando `/api/health`.
- Los datos de PostgreSQL **nunca** se borran en el despliegue.

## 5. Flujo de una petición / despliegue a través de mi capa
Petición: `Cliente → Nginx:80 → (/ estáticos | /api → backend:5000)`.
Despliegue: `merge a main → Actions validate → Actions deploy (SSH) → git reset --hard origin/main → docker compose up -d --build → curl health`.

## 6. Fragmentos importantes

Proxy de Nginx (mismo origen):
```nginx
location /api/ {
    proxy_pass http://backend_api;      # upstream backend:5000
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Despliegue seguro (no destructivo) en `deploy.yml`:
```bash
cd /opt/centro-cultural/app
git fetch --all && git reset --hard origin/main
docker compose up -d --build --remove-orphans   # NO borra postgres-data
curl --fail --silent http://localhost/api/health
```

## 7. Comandos que debo conocer
```bash
docker compose config --quiet
docker compose up -d --build --remove-orphans
docker compose ps
docker compose logs --tail=100
curl --fail http://localhost/api/health
gh secret set SERVER_IP        # configurar secretos
```

## 8. Salidas esperadas
- `docker compose ps` → 3 servicios `healthy`, solo Nginx con `0.0.0.0:80->80`.
- Workflow en GitHub → ambos jobs en verde.
- `curl /api/health` → 200.

## 9. Fallos comunes
- `502 Bad Gateway`: el backend aún no está sano.
- Falla el SSH: secreto `SSH_PRIVATE_KEY` mal configurado o Security Group cierra el 22.
- El deploy no arranca: `.env` ausente en el servidor.

## 10. Cómo diagnosticar fallos
- Revisar los logs del workflow en la pestaña **Actions** de GitHub.
- En el servidor: `docker compose logs --tail=100`.
- Probar SSH manualmente: `ssh -i clave usuario@IP`.

## 11. Cómo recuperarme
- Reejecutar el workflow desde GitHub (**Re-run jobs**).
- En el servidor: `docker compose up -d --build`.
- Rollback: `git reset --hard <commit_anterior>` y redeploy (los datos persisten).

## 12. Consideraciones de seguridad
- Solo el puerto 80 es público; 5000 y 5432 quedan internos.
- Secretos (IP, usuario, clave SSH) en **GitHub Secrets**, nunca en el repo.
- Cabeceras de seguridad y `server_tokens off` en Nginx.
- Comandos de deploy **no destructivos** (nunca `rm -rf` ni `prune --volumes`).
- Puerto 22 restringido a IPs de confianza en el Security Group.

## 13. Consideraciones de rendimiento
- `upstream` de Nginx con keepalive hacia el backend.
- Timeouts de proxy razonables (5s conexión, 30s lectura).
- `client_max_body_size 1m` para limitar payloads.
- Health checks para reinicios automáticos.

## 14. Diez preguntas probables del profesor
1. ¿Qué es un reverse proxy / API Gateway?
2. ¿Cómo evita CORS esta arquitectura?
3. ¿Por qué solo Nginx publica un puerto?
4. ¿Cómo funciona tu pipeline de CI/CD?
5. ¿Cómo proteges las credenciales del despliegue?
6. ¿Cómo garantizas que el deploy no borre los datos?
7. ¿Qué hace el job de validación?
8. ¿Cómo se conecta GitHub Actions a EC2?
9. ¿Cómo verificas que el despliegue funcionó?
10. ¿Cómo haces rollback?

## 15. Diez respuestas modelo
1. Es un servidor que recibe todas las peticiones y las distribuye: sirve los estáticos y reenvía `/api/` al backend. Actúa como única puerta de entrada (API Gateway).
2. Porque el frontend y la API comparten el mismo origen (`http://servidor/` y `http://servidor/api/`). El navegador no hace una petición entre orígenes distintos, así que no aplica CORS.
3. Para minimizar la superficie de ataque: el backend y la base de datos quedan en redes internas, inaccesibles desde Internet; solo Nginx expone el 80.
4. Al hacer push a `main`, el job `validate` valida `docker compose config`, la sintaxis de Python y construye la imagen; si pasa, el job `deploy` entra por SSH a EC2, actualiza el código y levanta los contenedores verificando el health.
5. Uso GitHub Secrets: `SERVER_IP`, `SERVER_USER` y `SSH_PRIVATE_KEY`. Nunca están en el repositorio y no se imprimen en los logs.
6. El deploy solo hace `git reset --hard` y `docker compose up -d --build`. Nunca borro el directorio `postgres-data` ni uso `prune --volumes`. Los datos están en un bind mount independiente de los contenedores.
7. Crea un `.env` con valores ficticios, corre `docker compose config --quiet`, compila los `.py` con `py_compile` y construye la imagen del backend. Si algo falla, se detiene antes de tocar el servidor.
8. Con SSH: guardo la clave privada del secreto en un archivo, añado el host a `known_hosts` con `ssh-keyscan` y ejecuto los comandos remotos con `ssh usuario@IP 'bash -s'`.
9. Tras levantar, hago `curl --fail http://localhost/api/health` con reintentos; si no responde 200, muestro los logs y el workflow falla.
10. Hago `git reset --hard <commit_estable>` en el servidor y vuelvo a levantar; como los datos persisten en el bind mount, no se pierde información.

## 16. Guion de defensa oral (2 minutos)
"Soy el responsable de DevOps. Diseñé la arquitectura de infraestructura: Nginx es el único punto de entrada, escucha en el puerto 80, sirve el frontend y reenvía todo lo que empieza con `/api/` al backend. Como frontend y API comparten origen, no hace falta configurar CORS. Orquesté los tres servicios con Docker Compose usando dos redes: una pública para Nginx y el backend, y una privada e interna para el backend y PostgreSQL, que nunca expone su puerto. Automaticé el despliegue con GitHub Actions: cuando algo se mergea a `main`, primero se valida la configuración y la sintaxis, y si todo pasa, un segundo job entra por SSH a la instancia EC2, actualiza el código y levanta los contenedores, verificando el health check. El despliegue es no destructivo: nunca borra los datos de PostgreSQL. Las credenciales del servidor están en GitHub Secrets."

## 17. Guion de defensa oral extendido (5 minutos)
Añade al de 2 minutos:
- **Nginx en detalle**: `upstream`, cabeceras reenviadas (Host, X-Real-IP, X-Forwarded-For/Proto), timeouts, `client_max_body_size`, cabeceras de seguridad y `server_tokens off`.
- **Redes**: pública vs privada interna; solo Nginx publica el 80.
- **CI/CD paso a paso**: trigger en `main`, job `validate`, job `deploy` con SSH, verificación de health, muestra de logs si falla.
- **Secretos**: `SERVER_IP`, `SERVER_USER`, `SSH_PRIVATE_KEY`; cómo configurarlos (ver `05_GUIA_DESPLIEGUE_AWS.md`).
- **Seguridad de la nube**: Security Group con 80 abierto, 22 restringido, 5432/5000 cerrados.
- **Rollback y persistencia**: reset a commit estable, datos intactos.
- Cierra con la relación entre capas (sección 20).

## 18. Checklist de demostración en vivo
- [ ] Mostrar `docker compose ps`: 3 servicios sanos, solo Nginx con puerto público.
- [ ] `curl http://localhost/` (frontend) y `curl http://localhost/api/health` (API) por el mismo origen.
- [ ] Enseñar el workflow en GitHub → Actions (jobs en verde).
- [ ] Mostrar los GitHub Secrets configurados (sin revelar valores).
- [ ] Hacer un cambio pequeño en una rama, PR, merge y ver el deploy automático.
- [ ] Mostrar que el deploy no borra `postgres-data`.

## 19. Lo que NUNCA debo decir mal
- **NO** digo que uso Kubernetes o Terraform: uso **Docker Compose**.
- **NO** digo que el backend/BD tienen puerto público: solo **Nginx**.
- **NO** digo que el deploy borra y recrea los datos: es **no destructivo**.
- **NO** pongo la IP o la clave SSH en el repo: van en **GitHub Secrets**.
- **NO** configuro CORS: la arquitectura de mismo origen lo hace innecesario.

## 20. Relación con las otras tres capas
- **Frontend**: le doy el mismo origen que la API sirviendo sus estáticos y proxying `/api/`.
- **Backend**: reenvío `/api/` a Gunicorn; no expongo su puerto; lo despliego con Compose.
- **Base de datos**: la coloco en una red privada interna y respaldo su persistencia con el bind mount/EBS; el deploy jamás borra sus datos.
