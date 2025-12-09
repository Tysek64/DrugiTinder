#!/bin/bash
# how to run: test-run.sh [--skip-populate]
set -e

IMAGE_NAME="pdb-demo:latest"
CONTAINER_NAME="pdb-test-run"
PORT=5432

echo ">>> 0/3: Building image: $IMAGE_NAME..."
docker build -t pdb-demo:latest .

echo ">>> 1/3: Deploying container: $CONTAINER_NAME on port $PORT..."
./deploy.sh "$CONTAINER_NAME" "$PORT"

if ! [ "$1" = "skip-populate"]; then
  echo ">>> 2/3: Populating the database..."
  ./populate.sh "$CONTAINER_NAME"
else
  echo ">>> 2/3: Skipping DB Populating as requested"
fi

echo ">>> 3/3: Altering the database..."
./migrate.sh "$CONTAINER_NAME"

echo ">>>TEST PASSED: Successfully run the demo (assuming the .SQL scripts are correct)."
echo ">>> To clean up, run: docker rm -f $CONTAINER_NAME"
