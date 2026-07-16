"""API REST del Centro Cultural Inteligente.

Flask + psycopg2. Expone un CRUD de visitantes y un health check.
Se sirve en producción mediante Gunicorn detrás de Nginx. El backend nunca
se publica directamente: solo Nginx expone el puerto 80.
"""

from __future__ import annotations

import logging
import os

import psycopg2
from flask import Flask, jsonify, request
from psycopg2 import Error as PgError

import db
from validation import ValidationError, parse_paginacion, validar_id, validar_visitante

# --- Configuración de logging estructurado (sin credenciales) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
logger = logging.getLogger("centro-cultural.api")

app = Flask(__name__)

# Límite de tamaño del cuerpo de la petición (16 KB es más que suficiente
# para un visitante y protege contra payloads abusivos).
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

# Espera activa a la base de datos durante el arranque de cada worker.
try:
    db.wait_for_db()
except Exception as exc:  # noqa: BLE001
    # No detenemos el proceso: /api/health reportará 503 y Docker reintentará.
    logger.error("Arranque sin base de datos disponible: %s", exc)


# ---------------------------------------------------------------------------
# Helpers de respuesta
# ---------------------------------------------------------------------------
def _error(mensaje: str, status: int):
    return jsonify({"error": mensaje}), status


def _fila_a_dict(fila: dict) -> dict:
    """Serializa una fila de la BD a JSON, convirtiendo fechas a ISO 8601."""
    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "correo": fila["correo"],
        "categoria": fila["categoria"],
        "fecha_registro": fila["fecha_registro"].isoformat()
        if fila.get("fecha_registro")
        else None,
        "fecha_actualizacion": fila["fecha_actualizacion"].isoformat()
        if fila.get("fecha_actualizacion")
        else None,
    }


# ---------------------------------------------------------------------------
# Manejadores de error globales
# ---------------------------------------------------------------------------
@app.errorhandler(ValidationError)
def _handle_validation(exc: ValidationError):
    return _error(exc.message, 400)


@app.errorhandler(413)
def _handle_too_large(_exc):
    return _error("El cuerpo de la petición es demasiado grande.", 413)


@app.errorhandler(404)
def _handle_not_found(_exc):
    return _error("Recurso no encontrado.", 404)


@app.errorhandler(405)
def _handle_method(_exc):
    return _error("Método no permitido.", 405)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    conectada = db.ping()
    body = {
        "status": "ok" if conectada else "degraded",
        "service": "centro-cultural-api",
        "database": "connected" if conectada else "disconnected",
    }
    return jsonify(body), (200 if conectada else 503)


