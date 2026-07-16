# 09 · Preguntas y Respuestas de Defensa

Banco de preguntas probables del profesor con respuestas precisas, alineadas con la implementación real. Más de 40 preguntas divididas por tema.

---

## Git Flow
**1. ¿Por qué nadie hace commits directos a `main`?**
Para garantizar revisión y trazabilidad. `main` está protegida y solo admite cambios vía Pull Request aprobado.

**2. ¿Cómo se demuestra la autoría real de cada integrante?**
En **Insights → Contributors** y con `git log`, cada commit está firmado con el correo de la cuenta de GitHub de su autor.

**3. ¿Cómo integran el trabajo de las cuatro ramas?**
Cada rama `feature/*` abre un PR hacia `main`; otro integrante lo revisa y aprueba, y se mergea desde la interfaz de GitHub.

**4. ¿Cómo resuelven un conflicto de merge?**
`git merge origin/main` en la rama, se editan las secciones marcadas, `git add` y `git commit`, luego `git push`.

**5. ¿Cómo evitan pushes directos a `main`?**
Con branch protection: "Require a pull request before merging" y "Do not allow bypassing".

## Frontend
**6. ¿Por qué rutas relativas y no una IP?**
Porque frontend y API comparten origen vía Nginx; el mismo código sirve en local y en AWS sin cambios.

**7. ¿Cómo previenen XSS?**
Renderizando con `textContent` y `createElement`, nunca `innerHTML` con datos del usuario.

**8. ¿Cómo refrescan la tabla sin recargar?**
Tras cada operación llaman a `cargarVisitantes()` que hace `GET` y reconstruye el `<tbody>`.

**9. ¿Qué framework de frontend usan?**
Ninguno: HTML5, CSS3 y JavaScript puro con Fetch API.

## Backend
**10. ¿Cómo evitan la inyección SQL?**
Con consultas parametrizadas (`execute(sql, params)`); nunca se concatena la entrada del usuario.

**11. ¿Por qué Gunicorn?**
Es un servidor WSGI de producción con múltiples workers/threads; el servidor de Flask es solo para desarrollo.

**12. ¿Cómo manejan transacciones?**
Un context manager hace `commit` en éxito, `rollback` en error y cierra siempre cursor y conexión.

**13. ¿Qué códigos HTTP devuelven?**
200, 201, 204, 400, 404, 409, 500 y 503 según el caso.

**14. ¿Cómo funciona la paginación?**
Parámetros `page` y `limit` (por defecto 1 y 50, máximo 100) con `LIMIT/OFFSET` y metadatos de total.

**15. ¿Dónde están las credenciales?**
En variables de entorno leídas con `os.environ`, provistas por el `.env`; nunca en el código.

## PostgreSQL
**16. ¿Qué constraints tiene la tabla?**
PRIMARY KEY (`id`), UNIQUE (`correo`) y CHECK (`categoria`).

**17. ¿Cómo se inicializa el esquema?**
`schema.sql` se monta en `/docker-entrypoint-initdb.d/` y se ejecuta en el primer arranque (datadir vacío).

**18. ¿Cómo se actualiza `fecha_actualizacion`?**
Con un trigger `BEFORE UPDATE` y también desde el backend.

**19. ¿Qué índices crearon y por qué?**
En `fecha_registro` (orden), `nombre` y `categoria` (búsqueda/filtrado).

## Docker
**20. ¿Qué es Docker Compose?**
Una herramienta para definir y orquestar múltiples contenedores con un solo archivo declarativo.

**21. ¿Qué hacen los health checks?**
Indican si un contenedor está sano; permiten `depends_on: service_healthy` y reinicios automáticos.

**22. ¿Qué es `restart: unless-stopped`?**
Reinicia el contenedor si falla o al reiniciar el host, salvo que se detenga manualmente.

**23. ¿Por qué imágenes Alpine/slim?**
Son mínimas: menos peso, menos superficie de ataque y arranque más rápido.

## Nginx
**24. ¿Qué es un reverse proxy / API Gateway?**
Un servidor que recibe todas las peticiones y las distribuye: sirve estáticos y reenvía `/api/` al backend.

**25. ¿Qué cabeceras reenvía Nginx al backend?**
Host, X-Real-IP, X-Forwarded-For y X-Forwarded-Proto.

**26. ¿Qué cabeceras de seguridad añade?**
X-Content-Type-Options, X-Frame-Options y Referrer-Policy; además `server_tokens off`.

## Seguridad
**27. ¿Cómo protegen las credenciales del despliegue?**
En GitHub Secrets (`SERVER_IP`, `SERVER_USER`, `SSH_PRIVATE_KEY`), nunca en el repo ni en logs.

**28. ¿Por qué el backend no expone puerto?**
Para que solo Nginx pueda alcanzarlo; reduce la superficie de ataque.

**29. ¿Qué es `no-new-privileges`?**
Impide que los procesos del contenedor escalen privilegios.

**30. ¿El backend corre como root?**
No, corre como un usuario no root (`appuser`) definido en el Dockerfile.

## Persistencia
**31. ¿Dónde viven los datos?**
En un bind mount del host (`POSTGRES_DATA_PATH`) respaldado por EBS, no dentro del contenedor.

**32. ¿Por qué sobreviven a `docker compose down`?**
Porque `down` elimina contenedores, pero el directorio del host con los datos permanece.

**33. Diferencia entre volumen y bind mount.**
Un volumen lo gestiona Docker; un bind mount enlaza una carpeta concreta del host. Aquí usamos bind mount.

**34. ¿Cómo respaldan los datos en AWS?**
Con snapshots de EBS o copiando el directorio de datos.

## AWS
**35. ¿Qué es EBS?**
Elastic Block Store: el disco de bloques persistente asociado a la instancia EC2.

**36. ¿Qué puertos abren en el Security Group?**
80 público, 22 restringido a IPs de confianza; 5432 y 5000 cerrados.

**37. ¿Usan base de datos gestionada?**
No, PostgreSQL corre en un contenedor autogestionado con persistencia en EBS.

## GitHub Actions
**38. ¿Cuándo se dispara el workflow?**
Solo con push a `main` (tras aprobar un PR).

**39. ¿Qué hace el job de validación?**
Crea un `.env` ficticio, valida `docker compose config`, compila el Python y construye la imagen del backend.

**40. ¿Cómo despliega el segundo job?**
Entra por SSH a EC2, hace `git reset --hard origin/main`, `docker compose up -d --build --remove-orphans` y verifica el health.

**41. ¿El despliegue borra los datos?**
No. Nunca ejecuta `rm -rf`, `prune --volumes` ni toca `postgres-data`.

## Chaos Engineering
**42. ¿Qué pasa si matan un contenedor?**
`restart: unless-stopped` lo reinicia; el backend reintenta la conexión a la BD.

**43. ¿Qué pasa si la BD no está lista al arrancar?**
`wait_for_db` reintenta y `depends_on: service_healthy` espera; mientras, `/api/health` devuelve 503.

**44. ¿Qué demuestra la prueba de persistencia?**
Que tras `down` + `up` los visitantes creados siguen existiendo (script con resultado PASS).

## Concurrencia
**45. ¿Cómo soportan varias peticiones a la vez?**
Gunicorn con 3 workers × 2 threads; validado con 50 peticiones concurrentes sin fallos.

**46. ¿Qué pasa con dos registros del mismo correo en paralelo?**
La constraint UNIQUE garantiza que solo uno se guarda; el otro recibe 409.

**47. ¿Cómo evitan cargar toda la tabla en memoria?**
Con paginación (`LIMIT/OFFSET`, máximo 100 por página).
