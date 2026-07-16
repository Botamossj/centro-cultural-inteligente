#!/usr/bin/env python3
"""Prueba de concurrencia contra la API de visitantes.

Envía múltiples peticiones POST concurrentes con correos únicos y reporta
éxitos, fallos, duración media y total. Usa solo la librería estándar.

Ejemplo:
    python scripts/test_concurrency.py --url http://localhost --requests 50 --concurrency 10
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed


def crear_visitante(base_url: str, indice: int) -> tuple[bool, float]:
    """Envía un POST y devuelve (exito, duracion_segundos)."""
    url = f"{base_url.rstrip('/')}/api/visitantes"
    correo = f"carga_{uuid.uuid4().hex[:12]}@example.com"
    payload = json.dumps(
        {
            "nombre": f"Carga {indice}",
            "correo": correo,
            "categoria": "General",
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            exito = resp.status == 201
    except urllib.error.HTTPError as exc:
        exito = exc.code == 201
    except Exception:
        exito = False
    duracion = time.perf_counter() - inicio
    return exito, duracion


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba de concurrencia de la API")
    parser.add_argument("--url", default="http://localhost", help="URL base (por Nginx)")
    parser.add_argument("--requests", type=int, default=50, help="Total de peticiones")
    parser.add_argument("--concurrency", type=int, default=10, help="Trabajadores concurrentes")
    args = parser.parse_args()

    print(f"URL base:      {args.url}")
    print(f"Peticiones:    {args.requests}")
    print(f"Concurrencia:  {args.concurrency}")
    print("Ejecutando...")

    exitosos = 0
    fallidos = 0
    duraciones: list[float] = []

    inicio_total = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futuros = [
            executor.submit(crear_visitante, args.url, i) for i in range(args.requests)
        ]
        for futuro in as_completed(futuros):
            exito, duracion = futuro.result()
            duraciones.append(duracion)
            if exito:
                exitosos += 1
            else:
                fallidos += 1
    duracion_total = time.perf_counter() - inicio_total

    promedio = sum(duraciones) / len(duraciones) if duraciones else 0.0

    print("=" * 40)
    print(f"Peticiones exitosas: {exitosos}")
    print(f"Peticiones fallidas: {fallidos}")
    print(f"Duración media:      {promedio * 1000:.1f} ms")
    print(f"Duración total:      {duracion_total:.2f} s")
    print("=" * 40)

    return 0 if fallidos == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