# ---------------------------------------------------------------------------
# Crear visitante
# ---------------------------------------------------------------------------
@app.post("/api/visitantes")
def crear_visitante():
    datos = validar_visitante(request.get_json(silent=True))
    try:
        with db.db_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO visitantes (nombre, correo, categoria)
                VALUES (%s, %s, %s)
                RETURNING id, nombre, correo, categoria,
                          fecha_registro, fecha_actualizacion;
                """,
                (datos["nombre"], datos["correo"], datos["categoria"]),
            )
            fila = cur.fetchone()
        logger.info("Visitante creado id=%s", fila["id"])
        return jsonify(_fila_a_dict(fila)), 201
    except psycopg2.errors.UniqueViolation:
        return _error("Ya existe un visitante con ese correo.", 409)
    except PgError as exc:
        logger.error("Error de BD al crear visitante: %s", exc.pgcode)
        return _error("Error interno al registrar el visitante.", 500)


# ---------------------------------------------------------------------------
# Listar visitantes (con paginación y búsqueda)
# ---------------------------------------------------------------------------
@app.get("/api/visitantes")
def listar_visitantes():
    page, limit = parse_paginacion(request.args.get("page"), request.args.get("limit"))
    search = (request.args.get("search") or "").strip()
    offset = (page - 1) * limit

    # Filtro de búsqueda parametrizado (nombre o correo). ILIKE + parámetro:
    # nunca se concatena la entrada del usuario dentro del SQL.
    where_sql = ""
    params: list[object] = []
    if search:
        where_sql = "WHERE nombre ILIKE %s OR correo ILIKE %s"
        patron = f"%{search}%"
        params.extend([patron, patron])

    try:
        with db.db_cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS total FROM visitantes {where_sql};", params)
            total = cur.fetchone()["total"]

            cur.execute(
                f"""
                SELECT id, nombre, correo, categoria,
                       fecha_registro, fecha_actualizacion
                FROM visitantes
                {where_sql}
                ORDER BY fecha_registro DESC, id DESC
                LIMIT %s OFFSET %s;
                """,
                [*params, limit, offset],
            )
            filas = cur.fetchall()
    except PgError as exc:
        logger.error("Error de BD al listar visitantes: %s", exc.pgcode)
        return _error("Error interno al listar visitantes.", 500)

    total_pages = (total + limit - 1) // limit if total else 0
    return jsonify(
        {
            "data": [_fila_a_dict(f) for f in filas],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
            },
        }
    )


# ---------------------------------------------------------------------------
# Obtener un visitante
# ---------------------------------------------------------------------------
@app.get("/api/visitantes/<visitante_id>")
def obtener_visitante(visitante_id: str):
    vid = validar_id(visitante_id)
    try:
        with db.db_cursor() as cur:
            cur.execute(
                """
                SELECT id, nombre, correo, categoria,
                       fecha_registro, fecha_actualizacion
                FROM visitantes WHERE id = %s;
                """,
                (vid,),
            )
            fila = cur.fetchone()
    except PgError as exc:
        logger.error("Error de BD al obtener visitante: %s", exc.pgcode)
        return _error("Error interno al obtener el visitante.", 500)

    if fila is None:
        return _error("Visitante no encontrado.", 404)
    return jsonify(_fila_a_dict(fila))


# ---------------------------------------------------------------------------
# Actualizar visitante
# ---------------------------------------------------------------------------
@app.put("/api/visitantes/<visitante_id>")
def actualizar_visitante(visitante_id: str):
    vid = validar_id(visitante_id)
    datos = validar_visitante(request.get_json(silent=True))
    try:
        with db.db_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE visitantes
                SET nombre = %s, correo = %s, categoria = %s
                WHERE id = %s
                RETURNING id, nombre, correo, categoria,
                          fecha_registro, fecha_actualizacion;
                """,
                (datos["nombre"], datos["correo"], datos["categoria"], vid),
            )
            fila = cur.fetchone()
        if fila is None:
            return _error("Visitante no encontrado.", 404)
        logger.info("Visitante actualizado id=%s", vid)
        return jsonify(_fila_a_dict(fila))
    except psycopg2.errors.UniqueViolation:
        return _error("Ya existe otro visitante con ese correo.", 409)
    except PgError as exc:
        logger.error("Error de BD al actualizar visitante: %s", exc.pgcode)
        return _error("Error interno al actualizar el visitante.", 500)


# ---------------------------------------------------------------------------
# Eliminar visitante
# ---------------------------------------------------------------------------
@app.delete("/api/visitantes/<visitante_id>")
def eliminar_visitante(visitante_id: str):
    vid = validar_id(visitante_id)
    try:
        with db.db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM visitantes WHERE id = %s;", (vid,))
            eliminado = cur.rowcount
    except PgError as exc:
        logger.error("Error de BD al eliminar visitante: %s", exc.pgcode)
        return _error("Error interno al eliminar el visitante.", 500)

    if eliminado == 0:
        return _error("Visitante no encontrado.", 404)
    logger.info("Visitante eliminado id=%s", vid)
    return "", 204


if __name__ == "__main__":
    # Solo para depuración local. En producción se usa Gunicorn.
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
