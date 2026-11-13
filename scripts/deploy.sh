
#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:?Provide image name as first argument}"

# Apenas imagens do GitHub Container Registry.
case "$IMAGE" in
  ghcr.io/*:*) ;;
  *)
    echo "Invalid image reference" >&2
    exit 1
    ;;
esac

# Configuração padrão para Caddy + API.
PUBLISH="127.0.0.1:8000:8000"
HEALTH_URL="http://127.0.0.1:8000/health"

# Permite configurações locais da EC2.
if [[ -f "$HOME/.cloud-tasks.env" ]]; then
  source "$HOME/.cloud-tasks.env"
fi

# A rede compartilhada com o Caddy deve existir.
if ! docker network inspect cloud-tasks-net >/dev/null 2>&1; then
  echo "Docker network cloud-tasks-net not found" >&2
  exit 1
fi

# Volume persistente para o SQLite.
docker volume create cloud-tasks-data >/dev/null

# Baixar a versão imutável antes de remover a anterior.
docker pull "$IMAGE"

# Recriar apenas a API, sem afetar o Caddy nem o volume.
docker rm -f cloud-tasks-api >/dev/null 2>&1 || true

docker run -d \
  --name cloud-tasks-api \
  --restart unless-stopped \
  --network cloud-tasks-net \
  -p "$PUBLISH" \
  -v cloud-tasks-data:/data \
  -e DB_PATH=/data/tasks.db \
  "$IMAGE"

# Verificar a saúde da nova versão.
for i in $(seq 1 20); do
  if curl --fail --silent --max-time 5 \
    "$HEALTH_URL" >/dev/null; then
    echo "Deploy succeeded: $IMAGE"
    exit 0
  fi
  sleep 2
done

echo "Deploy failed health check: $IMAGE" >&2
docker logs --tail 100 cloud-tasks-api >&2
exit 1
