#!/bin/bash
set -e

CONTAINER_NAME=${1:-pdb-demo}
MIGRATION_FILE="${2:-alter_db}.sql"

echo ">>> Migrating $CONTAINER_NAME to new schema."

cat "$MIGRATION_FILE" | docker exec -i "$CONTAINER_NAME" psql -U kbd -d pdb_demo

echo ">>> Migration Complete."
