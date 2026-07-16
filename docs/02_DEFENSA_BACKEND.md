# 02 · Defensa del Rol Backend

## 1. Nombre del rol
**Integrante B — Backend Developer.** Rama `feature/backend`.

## 2. Archivos bajo mi responsabilidad
- `backend/app.py` — endpoints REST y manejo de errores.
- `backend/db.py` — conexión, reintentos y transacciones.
- `backend/validation.py` — validación y normalización de datos.
- `backend/requirements.txt` — dependencias.
- `backend/Dockerfile` — imagen del backend con Gunicorn.

## 3. Objetivo de mi capa
Exponer una API REST robusta para el CRUD de visitantes, con validación, consultas parametrizadas, transacciones, health check y códigos HTTP correctos, servida en producción con Gunicorn.

## 4. Explicación detallada (fácil de memorizar)
- Flask define 6 endpoints (`health` + CRUD).
- Cada petición se valida en `validation.py` (campos, longitud, formato de correo, categoría permitida, id entero).
- `db.py` abre la conexión con credenciales de **variables de entorno**, ejecuta SQL **parametrizado** dentro de una transacción (`commit`/`rollback`) y cierra siempre cursor y conexión.
- Errores conocidos → códigos claros: 400 (validación), 404 (no existe), 409 (correo duplicado), 503 (BD caída), 500 (error interno).
- En producción manda **Gunicorn** (3 workers × 2 threads), nunca el servidor de desarrollo de Flask.

## 5. Flujo de una petición a través de mi capa
1. Nginx reenvía `POST /api/visitantes` a Gunicorn:5000.
2. Flask llama a `validar_visitante(request.get_json())`.
3. `db.db_cursor(commit=True)` abre conexión + cursor.
4. `INSERT ... RETURNING` parametrizado.
5. Éxito → `commit` y `201`; `UniqueViolation` → `409`; excepción → `rollback` y `500`.

## 6. Fragmentos de código importantes

Consulta parametrizada (nunca concatenación):
```python
cur.execute(
    "INSERT INTO visitantes (nombre, correo, categoria) VALUES (%s, %s, %s) RETURNING id, ...;",
    (datos["nombre"], datos["correo"], datos["categoria"]),
)
```

Transacción segura con context manager:
```python
@contextmanager
def db_cursor(commit=False):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
```

Credenciales por entorno:
```python
"password": os.environ.get("DB_PASSWORD", "")
```

## 7. Comandos que debo conocer
```bash
docker compose logs backend --tail=100
docker compose exec backend python -c "import db; print(db.ping())"
curl --fail http://localhost/api/health
python -m py_compile backend/app.py backend/db.py backend/validation.py
```

## 8. Salidas esperadas
- `GET /api/health` → `{"status":"ok","service":"centro-cultural-api","database":"connected"}` (200).
- `POST` válido → 201 con el visitante.
- `GET /api/visitantes` → `{"data":[...],"pagination":{...}}`.

## 9. Fallos comunes
- 503 en health → PostgreSQL no responde.
- 409 → correo duplicado (constraint UNIQUE).
- 400 → JSON inválido o campo faltante.
- El worker no arranca → error de importación o de conexión inicial.

## 10. Cómo diagnosticar fallos
- `docker compose logs backend` para ver el traceback y el `pgcode`.
- `docker compose exec backend python -c "import db; print(db.ping())"`.
- Verificar variables de entorno con `docker compose exec backend env | grep DB_`.

## 11. Cómo recuperarme
- Reiniciar el servicio: `docker compose restart backend`.
- El backend tiene **reintentos** de conexión al arrancar (`wait_for_db`).
- Si la BD está caída, el health devuelve 503 y Docker reinicia por `restart: unless-stopped`.

## 12. Consideraciones de seguridad
- **Consultas parametrizadas** → inmunidad a inyección SQL.
- Credenciales solo por variables de entorno, nunca en el código ni en logs.
- Límite de tamaño de cuerpo (`MAX_CONTENT_LENGTH = 16 KB`).
- Backend sin puerto público (solo accesible por Nginx en la red interna).
- Contenedor como usuario no root.

## 13. Consideraciones de rendimiento
- **Gunicorn** con 3 workers y 2 threads para concurrencia moderada.
- **Paginación** con `LIMIT/OFFSET` (máx. 100) para no cargar todo en memoria.
- Índices en la BD aprovechados por el `ORDER BY fecha_registro`.
- Conexiones abiertas y cerradas por petición de forma segura.

## 14. Diez preguntas probables del profesor
1. ¿Cómo evitas la inyección SQL?
2. ¿Cómo manejas las transacciones?
3. ¿Por qué Gunicorn y no `flask run`?
4. ¿Cómo lees las credenciales?
5. ¿Qué códigos HTTP usas y cuándo?
6. ¿Cómo implementas el health check?
7. ¿Cómo funciona la paginación?
8. ¿Qué pasa si la base de datos no está lista al arrancar?
9. ¿Cómo evitas correos duplicados?
10. ¿Cómo soportas peticiones concurrentes?

