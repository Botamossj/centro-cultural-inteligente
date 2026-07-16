"""Validación y normalización de datos de entrada.

Centraliza todas las reglas de negocio de validación para los visitantes.
Devuelve datos ya normalizados (recortados, correo en minúsculas) o lanza
`ValidationError` con un mensaje claro para el cliente.
"""

from __future__ import annotations

import re
from typing import Any

# Categorías permitidas: deben coincidir con el CHECK constraint de la BD.
CATEGORIAS_PERMITIDAS: frozenset[str] = frozenset(
    {"General", "Estudiante", "Adulto mayor", "VIP"}
)

NOMBRE_MIN_LEN = 2
NOMBRE_MAX_LEN = 120
CORREO_MAX_LEN = 150

# Expresión regular pragmática para validar el formato del correo.
_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    """Error de validación con mensaje apto para mostrar al cliente."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def validar_visitante(payload: Any) -> dict[str, str]:
    """Valida y normaliza el cuerpo de creación/actualización de un visitante.

    Devuelve un dict con las claves: nombre, correo, categoria.
    Lanza ValidationError si algún campo es inválido.
    """
    if not isinstance(payload, dict):
        raise ValidationError("El cuerpo de la petición debe ser un objeto JSON.")

    nombre = payload.get("nombre")
    correo = payload.get("correo")
    categoria = payload.get("categoria")

    # --- Nombre ---
    if not isinstance(nombre, str) or not nombre.strip():
        raise ValidationError("El campo 'nombre' es obligatorio.")
    nombre = nombre.strip()
    if len(nombre) < NOMBRE_MIN_LEN:
        raise ValidationError(
            f"El 'nombre' debe tener al menos {NOMBRE_MIN_LEN} caracteres."
        )
    if len(nombre) > NOMBRE_MAX_LEN:
        raise ValidationError(
            f"El 'nombre' no puede superar {NOMBRE_MAX_LEN} caracteres."
        )

    # --- Correo ---
    if not isinstance(correo, str) or not correo.strip():
        raise ValidationError("El campo 'correo' es obligatorio.")
    correo = correo.strip().lower()
    if len(correo) > CORREO_MAX_LEN:
        raise ValidationError(
            f"El 'correo' no puede superar {CORREO_MAX_LEN} caracteres."
        )
    if not _EMAIL_REGEX.match(correo):
        raise ValidationError("El 'correo' no tiene un formato válido.")

    # --- Categoría ---
    if not isinstance(categoria, str) or not categoria.strip():
        raise ValidationError("El campo 'categoria' es obligatorio.")
    categoria = categoria.strip()
    if categoria not in CATEGORIAS_PERMITIDAS:
        permitidas = ", ".join(sorted(CATEGORIAS_PERMITIDAS))
        raise ValidationError(f"La 'categoria' debe ser una de: {permitidas}.")

    return {"nombre": nombre, "correo": correo, "categoria": categoria}


def validar_id(valor: Any) -> int:
    """Valida que un identificador sea un entero positivo."""
    try:
        entero = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("El identificador debe ser un entero.") from None
    if entero <= 0:
        raise ValidationError("El identificador debe ser un entero positivo.")
    return entero


def parse_paginacion(page_raw: Any, limit_raw: Any) -> tuple[int, int]:
    """Interpreta y acota los parámetros de paginación.

    Defaults: page=1, limit=50. Límite máximo: 100.
    """
    try:
        page = int(page_raw) if page_raw is not None else 1
    except (TypeError, ValueError):
        page = 1
    try:
        limit = int(limit_raw) if limit_raw is not None else 50
    except (TypeError, ValueError):
        limit = 50

    if page < 1:
        page = 1
    if limit < 1:
        limit = 50
    if limit > 100:
        limit = 100
    return page, limit
