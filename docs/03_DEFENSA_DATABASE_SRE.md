# 03 · Defensa del Rol Base de Datos y SRE

## 1. Nombre del rol
**Integrante C — Database Administrator & SRE.** Rama `feature/database`.

## 2. Archivos bajo mi responsabilidad
- `database/schema.sql` — tabla, constraints, índices y trigger.
- Servicio `database` en `docker-compose.yml`.
- Configuración del volumen persistente (bind mount).
- Configuración de la red privada.
- Health check de PostgreSQL.
- Scripts `scripts/test_persistence.sh` y `scripts/verify_hardening.sh`.

## 3. Objetivo de mi capa
Garantizar el almacenamiento **persistente, íntegro y aislado** de los visitantes en PostgreSQL 16, con un esquema correcto, datos que sobreviven a la destrucción de contenedores y una base de datos inaccesible desde Internet.

## 4. Explicación detallada (fácil de memorizar)
- Tabla `visitantes` con **clave primaria** (`id`), **UNIQUE** en `correo` y **CHECK** en `categoria`.
- Índices en `fecha_registro`, `nombre` y `categoria` para acelerar orden y búsqueda.
- Un **trigger** refresca `fecha_actualizacion` en cada `UPDATE`.
- Los datos viven en un **bind mount** del host (`/var/lib/postgresql/data` → carpeta del host), respaldado por **EBS** en AWS.
- PostgreSQL solo está en `private_network` (interna) y **no publica el puerto 5432**.

## 5. Flujo de una petición a través de mi capa
1. El backend abre conexión por la red privada (host `database`, puerto 5432 interno).
2. Ejecuta un `INSERT/UPDATE/DELETE/SELECT` parametrizado.
3. PostgreSQL valida constraints (UNIQUE, CHECK) y escribe en su directorio de datos.
4. Ese directorio es un bind mount → la escritura llega al **disco del host (EBS)**.
5. Devuelve el resultado al backend.

## 6. Fragmentos importantes

Esquema (constraints):
```sql
CREATE TABLE IF NOT EXISTS visitantes (
    id BIGSERIAL PRIMARY KEY,
    correo VARCHAR(150) NOT NULL,
    categoria VARCHAR(30) NOT NULL,
    ...
    CONSTRAINT visitantes_correo_unique UNIQUE (correo),
    CONSTRAINT visitantes_categoria_check
        CHECK (categoria IN ('General','Estudiante','Adulto mayor','VIP'))
);
```

Persistencia y aislamiento (docker-compose.yml):
```yaml
database:
  image: postgres:16-alpine
  volumes:
    - ${POSTGRES_DATA_PATH:-./postgres-data}:/var/lib/postgresql/data
  networks:
    - private_network        # sin puerto 5432 publicado
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
```

## 7. Comandos que debo conocer
```bash
docker compose exec database pg_isready -U centro_user -d centro_cultural
docker compose exec database psql -U centro_user -d centro_cultural -c "SELECT COUNT(*) FROM visitantes;"
docker compose ps           # comprobar que 5432 NO está publicado
bash scripts/test_persistence.sh http://localhost
```

## 8. Salidas esperadas
- `pg_isready` → `accepting connections`.
- `\d visitantes` muestra columnas, PK, UNIQUE, CHECK e índices.
- `docker compose ps` → la fila de `database` **sin** puertos publicados.

## 9. Fallos comunes
- El schema no se aplica → el directorio de datos ya existía (init solo corre con datadir vacío).
- Permisos del directorio de datos en Linux.
- `UniqueViolation` al insertar correo repetido (comportamiento esperado).

## 10. Cómo diagnosticar fallos
- `docker compose logs database` (mensajes de arranque e init).
- `docker compose exec database psql ... -c "\d visitantes"`.
- Verificar el contenido del bind mount en el host (`ls $POSTGRES_DATA_PATH`).

## 11. Cómo recuperarme
- Si el schema no se aplicó por datadir preexistente, aplicarlo manualmente con `psql -f`.
- Reiniciar: `docker compose restart database`.
- Ante corrupción, restaurar desde copia del bind mount (EBS snapshot en AWS).

## 12. Consideraciones de seguridad
- Puerto 5432 **nunca publicado**; solo accesible por el backend en la red privada.
- `private_network` marcada como `internal: true` → sin salida a Internet.
- Credenciales por variables de entorno.
- `no-new-privileges: true` en el contenedor.

## 13. Consideraciones de rendimiento
- Índices en columnas de orden y búsqueda (`fecha_registro`, `nombre`, `categoria`).
- Tipos adecuados (`BIGSERIAL`, `VARCHAR` acotados, `TIMESTAMPTZ`).
- El backend pagina, evitando lecturas masivas.

## 14. Diez preguntas probables del profesor
1. ¿Cómo garantizas la persistencia de los datos?
2. ¿Cuál es la diferencia entre contenedor, imagen, volumen, bind mount, disco del host y EBS?
3. ¿Por qué el puerto 5432 no es accesible desde fuera?
4. ¿Qué constraints tiene tu tabla y para qué sirven?
5. ¿Cómo se inicializa el esquema automáticamente?
6. ¿Cómo se actualiza `fecha_actualizacion`?
7. ¿Qué índices creaste y por qué?
8. ¿Cómo probaste que los datos sobreviven a `docker compose down`?
9. ¿Qué es una red interna en Docker?
10. ¿Cómo recuperarías la base de datos ante un fallo del servidor?

