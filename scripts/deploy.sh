
#!/usr/bin/env bash
set -Eeuo pipefail

IMAGE="${1:?Informe a imagem como argumento}"

if [[ ! "$IMAGE" =~ ^ghcr.io/jpontesdev/computacao-em-nuvem:[0-9a-f]{40}$ ]]; then
  echo "Imagem ou tag inválida" >&2
  exit 1
fi

# Configuração local da EC2.
if [[ -f "$HOME/.cloud-tasks.env" ]]; then
  source "$HOME/.cloud-tasks.env"
fi

APP_NAME="${APP_NAME:-cloud-tasks-api}"
DATA_VOLUME="${DATA_VOLUME:-cloud-tasks-data}"
DOCKER_NETWORK="${DOCKER_NETWORK:-cloud-tasks-net}"
PUBLISH="${PUBLISH:-127.0.0.1:8000:8000}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
PREVIOUS="${APP_NAME}-previous"

docker network inspect "$DOCKER_NETWORK" >/dev/null
docker volume create "$DATA_VOLUME" >/dev/null

# Baixar antes de interromper a versão atual.
docker pull "$IMAGE"

if docker container inspect "$PREVIOUS" >/dev/null 2>&1; then
  echo "Contêiner de rollback pendente: $PREVIOUS" >&2
  exit 1
fi

replaced=0
new_attempt=0

restore_on_failure() {
  local result=$?
  trap - EXIT

  if (( result != 0 )); then
    echo "Deploy falhou. Verificando rollback..." >&2

    if (( replaced )); then
      docker logs --tail 40 "$APP_NAME" >&2 || true
      docker rm -f "$APP_NAME" >/dev/null 2>&1 || true

      if docker container inspect "$PREVIOUS" >/dev/null 2>&1; then
        docker rename "$PREVIOUS" "$APP_NAME"
        docker start "$APP_NAME"

        for i in $(seq 1 15); do
          if curl -fsS --max-time 5 \
            "http://127.0.0.1:$(echo "$PUBLISH" | cut -d: -f2)/health" >/dev/null; then
            echo "Rollback concluído e validado."
            exit "$result"
          fi
          sleep 2
        done

        echo "ATENÇÃO: versão anterior restaurada, mas health check falhou." >&2
      fi
    elif (( new_attempt )); then
      docker rm -f "$APP_NAME" >/dev/null 2>&1 || true
    fi
  fi

  exit "$result"
}

trap restore_on_failure EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Preservar o contêiner anterior.
if docker container inspect "$APP_NAME" >/dev/null 2>&1; then
  curl -fsS --max-time 5 "$HEALTH_URL" >/dev/null

  docker rename "$APP_NAME" "$PREVIOUS"
  replaced=1
  docker stop -t 20 "$PREVIOUS" >/dev/null
fi

# Subir a nova versão usando o mesmo volume.
new_attempt=1
docker run -d \
  --name "$APP_NAME" \
  --restart unless-stopped \
  --network "$DOCKER_NETWORK" \
  -p "$PUBLISH" \
  -v "$DATA_VOLUME:/data" \
  -e DB_PATH=/data/tasks.db \
  "$IMAGE"

# Só aceitar a versão depois do health check.
healthy=0

for i in $(seq 1 20); do
  if curl -fsS --max-time 5 "$HEALTH_URL" >/dev/null; then
    healthy=1
    break
  fi
  sleep 2
done

if (( healthy == 0 )); then
  echo "Nova versão não passou no health check" >&2
  exit 1
fi

# Não desfazer o deploy por falha de limpeza.
trap - EXIT

if (( replaced )); then
  if ! docker rm "$PREVIOUS" >/dev/null; then
    echo "ERRO: nova versão saudável, mas limpeza do contêiner anterior falhou." >&2
    exit 1
  fi
fi

echo "Deploy concluído: $IMAGE"