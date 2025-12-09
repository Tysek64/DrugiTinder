#!/bin/bash
# Usage: ./deploy.sh <container_name> <host_port>

set -eou pipefail

CONTAINER_NAME=${1:-pdb-demo}
HOST_PORT=${2:-5432}

echo ">>> Running $CONTAINER_NAME on port $HOST_PORT"

docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

docker run -d \
  --name "$CONTAINER_NAME" \
  -p "$HOST_PORT":5432 \
  pdb-demo:latest

echo ">>> Waiting for the DB..."
until docker exec "$CONTAINER_NAME" pg_isready -U postgres > /dev/null 2>&1; do
  sleep 1
done
echo ">>> $CONTAINER_NAME is ready."
