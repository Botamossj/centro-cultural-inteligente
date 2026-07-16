# 07 · Plan de Pruebas y Auditoría

Pruebas exactas para validar el sistema. Reemplaza `localhost` por la IP pública de EC2 cuando pruebes producción.

> Resultados reales obtenidos en el entorno local durante la construcción se indican con ✅.

---

## 1. CRUD completo
```bash
bash scripts/test_api.sh http://localhost
```
Verifica: health, crear, listar, obtener, actualizar, entrada inválida, correo duplicado, eliminar y 404 tras borrar. ✅ (9 PASS / 0 FAIL).

Manual:
```bash
# Crear
curl -X POST http://localhost/api/visitantes -H "Content-Type: application/json" \
  -d '{"nombre":"Ana Pérez","correo":"ana@example.com","categoria":"General"}'
# Listar
curl http://localhost/api/visitantes
# Obtener
curl http://localhost/api/visitantes/1
# Actualizar
curl -X PUT http://localhost/api/visitantes/1 -H "Content-Type: application/json" \
  -d '{"nombre":"Ana P.","correo":"ana@example.com","categoria":"VIP"}'
# Eliminar
curl -X DELETE http://localhost/api/visitantes/1 -i
```

## 2. Endpoint de salud
```bash
curl -i http://localhost/api/health
```
Esperado: `200` con `{"status":"ok","service":"centro-cultural-api","database":"connected"}`. ✅

## 3. Persistencia
```bash
bash scripts/test_persistence.sh http://localhost
```
Crea un visitante, hace `down` + `up` y verifica que sobrevive. Esperado: **PASS**. ✅

## 4. Hardening del puerto 5432
```bash
# Desde OTRA máquina, contra la IP pública de EC2:
bash scripts/verify_hardening.sh <IP_PUBLICA_EC2>
docker compose ps      # en el servidor: database SIN puerto publicado
```
Esperado: puerto 5432 no accesible; `docker compose ps` no muestra mapeo `5432`. ✅ (confirmado con `docker compose ps`).

> Nota: ejecutado sobre `localhost` en una máquina de desarrollo que ya tenía PostgreSQL instalado, el script marca 5432 como accesible (falso positivo del host, no del contenedor). La prueba válida es desde una máquina remota contra EC2.

## 5. Enrutamiento de Nginx
```bash
curl -I http://localhost/                 # estáticos (200)
curl -I http://localhost/api/health       # proxy a backend (200)
curl -I http://localhost/                 # cabeceras X-Content-Type-Options, X-Frame-Options
```

## 6. Peticiones concurrentes
```bash
python scripts/test_concurrency.py --url http://localhost --requests 50 --concurrency 10
```
Esperado: 50 exitosas / 0 fallidas. ✅ (50/50, ~3.35 s totales).

## 7. Reinicio de contenedores
```bash
docker compose restart
docker compose ps         # todos healthy
curl --fail http://localhost/api/health
```

## 8. `docker compose down`
```bash
docker compose down
ls "$POSTGRES_DATA_PATH"   # los datos siguen en el host
docker compose up -d
curl --fail http://localhost/api/health
```

## 9. Despliegue con GitHub Actions
1. Crear una rama, cambiar algo pequeño, PR y merge a `main`.
2. Revisar la pestaña **Actions**: job `validate` verde, luego job `deploy` verde.
3. Verificar el cambio en `http://<IP_PUBLICA>`.

## 10. Logs
```bash
docker compose logs --tail=100
docker compose logs backend
```
Verificar que **no** aparecen credenciales.

## 11. Datos de formulario inválidos
```bash
curl -i -X POST http://localhost/api/visitantes -H "Content-Type: application/json" \
  -d '{"nombre":"","correo":"malo","categoria":"Otra"}'
```
Esperado: `400` con mensaje de validación. ✅

## 12. Correo duplicado
```bash
# Crear dos veces el mismo correo
curl -X POST http://localhost/api/visitantes -H "Content-Type: application/json" \
  -d '{"nombre":"X","correo":"dup@example.com","categoria":"General"}'
curl -i -X POST http://localhost/api/visitantes -H "Content-Type: application/json" \
  -d '{"nombre":"Y","correo":"dup@example.com","categoria":"General"}'
```
Esperado: primero `201`, segundo `409`. ✅

## 13. Errores de API
| Caso | Esperado |
| ---- | -------- |
| `GET /api/visitantes/999999` | 404 |
| `PUT` sobre id inexistente | 404 |
| `DELETE` sobre id inexistente | 404 |
| Body no JSON | 400 |
| id no entero (`/api/visitantes/abc`) | 400 |
| BD caída | 503 en `/api/health` |

---

## Resumen de resultados locales
| Prueba | Comando | Resultado |
| ------ | ------- | --------- |
| CRUD + errores | `test_api.sh` | ✅ 9/9 PASS |
| Concurrencia | `test_concurrency.py` | ✅ 50/50 |
| Persistencia | `test_persistence.sh` | ✅ PASS |
| Health | `curl /api/health` | ✅ 200 |
| Puertos | `docker compose ps` | ✅ solo 80 publicado |
| Config | `docker compose config --quiet` | ✅ válido |
| Sintaxis Python | `py_compile` | ✅ OK |
