# Imagen mínima oficial de Python 3.12
FROM python:3.12-slim

# Buenas prácticas para Python en contenedores.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias primero para aprovechar la caché de capas.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación.
COPY . .

# Ejecutar como usuario no root por seguridad.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Healthcheck interno (usa la librería estándar, sin curl).
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD python -c "import urllib.request,sys; \
        r=urllib.request.urlopen('http://127.0.0.1:5000/api/health', timeout=4); \
        sys.exit(0 if r.status==200 else 1)" || exit 1

# Servidor de producción Gunicorn (nunca el servidor de desarrollo de Flask).
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--threads", "2", "--timeout", "30", "app:app"]
