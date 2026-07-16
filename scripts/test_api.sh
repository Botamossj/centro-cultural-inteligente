#!/usr/bin/env bash
# =====================================================================
# Pruebas funcionales de la API vía Nginx (puerto 80).
# Prueba: health, create, list, get, update, delete, entrada inválida
# y correo duplicado. Uso: bash scripts/test_api.sh [BASE_URL]
# =====================================================================
set -u

BASE_URL="${1:-http://localhost}"
API="${BASE_URL}/api"
PASS=0
FAIL=0

# Correo único para no chocar con ejecuciones anteriores.
EMAIL="qa_$(date +%s)@example.com"

check() {
  local descripcion="$1" esperado="$2" obtenido="$3"
  if [ "$obtenido" = "$esperado" ]; then
    echo "PASS: $descripcion (HTTP $obtenido)"
    PASS=$((PASS + 1))
  else
    echo "FAIL: $descripcion (esperado $esperado, obtenido $obtenido)"
    FAIL=$((FAIL + 1))
  fi
}

echo "== Base URL: $BASE_URL =="

# 1. Health
code=$(curl -s -o /dev/null -w "%{http_code}" "${API}/health")
check "Health check" "200" "$code"

# 2. Crear visitante
resp=$(curl -s -w "\n%{http_code}" -X POST "${API}/visitantes" \
  -H "Content-Type: application/json" \
  -d "{\"nombre\":\"QA Tester\",\"correo\":\"${EMAIL}\",\"categoria\":\"General\"}")
code=$(echo "$resp" | tail -n1)
body=$(echo "$resp" | sed '$d')
check "Crear visitante" "201" "$code"
NEW_ID=$(echo "$body" | grep -o '"id"[: ]*[0-9]*' | grep -o '[0-9]*' | head -n1)
echo "   -> ID creado: ${NEW_ID:-<ninguno>}"

# 3. Listar
code=$(curl -s -o /dev/null -w "%{http_code}" "${API}/visitantes")
check "Listar visitantes" "200" "$code"

# 4. Obtener uno
code=$(curl -s -o /dev/null -w "%{http_code}" "${API}/visitantes/${NEW_ID}")
check "Obtener visitante por id" "200" "$code"

# 5. Actualizar
code=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "${API}/visitantes/${NEW_ID}" \
  -H "Content-Type: application/json" \
  -d "{\"nombre\":\"QA Tester Editado\",\"correo\":\"${EMAIL}\",\"categoria\":\"VIP\"}")
check "Actualizar visitante" "200" "$code"

# 6. Entrada inválida (correo mal formado)
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API}/visitantes" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"X","correo":"no-es-correo","categoria":"General"}')
check "Rechazar entrada inválida" "400" "$code"

# 7. Correo duplicado
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API}/visitantes" \
  -H "Content-Type: application/json" \
  -d "{\"nombre\":\"Otro\",\"correo\":\"${EMAIL}\",\"categoria\":\"General\"}")
check "Rechazar correo duplicado" "409" "$code"

# 8. Eliminar
code=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${API}/visitantes/${NEW_ID}")
check "Eliminar visitante" "204" "$code"

# 9. Obtener eliminado -> 404
code=$(curl -s -o /dev/null -w "%{http_code}" "${API}/visitantes/${NEW_ID}")
check "Visitante eliminado devuelve 404" "404" "$code"

echo "======================================"
echo "Resultado: ${PASS} PASS / ${FAIL} FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
