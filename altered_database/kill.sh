#!/bin/bash
# Usage: ./kill.sh <container_name>
# Removes the container AND its associated anonymous volumes.

CONTAINER_NAME=${1:-pdb-demo}

echo ">>> KILLING: $CONTAINER_NAME and cleaning up volumes..."

docker rm -f -v "$CONTAINER_NAME" 2>/dev/null || true

echo ">>> CLEANUP COMPLETE: $CONTAINER_NAME is gone."
