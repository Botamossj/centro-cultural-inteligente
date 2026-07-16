#!/usr/bin/env bash
# =====================================================================
# Verificación de hardening de red.
# Comprueba que Nginx (80) y la API responden, y que el puerto 5432 de
# PostgreSQL NO está accesible.
#
# IMPORTANTE: para una auditoría real de exposición pública, este script
# debe ejecutarse DESDE OTRA MÁQUINA contra la IP pública de EC2, por
# ejemplo:  bash scripts/verify_hardening.sh <IP_PUBLICA_EC2>
# Ejecutarlo en el propio host solo comprueba el comportamiento local.
# =====================================================================
set -u

TARGET="${1:-localhost}"
WARN=0

echo "== Objetivo: ${TARGET} =="
echo "NOTA: para auditar la exposición pública real, ejecuta este script"
echo "      desde otra máquina usando la IP pública de la instancia EC2."
echo ""

# 1. Nginx en el puerto 80
echo "== 1. Nginx en puerto 80 =="
code=$(curl -s -o /dev/null -w "%{http_code}" "http://${TARGET}/" || echo "000")
if [ "$code" = "200" ] || [ "$code" = "304" ]; then
  echo "  OK: Nginx responde (HTTP $code)."
else
  echo "  ADVERTENCIA: Nginx no respondió correctamente (HTTP $code)."
fi

# 2. API a través de Nginx
echo "== 2. API /api/health =="
code=$(curl -s -o /dev/null -w "%{http_code}" "http://${TARGET}/api/health" || echo "000")
if [ "$code" = "200" ]; then
  echo "  OK: la API responde vía Nginx."
else
  echo "  ADVERTENCIA: la API no respondió (HTTP $code)."
fi

# 3. Puerto 5432 (PostgreSQL) NO debe estar accesible
echo "== 3. Puerto 5432 (PostgreSQL) =="
if command -v nc > /dev/null 2>&1; then
  if nc -z -w 3 "${TARGET}" 5432 2>/dev/null; then
    echo "  ADVERTENCIA CRÍTICA: el puerto 5432 ESTÁ accesible. ¡Debe estar cerrado!"
    WARN=1
  else
    echo "  OK: el puerto 5432 no es accesible (filtrado/cerrado)."
  fi
else
  # Alternativa sin netcat: intento de conexión con /dev/tcp de bash.
  if timeout 3 bash -c "echo > /dev/tcp/${TARGET}/5432" 2>/dev/null; then
    echo "  ADVERTENCIA CRÍTICA: el puerto 5432 ESTÁ accesible. ¡Debe estar cerrado!"
    WARN=1
  else
    echo "  OK: el puerto 5432 no es accesible (filtrado/cerrado)."
  fi
fi

echo "======================================"
if [ "$WARN" -eq 1 ]; then
  echo "RESULTADO: se detectó exposición del puerto 5432. Revisa el hardening."
  exit 1
else
  echo "RESULTADO: no se detectó exposición del puerto 5432."
  exit 0
fi
