"""Acceso a la base de datos PostgreSQL.

Encapsula la conexión a PostgreSQL usando psycopg2. Las credenciales se
leen exclusivamente desde variables de entorno; nunca se escriben en el
código. Incluye lógica de reintentos para tolerar el arranque simultáneo
de los contenedores (el backend puede iniciar antes que la base de datos).
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import Iterator

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("centro-cultural.db")


def _db_config() -> dict[str, str | int]:
    """Construye la configuración de conexión desde variables de entorno."""
    return {
        "host": os.environ.get("DB_HOST", "database"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "dbname": os.environ.get("DB_NAME", "centro_cultural"),
        "user": os.environ.get("DB_USER", "centro_user"),
        "password": os.environ.get("DB_PASSWORD", ""),
    }


def get_connection() -> PgConnection:
    """Abre una nueva conexión a PostgreSQL.

    No registra la contraseña en los logs para evitar filtraciones.
    """
    config = _db_config()
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        dbname=config["dbname"],
        user=config["user"],
        password=config["password"],
        connect_timeout=5,
    )
    conn.autocommit = False
    return conn


def wait_for_db(max_retries: int = 30, delay_seconds: float = 2.0) -> None:
    """Espera a que la base de datos acepte conexiones durante el arranque.

    Reintenta hasta `max_retries` veces. Lanza la última excepción si nunca
    llega a conectar, de modo que el contenedor falle de forma visible.
    """
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            conn = get_connection()
            conn.close()
            logger.info("Conexión a la base de datos establecida (intento %d).", attempt)
            return
        except OperationalError as exc:
            last_error = exc
            logger.warning(
                "Base de datos no disponible (intento %d/%d). Reintentando en %.1fs...",
                attempt,
                max_retries,
                delay_seconds,
            )
            time.sleep(delay_seconds)
    logger.error("No fue posible conectar a la base de datos tras %d intentos.", max_retries)
    raise RuntimeError("La base de datos no está disponible") from last_error


def ping() -> bool:
    """Comprueba rápidamente si la base de datos responde. Usado por /api/health."""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
            return True
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001 - health check debe ser tolerante
        logger.warning("Health check de base de datos falló: %s", exc.__class__.__name__)
        return False


@contextmanager
def db_cursor(commit: bool = False) -> Iterator[RealDictCursor]:
    """Context manager que entrega un cursor y maneja transacciones.

    - Hace commit si `commit=True` y no hubo excepción.
    - Hace rollback ante cualquier excepción.
    - Cierra siempre cursor y conexión.
    """
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
