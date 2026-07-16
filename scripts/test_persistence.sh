#!/usr/bin/env bash
# =====================================================================
# Prueba de persistencia (Chaos Engineering).
# Crea un visitante, reinicia los contenedores con `down` + `up` y
# verifica que el dato sobrevive. NUNCA borra el directorio de datos.
# Uso: bash scripts/test_persistence.sh [BASE_URL]
# =====================================================================
set -u

BASE_URL="${1:-http://localhost}"
API="${BASE_URL}/api"
EMAIL="persist_$(date +%s)@example.com"
NOMBRE="Persistencia $(date +%s)"

esperar_health() {
  echo "Esperando health check..."
  for i in $(seq 1 24); do
    if curl -s --fail "${API}/health" > /dev/null; then
      echo "  -> API saludable."
      return 0
    fi
    sleep 5
  done
  echo "  -> La API no respondió a tiempo."
  return 1
}

echo "== 1. Creando visitante de prueba =="
resp=$(curl -s -X POST "${API}/visitantes" \
  -H "Content-Type: application/json" \
  -d "{\"nombre\":\"${NOMBRE}\",\"correo\":\"${EMAIL}\",\"categoria\":\"General\"}")
echo "$resp"

echo "== 2. Verificando que existe antes del reinicio =="
antes=$(curl -s "${API}/visitantes?search=${EMAIL}")
if echo "$antes" | grep -q "$EMAIL"; then
  echo "  -> Encontrado antes del reinicio."
else
  echo "FAIL: no se pudo crear/encontrar el visitante inicial."
  exit 1
fi

echo "== 3. docker compose down (SIN borrar volúmenes ni datos) =="
docker compose down

echo "== 4. docker compose up -d =="
docker compose up -d

esperar_health || { echo "FAIL: la API no volvió a estar disponible."; exit 1; }

echo "== 5. Verificando que el visitante sigue existiendo =="
despues=$(curl -s "${API}/visitantes?search=${EMAIL}")
if echo "$despues" | grep -q "$EMAIL"; then
  echo "======================================"
  echo "PASS: los datos PERSISTIERON tras el reinicio de contenedores."
  exit 0
else
  echo "======================================"
  echo "FAIL: los datos NO persistieron. Revisa el bind mount / volumen."
  exit 1
fi