## 15. Diez respuestas modelo
1. Los datos se escriben en un bind mount: la carpeta `/var/lib/postgresql/data` del contenedor apunta a una carpeta del host (respaldada por EBS). `docker compose down` borra el contenedor, pero la carpeta del host queda intacta.
2. La **imagen** es la plantilla (postgres:16-alpine); el **contenedor** es una instancia en ejecución; un **volumen** es almacenamiento gestionado por Docker; un **bind mount** enlaza una carpeta concreta del host; el **disco del host** es el sistema de archivos físico; **EBS** es el disco de bloque de AWS que respalda ese sistema de archivos en EC2.
3. Porque no incluyo `ports: 5432:5432` y PostgreSQL solo está en una red privada interna; el único que la alcanza es el backend dentro de Docker.
4. `PRIMARY KEY` en `id` (identidad única), `UNIQUE` en `correo` (no se repiten correos) y `CHECK` en `categoria` (solo valores válidos). Garantizan integridad a nivel de base de datos.
5. Monto `schema.sql` en `/docker-entrypoint-initdb.d/`; PostgreSQL lo ejecuta automáticamente en el **primer arranque**, cuando el directorio de datos está vacío.
6. Con un trigger `BEFORE UPDATE` que asigna `CURRENT_TIMESTAMP` a `fecha_actualizacion`; además el backend también la actualiza, así que hay doble garantía.
7. Índices en `fecha_registro` (para el orden del listado), `nombre` y `categoria` (para búsqueda y filtrado). Aceleran las consultas más frecuentes.
8. Con `test_persistence.sh`: creo un visitante, hago `docker compose down`, luego `up -d`, espero al health y verifico que el visitante sigue existiendo. El resultado fue PASS.
9. Es una red sin acceso al exterior (`internal: true`); los contenedores se comunican entre sí pero no pueden salir ni recibir tráfico de Internet.
10. En AWS restauraría desde un snapshot de EBS o desde la copia del directorio de datos; localmente, desde una copia del bind mount. El esquema se recrea solo si el datadir está vacío.

## 16. Guion de defensa oral (2 minutos)
"Soy el responsable de la base de datos y la fiabilidad. Uso PostgreSQL 16. La tabla `visitantes` tiene clave primaria, una restricción UNIQUE en el correo para que no se repita, y un CHECK que solo permite las cuatro categorías válidas. Creé índices en fecha, nombre y categoría para acelerar el listado y la búsqueda. Lo más importante es la persistencia: los datos no viven dentro del contenedor, sino en un bind mount hacia el disco del host, que en AWS es un volumen EBS. Por eso, aunque haga `docker compose down` y recree los contenedores, los datos siguen ahí. Lo demostré con un script que crea un visitante, reinicia todo y confirma que sigue existiendo. Además, PostgreSQL está en una red privada interna y no publica el puerto 5432, así que es inaccesible desde Internet."

## 17. Guion de defensa oral extendido (5 minutos)
Añade al de 2 minutos:
- **Diferencias de almacenamiento**: explica imagen vs contenedor vs volumen vs bind mount vs disco del host vs EBS (sección 15.2).
- **Inicialización**: "El esquema se aplica solo en el primer arranque vía `/docker-entrypoint-initdb.d`."
- **`fecha_actualizacion`**: "Un trigger BEFORE UPDATE la refresca automáticamente."
- **Health check**: "`pg_isready` le dice a Docker cuándo la BD está lista; el backend espera a ese estado con `depends_on: service_healthy`."
- **Hardening**: "Red interna, sin puerto 5432, `no-new-privileges`. Verifico la exposición con `verify_hardening.sh` desde otra máquina."
- **Recuperación**: snapshots de EBS.
- Cierra con la relación entre capas (sección 20).

## 18. Checklist de demostración en vivo
- [ ] `docker compose exec database psql -U centro_user -d centro_cultural -c "\d visitantes"` → mostrar PK, UNIQUE, CHECK, índices.
- [ ] Insertar un visitante desde la app.
- [ ] `docker compose down` y luego `docker compose up -d`.
- [ ] Confirmar que el visitante sigue existiendo (`SELECT COUNT(*)`).
- [ ] `docker compose ps` mostrando que `database` no publica puertos.
- [ ] Intentar `UPDATE` y ver que `fecha_actualizacion` cambia.

## 19. Lo que NUNCA debo decir mal
- **NO** digo que los datos están "dentro del contenedor": están en un **bind mount** en el host/EBS.
- **NO** digo que uso una base de datos gestionada (RDS): es PostgreSQL **autogestionada** en el contenedor.
- **NO** expongo el puerto 5432.
- **NO** confundo volumen con bind mount: aquí uso **bind mount** a una ruta del host.

## 20. Relación con las otras tres capas
- **Backend**: es el único que se conecta a mí, por la red privada, con consultas parametrizadas.
- **Frontend**: no me toca nunca directamente.
- **DevOps**: define las redes y el bind mount en Docker Compose; en AWS provee el volumen EBS que respalda mi persistencia.