## 15. Diez respuestas modelo
1. Uso siempre `cursor.execute(sql, params)` con marcadores `%s`; psycopg2 escapa los valores. Nunca concateno strings con datos del usuario.
2. Con un context manager: hago `commit` solo si todo salió bien, `rollback` ante cualquier excepción, y siempre cierro cursor y conexión en `finally`.
3. Porque `flask run` es un servidor de desarrollo de un solo hilo, no apto para producción. Gunicorn maneja múltiples workers y threads y es estable bajo carga.
4. Con `os.environ.get("DB_PASSWORD")`; las credenciales vienen del `.env` vía Docker Compose y nunca se escriben en el código ni se registran en logs.
5. 200 (OK), 201 (creado), 204 (eliminado sin cuerpo), 400 (validación), 404 (no existe), 409 (conflicto por correo), 500 (error interno), 503 (BD caída).
6. `/api/health` ejecuta `SELECT 1` contra la BD; si responde devuelvo 200 con `database: connected`, si no, 503 con `disconnected`.
7. Leo `page` y `limit` (por defecto 1 y 50, máximo 100), calculo el `OFFSET`, cuento el total y devuelvo `data` + `pagination`.
8. `wait_for_db()` reintenta hasta 30 veces con espera; además `depends_on: condition: service_healthy` hace que el backend arranque tras el healthcheck de la BD.
9. Hay una constraint `UNIQUE` en `correo`; si se viola, psycopg2 lanza `UniqueViolation` y respondo 409 con un mensaje claro.
10. Gunicorn con 3 workers × 2 threads atiende varias peticiones en paralelo; cada una usa su propia conexión, y la BD garantiza consistencia. Lo probé con 50 peticiones concurrentes sin fallos.

## 16. Guion de defensa oral (2 minutos)
"Soy el responsable del backend. Desarrollé una API REST en Flask con seis endpoints: un health check y el CRUD completo de visitantes. Cada petición pasa por validación —campos obligatorios, longitud del nombre, formato del correo, categoría permitida y id entero— y normalizo los datos (recorto espacios y paso el correo a minúsculas). Todas las consultas a PostgreSQL son parametrizadas, así que soy inmune a la inyección SQL. Manejo transacciones con commit y rollback, y cierro siempre las conexiones. Las credenciales vienen de variables de entorno, nunca del código. Devuelvo códigos HTTP precisos: 201 al crear, 409 si el correo está duplicado, 404 si no existe, 503 si la base de datos cae. En producción sirvo la app con Gunicorn, no con el servidor de desarrollo, y tengo reintentos de conexión al arrancar."

## 17. Guion de defensa oral extendido (5 minutos)
Añade al de 2 minutos:
- **Health check**: "Ejecuta `SELECT 1`; Docker lo usa para saber si el contenedor está sano."
- **Paginación**: "Uso `LIMIT/OFFSET` con máximo 100 para no cargar toda la tabla en memoria; devuelvo metadatos de paginación."
- **Concurrencia**: "Gunicorn con 3 workers y 2 threads; lo validé con `test_concurrency.py`, 50 peticiones, 10 concurrentes, sin fallos."
- **Arranque resiliente**: "`wait_for_db` reintenta la conexión, y `depends_on: service_healthy` espera a la BD."
- **Seguridad**: parametrización, límite de payload, usuario no root, sin puerto público.
- Cierra con la relación con las otras capas (sección 20).

## 18. Checklist de demostración en vivo
- [ ] `curl http://localhost/api/health` → 200 y `database: connected`.
- [ ] `curl -X POST .../api/visitantes` con datos válidos → 201.
- [ ] POST con correo inválido → 400.
- [ ] POST con correo repetido → 409.
- [ ] `GET /api/visitantes?page=1&limit=5` → estructura con `pagination`.
- [ ] `docker compose logs backend` mostrando logs sin credenciales.

## 19. Lo que NUNCA debo decir mal
- **NO** digo que uso SQLAlchemy: uso **psycopg2** directo.
- **NO** digo que concateno SQL: uso **consultas parametrizadas**.
- **NO** digo que uso `flask run` en producción: uso **Gunicorn**.
- **NO** digo que las credenciales están en el código: están en **variables de entorno**.

## 20. Relación con las otras tres capas
- **Frontend**: consume mi API por rutas relativas; le devuelvo JSON y códigos HTTP claros.
- **Base de datos**: me conecto por la red privada con `psycopg2`; respeto sus constraints (UNIQUE, CHECK).
- **DevOps/Nginx**: Nginx me reenvía `/api/`; no publico mi puerto 5000; Gunicorn es mi servidor de producción dentro del contenedor.
